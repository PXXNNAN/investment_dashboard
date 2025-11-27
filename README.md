# Investment Dashboard

Personal Investment Portfolio Dashboard built with Flask and Google Sheets for tracking investments, monitoring portfolio performance, and providing rebalancing recommendations.

## Features

- 📊 **Dashboard** - Overview with charts and analytics
- 💰 **Current Assets** - Track portfolio snapshots
- 🔄 **Investments** - Record transactions (Deposit, Withdraw, Buy, Sell)
- ⚙️ **Settings** - Configure categories and target allocations
- 📈 **Portfolio Rebalancing** - Get recommendations to match target allocation

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: Google Sheets (gspread API)
- **Frontend**: Bootstrap 5 + Chart.js
- **Testing**: pytest

## Project Structure

```
investment_dashboard/
├── app.py                      # Flask application (uses services)
├── config/
│   └── settings.py            # Configuration
├── models/
│   ├── asset.py               # Asset data model
│   ├── investment.py          # Investment data model
│   └── dividend.py            # Dividend data model
├── services/
│   ├── google_sheets_service.py  # Google Sheets API wrapper
│   ├── asset_service.py       # Asset business logic
│   ├── investment_service.py  # Investment business logic
│   ├── dividend_service.py    # Dividend business logic
│   ├── settings_service.py    # Settings business logic
│   └── dashboard_service.py   # Dashboard calculations
├── utils/
│   ├── date_utils.py          # Date parsing/formatting
│   └── amount_utils.py        # Amount parsing/formatting
├── tests/                      # Unit tests
├── templates/                  # HTML templates
├── static/                     # CSS files
└── credentials/                # Google service account
```

## Installation

1. **Clone the repository**

```bash
git clone <your-repo-url>
cd investment_dashboard
```

2. **Create virtual environment**

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up Google Sheets credentials**

- Create a Google Cloud project
- Enable Google Sheets API
- Create a service account
- Download JSON credentials
- Save as `credentials/service_account.json`

5. **Create Google Sheet**

- Create a new Google Sheet named "Investment_Db"
- Share it with your service account email
- Create three worksheets: "Settings", "Current Asset", "Investment"

## Running the Application

```bash
python app.py
```

Visit `http://127.0.0.1:5000` in your browser.

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test File

```bash
pytest tests/test_utils/test_date_utils.py -v
```

### Run with Coverage

```bash
pytest tests/ --cov=. --cov-report=html
```

View coverage report: `open htmlcov/index.html`

### Run Tests by Category

```bash
# Test utilities only
pytest tests/test_utils/ -v

# Test models only
pytest tests/test_models/ -v

# Test services only
pytest tests/test_services/ -v
```

## Development

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for all functions/classes
- Keep functions focused and small

### Adding New Features

1. Write tests first (TDD)
2. Implement the feature
3. Run tests to verify
4. Update documentation

## License

MIT License
