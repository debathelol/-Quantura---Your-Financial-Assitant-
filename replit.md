# Overview

This is a comprehensive dual-format financial analysis application built with Streamlit and PostgreSQL. The app intelligently detects and analyzes two types of data:

1. **Personal Finance Transactions**: Upload transaction data (CSV or Excel) with automatic categorization, budget tracking, expense breakdowns, and forecasting
2. **Corporate Overview Data**: Analyze company financial metrics including revenue trends, net income, market cap, and employee growth

The app uses smart detection to automatically identify the data format and provide appropriate analysis tools. Personal finance features include customizable rule-based pattern matching, budget alerts, and persistent database storage. Corporate analysis provides year-over-year comparisons and trend visualizations.

**Last Updated**: November 9, 2025

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Framework
**Decision**: Streamlit  
**Rationale**: Streamlit provides a rapid, Python-native way to build interactive data applications without requiring separate frontend code. This allows for quick prototyping and seamless integration with data analysis libraries.

**Pros**:
- Minimal boilerplate code
- Native Python integration
- Built-in caching and state management
- Automatic UI generation from Python code

**Cons**:
- Limited customization compared to traditional web frameworks
- Single-user session model

## Data Processing Pipeline
**Decision**: Pandas-based ETL with automated categorization  
**Rationale**: The application uses Pandas for data ingestion and transformation, with a rule-based categorization system using regex patterns to automatically classify transactions.

**Key Components**:
1. **Data Loading**: Supports both CSV and Excel file formats
2. **Date Parsing**: Converts date fields with error handling
3. **Auto-categorization**: Rule-based pattern matching on transaction descriptions
4. **Data Validation**: Removes invalid numeric amounts and missing dates

**Categories Detected**:
- Income (salary, freelance, revenue)
- Expense (rent, utilities, food, transport, bills)
- Investment (stocks, crypto)
- Uncategorized (fallback)

## Time Series Analysis
**Decision**: Monthly aggregation with period-based grouping  
**Rationale**: Financial data is most meaningful when analyzed over monthly periods, allowing users to identify spending patterns and track trends.

**Approach**:
- Convert transactions to monthly periods using Pandas Period functionality
- Group by month and category for aggregated views
- Fill missing months to maintain continuous time series

## Forecasting Capability
**Decision**: Scikit-learn Linear Regression  
**Rationale**: Simple linear models provide interpretable predictions for basic financial forecasting without requiring complex machine learning infrastructure.

**Use Case**: Project future income/expense trends based on historical patterns

## Visualization Strategy
**Decision**: Matplotlib and Seaborn  
**Rationale**: These libraries provide publication-quality visualizations that integrate seamlessly with Streamlit and Pandas.

**Expected Visualizations**:
- Monthly spending trends
- Category breakdowns
- Income vs. expense comparisons

## Report Generation
**Decision**: ReportLab for PDF export  
**Rationale**: Users need exportable reports for record-keeping and sharing.

**Components**:
- PDF generation with structured layouts
- Tables for transaction summaries
- Integration with analysis results

## Database Persistence
**Decision**: PostgreSQL with psycopg2  
**Rationale**: User-defined rules and budgets need to persist across sessions. PostgreSQL provides reliable, ACID-compliant storage for these critical settings.

**Database Schema**:
- `custom_rules`: Stores user-defined keyword-to-category mappings
- `budgets`: Stores budget amounts per category with timestamps

**Features**:
- Custom categorization rules persist across sessions
- Budget settings persist and track spending against limits
- Duplicate keyword prevention
- Error handling with user-visible feedback

## Dual-Format Data Support (November 2025)

### Intelligent Data Detection
The app now automatically detects and handles two distinct data formats:

**1. Personal Finance Transactions**
- Required columns: `Date`, `Description`, `Amount`
- Features: Auto-categorization, budgets, custom rules, expense breakdown, seasonal analysis
- Use case: Bank statements, credit card transactions, personal spending tracking

**2. Corporate Overview Data**
- Detected columns: `Year`, `Revenue`, `Net Income`, `Market Cap`, `Employees`, etc.
- Features: Revenue trends, income comparisons, employee growth, year-over-year metrics
- Use case: Company financial reports, brand performance analysis, corporate benchmarking

### Detection Algorithm
Uses fuzzy column matching to identify data type:
- Corporate indicators: year, revenue, net income, market cap, employees, ceo
- Personal finance indicators: date, description, amount, transaction
- Threshold: 3+ matches for corporate, 2+ for personal finance

### Separate Analysis Paths
- Data is NOT mixed - corporate and personal finance files are analyzed independently
- Each type gets custom UI, visualizations, and metrics
- Database features (custom rules, budgets) only apply to personal finance data

## Recent Enhancements (November 2025)

### New Features Added:
1. **Custom Categorization Rules**: Users can add/delete persistent keyword rules that override default categorization
2. **Budget Tracking**: Set budgets per category with visual alerts (red >100%, yellow >90%, green <90%)
3. **Expense Subcategorization**: Automatic breakdown into Housing, Food & Dining, Transportation, Utilities, Other with pie chart visualization
4. **Year-over-Year Analysis**: Compare financial data across multiple years
5. **Seasonal Trend Detection**: Identify spending patterns by season (Winter, Spring, Summer, Fall)
6. **Date Range Filtering**: Filter analysis to specific date ranges
7. **Multi-file Upload**: Upload and compare multiple CSV/Excel files simultaneously
8. **Enhanced UI**: Tabbed interface for different analysis views

### Robustness Improvements:
- Empty date range handling with user warnings
- Missing category protection (ensures Income, Expense, Investment columns exist)
- Forecast safety checks for insufficient data
- Pie chart validation to prevent negative/zero value errors
- Memory leak prevention with matplotlib figure cleanup
- Duplicate rule prevention
- Database error visibility to users

# External Dependencies

## Data Analysis Libraries
- **Pandas**: Core data manipulation and time series analysis
- **NumPy**: Numerical operations and array handling
- **Scikit-learn**: Linear regression for financial forecasting

## Visualization Libraries
- **Matplotlib**: Base plotting library
- **Seaborn**: Statistical visualizations with enhanced aesthetics

## PDF Generation
- **ReportLab**: Professional PDF document creation with tables and formatted text

## Web Framework
- **Streamlit**: Interactive web application framework with built-in widgets and caching

## Utility Libraries
- **re** (built-in): Regular expressions for transaction categorization
- **io.BytesIO** (built-in): In-memory file handling for PDF generation
- **base64** (built-in): Encoding for file downloads

## Data Formats Supported
- CSV files (via Pandas)
- Excel files (via Pandas with openpyxl/xlrd)

**Expected Data Schema**:
- `Date`: Transaction date
- `Description`: Text description for categorization
- `Amount`: Numeric transaction value