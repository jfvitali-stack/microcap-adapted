# 🚀 Micro-Cap Portfolio Challenge

**30-Day Automated Trading Experiment | Target: 300-500% Returns**

## 📊 Portfolio Overview

This repository tracks a concentrated micro-cap investment strategy focused on:
- **GEVO** (299 shares) - Sustainable Aviation Fuel
- **FEIM** (10 shares) - Defense & Aerospace Electronics  
- **ARQ** (37 shares) - Activated Carbon Technology
- **UPXI** (17 shares) - E-commerce Consolidator

**Starting Value:** $995.74 (August 8, 2025)  
**Challenge Period:** 30 days  
**Strategy:** Catalyst-driven, concentrated positions with automated risk management

## 🎯 Key Features

- **Automated Price Tracking** via Alpha Vantage API
- **Stop-Loss Management** with automatic execution
- **Daily Performance Reports** (Markdown & HTML)
- **Professional Analytics** with Sharpe/Sortino ratios
- **Real-time Dashboard** with GitHub Pages
- **Complete Trade Logging** and audit trail

## 📁 Repository Structure

```
├── config.json                    # Portfolio configuration
├── main.py                        # Core tracking script  
├── market_tracker.py              # Market context analysis
├── microcap_manager.py            # Advanced portfolio management
├── requirements.txt               # Python dependencies
├── .github/workflows/
│   ├── schedule.yml               # Daily portfolio updates
│   ├── market_context.yml         # Market data collection
│   └── daily_reporting.yml        # Automated reporting
├── docs/
│   ├── index.html                 # Portfolio dashboard
│   ├── latest.json                # Current portfolio data
│   ├── latest_report.md           # Latest performance report
│   └── market_context.json        # Market environment data
├── data/
│   ├── portfolio_history.csv      # Historical performance
│   └── market_history.csv         # Market context history
├── reporting/
│   ├── portfolio_config.yml       # Reporting configuration
│   ├── portfolio_report_generator.py # Report generator
│   └── requirements.txt           # Reporting dependencies
├── reports/                       # Daily markdown reports
├── excel_reports/                 # Excel analysis files
└── state/
    └── portfolio_state.json       # Current positions
```

## ⚡ Quick Start

### 1. Setup
```bash
git clone https://github.com/[username]/microcap-portfolio-tracker_claude
cd microcap-portfolio-tracker_claude
pip install -r requirements.txt
```

### 2. Configuration
Add your Alpha Vantage API key as a GitHub secret:
- Go to Settings → Secrets → Actions
- Add `ALPHAVANTAGE_API_KEY` with your API key

### 3. Automation
The system runs automatically:
- **20:20 UTC** - Portfolio price updates
- **20:25 UTC** - Market context analysis  
- **20:30 UTC** - Report generation

### 4. View Results
- **Live Dashboard:** https://[username].github.io/microcap-portfolio-tracker_claude
- **Latest Report:** [docs/latest_report.md](docs/latest_report.md)
- **Performance Data:** [data/portfolio_history.csv](data/portfolio_history.csv)

## 📈 Investment Strategy

### Core Thesis
Concentrated micro-cap positions with:
- **Near-term catalysts** (earnings, approvals, partnerships)
- **Strong fundamentals** relative to market cap
- **Momentum reversal patterns**
- **Sector positioning** for 2025 outperformance

### Risk Management
- **Stop-losses:** GEVO $0.95, FEIM $26.50, ARQ $5.80, UPXI $4.75
- **Position sizing:** 35%/30%/25%/10% allocation
- **Daily monitoring** with automated alerts
- **Professional metrics** tracking

### Target Scenarios
- **Bull Case (40%):** 400-500% return
- **Base Case (35%):** 150-300% return  
- **Bear Case (25%):** -20% to +50% return

## 🔧 Advanced Usage

### Manual Portfolio Management
```bash
python microcap_manager.py
```

### Generate Custom Reports
```bash
cd reporting
python portfolio_report_generator.py
```

### Market Analysis
```bash
python market_tracker.py
```

## 📊 Data Sources

- **Price Data:** Alpha Vantage (real-time stock prices)
- **Market Context:** yfinance (indices, sector ETFs)
- **Risk Management:** Automated stop-loss execution
- **Performance Analytics:** Custom calculations with industry-standard metrics

## 🤖 Automation Features

- **GitHub Actions** for daily data collection
- **Automated stop-loss** execution when triggered
- **HTML dashboard** with real-time updates
- **Excel report** generation with multiple sheets
- **Trade logging** with complete audit trail

## 📈 Performance Tracking

The system tracks:
- **Daily portfolio value** and returns
- **Individual position** performance
- **Risk metrics** (stop-loss proximity, allocation)
- **Market context** (sector rotation, sentiment)
- **Professional ratios** (Sharpe, Sortino)

## 🛡️ Risk Disclosures

- **High-risk strategy** with concentrated positions
- **Micro-cap volatility** can cause significant swings
- **Stop-losses** may not execute in volatile markets
- **Past performance** does not guarantee future results
- **Educational purpose** - not investment advice

## 📞 Support

- **Issues:** Use GitHub Issues for bugs/features
- **Data:** All data is public and auditable
- **Updates:** Check commits for daily performance

## 📜 License

MIT License - See LICENSE file for details

---

**⚠️ Disclaimer:** This is an experimental trading strategy for educational purposes. All investments carry risk of loss. Past performance does not guarantee future results.
