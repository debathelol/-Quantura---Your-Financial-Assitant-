# Overview

This is a comprehensive dual-format financial analysis application built with Streamlit and PostgreSQL. The app intelligently detects and analyzes two types of data: Personal Finance Transactions and Corporate Overview Data. Its main purpose is to provide users with tools for financial tracking, forecasting, and reporting, aiming to simplify financial management for individuals and offer insightful analytics for businesses. Key capabilities include automatic transaction categorization, budget tracking, financial forecasting, and multi-currency support for personal finance, alongside revenue trend analysis, financial ratio calculation, and competitor comparison for corporate data. The project ambitions include providing a user-friendly and powerful platform for diverse financial analysis needs.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## UI/UX Decisions
The application uses Streamlit for its frontend, enabling rapid development of interactive data applications with a Python-native approach. The design prioritizes clarity and user-friendliness, featuring a tabbed interface for different analysis views and a customizable dashboard with smooth animations (slide-in, fade-up, scale-in) for enhanced user experience. Visualizations are generated using Matplotlib, Seaborn, and Plotly, ensuring high-quality, interactive charts for better data interpretation.

## Recent Implementation Updates

### November 9, 2025 - Financial Tools Section
Added two powerful financial calculators with interactive visualizations:

1. **Magic of Compounding Calculator**:
   - Compound interest calculations with monthly contributions
   - Supports multiple compounding frequencies (Daily, Monthly, Quarterly, Annually)
   - Optional inflation adjustment for real value calculations
   - Interactive Plotly charts showing wealth growth trajectory
   - Rule of 72 for doubling time calculations
   - Year-by-year breakdown tables
   - Smart insights showing ROI and crossover points

2. **Smart Car Purchase Calculator - 20-5-10 Rule**:
   - Implements financial best practice: 20% down, 5-year max loan, EMI ≤ 10% salary
   - Accurate EMI calculations using standard formula
   - **Edge case handling**: Properly handles zero-interest loans with simple amortization
   - Color-coded affordability verdicts (Green/Yellow/Red)
   - Interactive Plotly charts showing EMI vs salary budget
   - Complete payment breakdowns with total cost analysis
   - Smart recommendations based on rule violations
   - Helps users avoid car loan debt traps

Both calculators feature:
- Real-time calculations with instant updates
- Professional Plotly visualizations
- Comprehensive KPI metrics
- User-friendly 3-column layouts
- Expandable/collapsible sections
- Controlled by sidebar toggle: "🪄 Financial Tools"

## Technical Implementations
- **Intelligent Data Detection**: Automatically identifies incoming data as either "Personal Finance Transactions" (requiring `Date`, `Description`, `Amount`) or "Corporate Overview Data" (requiring `Year`, `Revenue`, `Net Income`, `Market Cap`, `Employees`) using fuzzy column matching.
- **Data Processing**: Leverages Pandas for ETL (Extract, Transform, Load), including robust date parsing, rule-based auto-categorization using regex, and data validation. Supports CSV and Excel formats.
- **Time Series Analysis**: Aggregates financial data monthly using Pandas Period functionality to identify spending patterns and track trends.
- **Financial Forecasting**: Employs Scikit-learn's Linear Regression for basic, interpretable predictions of future income/expense trends.
- **Database Persistence**: PostgreSQL with psycopg2 stores user-defined custom categorization rules, budget settings, and savings goals, ensuring data persistence across sessions.
- **Report Generation**: Uses ReportLab for generating professional, exportable PDF reports for both personal and corporate analysis, including structured layouts and tables.
- **Multi-Currency Support**: Supports 10 currencies (USD, EUR, GBP, CAD, AUD, JPY, CNY, INR, MXN, BRL) with automatic conversion using hardcoded exchange rates.
- **Financial Tools**: Includes a "Magic of Compounding Calculator" with interactive visualizations and a "Smart Car Purchase Calculator" based on the 20-5-10 rule for affordability checks and recommendations.
- **Smart Insights**: Provides automated financial highlights such as biggest expense detection, month-over-month spending change alerts, unusual large transaction detection, and savings rate calculations.
- **Recurring Transaction Detection**: Identifies subscriptions and recurring bills based on transaction description, amount consistency, and time interval regularity.

## Feature Specifications
- **Personal Finance**:
    - Automatic categorization (Income, Expense, Investment, Uncategorized)
    - Custom categorization rules
    - Budget tracking with visual alerts
    - Expense subcategorization
    - Savings goals tracker
    - Multi-currency support
    - Monthly spending trends, category breakdowns, income vs. expense comparisons
    - CSV/Excel export of filtered data and monthly summaries
- **Corporate Analysis**:
    - Revenue trends, income comparisons, employee growth
    - Year-over-year metrics
    - Financial ratios (profit margin, revenue per employee, revenue growth %, employee growth %)
    - Competitor comparison with multi-company side-by-side metrics and interactive charts
    - Downloadable PDF reports
- **General**:
    - Customizable dashboard
    - Chart PNG downloads
    - Date range filtering
    - Multi-file upload

## System Design Choices
The architecture emphasizes a modular approach, separating data ingestion, processing, analysis, and presentation layers. Streamlit allows for a unified Python codebase for both backend logic and frontend display. PostgreSQL ensures reliable, ACID-compliant storage for critical user data, supporting the application's stateful components. A hybrid visualization strategy uses Plotly for interactive components and Matplotlib/Seaborn for static, high-quality outputs.

# External Dependencies

## Data Analysis Libraries
- **Pandas**: Core data manipulation and time series analysis.
- **NumPy**: Numerical operations and array handling.
- **Scikit-learn**: Linear regression for financial forecasting.

## Visualization Libraries
- **Matplotlib**: Base plotting library.
- **Seaborn**: Statistical visualizations with enhanced aesthetics.
- **Plotly**: Interactive charting for specific features like company comparison and calculators.

## PDF Generation
- **ReportLab**: Professional PDF document creation.

## Web Framework
- **Streamlit**: Interactive web application framework.

## Database
- **PostgreSQL**: For persistent storage of user rules, budgets, and savings goals.
- **psycopg2**: Python adapter for PostgreSQL.

## Utility Libraries
- **re**: Regular expressions for transaction categorization.
- **io.BytesIO**: In-memory file handling.
- **base64**: Encoding for file downloads.

## Data Formats Supported
- CSV files.
- Excel files (requires `openpyxl`/`xlrd`).