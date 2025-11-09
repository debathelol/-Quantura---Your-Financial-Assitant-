# Overview

This dual-format financial analysis application, built with Streamlit and PostgreSQL, intelligently analyzes Personal Finance Transactions and Corporate Overview Data. Its primary purpose is to offer tools for financial tracking, forecasting, and reporting, aiming to simplify financial management for individuals and provide insightful analytics for businesses. Key capabilities include automatic transaction categorization, budget tracking, financial forecasting, multi-currency support for personal finance, revenue trend analysis, financial ratio calculation, and competitor comparison for corporate data. The project aspires to be a user-friendly and powerful platform for diverse financial analysis needs.

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

## Feature Specifications
- **Personal Finance**: Automatic categorization (Income, Expense, Investment, Uncategorized), custom categorization rules, budget tracking, expense subcategorization, savings goals, multi-currency support, monthly spending trends, income vs. expense comparisons, and CSV/Excel export.
- **Corporate Analysis**: Revenue trends, income comparisons, employee growth, year-over-year metrics, financial ratios, competitor comparison with interactive charts, and downloadable PDF reports.
- **General**: Customizable dashboard, chart PNG downloads, date range filtering, multi-file upload, and an AI-powered financial assistant.

## System Design Choices
The architecture adopts a modular approach, separating data ingestion, processing, analysis, and presentation. Streamlit provides a unified Python codebase for frontend and backend. PostgreSQL ensures reliable, ACID-compliant storage for critical user data. A hybrid visualization strategy uses Plotly for interactive elements and Matplotlib/Seaborn for static outputs.

# External Dependencies

## Data Analysis Libraries
- **Pandas**: Data manipulation and time series.
- **NumPy**: Numerical operations.
- **Scikit-learn**: Linear regression for forecasting.

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
- **OpenAI GPT-4o-mini**: Via Replit AI Integrations for the chatbot.

## Data Formats Supported
- CSV files.
- Excel files (requires `openpyxl`/`xlrd`).