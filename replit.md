# Overview

This comprehensive financial analysis application, built with Streamlit and PostgreSQL, offers three major capabilities: (1) Personal Finance Transactions analysis with auto-categorization, budget tracking, and forecasting; (2) Corporate Overview Data with revenue trends and financial ratios; and (3) AI-Powered Quantitative Stock Analysis with Monte Carlo simulations, ARIMA forecasting, GARCH volatility, Black-Scholes options pricing, and portfolio optimization. The application aims to be a complete financial management platform for individuals, businesses, and investors with advanced quantitative tools and AI insights.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## UI/UX Decisions
The application utilizes Streamlit for its frontend, focusing on clarity and user-friendliness with a tabbed interface and a customizable dashboard featuring smooth animations. A sticky navigation bar provides quick access to major sections (Home, Upload Data, Currency, AI Chat, Financial Tools, Analysis, Budget, Savings Goals) with glassmorphism styling and macOS-style hover animations. Visualizations are generated using Matplotlib, Seaborn, and Plotly for high-quality, interactive charts.

### Mobile Responsiveness (November 9, 2025)
Added comprehensive mobile-first responsive design for smooth experience on all devices:

**Responsive Breakpoints**:
- **Tablet (≤768px)**: Compact navigation, 3-column feature grid, optimized spacing
- **Mobile (≤480px)**: 2-column layout, touch-optimized controls, reduced padding
- **Small Phones (≤360px)**: Further size adjustments for tiny screens
- **Landscape Mode**: Horizontal layout optimizations

**Touch Optimizations**:
- **Minimum tap targets**: 44-48px height following iOS/Android guidelines
- **Touch-friendly inputs**: 48px height, 16px font (prevents iOS auto-zoom)
- **Tactile feedback**: Scale transform (0.97) on button press for visual response
- **Tap highlight**: Purple glow effect for better touch visibility
- **Disabled hover on touch devices**: Clean UX using `@media (hover: none)`

**Performance Enhancements**:
- Lighter animations on mobile (0.3-0.4s vs 0.6s desktop)
- Reduced transform distances (-10px vs -30px)
- Simplified glow effects for better frame rates
- Optimized transitions (0.2s ease vs complex cubic-bezier)

**Layout Adaptations**:
- Feature cards: 3 columns (tablet) → 2 columns (mobile)
- Navigation: Responsive wrapping with smaller fonts
- Columns: Stack vertically on mobile
- Sidebar: 85% width, max 300px on small screens
- Content padding: 1rem mobile vs desktop spacing

**Testing**: Verified on iPhone SE (375x667) and iPad (768x1024) viewports with successful navigation, interaction, and calculator usage.

## Technical Implementations
The system features intelligent data detection to differentiate between "Personal Finance Transactions" and "Corporate Overview Data" using fuzzy column matching. Pandas is used for ETL, robust date parsing, rule-based auto-categorization, and data validation across CSV and Excel formats. Time series analysis aggregates financial data monthly for trend identification. Scikit-learn's Linear Regression is employed for basic financial forecasting. PostgreSQL, accessed via psycopg2, stores user-defined categorization rules, budget settings, and savings goals, ensuring data persistence. ReportLab generates professional, exportable PDF reports. Multi-currency support is provided for 10 currencies with hardcoded exchange rates. The application includes seven comprehensive financial calculators for compounding, car purchases, salary expenditure planning, retirement planning, debt payoff, investment portfolio analysis, and rent vs. buy comparisons, all featuring real-time calculations, Plotly visualizations, and smart insights. An intelligent AI chatbot (OpenAI GPT-4o-mini via Replit AI Integrations) provides personalized financial guidance, conversational Q&A, data-aware responses, and calculator recommendations, maintaining session-based chat history. Automated financial highlights include expense detection, month-over-month spending alerts, and recurring transaction identification.

### AI-Powered Stock Analyzer (November 10, 2025)
Implemented a comprehensive quantitative stock analysis system with AI-powered insights:

**Data Sources**:
- **Alpha Vantage API**: Primary source for real-time quotes and historical data (requires ALPHA_VANTAGE_API_KEY)
- **Yahoo Finance**: Fallback data source via yfinance library
- **Support**: Stocks, ETFs, and major market indices

**Quantitative Analysis Features**:
1. **Monte Carlo Simulations**: 1000-path price projections with percentile fan charts (5th, 25th, 50th, 75th, 95th)
2. **ARIMA Forecasting**: Time series prediction with confidence intervals using statsmodels
3. **GARCH Volatility**: Volatility clustering and 30-day volatility forecasts using arch library
4. **Black-Scholes Pricing**: Option pricing with full Greeks (Delta, Gamma, Vega, Theta, Rho)
5. **Risk Metrics**: Sharpe ratio, Beta, Alpha, correlation, Sortino ratio, volatility analysis
6. **PCA Analysis**: Principal component analysis for portfolio dimensionality reduction
7. **Statistical Summary**: Mean, std dev, skewness, kurtosis, percentiles

**AI Analysis Engine** (`services/stock_ai_analyzer.py`):
- **Stock Ratings**: AI generates Buy/Sell/Hold ratings with confidence scores
- **Risk Assessment**: Low/Medium/High risk classification
- **Key Insights**: 3-4 actionable bullet points per stock
- **Portfolio Insights**: Diversification scoring, correlation analysis, rebalancing suggestions
- **Model**: OpenAI GPT-4o-mini for intelligent analysis

**User Interface** (4-Tab Layout):
1. **Single Stock Analysis**: Candlestick charts, Monte Carlo, ARIMA, GARCH, risk metrics, AI ratings
2. **Portfolio Analysis**: Correlation heatmap, risk-return scatter, PCA, AI portfolio insights
3. **Options Pricing**: Interactive Black-Scholes calculator with Greeks sensitivity charts
4. **Advanced Analytics**: Statistical distributions, histogram analysis, custom metrics

**Visualizations** (`ui_components/stock_charts.py`):
- Candlestick charts with OHLC data
- Monte Carlo fan charts with probability bands
- ARIMA forecasts with confidence intervals
- Correlation heatmaps for multi-stock analysis
- Risk-return scatter plots with Sharpe-weighted bubbles
- GARCH volatility trend charts
- PCA variance explanation charts
- Greeks sensitivity curves

**Technical Implementation** (`services/stock_analyzer.py`):
- Object-oriented `StockAnalyzer` class
- Libraries: scipy (stats, optimization), statsmodels (ARIMA), arch (GARCH), yfinance, sklearn (PCA, regression)
- Comprehensive error handling for API failures and insufficient data
- Efficient data caching and returns calculation

### AI Budget Advisor (November 10, 2025)
Implemented an AI-powered budget recommendation system that analyzes spending patterns and suggests optimal budgets:

**Core Functionality**:
- **Analysis Engine**: `get_ai_budget_recommendations(df)` function analyzes transaction data including category spending, monthly averages, and date ranges
- **AI Model**: Uses OpenAI GPT-4o-mini to provide intelligent budget recommendations based on spending patterns
- **Output Format**: Returns JSON with recommended budgets (Income, Expense, Investment), explanation, and actionable tip
- **Error Handling**: Comprehensive handling for API failures, rate limits, authentication issues, and JSON parsing errors

**User Interface**:
- **Location**: Integrated into Budget Settings section in sidebar
- **Primary Button**: "Get AI Recommendations" (purple primary button) triggers analysis
- **AI Insights Card**: Purple gradient background displaying AI explanation and recommendations
- **Metrics Display**: Three metric cards showing recommended budgets for Income, Expense, and Investment
- **Pro Tip**: Actionable financial advice presented in info box
- **Apply Button**: One-click application of all AI-recommended budgets

**Data Flow**:
1. User uploads transaction data via file uploader
2. Data stored in `st.session_state.processed_df` for cross-component access
3. AI analyzes spending patterns, current budgets, and monthly averages
4. Recommendations stored in `st.session_state.ai_budget_recommendations`
5. User reviews AI insights and can apply with single button click
6. Budgets saved to PostgreSQL database and success message persists across rerun

**Session State Management**:
- `processed_df`: Stores uploaded transaction data for AI analysis
- `primary_type`: Tracks data type (personal_finance or corporate)
- `ai_budget_recommendations`: Stores AI analysis results
- `budget_apply_success`: Persists success message across page reruns
- State automatically cleared on upload errors or file removal

## Feature Specifications
- **Personal Finance**: Automatic categorization (Income, Expense, Investment, Uncategorized), custom categorization rules, budget tracking, expense subcategorization, savings goals, multi-currency support, monthly spending trends, income vs. expense comparisons, and CSV/Excel export.
- **Corporate Analysis**: Revenue trends, income comparisons, employee growth, year-over-year metrics, financial ratios, competitor comparison with interactive charts, and downloadable PDF reports.
- **Stock Analysis**: Real-time quotes, Monte Carlo simulations, ARIMA forecasting, GARCH volatility, Black-Scholes options pricing, risk metrics (Sharpe, Beta, Alpha), portfolio correlation analysis, PCA, AI-powered buy/sell ratings, and comprehensive visualizations.
- **General**: Customizable dashboard, chart PNG downloads, date range filtering, multi-file upload, an AI-powered financial assistant, and AI budget recommendations.

## System Design Choices
The architecture adopts a modular approach, separating data ingestion, processing, analysis, and presentation. Streamlit provides a unified Python codebase for frontend and backend. PostgreSQL ensures reliable, ACID-compliant storage for critical user data. A hybrid visualization strategy uses Plotly for interactive elements and Matplotlib/Seaborn for static outputs.

# External Dependencies

## Data Analysis Libraries
- **Pandas**: Data manipulation and time series.
- **NumPy**: Numerical operations.
- **Scikit-learn**: Linear regression for forecasting, PCA for portfolio analysis.
- **SciPy**: Statistical functions and optimization.
- **Statsmodels**: ARIMA time series forecasting.
- **Arch**: GARCH volatility modeling.
- **yfinance**: Yahoo Finance data fetching.

## Visualization Libraries
- **Matplotlib**: Base plotting.
- **Seaborn**: Statistical visualizations.
- **Plotly**: Interactive charting.

## PDF Generation
- **ReportLab**: Professional PDF creation.

## Web Framework
- **Streamlit**: Interactive web applications.

## Database
- **PostgreSQL**: Persistent storage.
- **psycopg2**: Python adapter for PostgreSQL.

## Utility Libraries
- **re**: Regular expressions.
- **io.BytesIO**: In-memory file handling.
- **base64**: Encoding for file downloads.

## AI Integration
- **OpenAI GPT-4o-mini**: Via Replit AI Integrations for the chatbot, budget recommendations, and stock analysis.

## Financial APIs
- **Alpha Vantage**: Real-time stock quotes and historical data (requires ALPHA_VANTAGE_API_KEY).

## Data Formats Supported
- CSV files.
- Excel files (requires `openpyxl`/`xlrd`).