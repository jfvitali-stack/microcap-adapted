"""Portfolio monitoring and health check script."""

import json
import csv
import os
from datetime import datetime, timedelta
from pathlib import Path
import requests

def check_data_freshness():
    """Check if portfolio data is up to date."""
    issues = []
    
    # Check latest.json
    if os.path.exists("docs/latest.json"):
        with open("docs/latest.json", "r") as f:
            data = json.load(f)
            last_date = datetime.strptime(data["date"], "%Y-%m-%d")
            days_old = (datetime.now() - last_date).days
            
            if days_old > 3:
                issues.append(f"Portfolio data is {days_old} days old")
            
            # Check for null prices
            null_prices = [symbol for symbol, price in data["prices"].items() if price is None]
            if null_prices:
                issues.append(f"Missing prices for: {', '.join(null_prices)}")
    else:
        issues.append("Missing latest.json file")
    
    return issues

def check_stop_losses():
    """Monitor positions approaching stop-loss levels."""
    warnings = []
    
    if os.path.exists("docs/latest.json"):
        with open("docs/latest.json", "r") as f:
            data = json.load(f)
            
        stops = {"GEVO": 0.95, "FEIM": 26.50, "ARQ": 5.80, "UPXI": 4.75}
        
        for symbol, stop_price in stops.items():
            current_price = data["prices"].get(symbol)
            if current_price:
                buffer = ((current_price - stop_price) / stop_price) * 100
                
                if buffer < 10:
                    warnings.append(f"{symbol}: Only {buffer:.1f}% above stop-loss")
                elif buffer < 20:
                    warnings.append(f"{symbol}: {buffer:.1f}% above stop-loss (watch closely)")
    
    return warnings

def check_portfolio_health():
    """Comprehensive portfolio health check."""
    print("🔍 PORTFOLIO HEALTH CHECK")
    print("=" * 40)
    
    # Data freshness
    issues = check_data_freshness()
    if issues:
        print("❌ DATA ISSUES:")
        for issue in issues:
            print(f"   • {issue}")
    else:
        print("✅ Data is fresh and complete")
    
    # Stop-loss monitoring
    warnings = check_stop_losses()
    if warnings:
        print("\n⚠️  STOP-LOSS WARNINGS:")
        for warning in warnings:
            print(f"   • {warning}")
    else:
        print("✅ All positions have healthy stop-loss buffers")
    
    # Portfolio performance summary
    if os.path.exists("docs/latest.json"):
        with open("docs/latest.json", "r") as f:
            data = json.load(f)
            
        total_value = float(data.get("total_value", 0))
        initial_value = 995.74
        return_pct = ((total_value - initial_value) / initial_value) * 100
        
        print(f"\n📊 CURRENT PERFORMANCE:")
        print(f"   • Portfolio Value: ${total_value:,.2f}")
        print(f"   • Total Return: {return_pct:+.2f}%")
        print(f"   • Last Update: {data['date']}")
    
    print("\n" + "=" * 40)

def validate_api_connection():
    """Test API connectivity."""
    api_key = os.environ.get("ALPHAVANTAGE_API_KEY")
    
    if not api_key:
        print("❌ No API key found")
        return False
    
    try:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=GEVO&apikey={api_key}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if "Time Series (Daily)" in data:
            print("✅ API connection successful")
            return True
        else:
            print(f"❌ API error: {data}")
            return False
            
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False

def main():
    """Run all monitoring checks."""
    print("🚀 MICRO-CAP PORTFOLIO MONITOR")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()
    
    # API check
    validate_api_connection()
    print()
    
    # Portfolio health
    check_portfolio_health()

if __name__ == "__main__":
    main()
