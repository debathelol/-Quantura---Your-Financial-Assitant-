# Overview

This is a comprehensive dual-format financial analysis application built with Streamlit and PostgreSQL. The app intelligently detects and analyzes two types of data: Personal Finance Transactions and Corporate Overview Data. Its main purpose is to provide users with tools for financial tracking, forecasting, and reporting, aiming to simplify financial management for individuals and offer insightful analytics for businesses. Key capabilities include automatic transaction categorization, budget tracking, financial forecasting, and multi-currency support for personal finance, alongside revenue trend analysis, financial ratio calculation, and competitor comparison for corporate data. The project ambitions include providing a user-friendly and powerful platform for diverse financial analysis needs.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## UI/UX Decisions
The application uses Streamlit for its frontend, enabling rapid development of interactive data applications with a Python-native approach. The design prioritizes clarity and user-friendliness, featuring a tabbed interface for different analysis views and a customizable dashboard with smooth animations (slide-in, fade-up, scale-in) for enhanced user experience. Visualizations are generated using Matplotlib, Seaborn, and Plotly, ensuring high-quality, interactive charts for better data interpretation.

**Navigation Enhancement**: Added a sticky navigation bar at the top of the page with smooth scrolling to major sections. Users can instantly jump to: Home, Upload Data, Currency, Financial Tools, Analysis, Budget, and Savings Goals with a single click. The navigation features glassmorphism styling (backdrop blur, gradient background) and Mac OS-style hover animations, staying visible as users scroll for quick access to any section.

## Recent Implementation Updates

### November 9, 2025 - Financial Tools Section
Added SIX comprehensive financial calculators with interactive visualizations:

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

3. **Salary Expenditure Planner - Strategic Blueprints**:
   - Three proven financial mindsets: Stable (Safety Fortress), Balanced (Smart Builder), Aggressive (Accelerator)
   - Personalized budget allocation recommendations based on selected strategy
   - **Stable Plan**: 55-60% essentials, 20-25% savings, 5-10% investments - for new earners and uncertain environments
   - **Balanced Plan**: 50% essentials, 15-20% savings, 20-25% investments - for moderate risk tolerance and steady growth
   - **Aggressive Plan**: 40-45% essentials, 10-15% savings, 35-45% investments - for maximizing returns with long-term outlook
   - Interactive allocation breakdown with percentage ranges and dollar amounts
   - Plotly donut chart visualization of budget distribution
   - Financial projections with 4 KPI metrics: Savings Goal, Investments (with 7% growth), Total Wealth, Safety Net
   - Multi-trace projection chart showing wealth growth trajectory over 3-24 months
   - AI-style smart insights with emergency fund timeline and plan-specific recommendations
   - Helps users choose the right strategy for their financial goals and situation

4. **Retirement Planning Calculator - Am I On Track?**:
   - Comprehensive retirement readiness analysis
   - Inputs: Current age, retirement age, current savings, monthly contribution, expected return, retirement expenses, Social Security/pension
   - Future value calculations using compound interest formulas
   - Retirement needs projection (monthly gap × years in retirement)
   - On-track vs shortfall analysis with actionable insights
   - **4 KPI Metrics**: Total at retirement, total needed, years money lasts, monthly retirement income
   - Interactive Plotly chart showing savings growth trajectory from current age to retirement
   - Target line visualization comparing projected savings vs retirement goal
   - Detailed retirement income breakdown table (Social Security + portfolio withdrawals)
   - **Smart Insights**: Action recommendations (increase contribution by $X), alternative retirement age calculations, early retirement possibilities
   - Handles edge cases: infinite money duration when Social Security covers all expenses

5. **Debt Payoff Planner - Get Out of Debt Faster!**:
   - Dynamic debt entry system (1-10 debts with name, balance, interest rate, minimum payment)
   - **Two Strategy Comparison**: Snowball (smallest first) vs Avalanche (highest interest first)
   - Month-by-month amortization simulation with accurate interest calculations
   - Each debt gets monthly interest applied, then principal reduction from payments
   - Extra payment allocation to target debt based on strategy
   - **Side-by-side metrics**: Payoff timeline, total paid, total interest for both methods
   - Winner recommendation showing savings and time difference
   - Interactive Plotly timeline chart showing debt reduction journey (Avalanche method)
   - Payoff order table with month-by-month debt elimination schedule
   - **Smart Insights**: Total debt summary, minimum payment totals, weighted average interest rate, freedom date calculation
   - Aggressive strategy detection (extra payment ≥ 50% of minimums)
   - Real-world calendar projection (freedom date in Month/Year format)

6. **Investment Portfolio Analyzer - Optimize Your Investments**:
   - **Two input modes**: Manual entry (individual holdings) or Quick Allocation (percentage-based)
   - Asset types supported: Stocks, Bonds, Real Estate, Cash, Commodities, Crypto
   - **Diversification Score**: 0-100 scale based on concentration and number of asset types
   - Interactive Plotly donut chart showing asset allocation with hover details
   - Detailed breakdown table with value, percentage, and risk level for each asset type
   - **Age-based recommendations**: Rule of thumb (100 - age = stocks %, age = bonds %)
   - **Risk tolerance adjustments**: Conservative (-15% stocks), Moderate (baseline), Aggressive (+15% stocks)
   - Personalized allocation targets with current vs recommended comparison
   - **Rebalancing suggestions**: Specific dollar amounts to buy/sell for alignment
   - Triggers rebalancing when allocation differs >10% from recommendations
   - **Risk assessment**: High/Medium/Low risk classification based on volatile asset percentage
   - **Concentration risk alerts**: Warning when one asset type exceeds 40-60% of portfolio
   - Manual entry supports up to 20 individual holdings for detailed portfolio analysis

7. **Rent vs Buy Calculator - Make the Right Housing Decision**:
   - Comprehensive cost comparison between renting and buying over 1-30 years
   - **Rent scenario inputs**: Monthly rent, annual increase %, renter's insurance, upfront costs
   - **Buy scenario inputs**: Home price, down payment %, mortgage rate, loan term, property tax, HOA fees, insurance, maintenance %, closing costs, appreciation rate
   - **Year-by-year simulation**: Tracks cumulative costs, home equity, and investment values
   - **Accurate accounting**: Only counts interest (not principal) as cost - principal builds equity
   - **Opportunity cost analysis**: Models investing down payment difference at market returns
   - **Net worth comparison**: Rent + investments vs home equity - costs
   - **Break-even calculation**: Identifies year when buying becomes more profitable than renting
   - **8 Key metrics**: Total rent paid, total buy costs, home equity, monthly costs, home value, break-even point
   - **Dual Plotly charts**: Net worth comparison over time, cumulative costs comparison
   - Break-even marker visualization on net worth chart
   - **Smart Insights**: 
     - Winner verdict (buying vs renting advantage with dollar amounts)
     - Monthly savings analysis
     - Home appreciation/depreciation tracking
     - Timeline-based recommendations (short-term vs long-term considerations)
     - Investment growth projections if renting
   - Handles edge cases: No down payment, paid-off mortgages, zero interest rates

All calculators feature:
- Real-time calculations with instant updates
- Professional Plotly visualizations (line charts, donut charts, timelines)
- Comprehensive KPI metrics with delta indicators
- User-friendly layouts with column-based organization
- Expandable/collapsible sections for focused analysis
- Controlled by sidebar toggle: "🪄 Financial Tools"
- Smart personalized insights based on user inputs
- Edge case handling for zero values, infinite scenarios, and boundary conditions

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