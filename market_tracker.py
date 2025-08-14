import yfinance as yf
import pandas as pd
import json
import os
from datetime import datetime, timezone

def fetch_market_data():
    """Fetch market context data using yfinance"""
    
    # Define tickers for market context
    megacaps = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK-B']
    indices = ['SPY', 'QQQ', 'IWM', 'VTI']
    sectors = ['XLK', 'XLF', 'XLE', 'XLV', 'XLI']
    
    all_tickers = megacaps + indices + sectors
    
    try:
        # Fetch data for all tickers
        data = yf.download(all_tickers, period='2d', interval='1d', group_by='ticker')
        
        if data.empty:
            print("No data retrieved from yfinance")
            return None
            
        # Get the latest trading day
        latest_date = data.index[-1].strftime('%Y-%m-%d')
        
        market_data = {
            "date": latest_date,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "megacaps": {},
            "indices": {},
            "sectors": {},
            "market_mood": "NEUTRAL",
            "small_vs_large_cap": "NEUTRAL"
        }
        
        # Process megacap stocks
        for ticker in megacaps:
            try:
                if ticker in data.columns.levels[0]:
                    ticker_data = data[ticker]
                    if not ticker_data.empty and len(ticker_data) >= 2:
                        current_close = float(ticker_data['Close'].iloc[-1])
                        prev_close = float(ticker_data['Close'].iloc[-2])
                        daily_change = ((current_close - prev_close) / prev_close) * 100
                        volume = int(ticker_data['Volume'].iloc[-1]) if not pd.isna(ticker_data['Volume'].iloc[-1]) else 0
                        
                        market_data["megacaps"][ticker] = {
                            "price": round(current_close, 2),
                            "daily_change": round(daily_change, 2),
                            "volume": volume
                        }
            except Exception as e:
                print(f"Error processing {ticker}: {e}")
                market_data["megacaps"][ticker] = {"price": 0, "daily_change": 0, "volume": 0}
        
        # Process indices
        for ticker in indices:
            try:
                if ticker in data.columns.levels[0]:
                    ticker_data = data[ticker]
                    if not ticker_data.empty and len(ticker_data) >= 2:
                        current_close = float(ticker_data['Close'].iloc[-1])
                        prev_close = float(ticker_data['Close'].iloc[-2])
                        daily_change = ((current_close - prev_close) / prev_close) * 100
                        volume = int(ticker_data['Volume'].iloc[-1]) if not pd.isna(ticker_data['Volume'].iloc[-1]) else 0
                        
                        market_data["indices"][ticker] = {
                            "price": round(current_close, 2),
                            "daily_change": round(daily_change, 2),
                            "volume": volume
                        }
            except Exception as e:
                print(f"Error processing {ticker}: {e}")
                market_data["indices"][ticker] = {"price": 0, "daily_change": 0, "volume": 0}
        
        # Process sector ETFs
        for ticker in sectors:
            try:
                if ticker in data.columns.levels[0]:
                    ticker_data = data[ticker]
                    if not ticker_data.empty and len(ticker_data) >= 2:
                        current_close = float(ticker_data['Close'].iloc[-1])
                        prev_close = float(ticker_data['Close'].iloc[-2])
                        daily_change = ((current_close - prev_close) / prev_close) * 100
                        volume = int(ticker_data['Volume'].iloc[-1]) if not pd.isna(ticker_data['Volume'].iloc[-1]) else 0
                        
                        market_data["sectors"][ticker] = {
                            "price": round(current_close, 2),
                            "daily_change": round(daily_change, 2),
                            "volume": volume
                        }
            except Exception as e:
                print(f"Error processing {ticker}: {e}")
                market_data["sectors"][ticker] = {"price": 0, "daily_change": 0, "volume": 0}
        
        # Calculate market mood based on megacap performance
        if market_data["megacaps"]:
            avg_megacap_change = sum([stock["daily_change"] for stock in market_data["megacaps"].values()]) / len(market_data["megacaps"])
            
            if avg_megacap_change > 1.0:
                market_data["market_mood"] = "BULLISH"
            elif avg_megacap_change < -1.0:
                market_data["market_mood"] = "BEARISH"
            else:
                market_data["market_mood"] = "NEUTRAL"
        
        # Calculate small vs large cap performance
        if "SPY" in market_data["indices"] and "IWM" in market_data["indices"]:
            spy_change = market_data["indices"]["SPY"]["daily_change"]
            iwm_change = market_data["indices"]["IWM"]["daily_change"]
            
            if iwm_change > spy_change + 0.5:
                market_data["small_vs_large_cap"] = "SMALL_CAPS_OUTPERFORMING"
            elif spy_change > iwm_change + 0.5:
                market_data["small_vs_large_cap"] = "LARGE_CAPS_OUTPERFORMING"
            else:
                market_data["small_vs_large_cap"] = "NEUTRAL"
        
        return market_data
        
    except Exception as e:
        print(f"Error fetching market data: {e}")
        return None

def save_market_data(market_data):
    """Save market data to JSON files"""
    if not market_data:
        print("No market data to save")
        return False
    
    try:
        # Ensure docs directory exists
        os.makedirs("docs", exist_ok=True)
        os.makedirs("data", exist_ok=True)
        
        # Save to docs for easy access
        with open("docs/market_context.json", "w") as f:
            json.dump(market_data, f, indent=2)
        
        # Append to historical data
        history_file = "data/market_history.csv"
        
        # Create CSV header if file doesn't exist
        if not os.path.exists(history_file):
            with open(history_file, "w") as f:
                headers = ["date", "market_mood", "small_vs_large_cap"]
                
                # Add megacap columns
                for ticker in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK-B']:
                    headers.extend([f"{ticker}_price", f"{ticker}_change"])
                
                # Add index columns  
                for ticker in ['SPY', 'QQQ', 'IWM', 'VTI']:
                    headers.extend([f"{ticker}_price", f"{ticker}_change"])
                
                # Add sector columns
                for ticker in ['XLK', 'XLF', 'XLE', 'XLV', 'XLI']:
                    headers.extend([f"{ticker}_price", f"{ticker}_change"])
                
                f.write(",".join(headers) + "\n")
        
        # Append today's data
        with open(history_file, "a") as f:
            row = [
                market_data["date"],
                market_data["market_mood"],
                market_data["small_vs_large_cap"]
            ]
            
            # Add megacap data
            for ticker in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK-B']:
                if ticker in market_data["megacaps"]:
                    row.extend([
                        market_data["megacaps"][ticker]["price"],
                        market_data["megacaps"][ticker]["daily_change"]
                    ])
                else:
                    row.extend([0, 0])
            
            # Add index data
            for ticker in ['SPY', 'QQQ', 'IWM', 'VTI']:
                if ticker in market_data["indices"]:
                    row.extend([
                        market_data["indices"][ticker]["price"],
                        market_data["indices"][ticker]["daily_change"]
                    ])
                else:
                    row.extend([0, 0])
            
            # Add sector data
            for ticker in ['XLK', 'XLF', 'XLE', 'XLV', 'XLI']:
                if ticker in market_data["sectors"]:
                    row.extend([
                        market_data["sectors"][ticker]["price"],
                        market_data["sectors"][ticker]["daily_change"]
                    ])
                else:
                    row.extend([0, 0])
            
            f.write(",".join(map(str, row)) + "\n")
        
        print(f"✅ Market data saved for {market_data['date']}")
        print(f"📊 Market mood: {market_data['market_mood']}")
        print(f"📈 Small vs Large cap: {market_data['small_vs_large_cap']}")
        
        return True
        
    except Exception as e:
        print(f"Error saving market data: {e}")
        return False

def main():
    """Main function to fetch and save market context data"""
    print("🔍 Fetching market context data...")
    
    market_data = fetch_market_data()
    
    if market_data:
        success = save_market_data(market_data)
        if success:
            print("✅ Market context update completed successfully")
            return 0
        else:
            print("❌ Failed to save market data")
            return 1
    else:
        print("❌ Failed to fetch market data")
        return 1

if __name__ == "__main__":
    exit(main())
