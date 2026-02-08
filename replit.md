# Overview

**Quantura** is a comprehensive financial analysis application designed for individuals, businesses, and investors. It integrates advanced quantitative tools and AI insights to provide three core functionalities: Personal Finance Transactions analysis (auto-categorization, budgeting, forecasting), Corporate Overview Data (revenue trends, financial ratios), and AI-Powered Quantitative Stock Analysis (Monte Carlo, ARIMA, GARCH, Black-Scholes, portfolio optimization). The project aims to be a complete financial management platform.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## UI/UX Decisions
The application uses Streamlit for a user-friendly, tabbed interface with a customizable dashboard, smooth animations, and a sticky navigation bar featuring glassmorphism styling and macOS-style hover effects. Visualizations are generated with Matplotlib, Seaborn, and Plotly for high-quality, interactive charts. The UI is designed to be mobile-first and fully responsive across various devices, with touch optimizations and performance enhancements for mobile.

## Technical Implementations
The system intelligently detects and processes financial data from CSV and Excel files using Pandas for ETL, robust date parsing, rule-based auto-categorization, and validation. It performs time series analysis and uses Scikit-learn for basic financial forecasting. PostgreSQL, accessed via psycopg2, stores user settings, categories, budgets, and savings goals. ReportLab generates professional PDF reports. Multi-currency support is available for 10 currencies.

The application includes seven comprehensive financial calculators with real-time calculations and Plotly visualizations. An intelligent AI chatbot, powered by OpenAI GPT-4o-mini via Replit AI Integrations, offers personalized financial guidance, data-aware responses, and session-based chat history. Automated features include expense detection, month-over-month spending alerts, and recurring transaction identification.

A comprehensive AI-powered global stock analysis system supports all global exchanges, automatically converting company names to ticker symbols. It uses Alpha Vantage and Yahoo Finance for data and offers: Monte Carlo simulations, ARIMA forecasting, GARCH volatility, Black-Scholes pricing with Greeks, risk metrics (Sharpe, Beta, Alpha, correlation, Sortino), PCA analysis, and statistical summaries. The AI analysis engine (OpenAI GPT-4o-mini) provides stock ratings, risk assessments, and actionable insights.

An AI Budget Advisor analyzes spending patterns to recommend optimal budgets (Income, Expense, Investment), providing explanations and actionable tips, with a one-click application feature. AI-powered "Explain this graph" buttons provide jargon-free, actionable explanations for complex financial visualizations (Monte Carlo, ARIMA, GARCH, correlation, risk-return, PCA) using GPT-4o-mini.

### Rate Limiting & Caching Strategy
To prevent Yahoo Finance API rate limiting, the application implements a comprehensive caching system:
- **Data Caching**: Stock price data and returns are cached for 5 minutes (300 seconds) using Streamlit's `@st.cache_data` decorator
- **Cache Coverage**: All stock data fetching locations (single stock analysis, portfolio analysis, advanced analytics, batch DCF screener) use cached helpers
- **Performance Benefits**: Analyzing the same stock multiple times within 5 minutes uses cached data (no additional API calls), providing instant results and preventing rate limit errors
- **Note**: Failed requests are also cached for 5 minutes to prevent repeated failed API calls

### AI Demo Mode Fallback System
To ensure professional demonstrations even during API failures or when credits run out, all AI features include intelligent demo mode fallbacks:
- **Automatic Activation**: Demo mode activates automatically when OpenAI API is unavailable (no API key, rate limits, network errors, parsing failures)
- **Clear Labeling**: All demo responses are clearly marked with ⚠️ **Demo Mode** prefix so users know they're seeing example content
- **Feature Coverage**: Demo mode supports all 6 AI features:
  - Stock AI Recommendations (buy/sell ratings, risk analysis, key insights)
  - Portfolio Insights (diversification scores, rebalancing suggestions)
  - Graph Explanations (Monte Carlo, ARIMA, GARCH, correlation, risk-return, PCA)
  - Budget Advisor (income/expense/investment recommendations)
  - Financial Chatbot (general financial guidance)
- **Realistic Content**: Demo responses use authentic financial advice and educational content, not placeholder text
- **Seamless UX**: App functions normally in demo mode - no crashes, error messages, or broken features
- **Debug Logging**: All demo mode activations log "[DEMO MODE]" messages for troubleshooting
- **School Project Ready**: Perfect for classroom demonstrations where internet/API access may be unreliable

## Feature Specifications
- **Personal Finance**: Auto-categorization, custom rules, budget tracking, subcategorization, savings goals, multi-currency, spending trends, income vs. expense comparisons, CSV/Excel export.
- **Corporate Analysis**: Revenue trends, income comparisons, employee growth, YOY metrics, financial ratios, competitor analysis, PDF reports.
- **Stock Analysis**: Real-time quotes, Monte Carlo, ARIMA, GARCH, Black-Scholes, risk metrics, portfolio correlation, PCA, AI buy/sell ratings, AI graph explanations, comprehensive visualizations.
- **General**: Customizable dashboard, chart PNG downloads, date range filtering, multi-file upload, AI financial assistant, AI budget recommendations, AI graph explanations.

## System Design Choices
The architecture is modular, separating data ingestion, processing, analysis, and presentation. Streamlit unifies frontend and backend in Python. PostgreSQL provides reliable data storage. A hybrid visualization approach uses Plotly for interactivity and Matplotlib/Seaborn for static outputs.

# External Dependencies

## Data Analysis Libraries
- **Pandas**
- **NumPy**
- **Scikit-learn**
- **SciPy**
- **Statsmodels**
- **Arch**
- **yfinance**

## Visualization Libraries
- **Matplotlib**
- **Seaborn**
- **Plotly**

## PDF Generation
- **ReportLab**

## Web Framework
- **Streamlit**

## Database
- **PostgreSQL**
- **psycopg2**

## Utility Libraries
- **re**
- **io.BytesIO**
- **base64**

## AI Integration
- **OpenAI GPT-4o-mini**: Via Replit AI Integrations.

## Financial APIs
- **Alpha Vantage**: For real-time and historical stock data (requires `ALPHA_VANTAGE_API_KEY`).

## Data Formats Supported
- CSV files.
- Excel files.