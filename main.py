#!/usr/bin/env python3

import os
import json
import requests
import csv
from datetime import datetime
import pandas as pd

def save_json(path, data):
    if os.path.dirname(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def load_json(path, default=None):
    if default is None:
        default = {}
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return default

def get_stock_price(symbol, api_key):
    # Fallback prices in case API fails
    fallback_prices = {
        'MYOMO': 1.18,
        'CABA': 1.62,
        'GEVO': 1.73,
        'FEIM': 29.01,
        'ARQ': 7.39,
        'UPXI': 7.93,
        'SERV': 9.71
    }
    
    try:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
        response = requests.get(url, timeout=30)
        data = response.json()
        
        if 'Global Quote' in data and '05. price' in data['Global Quote']:
            return float(data['Global Quote']['05. price'])
        elif 'Global Quote' in data and data['Global Quote'] == {}:
            # Try alternative ticker for MYOMO
            if symbol == 'MYOMO':
                url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=MYO&apikey={api_key}"
                response = requests.get(url, timeout=30)
                data = response.json()
                if 'Global Quote' in data and '05. price' in data['Global Quote']:
                    return float(data['Global Quote']['05. price'])
        
        print(f"API failed for {symbol}, using fallback price: ${fallback_prices.get(symbol, 0)}")
        return fallback_prices.get(symbol, 0)
        
    except Exception as e:
        print(f"Error fetching {symbol}: {e}, using fallback: ${fallback_prices.get(symbol, 0)}")
        return fallback_prices.get(symbol, 0)

def execute_trading_decisions(holdings, prices, date, cash):
    decisions_file = "trading_decisions.json"
    
    if not os.path.exists(decisions_file):
        print(f"No trading decisions file found: {decisions_file}")
        return holdings, [], cash
    
    try:
        with open(decisions_file, 'r') as f:
            decisions_data = json.load(f)
    except Exception as e:
        print(f"Error loading trading decisions: {e}")
        return holdings, [], cash
    
    if "execution_queue" not in decisions_data:
        print("No execution_queue found in trading decisions")
        return holdings, [], cash
    
    executed_actions = []
    
    for trade in decisions_data["execution_queue"]:
        if trade.get("status") != "PENDING":
            continue
            
        symbol = trade["symbol"]
        action = trade["action"]
        
        print(f"🔄 Processing {action} {symbol}...")
        
        if action == "TRIM":
            current_qty = holdings.get(symbol, 0)
            target_qty = trade["target_quantity"]
            shares_to_sell = current_qty - target_qty
            
            if shares_to_sell > 0 and current_qty > 0:
                price = prices.get(symbol, 0)
                proceeds = shares_to_sell * price
                cash += proceeds
                holdings[symbol] = target_qty
                executed_actions.append(f"✅ TRIM {symbol}: {current_qty} → {target_qty} shares, +${proceeds:.2f} cash")
                print(f"✅ Executed: TRIM {symbol}: {shares_to_sell} shares @ ${price:.4f} = ${proceeds:.2f}")
            else:
                print(f"⚠️ Cannot trim {symbol}: insufficient shares")
                
        elif action == "ADD":
            target_value = trade.get("target_purchase_value", 0)
            if target_value > 0 and cash >= target_value:
                price = prices.get(symbol, 0)
                if price > 0:
                    shares_to_buy = int(target_value / price)
                    cost = shares_to_buy * price
                    if cost <= cash:
                        cash -= cost
                        holdings[symbol] = holdings.get(symbol, 0) + shares_to_buy
                        executed_actions.append(f"✅ ADD {symbol}: +{shares_to_buy} shares @ ${price:.4f} = ${cost:.2f}")
                        print(f"✅ Executed: ADD {symbol}: {shares_to_buy} shares @ ${price:.4f} = ${cost:.2f}")
                    else:
                        print(f"⚠️ Insufficient cash for {symbol}: need ${cost:.2f}, have ${cash:.2f}")
                else:
                    print(f"⚠️ No price available for {symbol}")
            else:
                print(f"⚠️ Cannot add {symbol}: insufficient cash (${cash:.2f}) for target ${target_value:.2f}")
        
        elif action in ["SELL_ALL", "BUY_NEW"]:
            # Handle legacy trade formats
            if action == "SELL_ALL":
                current_qty = holdings.get(symbol, 0)
                if current_qty > 0:
                    price = prices.get(symbol, 0)
                    proceeds = current_qty * price
                    cash += proceeds
                    holdings[symbol] = 0
                    executed_actions.append(f"✅ SELL ALL {symbol}: {current_qty} shares @ ${price:.4f} = ${proceeds:.2f}")
                    print(f"✅ Executed: SELL ALL {symbol}: {current_qty} shares @ ${price:.4f} = ${proceeds:.2f}")
                    
            elif action == "BUY_NEW":
                target_value = trade.get("target_value", 0)
                if target_value > 0 and cash >= target_value:
                    price = prices.get(symbol, 0)
                    if price > 0:
                        shares_to_buy = int(target_value / price)
                        cost = shares_to_buy * price
                        if cost <= cash:
                            cash -= cost
                            holdings[symbol] = shares_to_buy
                            executed_actions.append(f"✅ BUY NEW {symbol}: {shares_to_buy} shares @ ${price:.4f} = ${cost:.2f}")
                            print(f"✅ Executed: BUY NEW {symbol}: {shares_to_buy} shares @ ${price:.4f} = ${cost:.2f}")
    
    # Mark all trades as completed by clearing the file
    try:
        decisions_data["execution_queue"] = []
        decisions_data["last_executed"] = datetime.now().isoformat()
        save_json(decisions_file, decisions_data)
        print("📋 Trading decisions cleared after execution")
    except Exception as e:
        print(f"Error clearing trading decisions: {e}")
    
    return holdings, executed_actions, cash

def main():
    # Get API key
    api_key = os.environ.get('ALPHAVANTAGE_API_KEY')
    if not api_key:
        print("Error: ALPHAVANTAGE_API_KEY environment variable not set")
        return 1
    
    print(f"✅ Using API key: {api_key[:10]}...")
    
    # Initialize or load existing portfolio
    holdings = load_json("data/holdings.json", {
        "GEVO": 0, "FEIM": 0, "ARQ": 37, "UPXI": 17, "SERV": 26, "MYOMO": 209, "CABA": 112
    })
    
    cash = load_json("data/cash.json", {"cash": 99.04}).get("cash", 99.04)
    
    print(f"📊 Loading existing holdings and cash...")
    print(f"✅ Loaded holdings: {holdings}")
    print(f"✅ Loaded cash: ${cash:.2f}")
    
    # Define all symbols
    symbols = ["GEVO", "FEIM", "ARQ", "UPXI", "SERV", "MYOMO", "CABA"]
    
    # Fetch current prices
    print(f"📈 Fetching current stock prices...")
    prices = {}
    for symbol in symbols:
        print(f"Fetching {symbol}...")
        price = get_stock_price(symbol, api_key)
        if price:
            prices[symbol] = price
            print(f"Fetched {symbol}: ${price:.4f}")
        else:
            print(f"Failed to fetch {symbol}")
    
    if not prices:
        print("Error: No prices fetched successfully")
        return 1
    
    # Get current date
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Execute trading decisions
    print(f"🔄 Processing trading decisions...")
    print(f"🤖 Checking Claude's trading decisions...")
    holdings, claude_actions, cash = execute_trading_decisions(holdings, prices, current_date, cash)
    
    # Calculate portfolio values
    print(f"💰 Calculating portfolio values...")
    values = {}
    quantities = {}
    total_value = cash
    
    for symbol in symbols:
        qty = holdings.get(symbol, 0)
        price = prices.get(symbol, 0)
        value = qty * price
        
        if qty > 0:  # Only include positions actually held
            quantities[symbol] = qty
            values[symbol] = f"{value:.2f}"
            total_value += value
            print(f"Holdings after trading: {symbol}: {qty} shares @ ${price:.4f} = ${value:.2f}")
    
    print(f"Cash after trading: ${cash:.2f}")
    print(f"💼 Total portfolio value: ${total_value:.2f}")
    
    # Load previous day data for daily changes
    previous_data = {}
    daily_changes = {"individual": {}, "portfolio": {"total_change": 0, "total_change_pct": 0}}
    
    try:
        previous_data = load_json("docs/latest.json")
        if previous_data.get("total_value"):
            prev_total = float(previous_data["total_value"])
            total_change = total_value - prev_total
            total_change_pct = (total_change / prev_total) * 100
            daily_changes["portfolio"] = {
                "total_change": total_change,
                "total_change_pct": total_change_pct
            }
            print(f"Daily portfolio change: ${total_change:.2f} ({total_change_pct:.2f}%)")
        
        # Calculate individual stock changes
        for symbol in quantities:
            prev_price = previous_data.get("prices", {}).get(symbol, prices[symbol])
            curr_price = prices[symbol]
            price_change = curr_price - prev_price
            price_change_pct = (price_change / prev_price) * 100 if prev_price > 0 else 0
            value_change = quantities[symbol] * price_change
            
            daily_changes["individual"][symbol] = {
                "price_change": price_change,
                "price_change_pct": price_change_pct,
                "value_change": value_change
            }
            
    except Exception as e:
        print(f"Error loading previous day data: {e}")
        print("Continuing without daily change calculation...")
    
    # Prepare data for JSON output
    json_data = {
        "date": current_date,
        "cash": f"{cash:.2f}",
        "total_value": f"{total_value:.2f}",
        "prices": {symbol: prices[symbol] for symbol in symbols if symbol in prices},
        "quantities": quantities,
        "values": values,
        "actions": "; ".join(claude_actions) if claude_actions else "No trades executed",
        "daily_changes": daily_changes,
        "claude_decisions_executed": len(claude_actions) > 0
    }
    
    # Save all data
    os.makedirs("data", exist_ok=True)
    os.makedirs("docs", exist_ok=True)
    
    save_json("data/holdings.json", holdings)
    save_json("data/cash.json", {"cash": cash})
    save_json("docs/latest.json", json_data)
    
    # Create markdown report
    report_lines = [
        "# Portfolio Report",
        f"**As of (latest close)**: {current_date}",
        ""
    ]
    
    for symbol in quantities:
        qty = quantities[symbol]
        price = prices[symbol]
        value = float(values[symbol])
        report_lines.append(f"- {symbol}: close {price:.4f}, qty {qty}, value ${value:.2f}")
    
    if cash > 0:
        report_lines.append(f"\nCash: ${cash:.2f}")
    
    report_lines.append(f"**Total value**: ${total_value:.2f}")
    
    if claude_actions:
        report_lines.append(f"\n**Executed trades**: {'; '.join(claude_actions)}")
    
    with open("docs/latest_report.md", "w") as f:
        f.write("\n".join(report_lines))
    
    print(f"📊 Portfolio updated successfully!")
    print(f"Total value: ${total_value:.2f}")
    print(f"Cash: ${cash:.2f}")
    
    if claude_actions:
        print("✅ Executed trades:")
        for action in claude_actions:
            print(f"  {action}")
    
    return 0

if __name__ == "__main__":
    exit(main())
