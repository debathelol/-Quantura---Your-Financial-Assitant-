# 📊 Financial Analytics Dashboard

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
![Quantura-images-0](https://github.com/user-attachments/assets/371ba0ed-a7fd-4231-acf0-07f99f4a363e)
![Quantura-images-1](https://github.com/user-attachments/assets/470d1435-67c1-4e21-802e-a485cd3f54af)
![Quantura-images-2](https://github.com/user-attachments/assets/d3f288d9-5ba4-472c-9935-6ec7bc867b08)
![Quantura-images-3](https://github.com/user-attachments/assets/b3a8be96-ed2d-42a9-82d6-de630eadfae2)
![Quantura-images-4](https://github.com/user-attachments/assets/fc10ac23-93f0-4597-ba92-32e8b9bdccc4)

![Quantura-images-5](https://github.com/user-attachments/assets/1bd561db-5a10-4372-889e-f131c602ae3f)
![Quantura-images-6](https://github.com/user-attachments/assets/9d8bf428-fd1d-4b44-9796-68bbde9ff397)
![Quantura-images-7](https://github.com/user-attachments/assets/aed87ebf-3c89-4f54-bda2-cb7a3d556c50)
![Quantura-images-8](https://github.com/user-attachments/assets/022ef70a-6bb4-4d55-b8fc-8dc6503f79b0)
![Quantura-images-9](https://github.com/user-attachments/assets/eec80923-7716-4154-9ac8-9c8ecc9bf038)
![Quantura-images-10](https://github.com/user-attachments/assets/a12f39f5-e34a-4f44-a039-75fd37adfee1)
![Quantura-images-11](https://github.com/user-attachments/assets/00419c71-91b8-4f69-b481-9a8b02a19ea7)
![Quantura-images-12](https://github.com/user-attachments/assets/7c386e7c-1c28-49f3-a22f-e57797f0bec7)
![Quantura-images-13](https://github.com/user-attachments/assets/0c83c96a-1772-4911-9576-9744427c6af3)

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



---

⭐ If you found this project helpful, please consider giving it a star!
