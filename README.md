![StreamlitPandas - Replit_page-0001](https://github.com/user-attachments/assets/1c901558-e5f2-459d-9ec3-04d25aaca81c)# 📊 Financial Analytics Dashboard

A comprehensive financial analytics application built with Streamlit that provides AI-powered stock analysis, portfolio management, personal finance tracking, and advanced quantitative analysis tools.

## 🌟 Features

### 📈 Global Stock Analysis
- **AI-Powered Company Lookup**: Simply type any company name (Apple, Tesla, Toyota, etc.) - no ticker symbols needed!
- **Advanced Analytics**:
  - Monte Carlo simulations for price predictions
  - ARIMA forecasting for time series analysis
  - GARCH volatility modeling
  - Black-Scholes options pricing
  - Risk metrics (Sharpe ratio, Beta, Alpha, VaR)
  - Correlation analysis with market benchmarks

### 💼 Portfolio Management
- Multi-stock portfolio analysis
- Diversification recommendations
- Risk-adjusted returns calculation
- AI-powered portfolio insights
- Efficient frontier visualization

### 💰 Personal Finance
- Transaction analysis and categorization
- Budget tracking and visualization
- Spending pattern analysis
- Monthly/yearly financial summaries
- Export reports to PDF

### 🏢 Corporate Finance
- Financial statement analysis
- Multi-company comparisons
- Ratio analysis (liquidity, profitability, efficiency)
- AI-powered financial insights

### 🤖 AI Assistant
- Ask questions about your finances
- Get personalized budgeting advice
- Financial calculations and conversions
- Powered by GPT-5-mini

## 🚀 Live Demo

[Add your deployed app link here]


## 📸 Screenshots

![StreamlitPandas - Replit_page-0001](https://github.com/user-attachments/assets/bfb6e20b-ffe9-495d-b8da-000bbf92421b)
![StreamlitPandas - Replit_page-0002](https://github.com/user-attachments/assets/8acb37c9-2082-46d1-bdc5-fd305046ccca)
![StreamlitPandas - Replit_page-0003](https://github.com/user-attachments/assets/c0226e97-1c77-447b-801d-e46230abc965)
![StreamlitPandas - Replit_page-0004](https://github.com/user-attachments/assets/38df91f8-dcae-49e5-a5e4-b028634b4f04)
![StreamlitPandas - Replit_page-0005](https://github.com/user-attachments/assets/c040c3b3-ee4e-400f-8a39-98ae0378c890)
![StreamlitPandas - Replit_page-0006](https://github.com/user-attachments/assets/92f0aeb6-df1c-4f87-9fe3-408444075f4a)
![StreamlitPandas - Replit_page-0007](https://github.com/user-attachments/assets/fec9c3cb-f6a7-4dc7-921b-c27a2554fd9d)
![StreamlitPandas - Replit_page-0008](https://github.com/user-attachments/assets/a3b7a9f1-1a07-43e9-a757-510bd3a20a1a)
![StreamlitPandas - Replit_page-0009](https://github.com/user-attachments/assets/150b82c8-8a0e-4b40-915a-9445230007ae)
![StreamlitPandas - Replit_page-0010](https://github.com/user-attachments/assets/367a217a-fd3b-477c-a61f-fdbd560ae7f4)
![StreamlitPandas - Replit_page-0011](https://github.com/user-attachments/assets/fb45dfdd-122a-403f-a69e-4daaa6e784c0)
![StreamlitPandas - Replit_page-0012](https://github.com/user-attachments/assets/33a311c2-a95d-4887-8ce9-05edbdce052e)
![StreamlitPandas - Replit_page-0011](https://github.com/user-attachments/assets/af9deae4-fbbb-45d3-8941-ab984bb32e9d)
![StreamlitPandas - Replit_page-0013](https://github.com/user-attachments/assets/564cd8ce-2297-4278-935f-747854b17245)
![StreamlitPandas - Replit_page-0014](https://github.com/user-attachments/assets/7d2e0dbc-cdeb-403f-94cc-98ae7f6f0928)
![StreamlitPandas - Replit_page-0015](https://github.com/user-attachments/assets/3b6af964-d515-49d9-988c-92318ba1727c)


## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **Data Analysis**: Pandas, NumPy, SciPy
- **Visualization**: Plotly, Matplotlib, Seaborn
- **Machine Learning**: scikit-learn, statsmodels, arch
- **Financial Data**: yfinance
- **AI**: OpenAI GPT-5-mini
- **Database**: PostgreSQL (optional)
- **PDF Generation**: ReportLab

## 📋 Prerequisites

- Python 3.11 or higher
- OpenAI API key (for AI features)

## 💻 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/financial-analytics-dashboard.git
cd financial-analytics-dashboard
```

2. Install dependencies:
```bash
pip install -r requirements-github.txt
```

3. Set up environment variables:
Create a `.streamlit/secrets.toml` file:
```toml
OPENAI_API_KEY = "your-api-key-here"
```

Or set environment variables:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

4. Run the application:
```bash
streamlit run app.py
```

## 🌐 Deploying to Streamlit Cloud (FREE)

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub
4. Click "New app"
5. Select your repository and branch
6. Set the main file path: `app.py`
7. Add your secrets (API keys) in the "Advanced settings"
8. Click "Deploy"!

Your app will be live at: `https://yourusername-financial-analytics-dashboard.streamlit.app`

## 📁 Project Structure

```
financial-analytics-dashboard/
├── app.py                      # Main application file
├── services/
│   ├── stock_analyzer.py       # Stock analysis logic
│   ├── stock_ai_analyzer.py    # AI-powered analysis
│   ├── company_lookup.py       # Company name to ticker conversion
│   └── database.py             # Database operations
├── ui_components/
│   ├── charts.py               # Chart components
│   ├── metrics.py              # Metric displays
│   ├── progress.py             # Progress indicators
│   └── stock_charts.py         # Stock-specific charts
├── .streamlit/
│   └── config.toml             # Streamlit configuration
├── requirements-github.txt     # Python dependencies
└── README.md                   # This file
```

## 🎯 Usage

### Stock Analysis
1. Navigate to "Stock Analyzer" section
2. Enter a company name (e.g., "Apple", "Tesla", "Microsoft")
3. Click "Analyze" to get:
   - Real-time stock data
   - Price charts with technical indicators
   - Monte Carlo simulations
   - AI-powered insights and recommendations

### Portfolio Analysis
1. Go to "Portfolio Analysis" tab
2. Enter multiple stock symbols
3. Set your investment amounts
4. Get diversification analysis and optimization suggestions

### Personal Finance
1. Upload your transaction CSV file
2. View categorized spending analysis
3. Track your budget vs actual spending
4. Export detailed reports

### Corporate Analysis
1. Upload financial statements (Excel format)
2. Compare multiple companies
3. View key financial ratios
4. Get AI-powered insights

## 📊 Sample Data

The project includes sample CSV files for testing:
- `sample_data.csv` - Personal finance transactions
- `sample_data_multi_year.csv` - Multi-year financial data

## 🔒 Security & Privacy

- API keys are stored securely using Streamlit secrets
- No financial data is stored on servers
- All analysis is performed client-side
- Database operations use parameterized queries

## 🤝 Contributing

This is a school project, but suggestions and improvements are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 👨‍🎓 About This Project

This financial analytics dashboard was created as a school project to demonstrate:
- Full-stack application development
- Financial data analysis and visualization
- Integration of AI/ML technologies
- Real-world problem solving

## 🙏 Acknowledgments

- Stock data provided by [Yahoo Finance](https://finance.yahoo.com/)
- AI capabilities powered by [OpenAI](https://openai.com/)
- Built with [Streamlit](https://streamlit.io/)

## 📧 Contact

debarghya47@gmail.com

Project Link: [https://github.com/yourusername/financial-analytics-dashboard](https://github.com/yourusername/financial-analytics-dashboard)

---

⭐ If you found this project helpful, please consider giving it a star!
