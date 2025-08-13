import csv
import os
from datetime import datetime

def backfill_daily_changes():
    """
    Backfill daily changes for existing portfolio history data
    """
    csv_path = "data/portfolio_history.csv"
    backup_path = "data/portfolio_history_backup.csv"
    
    if not os.path.exists(csv_path):
        print("No existing portfolio history found")
        return
    
    # Read existing data
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if len(rows) < 2:
        print("Need at least 2 rows of data to calculate changes")
        return
    
    # Create backup
    import shutil
    shutil.copy2(csv_path, backup_path)
    print(f"Backup created: {backup_path}")
    
    # Define symbols
    symbols = ['GEVO', 'FEIM', 'ARQ', 'UPXI']
    
    # Process each row and calculate changes
    enhanced_rows = []
    
    for i, row in enumerate(rows):
        enhanced_row = row.copy()
        
        if i == 0:
            # First row - no previous data, set changes to 0
            for sym in symbols:
                enhanced_row[f'{sym}_price_change'] = '0.0000'
                enhanced_row[f'{sym}_price_change_pct'] = '0.00'
                enhanced_row[f'{sym}_value_change'] = '0.00'
            enhanced_row['portfolio_change'] = '0.00'
            enhanced_row['portfolio_change_pct'] = '0.00'
        else:
            # Calculate changes vs previous row
            prev_row = rows[i-1]
            
            # Individual stock changes
            for sym in symbols:
                try:
                    current_price = float(row[f'{sym}_close']) if row[f'{sym}_close'] else 0
                    prev_price = float(prev_row[f'{sym}_close']) if prev_row[f'{sym}_close'] else 0
                    quantity = int(row[f'{sym}_qty']) if row[f'{sym}_qty'] else 0
                    
                    if prev_price > 0:
                        price_change = current_price - prev_price
                        price_change_pct = (price_change / prev_price) * 100
                        value_change = price_change * quantity
                    else:
                        price_change = 0
                        price_change_pct = 0
                        value_change = 0
                    
                    enhanced_row[f'{sym}_price_change'] = f'{price_change:.4f}'
                    enhanced_row[f'{sym}_price_change_pct'] = f'{price_change_pct:.2f}'
                    enhanced_row[f'{sym}_value_change'] = f'{value_change:.2f}'
                    
                except (ValueError, KeyError):
                    enhanced_row[f'{sym}_price_change'] = '0.0000'
                    enhanced_row[f'{sym}_price_change_pct'] = '0.00'
                    enhanced_row[f'{sym}_value_change'] = '0.00'
            
            # Portfolio changes
            try:
                current_total = float(row['total_value'])
                prev_total = float(prev_row['total_value'])
                
                portfolio_change = current_total - prev_total
                portfolio_change_pct = (portfolio_change / prev_total) * 100 if prev_total > 0 else 0
                
                enhanced_row['portfolio_change'] = f'{portfolio_change:.2f}'
                enhanced_row['portfolio_change_pct'] = f'{portfolio_change_pct:.2f}'
                
            except (ValueError, KeyError):
                enhanced_row['portfolio_change'] = '0.00'
                enhanced_row['portfolio_change_pct'] = '0.00'
        
        enhanced_rows.append(enhanced_row)
    
    # Write enhanced data with new header
    new_header = list(rows[0].keys()) if rows else []
    
    # Add new columns if they don't exist
    for sym in symbols:
        if f'{sym}_price_change' not in new_header:
            new_header.append(f'{sym}_price_change')
    for sym in symbols:
        if f'{sym}_price_change_pct' not in new_header:
            new_header.append(f'{sym}_price_change_pct')
    for sym in symbols:
        if f'{sym}_value_change' not in new_header:
            new_header.append(f'{sym}_value_change')
    
    if 'portfolio_change' not in new_header:
        new_header.append('portfolio_change')
    if 'portfolio_change_pct' not in new_header:
        new_header.append('portfolio_change_pct')
    
    # Write the enhanced CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=new_header)
        writer.writeheader()
        writer.writerows(enhanced_rows)
    
    print(f"✅ Successfully backfilled {len(enhanced_rows)} rows with daily changes")
    print(f"📊 Added columns: price_change, price_change_pct, value_change for each stock")
    print(f"📈 Added portfolio-level daily changes")
    print(f"🔄 Original data backed up to: {backup_path}")

if __name__ == "__main__":
    backfill_daily_changes()
