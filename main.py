import os, json, csv, sys, time
from datetime import datetime
from dateutil import tz
import requests

ALPHA_URL = "https://www.alphavantage.co/query"
API_KEY = os.environ.get("ALPHAVANTAGE_API_KEY")

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

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
    # Latest trading day (sorted desc)
    latest_date = sorted(ts.keys())[-1]
    close_key = "4. close" if not use_adjusted else "5. adjusted close"
    close = float(ts[latest_date][close_key])
    return latest_date, close

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
            "holdings": {
                "GEVO": 299,
                "FEIM": 10,
                "ARQ": 37,
                "UPXI": 17
            },
            "last_valuation_date": "2025-08-08"
        }
        save_json(state_path, initial_state)
    
    state = load_json(state_path)
    symbols = cfg["symbols"]
    use_adj = cfg.get("use_adjusted_close", False)
    stops = cfg["stops"]
    holdings = state["holdings"]
    cash = float(state["cash"])

    latest_prices = {}
    latest_date = None

    # Rate limiting: 5 req/min free plan
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
            time.sleep(15)  # Rate limiting

    # Only proceed if we have a valid date
    if latest_date is None:
        print("No valid data fetched")
        sys.exit(1)

    # Apply stop-loss on a closing basis
    actions = []
    for sym in symbols:
        if sym not in latest_prices or latest_prices[sym] is None:
            continue
            
        stop = float(stops[sym])
        if holdings.get(sym, 0) > 0 and latest_prices[sym] <= stop:
            qty = int(holdings[sym])
            proceed = qty * latest_prices[sym]
            cash += proceed
            holdings[sym] = 0
            actions.append(f"STOP SELL {sym} {qty} @ {latest_prices[sym]:.4f}")

    # Compute portfolio value
    position_values = {}
    total_value = float(cash)
    
    for sym in symbols:
        if sym in latest_prices and latest_prices[sym] is not None:
            position_values[sym] = int(holdings.get(sym, 0)) * latest_prices[sym]
            total_value += position_values[sym]
        else:
            position_values[sym] = 0

    # CSV append
    os.makedirs("data", exist_ok=True)
    csv_path = "data/portfolio_history.csv"
    exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(["date","cash"] + [f"{s}_close" for s in symbols] + [f"{s}_qty" for s in symbols] + [f"{s}_value" for s in symbols] + ["total_value","actions"])
        
        # Build row data
        row_data = [latest_date, f"{cash:.2f}"]
        
        # Add prices
        for s in symbols:
            if s in latest_prices and latest_prices[s] is not None:
                row_data.append(f"{latest_prices[s]:.4f}")
            else:
                row_data.append("")
        
        # Add quantities
        for s in symbols:
            row_data.append(int(holdings.get(s, 0)))
        
        # Add values
        for s in symbols:
            row_data.append(f"{position_values[s]:.2f}")
        
        # Add totals
        row_data.extend([f"{total_value:.2f}", "; ".join(actions)])
        
        w.writerow(row_data)

    # Persist state
    state["cash"] = round(cash, 2)
    state["holdings"] = holdings
    state["last_valuation_date"] = latest_date
    save_json(state_path, state)

    # Create latest JSON for reporting system
    latest_json = {
        "date": latest_date,
        "cash": f"{cash:.2f}",
        "total_value": f"{total_value:.2f}" if total_value > 0 else None,
        "prices": {sym: latest_prices.get(sym) for sym in symbols},
        "quantities": {sym: holdings.get(sym, 0) for sym in symbols},
        "values": {sym: f"{position_values[sym]:.2f}" for sym in symbols},
        "actions": "; ".join(actions) if actions else None
    }
    
    os.makedirs("docs", exist_ok=True)
    save_json("docs/latest.json", latest_json)

    # Report
    os.makedirs("reports", exist_ok=True)
    with open("reports/latest_report.md", "w", encoding="utf-8") as f:
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

    # Copy to docs for easy access
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

    print(f"OK {latest_date} total ${total_value:.2f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
