import os, json, csv, sys, time
from datetime import datetime
from dateutil import tz
import requests

ALPHA_URL = "https://www.alphavantage.co/query"
API_KEY = os.environ.get("ALPHAVANTAGE_API_KEY")

def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def fetch_daily_close(symbol, use_adjusted=False):
    params = {
        "function": "TIME_SERIES_DAILY_ADJUSTED" if use_adjusted else "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": API_KEY
    }
    r = requests.get(ALPHA_URL, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    key = "Time Series (Daily)"
    if key not in data:
        raise RuntimeError(f"Alpha Vantage error for {symbol}: {data}")
    ts = data[key]
    latest_date = sorted(ts.keys())[-1]
    close_key = "4. close" if not use_adjusted else "5. adjusted close"
    close = float(ts[latest_date][close_key])
    return latest_date, close

def check_trading_decisions():
    """Load Claude's trading decisions"""
    decisions_path = "trading_decisions.json"
    
    if not os.path.exists(decisions_path):
        return []
    
    try:
        with open(decisions_path, 'r', encoding='utf-8') as f:
            decisions = json.load(f)
        return decisions.get('execution_queue', [])
    except Exception as e:
        print(f"Error reading trading decisions: {e}")
        return []

def execute_trading_decisions(holdings, latest_prices, latest_date, cash):
    """Execute Claude's trading decisions automatically"""
    decisions = check_trading_decisions()
    executed_actions = []
    total_proceeds = 0
    
    if not decisions:
        return holdings, executed_actions, cash
    
    print("🤖 Checking Claude's trading decisions...")
    
    for decision in decisions:
        symbol = decision.get('symbol')
        action = decision.get('action')
        target_qty = decision.get('target_quantity', 0)
        current_qty = holdings.get(symbol, 0)
        
        if symbol not in latest_prices or latest_prices[symbol] is None:
            continue
            
        price = latest_prices[symbol]
        
        if action == "SELL_ALL":
            if current_qty > 0:
                proceeds = current_qty * price
                cash += proceeds
                total_proceeds += proceeds
                holdings[symbol] = 0
                executed_actions.append(f"🤖 CLAUDE SELL ALL {symbol}: {current_qty} shares @ ${price:.4f} = ${proceeds:.2f}")
                print(f"✅ Executed: SELL ALL {symbol} - ${proceeds:.2f} proceeds")
        
        elif action == "SELL_PARTIAL":
            if current_qty > target_qty:
                sell_qty = current_qty - target_qty
                proceeds = sell_qty * price
                cash += proceeds
                total_proceeds += proceeds
                holdings[symbol] = target_qty
                executed_actions.append(f"🤖 CLAUDE SELL {symbol}: {sell_qty} shares @ ${price:.4f} = ${proceeds:.2f}")
                print(f"✅ Executed: SELL {sell_qty} {symbol} shares - ${proceeds:.2f} proceeds")
        
        elif action == "TRIM_TO":
            if current_qty > target_qty:
                trim_qty = current_qty - target_qty
                proceeds = trim_qty * price
                cash += proceeds
                total_proceeds += proceeds
                holdings[symbol] = target_qty
                executed_actions.append(f"🤖 CLAUDE TRIM {symbol}: {trim_qty} shares @ ${price:.4f} = ${proceeds:.2f}")
                print(f"✅ Executed: TRIM {symbol} to {target_qty} shares - ${proceeds:.2f} proceeds")
        
        elif action == "HOLD":
            # No action needed, just log
            print(f"📊 HOLD {symbol}: {current_qty} shares")
    
    # Archive executed decisions
    if executed_actions:
        executed_log = {
            "execution_date": latest_date,
            "total_proceeds": total_proceeds,
            "executed_actions": executed_actions,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save execution log
        log_path = f"logs/claude_executions_{latest_date}.json"
        os.makedirs("logs", exist_ok=True)
        save_json(log_path, executed_log)
        
        # Clear execution queue
        decisions_data = load_json("trading_decisions.json")
        decisions_data["execution_queue"] = []
        decisions_data["last_execution"] = latest_date
        decisions_data["last_execution_summary"] = f"Executed {len(executed_actions)} orders, ${total_proceeds:.2f} proceeds"
        save_json("trading_decisions.json", decisions_data)
        
        print(f"💰 Total proceeds from Claude's decisions: ${total_proceeds:.2f}")
    else:
        print("📋 No trading actions to execute")
    
    return holdings, executed_actions, cash

def get_previous_day_data():
    """Load previous day's portfolio data for comparison"""
    csv_path = "data/portfolio_history.csv"
    if not os.path.exists(csv_path):
        return None
    
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
            if len(rows) >= 1:
                return rows[-1]
    except:
        pass
    return None

def calculate_daily_changes(current_prices, current_total, previous_data, symbols):
    """Calculate daily changes for each position and total portfolio"""
    changes = {}
    
    if not previous_data:
        for symbol in symbols:
            changes[symbol] = {'price_change': 0.0, 'price_change_pct': 0.0, 'value_change': 0.0}
        changes['portfolio'] = {'total_change': 0.0, 'total_change_pct': 0.0}
        return changes
    
    for symbol in symbols:
        if symbol in current_prices and current_prices[symbol] is not None:
            current_price = current_prices[symbol]
            prev_price_key = f"{symbol}_close"
            
            if prev_price_key in previous_data and previous_data[prev_price_key]:
                try:
                    prev_price = float(previous_data[prev_price_key])
                    price_change = current_price - prev_price
                    price_change_pct = (price_change / prev_price) * 100 if prev_price != 0 else 0
                    
                    qty_key = f"{symbol}_qty"
                    quantity = int(previous_data.get(qty_key, 0)) if qty_key in previous_data else 0
                    value_change = price_change * quantity
                    
                    changes[symbol] = {
                        'price_change': price_change,
                        'price_change_pct': price_change_pct,
                        'value_change': value_change
                    }
                except (ValueError, TypeError):
                    changes[symbol] = {'price_change': 0.0, 'price_change_pct': 0.0, 'value_change': 0.0}
            else:
                changes[symbol] = {'price_change': 0.0, 'price_change_pct': 0.0, 'value_change': 0.0}
        else:
            changes[symbol] = {'price_change': 0.0, 'price_change_pct': 0.0, 'value_change': 0.0}
    
    try:
        prev_total = float(previous_data.get('total_value', 0))
        total_change = current_total - prev_total
        total_change_pct = (total_change / prev_total) * 100 if prev_total != 0 else 0
        changes['portfolio'] = {'total_change': total_change, 'total_change_pct': total_change_pct}
    except (ValueError, TypeError):
        changes['portfolio'] = {'total_change': 0.0, 'total_change_pct': 0.0}
    
    return changes

def main():
    if not API_KEY:
        print("Missing ALPHAVANTAGE_API_KEY")
        sys.exit(1)

    cfg = load_json("config.json")
    
    # Initialize state file if it doesn't exist
    state_path = "state/portfolio_state.json"
    if not os.path.exists(state_path):
        os.makedirs("state", exist_ok=True)
        initial_state = {
            "cash": 0,
            "holdings": {"GEVO": 299, "FEIM": 10, "ARQ": 37, "UPXI": 17},
            "last_valuation_date": "2025-08-08"
        }
        save_json(state_path, initial_state)
    
    state = load_json(state_path)
    symbols = cfg["symbols"]
    use_adj = cfg.get("use_adjusted_close", False)
    stops = cfg["stops"]
    holdings = state["holdings"]
    cash = float(state["cash"])

    previous_data = get_previous_day_data()
    latest_prices = {}
    latest_date = None

    # Fetch prices with rate limiting
    for i, sym in enumerate(symbols):
        try:
            d, px = fetch_daily_close(sym, use_adjusted=use_adj)
            latest_prices[sym] = px
            latest_date = d if latest_date is None else max(latest_date, d)
            print(f"Fetched {sym}: ${px:.4f}")
        except Exception as e:
            print(f"Error fetching {sym}: {e}")
            latest_prices[sym] = None
            
        if i < len(symbols) - 1:
            time.sleep(15)

    if latest_date is None:
        print("No valid data fetched")
        sys.exit(1)

    # 🤖 EXECUTE CLAUDE'S TRADING DECISIONS FIRST
    holdings, claude_actions, cash = execute_trading_decisions(holdings, latest_prices, latest_date, cash)

    # Apply stop-loss rules
    stop_actions = []
    for sym in symbols:
        if sym not in latest_prices or latest_prices[sym] is None:
            continue
            
        stop = float(stops[sym])
        if holdings.get(sym, 0) > 0 and latest_prices[sym] <= stop:
            qty = int(holdings[sym])
            proceeds = qty * latest_prices[sym]
            cash += proceeds
            holdings[sym] = 0
            stop_actions.append(f"🛑 STOP LOSS {sym} {qty} @ {latest_prices[sym]:.4f}")

    # Combine all actions
    actions = claude_actions + stop_actions

    # Compute portfolio value
    position_values = {}
    total_value = float(cash)
    
    for sym in symbols:
        if sym in latest_prices and latest_prices[sym] is not None:
            position_values[sym] = int(holdings.get(sym, 0)) * latest_prices[sym]
            total_value += position_values[sym]
        else:
            position_values[sym] = 0

    # Calculate daily changes
    daily_changes = calculate_daily_changes(latest_prices, total_value, previous_data, symbols)

    # Save to CSV with enhanced data
    os.makedirs("data", exist_ok=True)
    csv_path = "data/portfolio_history.csv"
    exists = os.path.exists(csv_path)
    
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not exists:
            header = ["date","cash"] + [f"{s}_close" for s in symbols] + [f"{s}_qty" for s in symbols] + [f"{s}_value" for s in symbols] + ["total_value","actions"]
            header += [f"{s}_price_change" for s in symbols] + [f"{s}_price_change_pct" for s in symbols] + [f"{s}_value_change" for s in symbols]
            header += ["portfolio_change", "portfolio_change_pct"]
            w.writerow(header)
        
        row_data = [latest_date, f"{cash:.2f}"]
        
        for s in symbols:
            if s in latest_prices and latest_prices[s] is not None:
                row_data.append(f"{latest_prices[s]:.4f}")
            else:
                row_data.append("")
        
        for s in symbols:
            row_data.append(int(holdings.get(s, 0)))
        
        for s in symbols:
            row_data.append(f"{position_values[s]:.2f}")
        
        row_data.extend([f"{total_value:.2f}", "; ".join(actions)])
        
        for s in symbols:
            row_data.append(f"{daily_changes[s]['price_change']:.4f}")
        for s in symbols:
            row_data.append(f"{daily_changes[s]['price_change_pct']:.2f}")
        for s in symbols:
            row_data.append(f"{daily_changes[s]['value_change']:.2f}")
        
        row_data.append(f"{daily_changes['portfolio']['total_change']:.2f}")
        row_data.append(f"{daily_changes['portfolio']['total_change_pct']:.2f}")
        
        w.writerow(row_data)

    # Update state
    state["cash"] = round(cash, 2)
    state["holdings"] = holdings
    state["last_valuation_date"] = latest_date
    save_json(state_path, state)

    # Enhanced JSON output
    latest_json = {
        "date": latest_date,
        "cash": f"{cash:.2f}",
        "total_value": f"{total_value:.2f}" if total_value > 0 else None,
        "prices": {sym: latest_prices.get(sym) for sym in symbols},
        "quantities": {sym: holdings.get(sym, 0) for sym in symbols},
        "values": {sym: f"{position_values[sym]:.2f}" for sym in symbols},
        "actions": "; ".join(actions) if actions else None,
        "daily_changes": {
            "individual": {sym: daily_changes[sym] for sym in symbols},
            "portfolio": daily_changes['portfolio']
        },
        "claude_decisions_executed": len(claude_actions) > 0
    }
    
    os.makedirs("docs", exist_ok=True)
    save_json("docs/latest.json", latest_json)

    # Enhanced reports
    os.makedirs("reports", exist_ok=True)
    with open("reports/latest_report.md", "w", encoding="utf-8") as f:
        f.write(f"# Portfolio Report\n")
        f.write(f"**As of (latest close)**: {latest_date}\n\n")
        
        if claude_actions:
            f.write(f"**🤖 Claude's Trading Actions:**\n")
            for action in claude_actions:
                f.write(f"- {action}\n")
            f.write(f"\n")
        
        if previous_data:
            portfolio_change = daily_changes['portfolio']['total_change']
            portfolio_change_pct = daily_changes['portfolio']['total_change_pct']
            f.write(f"**Portfolio Performance:**\n")
            f.write(f"- Current Value: ${total_value:.2f}\n")
            f.write(f"- Daily Change: ${portfolio_change:+.2f} ({portfolio_change_pct:+.2f}%)\n\n")
        
        f.write(f"**Individual Positions:**\n")
        for sym in symbols:
            price = latest_prices.get(sym, 0)
            qty = holdings.get(sym, 0)
            value = position_values.get(sym, 0)
            
            if price:
                change_info = ""
                if sym in daily_changes:
                    price_chg = daily_changes[sym]['price_change']
                    price_chg_pct = daily_changes[sym]['price_change_pct']
                    value_chg = daily_changes[sym]['value_change']
                    change_info = f" (${price_chg:+.4f}, {price_chg_pct:+.2f}%, ${value_chg:+.2f})"
                
                f.write(f"- {sym}: ${price:.4f}, qty {qty}, value ${value:.2f}{change_info}\n")
            else:
                f.write(f"- {sym}: NO DATA, qty {qty}\n")
        
        f.write(f"\nCash: ${cash:.2f}\n")
        f.write(f"**Total value**: ${total_value:.2f}\n")
        if actions:
            f.write(f"\n**Actions**: {', '.join(actions)}\n")

    # Copy to docs
    with open("docs/latest_report.md", "w", encoding="utf-8") as f:
        f.write(f"# Portfolio Report\n")
        f.write(f"**As of (latest close)**: {latest_date}\n\n")
        
        for sym in symbols:
            price = latest_prices.get(sym, 0)
            qty = holdings.get(sym, 0)
            value = position_values.get(sym, 0)
            if price:
                f.write(f"- {sym}: close {price:.4f}, qty {qty}, value ${value:.2f}\n")
            else:
                f.write(f"- {sym}: NO DATA, qty {qty}\n")
        f.write(f"\nCash: ${cash:.2f}\n")
        f.write(f"**Total value**: ${total_value:.2f}\n")
        if actions:
            f.write(f"\n**Actions**: {', '.join(actions)}\n")

    print(f"✅ Portfolio updated: {latest_date} total ${total_value:.2f}")
    if previous_data:
        portfolio_change = daily_changes['portfolio']['total_change']
        portfolio_change_pct = daily_changes['portfolio']['total_change_pct']
        print(f"📊 Daily change: ${portfolio_change:+.2f} ({portfolio_change_pct:+.2f}%)")
    
    if claude_actions:
        print(f"🤖 Executed {len(claude_actions)} Claude trading decisions")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
