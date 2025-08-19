#!/usr/bin/env python3

import json
import os
import sys
import requests
import csv
from datetime import datetime, timedelta
import pandas as pd

def save_json(path, data):
“”“Save data to JSON file with proper directory handling”””
directory = os.path.dirname(path)
if directory:  # Only create directory if path has one
os.makedirs(directory, exist_ok=True)
with open(path, ‘w’) as f:
json.dump(data, f, indent=2)

def load_json(path):
“”“Load data from JSON file”””
try:
with open(path, ‘r’) as f:
return json.load(f)
except FileNotFoundError:
return {}

def get_alpha_vantage_price(symbol, api_key):
“”“Get current stock price from Alpha Vantage”””
url = f”https://www.alphavantage.co/query”
params = {
‘function’: ‘GLOBAL_QUOTE’,
‘symbol’: symbol,
‘apikey’: api_key
}

```
try:
    response = requests.get(url, params=params)
    data = response.json()
    
    if 'Global Quote' in data:
        price = float(data['Global Quote']['05. price'])
        return price
    else:
        print(f"Error fetching {symbol}: {data}")
        return None
except Exception as e:
    print(f"Error fetching {symbol}: {e}")
    return None
```

def calculate_daily_changes(current_data, previous_data):
“”“Calculate daily changes for portfolio and individual positions”””
if not previous_data:
return None

```
# Calculate individual stock changes
individual_changes = {}
for symbol in current_data['prices']:
    if symbol in previous_data.get('prices', {}):
        current_price = current_data['prices'][symbol]
        prev_price = previous_data['prices'][symbol]
        current_qty = current_data['quantities'][symbol]
        
        price_change = current_price - prev_price
        price_change_pct = (price_change / prev_price) * 100 if prev_price > 0 else 0
        value_change = price_change * current_qty
        
        individual_changes[symbol] = {
            'price_change': price_change,
            'price_change_pct': price_change_pct,
            'value_change': value_change
        }

# Calculate portfolio changes
current_total = float(current_data['total_value'])
prev_total = float(previous_data.get('total_value', current_total))

total_change = current_total - prev_total
total_change_pct = (total_change / prev_total) * 100 if prev_total > 0 else 0

return {
    'individual': individual_changes,
    'portfolio': {
        'total_change': total_change,
        'total_change_pct': total_change_pct
    }
}
```

def get_previous_day_data():
“”“Get the most recent previous day’s data for comparison”””
try:
df = pd.read_csv(‘data/portfolio_history.csv’)
if len(df) >= 2:
# Get second to last row (previous day)
prev_row = df.iloc[-2]

```
        # Reconstruct the data structure
        symbols = ['GEVO', 'FEIM', 'ARQ', 'UPXI', 'SERV', 'MYOMO', 'CABA']
        prices = {}
        quantities = {}
        
        for symbol in symbols:
            if f'{symbol}_price' in prev_row and f'{symbol}_qty' in prev_row:
                if pd.notna(prev_row[f'{symbol}_price']) and prev_row[f'{symbol}_qty'] > 0:
                    prices[symbol] = prev_row[f'{symbol}_price']
                    quantities[symbol] = prev_row[f'{symbol}_qty']
        
        return {
            'prices': prices,
            'quantities': quantities,
            'total_value': str(prev_row['total_value'])
        }
except Exception as e:
    print(f"Error loading previous day data: {e}")

return None
```

def execute_trading_decisions(holdings, prices, date, cash):
“”“Execute Claude’s trading decisions from JSON file”””
claude_actions = []

```
try:
    with open('trading_decisions.json', 'r') as f:
        decisions_data = json.load(f)
    
    if not decisions_data.get('execution_queue'):
        return holdings, claude_actions, cash
    
    print("🤖 Checking Claude's trading decisions...")
    
    for order in decisions_data['execution_queue']:
        symbol = order['symbol']
        action = order['action']
        
        if action == "SELL_ALL":
            if symbol in holdings and holdings[symbol] > 0:
                shares_to_sell = holdings[symbol]
                proceeds = shares_to_sell * prices[symbol]
                cash += proceeds
                holdings[symbol] = 0
                action_msg = f"SELL ALL {symbol}: {shares_to_sell} shares @ ${prices[symbol]:.4f} = ${proceeds:.2f}"
                claude_actions.append(action_msg)
                print(f"✅ Executed: {action_msg}")
        
        elif action == "TRIM_TO":
            target_qty = order['target_quantity']
            if symbol in holdings and holdings[symbol] > target_qty:
                shares_to_sell = holdings[symbol] - target_qty
                proceeds = shares_to_sell * prices[symbol]
                cash += proceeds
                holdings[symbol] = target_qty
                action_msg = f"TRIM {symbol} to {target_qty} shares - ${proceeds:.2f} proceeds"
                claude_actions.append(action_msg)
                print(f"✅ Executed: {action_msg}")
        
        elif action == "BUY_NEW":
            target_value = order.get('target_value', 0)
            if target_value > 0 and cash >= target_value:
                if symbol in prices and prices[symbol] > 0:
                    shares_to_buy = int(target_value / prices[symbol])
                    cost = shares_to_buy * prices[symbol]
                    if cost <= cash:
                        cash -= cost
                        holdings[symbol] = holdings.get(symbol, 0) + shares_to_buy
                        action_msg = f"BUY {symbol}: {shares_to_buy} shares @ ${prices[symbol]:.4f} = ${cost:.2f}"
                        claude_actions.append(action_msg)
                        print(f"✅ Executed: {action_msg}")
        
        elif action == "HOLD":
            print(f"📊 HOLD {symbol}: {order.get('current_quantity', 0)} shares")
    
    # Mark decisions as executed
    decisions_data['claude_decisions_executed'] = True
    decisions_data['execution_date'] = date
    
    # Clear execution queue
    decisions_data['execution_queue'] = []
    
    # Save updated decisions
    save_json("trading_decisions.json", decisions_data)
    
except FileNotFoundError:
    print("No trading decisions file found")
except Exception as e:
    print(f"Error executing trading decisions: {e}")

return holdings, claude_actions, cash
```

def main():
# Configuration
SYMBOLS = [‘GEVO’, ‘FEIM’, ‘ARQ’, ‘UPXI’, ‘SERV’, ‘MYOMO’, ‘CABA’]
API_KEY = os.environ.get(‘ALPHA_VANTAGE_API_KEY’)

```
if not API_KEY:
    print("Error: ALPHA_VANTAGE_API_KEY environment variable not set")
    return 1

# Create directories
os.makedirs('data', exist_ok=True)
os.makedirs('docs', exist_ok=True)

# Load current holdings
try:
    with open('data/holdings.json', 'r') as f:
        holdings = json.load(f)
except FileNotFoundError:
    holdings = {symbol: 0 for symbol in SYMBOLS}

# Load cash
try:
    with open('data/cash.json', 'r') as f:
        cash_data = json.load(f)
        cash = cash_data.get('cash', 0.0)
except FileNotFoundError:
    cash = 0.0

# Fetch current prices
prices = {}
for symbol in SYMBOLS:
    print(f"Fetching {symbol}...")
    price = get_alpha_vantage_price(symbol, API_KEY)
    if price:
        prices[symbol] = price
        print(f"Fetched {symbol}: ${price:.4f}")
    else:
        print(f"Failed to fetch {symbol}")

# Get current date
current_date = datetime.now().strftime('%Y-%m-%d')

# Execute Claude's trading decisions
holdings, claude_actions, cash = execute_trading_decisions(holdings, prices, current_date, cash)

# Calculate portfolio values
values = {}
total_value = cash

for symbol in SYMBOLS:
    if symbol in holdings and symbol in prices and holdings[symbol] > 0:
        value = holdings[symbol] * prices[symbol]
        values[symbol] = f"{value:.2f}"
        total_value += value
    else:
        values[symbol] = "0.00"

# Get previous day data for daily changes
previous_data = get_previous_day_data()

# Current data structure
current_data = {
    'date': current_date,
    'prices': {k: v for k, v in prices.items() if k in holdings and holdings[k] > 0},
    'quantities': {k: v for k, v in holdings.items() if v > 0},
    'total_value': str(total_value)
}

# Calculate daily changes
daily_changes = calculate_daily_changes(current_data, previous_data)

# Create complete portfolio data
portfolio_data = {
    'date': current_date,
    'cash': f"{cash:.2f}",
    'total_value': f"{total_value:.2f}",
    'prices': {k: v for k, v in prices.items() if k in holdings and holdings[k] > 0},
    'quantities': {k: v for k, v in holdings.items() if v > 0},
    'values': {k: v for k, v in values.items() if k in holdings and holdings[k] > 0},
    'actions': claude_actions[0] if claude_actions else None,
    'daily_changes': daily_changes,
    'claude_decisions_executed': bool(claude_actions)
}

# Save data
save_json('docs/latest.json', portfolio_data)

# Save holdings and cash
save_json('data/holdings.json', holdings)
save_json('data/cash.json', {'cash': cash})

# Create CSV row
csv_row = {
    'date': current_date,
    'total_value': total_value,
    'cash': cash
}

# Add individual positions to CSV
for symbol in SYMBOLS:
    csv_row[f'{symbol}_price'] = prices.get(symbol, 0)
    csv_row[f'{symbol}_qty'] = holdings.get(symbol, 0)
    csv_row[f'{symbol}_value'] = float(values.get(symbol, 0))

# Save to CSV
csv_file = 'data/portfolio_history.csv'
file_exists = os.path.isfile(csv_file)

with open(csv_file, 'a', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=csv_row.keys())
    if not file_exists:
        writer.writeheader()
    writer.writerow(csv_row)

# Generate markdown report
report_lines = [
    "# Portfolio Report",
    f"**As of (latest close)**: {current_date}",
    ""
]

# Add individual positions
for symbol in SYMBOLS:
    if symbol in holdings and holdings[symbol] > 0 and symbol in prices:
        price = prices[symbol]
        qty = holdings[symbol]
        value = qty * price
        report_lines.append(f"- {symbol}: close {price:.4f}, qty {qty}, value ${value:.2f}")

# Add cash
report_lines.extend([
    "",
    f"Cash: ${cash:.2f}",
    f"**Total value**: ${total_value:.2f}"
])

# Add actions if any
if claude_actions:
    report_lines.extend([
        "",
        "## Recent Actions",
        ""
    ])
    for action in claude_actions:
        report_lines.append(f"- {action}")

# Save report
with open('docs/latest_report.md', 'w') as f:
    f.write('\n'.join(report_lines))

print(f"\n📊 Portfolio updated successfully!")
print(f"Total value: ${total_value:.2f}")
print(f"Cash: ${cash:.2f}")
if claude_actions:
    print(f"Claude actions executed: {len(claude_actions)}")

return 0
```

if **name** == “**main**”:
sys.exit(main())
