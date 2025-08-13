"""Micro-Cap Portfolio Management System
Adapted for Claude's 30-day trading challenge with GEVO, FEIM, ARQ, UPXI
"""

from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf
from typing import Any, cast
import os
import time

# File locations
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR
PORTFOLIO_CSV = DATA_DIR / "microcap_portfolio.csv"
TRADE_LOG_CSV = DATA_DIR / "microcap_trades.csv"
DECISIONS_LOG = DATA_DIR / "claude_decisions.csv"

# Challenge parameters
CHALLENGE_START = "2025-08-08"
CHALLENGE_END = "2025-09-09"
INITIAL_VALUE = 995.74

# Current positions from our experiment
INITIAL_PORTFOLIO = [
    {"ticker": "GEVO", "shares": 299, "buy_price": 1.18, "stop_loss": 0.95, "cost_basis": 352.82},
    {"ticker": "FEIM", "shares": 10, "buy_price": 29.53, "stop_loss": 26.50, "cost_basis": 295.30},
    {"ticker": "ARQ", "shares": 37, "buy_price": 6.62, "stop_loss": 5.80, "cost_basis": 244.94},
    {"ticker": "UPXI", "shares": 17, "buy_price": 6.04, "stop_loss": 4.75, "cost_basis": 102.68}
]

today = datetime.today().strftime("%Y-%m-%d")

def initialize_portfolio() -> tuple[pd.DataFrame, float]:
    """Initialize the micro-cap portfolio for the 30-day challenge."""
    portfolio_df = pd.DataFrame(INITIAL_PORTFOLIO)
    cash = 0.00  # Fully invested strategy
    
    print("🚀 Micro-Cap Portfolio Initialized")
    print(f"Start Date: {CHALLENGE_START}")
    print(f"End Date: {CHALLENGE_END}")
    print(f"Initial Value: ${INITIAL_VALUE:.2f}")
    print(f"Positions: {len(INITIAL_PORTFOLIO)}")
    
    return portfolio_df, cash

def fetch_current_prices(tickers: list[str]) -> dict[str, float]:
    """Fetch current market prices for given tickers."""
    prices = {}
    
    for ticker in tickers:
        try:
            data = yf.Ticker(ticker).history(period="1d")
            if not data.empty:
                prices[ticker] = round(float(data["Close"].iloc[-1]), 4)
            else:
                print(f"⚠️ No data available for {ticker}")
                prices[ticker] = None
        except Exception as e:
            print(f"❌ Error fetching {ticker}: {e}")
            prices[ticker] = None
    
    return prices

def calculate_portfolio_metrics(portfolio_df: pd.DataFrame, cash: float) -> dict:
    """Calculate comprehensive portfolio performance metrics."""
    tickers = portfolio_df["ticker"].tolist()
    prices = fetch_current_prices(tickers)
    
    total_value = cash
    positions = []
    
    for _, position in portfolio_df.iterrows():
        ticker = position["ticker"]
        shares = position["shares"]
        buy_price = position["buy_price"]
        stop_loss = position["stop_loss"]
        current_price = prices.get(ticker, 0)
        
        if current_price:
            position_value = shares * current_price
            pnl = (current_price - buy_price) * shares
            pnl_pct = ((current_price - buy_price) / buy_price) * 100
            stop_buffer = ((current_price - stop_loss) / stop_loss) * 100
            
            total_value += position_value
            
            positions.append({
                "ticker": ticker,
                "shares": shares,
                "buy_price": buy_price,
                "current_price": current_price,
                "position_value": position_value,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "stop_loss": stop_loss,
                "stop_buffer": stop_buffer,
                "allocation": 0  # Will calculate after total
            })
    
    # Calculate allocations
    for position in positions:
        position["allocation"] = (position["position_value"] / total_value) * 100
    
    # Overall portfolio metrics
    total_return = ((total_value - INITIAL_VALUE) / INITIAL_VALUE) * 100
    
    return {
        "date": today,
        "total_value": total_value,
        "cash": cash,
        "total_return": total_return,
        "positions": positions,
        "num_positions": len(positions)
    }

def check_stop_losses(portfolio_df: pd.DataFrame, cash: float) -> tuple[pd.DataFrame, float, list]:
    """Check for stop-loss triggers and execute automatic sells."""
    tickers = portfolio_df["ticker"].tolist()
    prices = fetch_current_prices(tickers)
    triggered_stops = []
    
    for idx, position in portfolio_df.iterrows():
        ticker = position["ticker"]
        current_price = prices.get(ticker, 0)
        stop_loss = position["stop_loss"]
        shares = position["shares"]
        
        if current_price and current_price <= stop_loss:
            # Stop loss triggered
            sell_value = shares * stop_loss
            cash += sell_value
            
            # Log the stop-loss sale
            stop_info = {
                "ticker": ticker,
                "shares": shares,
                "stop_price": stop_loss,
                "sell_value": sell_value
            }
            triggered_stops.append(stop_info)
            
            # Log trade
            log_trade("SELL", ticker, shares, stop_loss, "STOP LOSS TRIGGERED")
            
            print(f"🛑 STOP LOSS TRIGGERED: {ticker} sold {shares} shares at ${stop_loss:.2f}")
    
    # Remove stopped-out positions
    for stop in triggered_stops:
        portfolio_df = portfolio_df[portfolio_df["ticker"] != stop["ticker"]]
    
    return portfolio_df, cash, triggered_stops

def log_trade(action: str, ticker: str, shares: float, price: float, reason: str):
    """Log all trading decisions and executions."""
    trade_data = {
        "date": today,
        "action": action,
        "ticker": ticker,
        "shares": shares,
        "price": price,
        "value": shares * price,
        "reason": reason,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }
    
    # Append to trade log
    if TRADE_LOG_CSV.exists():
        df = pd.read_csv(TRADE_LOG_CSV)
        df = pd.concat([df, pd.DataFrame([trade_data])], ignore_index=True)
    else:
        df = pd.DataFrame([trade_data])
    
    df.to_csv(TRADE_LOG_CSV, index=False)

def log_claude_decision(decision_type: str, rationale: str, portfolio_value: float):
    """Log Claude's daily trading decisions."""
    decision_data = {
        "date": today,
        "decision_type": decision_type,
        "rationale": rationale,
        "portfolio_value": portfolio_value,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }
    
    if DECISIONS_LOG.exists():
        df = pd.read_csv(DECISIONS_LOG)
        df = pd.concat([df, pd.DataFrame([decision_data])], ignore_index=True)
    else:
        df = pd.DataFrame([decision_data])
    
    df.to_csv(DECISIONS_LOG, index=False)

def execute_buy_order(ticker: str, shares: float, price: float, stop_loss: float, 
                     portfolio_df: pd.DataFrame, cash: float) -> tuple[pd.DataFrame, float]:
    """Execute a buy order and update portfolio."""
    cost = shares * price
    
    if cost > cash:
        print(f"❌ Insufficient cash for {ticker} purchase: ${cost:.2f} needed, ${cash:.2f} available")
        return portfolio_df, cash
    
    # Check if position already exists
    existing = portfolio_df[portfolio_df["ticker"] == ticker]
    
    if not existing.empty:
        # Add to existing position
        idx = existing.index[0]
        current_shares = portfolio_df.at[idx, "shares"]
        current_cost_basis = portfolio_df.at[idx, "cost_basis"]
        
        new_shares = current_shares + shares
        new_cost_basis = current_cost_basis + cost
        new_avg_price = new_cost_basis / new_shares
        
        portfolio_df.at[idx, "shares"] = new_shares
        portfolio_df.at[idx, "cost_basis"] = new_cost_basis
        portfolio_df.at[idx, "buy_price"] = new_avg_price
        portfolio_df.at[idx, "stop_loss"] = stop_loss
        
    else:
        # New position
        new_position = {
            "ticker": ticker,
            "shares": shares,
            "buy_price": price,
            "stop_loss": stop_loss,
            "cost_basis": cost
        }
        portfolio_df = pd.concat([portfolio_df, pd.DataFrame([new_position])], ignore_index=True)
    
    cash -= cost
    log_trade("BUY", ticker, shares, price, "CLAUDE DECISION")
    print(f"✅ BUY ORDER EXECUTED: {shares} shares of {ticker} at ${price:.2f}")
    
    return portfolio_df, cash

def execute_sell_order(ticker: str, shares: float, price: float, 
                      portfolio_df: pd.DataFrame, cash: float) -> tuple[pd.DataFrame, float]:
    """Execute a sell order and update portfolio."""
    position = portfolio_df[portfolio_df["ticker"] == ticker]
    
    if position.empty:
        print(f"❌ Cannot sell {ticker}: Position not found")
        return portfolio_df, cash
    
    current_shares = position.iloc[0]["shares"]
    
    if shares > current_shares:
        print(f"❌ Cannot sell {shares} shares of {ticker}: Only own {current_shares}")
        return portfolio_df, cash
    
    sell_value = shares * price
    cash += sell_value
    
    if shares == current_shares:
        # Sell entire position
        portfolio_df = portfolio_df[portfolio_df["ticker"] != ticker]
    else:
        # Partial sell
        idx = position.index[0]
        remaining_shares = current_shares - shares
        buy_price = portfolio_df.at[idx, "buy_price"]
        
        portfolio_df.at[idx, "shares"] = remaining_shares
        portfolio_df.at[idx, "cost_basis"] = remaining_shares * buy_price
    
    log_trade("SELL", ticker, shares, price, "CLAUDE DECISION")
    print(f"✅ SELL ORDER EXECUTED: {shares} shares of {ticker} at ${price:.2f}")
    
    return portfolio_df, cash

def generate_daily_report(metrics: dict) -> str:
    """Generate professional daily trading report."""
    report = f"""
📊 MICRO-CAP PORTFOLIO DAILY REPORT - {metrics['date']}

💰 PORTFOLIO PERFORMANCE:
   Current Value: ${metrics['total_value']:,.2f}
   Starting Value: ${INITIAL_VALUE:,.2f}
   Total Return: {metrics['total_return']:+.2f}%
   Cash Balance: ${metrics['cash']:,.2f}

📈 POSITION ANALYSIS:
"""
    
    for pos in metrics['positions']:
        status = "🚀" if pos['pnl_pct'] > 10 else "✅" if pos['pnl_pct'] > 0 else "⚠️"
        report += f"""   {status} {pos['ticker']}: {pos['shares']} shares @ ${pos['current_price']:.2f}
      Value: ${pos['position_value']:,.2f} | P&L: {pos['pnl_pct']:+.1f}% | Stop Buffer: {pos['stop_buffer']:+.1f}%
"""

    report += f"""
🎯 RISK MANAGEMENT:
   Active Positions: {metrics['num_positions']}
   Largest Position: {max([p['allocation'] for p in metrics['positions']], default=0):.1f}%
   
📊 CHALLENGE PROGRESS:
   Days Elapsed: {(datetime.strptime(today, '%Y-%m-%d') - datetime.strptime(CHALLENGE_START, '%Y-%m-%d')).days}
   Days Remaining: {(datetime.strptime(CHALLENGE_END, '%Y-%m-%d') - datetime.strptime(today, '%Y-%m-%d')).days}
"""
    
    return report

def save_daily_snapshot(metrics: dict):
    """Save daily portfolio snapshot to CSV."""
    snapshot_data = []
    
    for pos in metrics['positions']:
        snapshot_data.append({
            "date": metrics['date'],
            "ticker": pos['ticker'],
            "shares": pos['shares'],
            "buy_price": pos['buy_price'],
            "current_price": pos['current_price'],
            "position_value": pos['position_value'],
            "pnl": pos['pnl'],
            "pnl_pct": pos['pnl_pct'],
            "stop_loss": pos['stop_loss'],
            "stop_buffer": pos['stop_buffer'],
            "allocation": pos['allocation']
        })
    
    # Add summary row
    snapshot_data.append({
        "date": metrics['date'],
        "ticker": "TOTAL",
        "shares": "",
        "buy_price": "",
        "current_price": "",
        "position_value": metrics['total_value'],
        "pnl": metrics['total_value'] - INITIAL_VALUE,
        "pnl_pct": metrics['total_return'],
        "stop_loss": "",
        "stop_buffer": "",
        "allocation": 100.0
    })
    
    df = pd.DataFrame(snapshot_data)
    
    if PORTFOLIO_CSV.exists():
        existing = pd.read_csv(PORTFOLIO_CSV)
        # Remove today's data if it exists
        existing = existing[existing["date"] != today]
        df = pd.concat([existing, df], ignore_index=True)
    
    df.to_csv(PORTFOLIO_CSV, index=False)

def run_daily_update(portfolio_df: pd.DataFrame, cash: float) -> tuple[pd.DataFrame, float]:
    """Execute daily portfolio update and generate reports."""
    print(f"🔄 Running daily update for {today}")
    
    # Check stop losses first
    portfolio_df, cash, triggered_stops = check_stop_losses(portfolio_df, cash)
    
    # Calculate current metrics
    metrics = calculate_portfolio_metrics(portfolio_df, cash)
    
    # Generate and display report
    report = generate_daily_report(metrics)
    print(report)
    
    # Save daily snapshot
    save_daily_snapshot(metrics)
    
    # Log that we completed daily analysis
    log_claude_decision("DAILY_UPDATE", f"Portfolio analyzed. Value: ${metrics['total_value']:.2f}", metrics['total_value'])
    
    return portfolio_df, cash

def main():
    """Main execution function for the micro-cap experiment."""
    print("🚀 MICRO-CAP PORTFOLIO MANAGEMENT SYSTEM")
    print("="*50)
    
    # Check if this is first run
    if not PORTFOLIO_CSV.exists():
        portfolio_df, cash = initialize_portfolio()
        print("📋 Portfolio initialized from experiment parameters")
    else:
        print("📋 Loading existing portfolio state...")
        # Load latest state from CSV
        df = pd.read_csv(PORTFOLIO_CSV)
        latest_positions = df[(df["date"] == df["date"].max()) & (df["ticker"] != "TOTAL")]
        
        if not latest_positions.empty:
            portfolio_df = latest_positions[["ticker", "shares", "buy_price", "stop_loss"]].copy()
            portfolio_df["cost_basis"] = portfolio_df["shares"] * portfolio_df["buy_price"]
        else:
            portfolio_df, cash = initialize_portfolio()
        
        # Get latest cash balance (assuming 0 for fully invested strategy)
        cash = 0.0
    
    # Run daily update
    portfolio_df, cash = run_daily_update(portfolio_df, cash)
    
    print("\n" + "="*50)
    print("💡 Daily update complete. Portfolio ready for Claude's trading decisions.")
    print(f"📁 Data saved to: {DATA_DIR}")
    print(f"📊 Portfolio CSV: {PORTFOLIO_CSV}")
    print(f"📝 Trade Log: {TRADE_LOG_CSV}")
    print(f"🤖 Decisions Log: {DECISIONS_LOG}")

if __name__ == "__main__":
    main()
