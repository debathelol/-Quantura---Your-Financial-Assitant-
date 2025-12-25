import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import re
from io import BytesIO
import base64
from sklearn.linear_model import LinearRegression
import psycopg2
import os
from datetime import datetime
from ui_components.charts import fig_to_png_download, add_plotly_animations
from openai import OpenAI
import json
from services.stock_analyzer import StockAnalyzer
from services.stock_ai_analyzer import get_ai_stock_analysis, get_ai_portfolio_insights
from services.company_lookup import lookup_company_ticker
from ui_components.stock_charts import (
    create_candlestick_chart, create_monte_carlo_chart, create_arima_forecast_chart,
    create_correlation_heatmap, create_risk_return_scatter, create_volatility_chart,
    create_pca_chart, create_greeks_chart
)
from ui_components.metrics import render_metric_card, render_metric_row, render_highlight_box
from ui_components.progress import render_progress_bar, render_donut_chart, render_gauge_chart

# ============================================================================
# CACHED STOCK DATA FUNCTIONS - Prevents Yahoo Finance Rate Limiting
# ============================================================================

def get_cached_stock_data(ticker, period='2y'):
    """
    Fetch stock price history with caching for successful results only.
    Errors are not cached to allow immediate retry.

    Returns: (success, data_df, returns_series, error_message)
    """
    # Try to get from cache first
    cache_key = f"stock_data_{ticker}_{period}"
    if cache_key in st.session_state:
        cached = st.session_state[cache_key]
        # Check if cache is still valid (5 minutes)
        if (datetime.now() - cached['timestamp']).seconds < 300:
            return True, cached['data'], cached['returns'], None

    # Fetch fresh data
    analyzer = StockAnalyzer(ticker)
    success, error = analyzer.fetch_data_yfinance(period=period)

    if success and analyzer.data is not None:
        # Only cache successful results
        st.session_state[cache_key] = {
            'data': analyzer.data.copy(),
            'returns': analyzer.returns.copy() if analyzer.returns is not None else None,
            'timestamp': datetime.now()
        }
        return True, analyzer.data.copy(), analyzer.returns.copy() if analyzer.returns is not None else None, None

    # Don't cache errors - allow immediate retry
    return False, None, None, error

def get_cached_stock_quote(ticker):
    """Cache stock quote data for 5 minutes - only caches successful results"""
    # Try to get from cache first
    cache_key = f"stock_quote_{ticker}"
    if cache_key in st.session_state:
        cached = st.session_state[cache_key]
        # Check if cache is still valid (5 minutes)
        if (datetime.now() - cached['timestamp']).seconds < 300:
            return cached['quote'], None

    # Fetch fresh data
    analyzer = StockAnalyzer(ticker)
    success, error = analyzer.fetch_data_yfinance(period='5d')

    if success:
        quote, quote_error = analyzer.get_quote()
        if quote and not quote_error:
            # Only cache successful results
            st.session_state[cache_key] = {
                'quote': quote,
                'timestamp': datetime.now()
            }
        return quote, quote_error

    # Don't cache errors - allow immediate retry
    return None, error

def get_db_connection():
    """Get database connection. Returns None if DATABASE_URL not available."""
    try:
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            return None
        return psycopg2.connect(db_url)
    except Exception:
        return None

def get_custom_rules():
    try:
        conn = get_db_connection()
        if conn is None:
            return []
        cur = conn.cursor()
        cur.execute("SELECT keyword, category FROM custom_rules")
        rules = cur.fetchall()
        cur.close()
        conn.close()
        return rules
    except Exception as e:
        # Silently return empty list if database not available
        return []

def add_custom_rule(keyword, category):
    try:
        conn = get_db_connection()
        if conn is None:
            return False, "Database not available on this platform"
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM custom_rules WHERE keyword = %s", (keyword,))
        count = cur.fetchone()[0]
        if count > 0:
            cur.close()
            conn.close()
            return False, "Keyword already exists"
        cur.execute("INSERT INTO custom_rules (keyword, category) VALUES (%s, %s)", (keyword, category))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)

def delete_custom_rule(keyword):
    try:
        conn = get_db_connection()
        if conn is None:
            return False, "Database not available on this platform"
        cur = conn.cursor()
        cur.execute("DELETE FROM custom_rules WHERE keyword = %s", (keyword,))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)

def get_budgets():
    try:
        conn = get_db_connection()
        if conn is None:
            return {}
        cur = conn.cursor()
        cur.execute("SELECT category, budget_amount FROM budgets")
        budgets = dict(cur.fetchall())
        cur.close()
        conn.close()
        return budgets
    except Exception as e:
        # Silently return empty dict if database not available
        return {}

def set_budget(category, amount):
    try:
        conn = get_db_connection()
        if conn is None:
            return False, "Database not available on this platform"
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO budgets (category, budget_amount, updated_at) 
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (category) 
            DO UPDATE SET budget_amount = %s, updated_at = CURRENT_TIMESTAMP
        """, (category, amount, amount))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)

def get_savings_goals():
    try:
        conn = get_db_connection()
        if conn is None:
            return []
        cur = conn.cursor()
        cur.execute("""
            SELECT id, goal_name, target_amount, current_amount, deadline, created_at 
            FROM savings_goals ORDER BY created_at DESC
        """)
        goals = cur.fetchall()
        cur.close()
        conn.close()
        return goals
    except Exception as e:
        # Silently return empty list if database not available
        return []

def add_savings_goal(goal_name, target_amount, current_amount, deadline):
    try:
        conn = get_db_connection()
        if conn is None:
            return False, "Database not available on this platform"
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO savings_goals (goal_name, target_amount, current_amount, deadline) 
            VALUES (%s, %s, %s, %s)
        """, (goal_name, target_amount, current_amount, deadline))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)

def update_savings_goal(goal_id, current_amount):
    try:
        conn = get_db_connection()
        if conn is None:
            return False, "Database not available on this platform"
        cur = conn.cursor()
        cur.execute("""
            UPDATE savings_goals SET current_amount = %s WHERE id = %s
        """, (current_amount, goal_id))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)

def delete_savings_goal(goal_id):
    try:
        conn = get_db_connection()
        if conn is None:
            return False, "Database not available on this platform"
        cur = conn.cursor()
        cur.execute("DELETE FROM savings_goals WHERE id = %s", (goal_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)

def get_exchange_rates():
    """Returns exchange rates to USD (as of common reference rates)"""
    return {
        'USD': 1.0,
        'EUR': 1.08,
        'GBP': 1.27,
        'CAD': 0.72,
        'AUD': 0.65,
        'JPY': 0.0067,
        'CNY': 0.14,
        'INR': 0.012,
        'MXN': 0.058,
        'BRL': 0.20
    }

def convert_to_usd(amount, from_currency):
    """Convert amount from given currency to USD"""
    rates = get_exchange_rates()
    if from_currency in rates:
        return amount * rates[from_currency]
    return amount

def detect_data_type(df):
    """Detect if data is personal finance transactions or corporate overview"""
    columns_lower = [col.lower() for col in df.columns]
    
    # Corporate data indicators
    corporate_indicators = ['year', 'revenue', 'net income', 'market cap', 'employees', 'ceo']
    corporate_matches = sum(1 for indicator in corporate_indicators if any(indicator in col for col in columns_lower))
    
    # Personal finance indicators
    finance_indicators = ['date', 'description', 'amount', 'transaction']
    finance_matches = sum(1 for indicator in finance_indicators if any(indicator in col for col in columns_lower))
    
    if corporate_matches >= 3:
        return 'corporate'
    elif finance_matches >= 2:
        return 'personal_finance'
    else:
        return 'unknown'

def load_and_categorize(uploaded_file, custom_rules=None, currency='USD'):
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    data_type = detect_data_type(df)
    
    if data_type == 'corporate':
        # Corporate data - return as-is with metadata
        df['data_type'] = 'corporate'
        return df
    
    # Personal finance data - validate and categorize
    # Smart column detection - handle variations like "Amount (USD)", "Amount (EUR)", etc.
    # Prioritize exact matches first, then common variations
    def find_date_column(columns):
        # Exact matches first
        exact_matches = ['Date', 'date', 'DATE', 'Transaction Date', 'Posted Date', 'Posting Date']
        for col in columns:
            if col in exact_matches:
                return col
        # Common patterns
        for col in columns:
            col_lower = col.lower()
            if col_lower in ['date', 'transaction date', 'posted date', 'posting date', 'trans date']:
                return col
        # Fuzzy match (but must start with date or end with date)
        for col in columns:
            col_lower = col.lower()
            if col_lower.startswith('date') or col_lower.endswith('date'):
                return col
        return None
    
    def find_description_column(columns):
        # Exact matches first
        exact_matches = ['Description', 'description', 'DESCRIPTION', 'Desc', 'desc']
        for col in columns:
            if col in exact_matches:
                return col
        # Common patterns
        for col in columns:
            col_lower = col.lower()
            if col_lower in ['description', 'desc', 'transaction description', 'memo', 'narrative']:
                return col
        # Fuzzy match
        for col in columns:
            col_lower = col.lower()
            if 'description' in col_lower or 'desc' in col_lower:
                return col
        return None
    
    def find_amount_column(columns):
        # Exact matches first
        exact_matches = ['Amount', 'amount', 'AMOUNT']
        for col in columns:
            if col in exact_matches:
                return col
        # Common patterns with currency codes
        for col in columns:
            col_lower = col.lower()
            if col_lower.startswith('amount'):
                return col
        return None
    
    date_col = find_date_column(df.columns)
    desc_col = find_description_column(df.columns)
    amount_col = find_amount_column(df.columns)
    
    # Rename columns to standard format
    if date_col and desc_col and amount_col:
        df = df.rename(columns={
            date_col: 'Date',
            desc_col: 'Description',
            amount_col: 'Amount'
        })
    else:
        missing = []
        if not date_col: missing.append('Date')
        if not desc_col: missing.append('Description')
        if not amount_col: missing.append('Amount')
        raise ValueError(f"Missing required columns: {', '.join(missing)}. Your file has: {', '.join(df.columns.tolist())}. Please ensure your CSV has columns containing 'Date', 'Description', and 'Amount'.")
    
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    
    def categorize(desc):
        if pd.isna(desc):
            return 'Uncategorized'
        desc_lower = str(desc).lower()
        
        if custom_rules:
            for keyword, category in custom_rules:
                if keyword.lower() in desc_lower:
                    return category
        
        if re.search(r'salary|income|payment received|revenue|freelance', desc_lower):
            return 'Income'
        elif re.search(r'rent|utilities|food|transport|expense|bill|groceries', desc_lower):
            return 'Expense'
        elif re.search(r'invest|stock|crypto', desc_lower):
            return 'Investment'
        else:
            return 'Uncategorized'
    
    df['Category'] = df['Description'].apply(categorize)
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df = df[df['Amount'].notna()]
    
    # Apply currency conversion
    if currency != 'USD':
        df['Amount'] = df['Amount'].apply(lambda x: convert_to_usd(x, currency))
    
    df['data_type'] = 'personal_finance'
    
    return df

def analyze_corporate_data(df):
    """Analyze corporate overview data"""
    year_col = next((col for col in df.columns if 'year' in col.lower()), None)
    revenue_col = next((col for col in df.columns if 'revenue' in col.lower()), None)
    income_col = next((col for col in df.columns if 'net income' in col.lower() or 'income' in col.lower()), None)
    marketcap_col = next((col for col in df.columns if 'market cap' in col.lower()), None)
    employees_col = next((col for col in df.columns if 'employee' in col.lower()), None)
    
    return {
        'year_col': year_col,
        'revenue_col': revenue_col,
        'income_col': income_col,
        'marketcap_col': marketcap_col,
        'employees_col': employees_col
    }

def calculate_financial_ratios(df, col_info):
    """Calculate key financial ratios for corporate data"""
    ratios = {}
    
    if col_info['revenue_col'] and col_info['income_col']:
        latest_revenue = df[col_info['revenue_col']].iloc[-1]
        latest_income = df[col_info['income_col']].iloc[-1]
        if latest_revenue > 0:
            ratios['Profit Margin (%)'] = round((latest_income / latest_revenue) * 100, 2)
    
    if col_info['revenue_col'] and col_info['employees_col']:
        latest_revenue = df[col_info['revenue_col']].iloc[-1]
        latest_employees = df[col_info['employees_col']].iloc[-1]
        if latest_employees > 0:
            ratios['Revenue per Employee ($B)'] = round(latest_revenue / latest_employees, 4)
    
    if col_info['revenue_col'] and len(df) > 1:
        latest_revenue = df[col_info['revenue_col']].iloc[-1]
        previous_revenue = df[col_info['revenue_col']].iloc[-2]
        if previous_revenue > 0:
            ratios['Revenue Growth (%)'] = round(((latest_revenue - previous_revenue) / previous_revenue) * 100, 2)
    
    if col_info['employees_col'] and len(df) > 1:
        latest_employees = df[col_info['employees_col']].iloc[-1]
        previous_employees = df[col_info['employees_col']].iloc[-2]
        if previous_employees > 0:
            ratios['Employee Growth (%)'] = round(((latest_employees - previous_employees) / previous_employees) * 100, 2)
    
    return ratios

def build_company_comparison(all_dfs):
    """Build comparison dataframe for multiple companies"""
    comparison_data = []
    
    for df in all_dfs:
        if 'Source' not in df.columns or df.empty:
            continue
            
        company_name = df['Source'].iloc[0] if 'Source' in df.columns else "Unknown"
        col_info = analyze_corporate_data(df)
        
        company_metrics = {'Company': company_name}
        
        # Latest year
        if col_info['year_col']:
            company_metrics['Latest Year'] = df[col_info['year_col']].iloc[-1]
        
        # Revenue
        if col_info['revenue_col']:
            company_metrics['Revenue ($B)'] = round(df[col_info['revenue_col']].iloc[-1], 2)
        
        # Net Income
        if col_info['income_col']:
            company_metrics['Net Income ($B)'] = round(df[col_info['income_col']].iloc[-1], 2)
        
        # Employees
        if col_info['employees_col']:
            company_metrics['Employees'] = int(df[col_info['employees_col']].iloc[-1])
        
        # Financial Ratios
        ratios = calculate_financial_ratios(df, col_info)
        company_metrics.update(ratios)
        
        comparison_data.append(company_metrics)
    
    return pd.DataFrame(comparison_data)

def generate_corporate_pdf(df, col_info):
    """Generate PDF report for corporate data"""
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    company_name = df['Source'].iloc[0] if 'Source' in df.columns else "Corporate Report"
    
    story.append(Paragraph(f"Corporate Financial Report: {company_name}", styles['Title']))
    story.append(Spacer(1, 12))
    
    # Latest metrics
    latest_year = df[col_info['year_col']].iloc[-1] if col_info['year_col'] else "N/A"
    latest_revenue = df[col_info['revenue_col']].iloc[-1] if col_info['revenue_col'] else 0
    latest_income = df[col_info['income_col']].iloc[-1] if col_info['income_col'] else 0
    latest_employees = df[col_info['employees_col']].iloc[-1] if col_info['employees_col'] else 0
    
    story.append(Paragraph(f"Latest Year: {latest_year}", styles['Heading2']))
    story.append(Spacer(1, 6))
    
    metrics_data = [['Metric', 'Value']]
    if col_info['revenue_col']:
        metrics_data.append(['Revenue', f"${latest_revenue:.2f}B"])
    if col_info['income_col']:
        metrics_data.append(['Net Income', f"${latest_income:.2f}B"])
    if col_info['employees_col']:
        metrics_data.append(['Employees', f"{int(latest_employees):,}"])
    
    # Add financial ratios
    ratios = calculate_financial_ratios(df, col_info)
    for ratio_name, ratio_value in ratios.items():
        metrics_data.append([ratio_name, str(ratio_value)])
    
    table = Table(metrics_data)
    table.setStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Add Revenue Trend Chart
    if col_info['year_col'] and col_info['revenue_col']:
        story.append(Paragraph("Revenue Trend", styles['Heading2']))
        story.append(Spacer(1, 6))
        
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(df[col_info['year_col']], df[col_info['revenue_col']], 
                marker='o', linewidth=2, color='#6366f1')
        ax.set_xlabel('Year')
        ax.set_ylabel('Revenue (USD Billion)')
        ax.set_title('Revenue Growth Over Time')
        ax.grid(True, alpha=0.3)
        
        # Save chart to buffer
        chart_buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(chart_buffer, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        chart_buffer.seek(0)
        
        # Add chart to PDF
        img = RLImage(chart_buffer, width=5*inch, height=3.5*inch)
        story.append(img)
    
    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer

def analyze_finances(df, date_range=None):
    df_filtered = df.copy()
    if date_range:
        start_date, end_date = date_range
        df_filtered = df_filtered[(df_filtered['Date'] >= start_date) & (df_filtered['Date'] <= end_date)]
    
    if len(df_filtered) == 0:
        empty_metrics = {
            'Total Income': 0,
            'Total Expenses': 0,
            'Net Profit': 0,
            'Profit Margin (%)': 0,
            'Total Investments': 0,
            '3-Month Income Forecast': 0
        }
        empty_monthly = pd.DataFrame(columns=['Income', 'Expense', 'Investment'])
        return pd.Series(empty_metrics), empty_monthly, df_filtered
    
    df_filtered['Month'] = df_filtered['Date'].dt.to_period('M')
    monthly = df_filtered.groupby(['Month', 'Category'])['Amount'].sum().unstack(fill_value=0)
    
    all_months = pd.period_range(start=df_filtered['Date'].min().to_period('M'), 
                                 end=df_filtered['Date'].max().to_period('M'), freq='M')
    monthly = monthly.reindex(all_months, fill_value=0)
    
    for category in ['Income', 'Expense', 'Investment']:
        if category not in monthly.columns:
            monthly[category] = 0
    
    total_income = monthly['Income'].sum() if 'Income' in monthly.columns else 0
    total_expense = abs(monthly['Expense'].sum()) if 'Expense' in monthly.columns else 0
    total_invest = abs(monthly['Investment'].sum()) if 'Investment' in monthly.columns else 0
    profit = total_income - total_expense
    margin = (profit / total_income * 100) if total_income > 0 else 0
    
    if len(monthly) > 1 and 'Income' in monthly.columns and monthly['Income'].sum() > 0:
        months_num = np.arange(len(monthly)).reshape(-1, 1)
        income_trend = monthly['Income'].values.reshape(-1, 1)
        model = LinearRegression().fit(months_num, income_trend)
        future_months = np.arange(len(monthly), len(monthly) + 3).reshape(-1, 1)
        forecast = model.predict(future_months).flatten()
    else:
        forecast = [total_income] * 3
    
    metrics = {
        'Total Income': total_income,
        'Total Expenses': total_expense,
        'Net Profit': profit,
        'Profit Margin (%)': round(margin, 2),
        'Total Investments': total_invest,
        '3-Month Income Forecast': sum(forecast)
    }
    return pd.Series(metrics), monthly, df_filtered

def get_expense_subcategories(df):
    expenses_df = df[df['Category'] == 'Expense'].copy()
    
    def subcategorize(desc):
        if pd.isna(desc):
            return 'Other'
        desc_lower = str(desc).lower()
        if re.search(r'rent', desc_lower):
            return 'Housing'
        elif re.search(r'food|groceries|restaurant', desc_lower):
            return 'Food & Dining'
        elif re.search(r'transport|taxi|gas', desc_lower):
            return 'Transportation'
        elif re.search(r'utilities|bill|electric|water|internet|phone', desc_lower):
            return 'Utilities'
        else:
            return 'Other'
    
    expenses_df['Subcategory'] = expenses_df['Description'].apply(subcategorize)
    return expenses_df.groupby('Subcategory')['Amount'].sum()

def year_over_year_analysis(df):
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month
    
    yearly_data = df.groupby(['Year', 'Month', 'Category'])['Amount'].sum().unstack(fill_value=0)
    
    years = df['Year'].unique()
    if len(years) < 2:
        return None
    
    return yearly_data

def detect_seasonal_trends(df):
    df['Month'] = df['Date'].dt.month
    df['Season'] = df['Month'].apply(lambda x: 
        'Winter' if x in [12, 1, 2] else
        'Spring' if x in [3, 4, 5] else
        'Summer' if x in [6, 7, 8] else 'Fall')
    
    seasonal_spending = df[df['Category'] == 'Expense'].groupby('Season')['Amount'].sum()
    return seasonal_spending

def detect_recurring_transactions(df, min_transactions=3, max_time_std=5, max_amount_pct=0.05):
    """Detect recurring transactions (subscriptions, rent, etc.)"""
    if len(df) < min_transactions:
        return pd.DataFrame()
    
    df_copy = df.copy()
    df_copy['Date'] = pd.to_datetime(df_copy['Date'])
    df_copy = df_copy.sort_values(['Description', 'Date'])
    
    results = []
    
    for description, group in df_copy.groupby('Description'):
        if len(group) < min_transactions:
            continue
        
        for amount in group['Amount'].unique():
            # Handle negative amounts (expenses) by computing min/max correctly
            lower_bound = min(amount * (1 - max_amount_pct), amount * (1 + max_amount_pct))
            upper_bound = max(amount * (1 - max_amount_pct), amount * (1 + max_amount_pct))
            
            amount_group = group[group['Amount'].between(lower_bound, upper_bound)]
            
            if len(amount_group) < min_transactions:
                continue
            
            amount_group = amount_group.sort_values('Date')
            days_diff = amount_group['Date'].diff().dt.days.dropna()
            
            if len(days_diff) == 0:
                continue
            
            time_std = days_diff.std()
            mean_interval = days_diff.mean()
            
            if time_std <= max_time_std:
                # Determine frequency type
                if 28 <= mean_interval <= 32:
                    frequency = "Monthly"
                elif 6 <= mean_interval <= 8:
                    frequency = "Weekly"
                elif 85 <= mean_interval <= 95:
                    frequency = "Quarterly"
                else:
                    frequency = f"Every {int(mean_interval)} days"
                
                results.append({
                    'Description': description,
                    'Amount': amount,
                    'Frequency': frequency,
                    'Interval (days)': round(mean_interval, 1),
                    'Count': len(amount_group),
                    'Next Expected': amount_group['Date'].max() + pd.Timedelta(days=mean_interval)
                })
    
    return pd.DataFrame(results).sort_values('Amount', ascending=False) if results else pd.DataFrame()

def generate_smart_insights(df, date_range=None):
    """Generate automatic financial insights and anomalies"""
    insights = []
    
    if len(df) == 0:
        return insights
    
    # Calculate current period metrics
    if date_range:
        current_df = df[(df['Date'] >= date_range[0]) & (df['Date'] <= date_range[1])]
    else:
        current_df = df
    
    # Insight 1: Highest expense category
    expense_by_cat = current_df[current_df['Category'] == 'Expense'].groupby('Description')['Amount'].sum().sort_values(ascending=False)
    if len(expense_by_cat) > 0:
        top_expense = expense_by_cat.index[0]
        top_amount = expense_by_cat.iloc[0]
        insights.append({
            'type': 'info',
            'icon': '💰',
            'message': f"Your biggest expense is **{top_expense}** at **${top_amount:,.2f}**"
        })
    
    # Insight 2: Month-over-month comparison
    if 'Date' in current_df.columns and len(current_df) > 0:
        current_df['YearMonth'] = current_df['Date'].dt.to_period('M')
        monthly_spending = current_df[current_df['Category'] == 'Expense'].groupby('YearMonth')['Amount'].sum().sort_index()
        
        if len(monthly_spending) >= 2:
            last_month = monthly_spending.iloc[-1]
            prev_month = monthly_spending.iloc[-2]
            pct_change = ((last_month - prev_month) / prev_month * 100) if prev_month > 0 else 0
            
            if abs(pct_change) > 20:
                emoji = '📈' if pct_change > 0 else '📉'
                direction = 'increased' if pct_change > 0 else 'decreased'
                insights.append({
                    'type': 'warning' if pct_change > 0 else 'success',
                    'icon': emoji,
                    'message': f"Your spending {direction} by **{abs(pct_change):.1f}%** compared to last month"
                })
    
    # Insight 3: Detect unusual large transactions
    if len(current_df) > 10:
        mean_amount = current_df['Amount'].mean()
        std_amount = current_df['Amount'].std()
        threshold = mean_amount + (2 * std_amount)
        
        unusual = current_df[current_df['Amount'] > threshold]
        if len(unusual) > 0:
            insights.append({
                'type': 'warning',
                'icon': '⚠️',
                'message': f"Found **{len(unusual)}** unusually large transaction(s) above ${threshold:,.2f}"
            })
    
    # Insight 4: Income trend
    income_data = current_df[current_df['Category'] == 'Income']
    if len(income_data) > 0:
        total_income = income_data['Amount'].sum()
        total_expense = current_df[current_df['Category'] == 'Expense']['Amount'].sum()
        savings_rate = ((total_income - total_expense) / total_income * 100) if total_income > 0 else 0
        
        if savings_rate > 30:
            insights.append({
                'type': 'success',
                'icon': '🎯',
                'message': f"Great job! You're saving **{savings_rate:.1f}%** of your income"
            })
        elif savings_rate < 10:
            insights.append({
                'type': 'warning',
                'icon': '💡',
                'message': f"Your savings rate is **{savings_rate:.1f}%**. Consider reducing expenses to save more"
            })
    
    return insights

def generate_report(metrics, monthly, df):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    monthly[['Income', 'Expense']].plot(kind='bar', stacked=True, ax=ax1)
    ax1.set_title('Monthly Income vs Expenses')
    ax1.set_ylabel('Amount ($)')
    ax1.legend()
    
    net_profit = monthly.get('Income', 0) - monthly.get('Expense', 0)
    net_profit.plot(kind='line', ax=ax2, marker='o')
    ax2.set_title('Net Profit Trend')
    ax2.set_ylabel('Profit ($)')
    
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    chart_url = base64.b64encode(buf.getvalue()).decode()
    plt.close(fig)
    
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    story.append(Paragraph("Financial Report Summary", styles['Title']))
    story.append(Spacer(1, 12))
    
    data = [['Metric', 'Value']] + [[k, f"${float(v):,.2f}"] for k, v in metrics.items()]
    table = Table(data)
    table.setStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])
    story.append(table)
    story.append(Spacer(1, 12))
    story.append(Paragraph("Uncategorized Items for Review:", styles['Heading2']))
    uncat = df[df['Category'] == 'Uncategorized'][['Date', 'Description', 'Amount']]
    if not uncat.empty:
        uncat_data = [list(uncat.columns)] + uncat.values.tolist()
        uncat_table = Table(uncat_data)
        uncat_table.setStyle([('GRID', (0, 0), (-1, -1), 1, colors.black)])
        story.append(uncat_table)
    else:
        story.append(Paragraph("All items categorized! 🎉", styles['Normal']))
    
    doc.build(story)
    pdf_buffer.seek(0)
    
    return chart_url, pdf_buffer

# AI Chatbot Functions
def init_openai_client():
    """Initialize OpenAI client with Replit AI Integrations"""
    return OpenAI(
        api_key=os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY"),
        base_url=os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
    )

def get_financial_context(df=None):
    """Get financial data context for AI chatbot"""
    context = {}
    
    if df is not None and not df.empty:
        # Aggregate spending by category
        if 'Category' in df.columns and 'Amount' in df.columns:
            try:
                category_totals = df.groupby('Category')['Amount'].sum().to_dict()
                context['category_spending'] = {k: float(v) for k, v in category_totals.items()}
                context['total_spending'] = float(df['Amount'].sum())
            except Exception as e:
                print(f"Warning: Failed to aggregate spending data: {str(e)}")
        
        # Get date range
        if 'Date' in df.columns:
            try:
                context['date_range'] = {
                    'start': str(df['Date'].min()),
                    'end': str(df['Date'].max())
                }
            except Exception as e:
                print(f"Warning: Failed to extract date range: {str(e)}")
    
    # Get budgets
    try:
        budgets = get_budgets()
        context['budgets'] = {k: float(v) for k, v in budgets.items()}
    except Exception as e:
        print(f"Warning: Failed to fetch budgets: {str(e)}")
        context['budgets'] = {}
    
    # Get savings goals
    try:
        goals = get_savings_goals()
        context['savings_goals'] = []
        for goal in goals:
            context['savings_goals'].append({
                'name': goal[1],
                'target': float(goal[2]),
                'current': float(goal[3]),
                'deadline': str(goal[4]) if goal[4] else None
            })
    except Exception as e:
        print(f"Warning: Failed to fetch savings goals: {str(e)}")
        context['savings_goals'] = []
    
    return context

def get_ai_budget_recommendations(df):
    """Use AI to analyze spending patterns and recommend optimal budgets"""
    try:
        client = init_openai_client()
    except Exception as e:
        # Fallback to demo mode when client initialization fails
        print(f"[DEMO MODE] OpenAI client init failed, using demo budget data: {str(e)}")
        return {
            "budgets": {"Income": 5000, "Expense": 3500, "Investment": 1000},
            "explanation": "⚠️ **Demo Mode** - Based on typical spending patterns, we recommend allocating 50% to essential expenses, 30% to discretionary spending, and 20% to savings/investments. This balanced approach helps build wealth while maintaining lifestyle.",
            "tip": "⚠️ **Demo Mode** - Start by tracking every expense for 30 days to understand where your money actually goes. Small daily expenses often add up to surprisingly large amounts!"
        }, None
    
    if df is None or df.empty:
        return None, "No transaction data available. Please upload your financial data first."
    
    analysis_context = {}
    
    if 'Category' in df.columns and 'Amount' in df.columns:
        try:
            category_totals = df.groupby('Category')['Amount'].sum().to_dict()
            analysis_context['category_spending'] = {k: float(v) for k, v in category_totals.items()}
            analysis_context['total_spending'] = float(df['Amount'].sum())
            
            if 'Date' in df.columns:
                df_copy = df.copy()
                df_copy['Date'] = pd.to_datetime(df_copy['Date'])
                months = (df_copy['Date'].max() - df_copy['Date'].min()).days / 30.44
                if months > 0:
                    analysis_context['months_of_data'] = round(months, 1)
                    monthly_avg = df_copy.groupby(['Category', pd.Grouper(key='Date', freq='M')])['Amount'].sum().reset_index()
                    monthly_category_avg = monthly_avg.groupby('Category')['Amount'].mean().to_dict()
                    analysis_context['monthly_avg_by_category'] = {k: float(v) for k, v in monthly_category_avg.items()}
        except Exception as e:
            print(f"Warning: Failed to analyze spending data: {str(e)}")
            return None, f"Failed to analyze spending data: {str(e)}"
    
    current_budgets = get_budgets()
    analysis_context['current_budgets'] = {k: float(v) for k, v in current_budgets.items()}
    
    prompt = f"""Analyze this user's spending patterns and recommend optimal monthly budgets for Income, Expense, and Investment categories.

Spending Data:
{json.dumps(analysis_context, indent=2)}

Please provide:
1. Recommended monthly budgets for Income, Expense, and Investment
2. Brief explanation (2-3 sentences) of why these budgets make sense based on their spending patterns
3. One specific actionable tip

Format your response as JSON:
{{
    "budgets": {{"Income": <amount>, "Expense": <amount>, "Investment": <amount>}},
    "explanation": "<your explanation>",
    "tip": "<actionable tip>"
}}"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert financial advisor who analyzes spending patterns and provides practical budget recommendations. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        result_text = response.choices[0].message.content
        result_text = result_text.strip()
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        
        result = json.loads(result_text)
        return result, None
        
    except json.JSONDecodeError as e:
        print(f"[DEMO MODE] JSON parse error, using demo budget data: {str(e)}")
        # Fallback to demo mode
        return {
            "budgets": {"Income": 5000, "Expense": 3500, "Investment": 1000},
            "explanation": "⚠️ **Demo Mode** - Based on typical spending patterns, we recommend allocating 50% to essential expenses, 30% to discretionary spending, and 20% to savings/investments. This balanced approach helps build wealth while maintaining lifestyle.",
            "tip": "⚠️ **Demo Mode** - Start by tracking every expense for 30 days to understand where your money actually goes. Small daily expenses often add up to surprisingly large amounts!"
        }, None
    except Exception as e:
        error_msg = str(e)
        print(f"[DEMO MODE] API error, using demo budget data: {error_msg}")
        # Fallback to demo mode on any API error
        return {
            "budgets": {"Income": 5000, "Expense": 3500, "Investment": 1000},
            "explanation": "⚠️ **Demo Mode** - Based on typical spending patterns, we recommend allocating 50% to essential expenses, 30% to discretionary spending, and 20% to savings/investments. This balanced approach helps build wealth while maintaining lifestyle.",
            "tip": "⚠️ **Demo Mode** - Start by tracking every expense for 30 days to understand where your money actually goes. Small daily expenses often add up to surprisingly large amounts!"
        }, None

def chat_with_ai(user_message, context, chat_history):
    """Chat with AI about financial data"""
    try:
        client = init_openai_client()
    except Exception as e:
        # Fallback to demo mode when client initialization fails
        print(f"[DEMO MODE] OpenAI client init failed, using demo chatbot response: {str(e)}")
        return """⚠️ **Demo Mode** - I'm here to help with your financial questions! 

While the AI service is temporarily unavailable, here are some general financial tips:

- **Track your spending**: Understanding where your money goes is the first step to financial wellness
- **Build an emergency fund**: Aim for 3-6 months of expenses in a savings account
- **Invest for the long term**: Time in the market beats timing the market
- **Diversify your portfolio**: Don't put all your eggs in one basket

Please try your question again in a moment, or explore the other features of Quantura to analyze your finances!"""
    
    system_prompt = f"""You are a supportive financial coach for Quantura, helping users build wealth and make smart money decisions.

Your coaching style:
- Start with empathy and acknowledgment
- Share 1-2 specific, actionable insights based on their data
- End with a clear next step or encouraging question
- Use "you" and "your" to make it personal
- Be conversational, not robotic

Available Tools:
1. Magic of Compounding - See how investments grow
2. Car Purchase (20-5-10 Rule) - Smart car buying
3. Salary Planner - Budget your income wisely
4. Retirement Calculator - Plan your future
5. Debt Payoff - Get out of debt faster
6. Portfolio Analyzer - Diversify investments
7. Rent vs Buy - Housing decisions

Current Financial Data:
{json.dumps(context, indent=2)}

Response format:
1. Acknowledge their situation (1 sentence)
2. Share 2-3 actionable insights as bullet points
3. Recommend a specific calculator if relevant
4. End with an encouraging next step

Example: "I see you're spending $2,400/month on expenses. Here's what stands out:
• Your dining costs are 30% above average - try meal planning to save $200/month
• You're saving just 5% - bumping this to 15% could add $50K over 10 years
Want me to run the Compounding Calculator to show you the exact impact of saving more?"

Keep responses under 200 words, friendly, and focused on action."""
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add chat history (last 10 messages for context)
    for msg in chat_history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Add current user message
    messages.append({"role": "user", "content": user_message})
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        error_msg = str(e)
        print(f"[DEMO MODE] Chatbot API error, using demo response: {error_msg}")
        
        # Fallback to demo mode
        return """⚠️ **Demo Mode** - I'm here to help with your financial questions! 

While the AI service is temporarily unavailable, here are some general financial tips:

- **Track your spending**: Understanding where your money goes is the first step to financial wellness
- **Build an emergency fund**: Aim for 3-6 months of expenses in a savings account
- **Invest for the long term**: Time in the market beats timing the market
- **Diversify your portfolio**: Don't put all your eggs in one basket

Please try your question again in a moment, or explore the other features of Quantura to analyze your finances!"""

def explain_graph_with_ai(graph_type, data_context):
    """Use AI to explain a graph/visualization to the user in simple terms"""
    try:
        client = init_openai_client()
    except Exception as e:
        # Fallback to demo mode when client initialization fails
        print(f"[DEMO MODE] OpenAI client init failed, using demo graph explanation: {str(e)}")
        from services.stock_ai_analyzer import get_demo_graph_explanation
        return get_demo_graph_explanation(graph_type)
    
    # Create context-specific prompts based on graph type
    prompts = {
        "correlation_matrix": f"""Explain this stock correlation matrix in simple, everyday language:

{data_context}

Focus on:
- What correlation means for regular people
- Which stocks move together (high correlation)
- Which stocks are independent (low correlation)
- Why this matters for portfolio diversification
- Actionable insights for the investor

Keep it under 150 words, friendly, and avoid jargon.""",

        "risk_return_scatter": f"""Explain this risk-return scatter plot in simple terms:

{data_context}

Focus on:
- What the chart shows about each stock's performance
- Which stocks offer better risk-adjusted returns
- What the Sharpe ratio tells us
- Which stocks might be good/bad investments based on this
- Practical advice for portfolio construction

Keep it under 150 words, conversational, and actionable.""",

        "monte_carlo": f"""Explain this Monte Carlo simulation in everyday language:

{data_context}

Focus on:
- What this simulation predicts
- The range of possible outcomes
- What the confidence intervals mean
- How reliable these predictions are
- What the investor should do with this information

Keep it under 150 words, avoid technical jargon, be practical.""",

        "arima_forecast": f"""Explain this ARIMA price forecast simply:

{data_context}

Focus on:
- What the forecast predicts
- How confident we can be
- What factors could change this prediction
- Whether the investor should act on this
- Limitations of the forecast

Keep it under 150 words, clear and honest about uncertainty.""",

        "garch_volatility": f"""Explain this volatility forecast in simple terms:

{data_context}

Focus on:
- What volatility means for regular investors
- Whether volatility is increasing or decreasing
- What this means for risk
- When investors should pay attention to volatility
- Practical implications

Keep it under 150 words, friendly and actionable.""",

        "portfolio_pca": f"""Explain this PCA analysis simply:

{data_context}

Focus on:
- What this analysis reveals about the portfolio
- How the stocks relate to each other
- Whether the portfolio is well-diversified
- What adjustments might improve diversification
- Key takeaways

Keep it under 150 words, avoid technical terms, be practical."""
    }
    
    prompt = prompts.get(graph_type, f"Explain this financial chart in simple terms: {data_context}")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a friendly financial educator who explains complex charts in simple, everyday language. Avoid jargon and focus on actionable insights."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        # Fallback to demo mode on any error
        print(f"[DEMO MODE] Graph explanation error, using demo data: {str(e)}")
        from services.stock_ai_analyzer import get_demo_graph_explanation
        return get_demo_graph_explanation(graph_type)

st.set_page_config(page_title="Quantura", layout="wide")

# Dashboard Customization State
if 'show_company_section' not in st.session_state:
    st.session_state.show_company_section = True
if 'show_personal_section' not in st.session_state:
    st.session_state.show_personal_section = True
if 'show_currency_section' not in st.session_state:
    st.session_state.show_currency_section = True
if 'show_financial_tools' not in st.session_state:
    st.session_state.show_financial_tools = True
if 'show_stock_analyzer' not in st.session_state:
    st.session_state.show_stock_analyzer = True
if 'show_news_section' not in st.session_state:
    st.session_state.show_news_section = True
if 'show_ai_chat' not in st.session_state:
    st.session_state.show_ai_chat = True
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    /* Smooth Slide-In Animation for Sections */
    @keyframes slideInFromLeft {
        0% {
            transform: translateX(-30px);
            opacity: 0;
        }
        100% {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes fadeInUp {
        0% {
            transform: translateY(20px);
            opacity: 0;
        }
        100% {
            transform: translateY(0);
            opacity: 1;
        }
    }
    
    @keyframes scaleIn {
        0% {
            transform: scale(0.95);
            opacity: 0;
        }
        100% {
            transform: scale(1);
            opacity: 1;
        }
    }
    
    /* Apply animations to main sections */
    .main .block-container {
        animation: fadeInUp 0.6s ease-out;
    }
    
    [data-testid="stMetricValue"] {
        animation: scaleIn 0.5s ease-out;
    }
    
    .stTabs [data-baseweb="tab"] {
        animation: slideInFromLeft 0.4s ease-out;
    }
    
    /* Sidebar Styling with Beautiful Gradient */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, 
            #1e3a8a 0%,      /* Deep blue */
            #312e81 35%,     /* Indigo */
            #581c87 70%,     /* Purple */
            #831843 100%     /* Dark magenta */
        );
        box-shadow: 2px 0 20px rgba(0, 0, 0, 0.2);
    }
    
    section[data-testid="stSidebar"] > div {
        background: transparent;
    }
    
    /* Sidebar text colors */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] .stMarkdown {
        color: #ffffff !important;
    }
    
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label {
        color: #e0e7ff !important;
    }
    
    /* Sidebar dividers */
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.2);
    }
    
    /* Sidebar buttons */
    section[data-testid="stSidebar"] button {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: white;
        transition: all 0.3s ease;
    }
    
    section[data-testid="stSidebar"] button:hover {
        background: rgba(255, 255, 255, 0.2);
        border-color: rgba(255, 255, 255, 0.4);
        transform: translateY(-2px);
    }
    
    /* Sidebar checkbox */
    section[data-testid="stSidebar"] [data-testid="stCheckbox"] label {
        color: #ffffff !important;
        font-weight: 500;
    }
    
    /* Sidebar caption text */
    section[data-testid="stSidebar"] .stCaption {
        color: #c7d2fe !important;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #7c3aed 50%, #ec4899 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 20px 60px rgba(124, 58, 237, 0.3);
        position: relative;
        overflow: hidden;
        animation: glow 4s ease-in-out infinite;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: pulse 4s ease-in-out infinite;
    }
    
    .main-header::after {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        animation: shimmer 3s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 0.5; }
        50% { transform: scale(1.1); opacity: 0.8; }
    }
    
    @keyframes shimmer {
        0% { left: -100%; }
        100% { left: 200%; }
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    @keyframes glow {
        0%, 100% { box-shadow: 0 20px 60px rgba(124, 58, 237, 0.3); }
        50% { box-shadow: 0 25px 80px rgba(236, 72, 153, 0.5); }
    }
    
    .header-title {
        color: white;
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        margin: 0;
        font-family: 'Inter', sans-serif;
        text-shadow: 0 4px 20px rgba(0,0,0,0.3);
        position: relative;
        z-index: 1;
    }
    
    .header-subtitle {
        color: rgba(255,255,255,0.95);
        text-align: center;
        margin-top: 1rem;
        font-size: 1.3rem;
        font-weight: 300;
        font-family: 'Inter', sans-serif;
        position: relative;
        z-index: 1;
    }
    
    .header-tagline {
        color: #fbbf24;
        text-align: center;
        margin-top: 0.5rem;
        font-size: 1.1rem;
        font-weight: 500;
        font-family: 'Inter', sans-serif;
        font-style: italic;
        position: relative;
        z-index: 1;
        text-shadow: 0 2px 10px rgba(251, 191, 36, 0.5);
        animation: fadeInUp 1s ease-out 0.5s both;
    }
    
    .features-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-top: 2rem;
        position: relative;
        z-index: 1;
    }
    
    .feature-card {
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        transition: all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
        font-family: 'Inter', sans-serif;
        animation: float 3s ease-in-out infinite;
        position: relative;
        overflow: hidden;
    }
    
    .feature-card:nth-child(2) { animation-delay: 0.2s; }
    .feature-card:nth-child(3) { animation-delay: 0.4s; }
    .feature-card:nth-child(4) { animation-delay: 0.6s; }
    .feature-card:nth-child(5) { animation-delay: 0.8s; }
    .feature-card:nth-child(6) { animation-delay: 1s; }
    
    .feature-card::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
        transform: rotate(45deg);
        transition: all 0.6s ease;
    }
    
    .feature-card:hover::before {
        left: 100%;
    }
    
    .feature-card:hover {
        background: rgba(255, 255, 255, 0.25);
        transform: translateY(-10px) scale(1.05);
        box-shadow: 0 20px 50px rgba(236, 72, 153, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.4);
    }
    
    .feature-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    
    .feature-text {
        color: white;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
    }
    
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #a78bfa !important;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f8fafc;
        padding: 10px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 8px;
        color: white !important;
        font-weight: 600;
        padding: 12px 24px;
        border: none;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #ec4899 0%, #f59e0b 100%);
        box-shadow: 0 4px 15px rgba(236, 72, 153, 0.4);
    }
    
    /* Button Styling */
    .stButton>button {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 2.5rem;
        font-weight: 600;
        transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .stButton>button::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
    }
    
    .stButton>button:hover::before {
        width: 300px;
        height: 300px;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
        box-shadow: 0 8px 30px rgba(59, 130, 246, 0.6);
        transform: translateY(-3px) scale(1.02);
    }
    
    .stButton>button:active {
        transform: translateY(-1px) scale(0.98);
    }
    
    /* Download Button Styling */
    .stDownloadButton>button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 2.5rem;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
        transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
        position: relative;
        overflow: hidden;
    }
    
    .stDownloadButton>button::after {
        content: '✨';
        position: absolute;
        top: 50%;
        right: -20px;
        transform: translateY(-50%);
        opacity: 0;
        transition: all 0.4s ease;
    }
    
    .stDownloadButton>button:hover::after {
        right: 20px;
        opacity: 1;
    }
    
    .stDownloadButton>button:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        box-shadow: 0 8px 30px rgba(16, 185, 129, 0.6);
        transform: translateY(-3px) scale(1.02);
        padding-right: 3.5rem;
    }
    
    .stDownloadButton>button:active {
        transform: translateY(-1px) scale(0.98);
    }
    
    /* Metric Cards */
    [data-testid="stMetricValue"] {
        color: #6366f1;
        font-weight: 700;
    }
    
    /* File Uploader */
    [data-testid="stFileUploader"] {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0e7ff 100%);
        border: 2px dashed #818cf8;
        border-radius: 12px;
        padding: 2rem;
    }
    
    /* Success/Warning/Error Messages */
    .stSuccess {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        border-left: 4px solid #10b981;
    }
    
    .stWarning {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border-left: 4px solid #f59e0b;
    }
    
    .stError {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border-left: 4px solid #ef4444;
    }
    
    /* Data Frame */
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
    }
    
    [data-testid="stDataFrame"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.15);
    }
    
    /* Subheaders */
    h3 {
        color: #4f46e5 !important;
        font-weight: 700 !important;
    }
    
    /* Mac OS Style Hover Effects */
    .stMetric {
        transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
        cursor: pointer;
        border-radius: 10px;
        padding: 0.5rem;
    }
    
    .stMetric:hover {
        transform: scale(1.03);
        background: rgba(99, 102, 241, 0.05);
    }
    
    /* File Uploader Mac OS Effect */
    [data-testid="stFileUploader"]:hover {
        transform: scale(1.01);
        box-shadow: 0 8px 30px rgba(129, 140, 248, 0.2);
    }
    
    /* Input Fields */
    input[type="text"], input[type="number"], input[type="date"] {
        transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1) !important;
    }
    
    input[type="text"]:hover, input[type="number"]:hover, input[type="date"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15) !important;
    }
    
    input[type="text"]:focus, input[type="number"]:focus, input[type="date"]:focus {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.25) !important;
    }
    
    /* Select Dropdown */
    select {
        transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1) !important;
    }
    
    select:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15) !important;
    }
    
    /* Tab Mac OS Style */
    .stTabs [data-baseweb="tab"] {
        transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        transform: translateY(-2px) scale(1.02);
    }
    
    /* Chart Containers */
    [data-testid="stImage"] {
        transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
        border-radius: 12px;
        overflow: hidden;
    }
    
    [data-testid="stImage"]:hover {
        transform: scale(1.02);
        box-shadow: 0 12px 40px rgba(0,0,0,0.15);
    }
    
    /* Success/Warning/Error Messages Mac OS */
    .stSuccess, .stWarning, .stError {
        transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
        cursor: pointer;
    }
    
    .stSuccess:hover {
        transform: translateX(5px);
        box-shadow: -4px 4px 12px rgba(16, 185, 129, 0.2);
    }
    
    .stWarning:hover {
        transform: translateX(5px);
        box-shadow: -4px 4px 12px rgba(245, 158, 11, 0.2);
    }
    
    .stError:hover {
        transform: translateX(5px);
        box-shadow: -4px 4px 12px rgba(239, 68, 68, 0.2);
    }
    
    /* Sidebar Items */
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        transition: all 0.2s cubic-bezier(0.4, 0.0, 0.2, 1);
    }
    
    [data-testid="stSidebar"] button:hover {
        transform: scale(1.02);
    }
    
    /* Glowing Section Effects */
    .element-container {
        transition: all 0.4s cubic-bezier(0.4, 0.0, 0.2, 1);
    }
    
    /* Expander Glowing Effects */
    .streamlit-expanderHeader {
        transition: all 0.4s cubic-bezier(0.4, 0.0, 0.2, 1) !important;
        border-radius: 12px !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.1)) !important;
        box-shadow: 0 0 30px rgba(99, 102, 241, 0.4), 
                    0 0 60px rgba(139, 92, 246, 0.2),
                    inset 0 0 20px rgba(255, 255, 255, 0.1) !important;
        transform: translateX(5px) scale(1.01);
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
    }
    
    /* Container Glow on Hover */
    [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
        transition: all 0.4s cubic-bezier(0.4, 0.0, 0.2, 1);
        border-radius: 12px;
        padding: 1rem;
    }
    
    [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"]:hover {
        box-shadow: 0 0 25px rgba(99, 102, 241, 0.3),
                    0 0 50px rgba(139, 92, 246, 0.15);
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.02), rgba(139, 92, 246, 0.02));
    }
    
    /* Column Glow Effects */
    [data-testid="column"] {
        transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
        border-radius: 10px;
        padding: 0.5rem;
    }
    
    [data-testid="column"]:hover {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.05), rgba(139, 92, 246, 0.05));
        box-shadow: 0 0 20px rgba(99, 102, 241, 0.2);
        transform: scale(1.01);
    }
    
    /* Enhanced Metric Glow */
    [data-testid="metric-container"] {
        transition: all 0.4s cubic-bezier(0.4, 0.0, 0.2, 1);
        border-radius: 12px;
        padding: 1rem;
    }
    
    [data-testid="metric-container"]:hover {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(139, 92, 246, 0.08));
        box-shadow: 0 0 30px rgba(99, 102, 241, 0.4),
                    0 8px 25px rgba(99, 102, 241, 0.2);
        transform: translateY(-5px) scale(1.03);
        border: 1px solid rgba(99, 102, 241, 0.3);
    }
    
    /* Plotly Chart Glow */
    .js-plotly-plot {
        transition: all 0.4s cubic-bezier(0.4, 0.0, 0.2, 1);
        border-radius: 12px;
    }
    
    .js-plotly-plot:hover {
        box-shadow: 0 0 40px rgba(99, 102, 241, 0.3),
                    0 0 80px rgba(139, 92, 246, 0.15);
        transform: scale(1.01);
    }
    
    /* Divider Glow Animation */
    hr {
        transition: all 0.4s ease;
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #6366f1, transparent);
    }
    
    hr:hover {
        box-shadow: 0 0 20px rgba(99, 102, 241, 0.6);
        height: 3px;
    }
    
    /* Progress Bar Glow */
    .stProgress > div > div {
        transition: all 0.3s ease;
    }
    
    .stProgress:hover > div > div {
        box-shadow: 0 0 20px rgba(99, 102, 241, 0.6);
    }
    
    /* Text Input Enhanced Glow */
    .stTextInput input {
        transition: all 0.4s cubic-bezier(0.4, 0.0, 0.2, 1) !important;
    }
    
    .stTextInput input:hover {
        box-shadow: 0 0 15px rgba(99, 102, 241, 0.3) !important;
        border-color: rgba(99, 102, 241, 0.5) !important;
    }
    
    .stTextInput input:focus {
        box-shadow: 0 0 25px rgba(99, 102, 241, 0.5),
                    0 0 50px rgba(139, 92, 246, 0.2) !important;
        border-color: #6366f1 !important;
    }
    
    /* Number Input Glow */
    .stNumberInput input {
        transition: all 0.4s cubic-bezier(0.4, 0.0, 0.2, 1) !important;
    }
    
    .stNumberInput input:hover {
        box-shadow: 0 0 15px rgba(99, 102, 241, 0.3) !important;
    }
    
    .stNumberInput input:focus {
        box-shadow: 0 0 25px rgba(99, 102, 241, 0.5),
                    0 0 50px rgba(139, 92, 246, 0.2) !important;
    }
    
    /* Slider Glow */
    .stSlider:hover {
        filter: drop-shadow(0 0 10px rgba(99, 102, 241, 0.5));
    }
    
    /* Form Container Glow */
    [data-testid="stForm"] {
        transition: all 0.4s cubic-bezier(0.4, 0.0, 0.2, 1);
        border-radius: 12px;
    }
    
    [data-testid="stForm"]:hover {
        box-shadow: 0 0 30px rgba(99, 102, 241, 0.3),
                    0 0 60px rgba(139, 92, 246, 0.15);
        border-color: rgba(99, 102, 241, 0.4) !important;
    }
    
    /* Sticky Navigation Bar */
    .nav-container {
        position: sticky;
        top: 0;
        z-index: 999;
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.98), rgba(88, 28, 135, 0.98));
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        padding: 15px 30px;
        margin: -20px -30px 30px -30px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        border-bottom: 1px solid rgba(255, 255, 255, 0.15);
    }
    
    .nav-menu {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        justify-content: center;
        align-items: center;
    }
    
    .nav-item {
        display: inline-block;
        padding: 10px 20px;
        background: rgba(255, 255, 255, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.35);
        border-radius: 12px;
        color: #ffffff !important;
        text-decoration: none;
        font-weight: 700;
        font-size: 14px;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
        cursor: pointer;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
    }
    
    /* Force white text on navigation links */
    .nav-item,
    .nav-item:link,
    .nav-item:visited,
    .nav-item:active {
        color: #ffffff !important;
    }
    
    .nav-item:hover {
        background: rgba(255, 255, 255, 0.4);
        transform: translateY(-3px) scale(1.05);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
        border-color: rgba(255, 255, 255, 0.5);
        text-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
    }
    
    .nav-item:active {
        transform: translateY(-1px) scale(1.02);
    }
    
    /* Smooth scrolling */
    html {
        scroll-behavior: smooth;
    }
    
    /* Section Headers */
    .section-anchor {
        scroll-margin-top: 80px;
    }
    
    /* =====================================================
       MOBILE RESPONSIVE DESIGN - SMOOTH & TOUCH-OPTIMIZED
       ===================================================== */
    
    /* Tablet Devices (Portrait) */
    @media only screen and (max-width: 768px) {
        /* Navigation - Compact on tablets */
        .nav-container {
            padding: 12px 20px;
            margin: -20px -20px 25px -20px;
        }
        
        .nav-menu {
            gap: 6px;
        }
        
        .nav-item {
            padding: 8px 16px;
            font-size: 13px;
        }
        
        /* Header adjustments */
        .main-header {
            padding: 20px 15px;
        }
        
        .header-title {
            font-size: 2.2rem !important;
        }
        
        .header-subtitle {
            font-size: 1rem !important;
        }
        
        .features-grid {
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
        }
        
        .feature-card {
            padding: 12px;
        }
        
        .feature-icon {
            font-size: 1.8rem;
        }
        
        .feature-text {
            font-size: 0.75rem;
        }
    }
    
    /* Mobile Phones (All orientations) */
    @media only screen and (max-width: 480px) {
        /* Smooth transitions for all interactive elements */
        * {
            -webkit-tap-highlight-color: rgba(99, 102, 241, 0.3);
            -webkit-touch-callout: none;
        }
        
        /* Navigation - Mobile optimized */
        .nav-container {
            padding: 10px 12px;
            margin: -10px -12px 20px -12px;
        }
        
        .nav-menu {
            gap: 5px;
            justify-content: space-between;
        }
        
        .nav-item {
            padding: 8px 10px;
            font-size: 11px;
            border-radius: 8px;
            min-height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .nav-item:hover {
            transform: scale(1.05);
        }
        
        .nav-item:active {
            transform: scale(0.98);
            background: rgba(255, 255, 255, 0.4);
        }
        
        /* Header - Mobile friendly */
        .main-header {
            padding: 20px 12px;
        }
        
        .header-title {
            font-size: 1.8rem !important;
            margin-bottom: 8px;
        }
        
        .header-subtitle {
            font-size: 0.9rem !important;
            margin-bottom: 5px;
        }
        
        .header-tagline {
            font-size: 0.85rem !important;
        }
        
        /* Feature cards - 2 columns on mobile */
        .features-grid {
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            padding: 10px 0;
        }
        
        .feature-card {
            padding: 10px;
            min-height: 80px;
        }
        
        .feature-icon {
            font-size: 1.5rem;
            margin-bottom: 4px;
        }
        
        .feature-text {
            font-size: 0.7rem;
        }
        
        /* Touch-friendly buttons - minimum 44px tap target */
        .stButton button {
            min-height: 48px !important;
            padding: 12px 24px !important;
            font-size: 15px !important;
            border-radius: 12px !important;
            transition: all 0.2s ease !important;
        }
        
        .stButton button:active {
            transform: scale(0.97) !important;
            box-shadow: 0 2px 8px rgba(99, 102, 241, 0.4) !important;
        }
        
        /* Touch-friendly inputs */
        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea {
            min-height: 48px !important;
            font-size: 16px !important;
            padding: 12px !important;
            border-radius: 10px !important;
        }
        
        /* Select dropdowns */
        .stSelectbox > div > div {
            min-height: 48px !important;
            font-size: 15px !important;
        }
        
        /* Sliders - larger touch area */
        .stSlider {
            padding: 15px 0 !important;
        }
        
        /* Checkboxes - bigger tap targets */
        [data-testid="stCheckbox"] {
            min-height: 44px;
            display: flex;
            align-items: center;
        }
        
        /* Radio buttons */
        [data-testid="stRadio"] label {
            min-height: 44px;
            display: flex;
            align-items: center;
        }
        
        /* Tabs - touch friendly */
        .stTabs [data-baseweb="tab"] {
            min-height: 48px !important;
            font-size: 14px !important;
            padding: 12px 16px !important;
        }
        
        /* Expanders - larger touch target */
        .streamlit-expanderHeader {
            min-height: 48px !important;
            padding: 12px 16px !important;
            font-size: 15px !important;
        }
        
        /* Metrics - better spacing on mobile */
        [data-testid="stMetric"] {
            padding: 12px !important;
        }
        
        [data-testid="stMetricValue"] {
            font-size: 1.3rem !important;
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 0.85rem !important;
        }
        
        /* Chat interface - mobile optimized */
        .stChatMessage {
            padding: 12px !important;
            margin-bottom: 10px !important;
        }
        
        .stChatInput textarea {
            min-height: 48px !important;
            font-size: 16px !important;
        }
        
        /* File uploader - touch friendly */
        [data-testid="stFileUploader"] button {
            min-height: 48px !important;
            font-size: 15px !important;
        }
        
        /* Sidebar on mobile */
        section[data-testid="stSidebar"] {
            width: 85% !important;
            max-width: 300px !important;
        }
        
        /* Columns stack on mobile */
        [data-testid="column"] {
            width: 100% !important;
            margin-bottom: 15px;
        }
        
        /* Reduce padding on main container */
        .block-container {
            padding: 1rem 1rem !important;
        }
        
        /* Section anchors adjusted for mobile nav */
        .section-anchor {
            scroll-margin-top: 60px;
        }
        
        /* Smooth animations - optimized for mobile performance */
        @keyframes mobileSlideIn {
            0% {
                transform: translateX(-10px);
                opacity: 0;
            }
            100% {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes mobileFadeIn {
            0% {
                opacity: 0;
            }
            100% {
                opacity: 1;
            }
        }
        
        /* Apply lighter animations on mobile for better performance */
        .main .block-container {
            animation: mobileFadeIn 0.4s ease-out;
        }
        
        [data-testid="stMetricValue"] {
            animation: mobileSlideIn 0.3s ease-out;
        }
        
        /* Reduce glow effects on mobile for better performance */
        .stButton button:hover {
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
        }
        
        /* Simplify hover effects on touch devices */
        @media (hover: none) and (pointer: coarse) {
            .nav-item:hover {
                transform: none;
            }
            
            .feature-card:hover {
                transform: none;
            }
            
            /* Keep active states for feedback */
            .nav-item:active,
            .feature-card:active,
            .stButton button:active {
                transform: scale(0.97);
            }
        }
    }
    
    /* Extra small phones */
    @media only screen and (max-width: 360px) {
        .nav-item {
            padding: 6px 8px;
            font-size: 10px;
        }
        
        .header-title {
            font-size: 1.5rem !important;
        }
        
        .features-grid {
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
        }
        
        .feature-icon {
            font-size: 1.3rem;
        }
        
        .feature-text {
            font-size: 0.65rem;
        }
    }
    
    /* Landscape mode on phones */
    @media only screen and (max-height: 480px) and (orientation: landscape) {
        .nav-container {
            padding: 8px 15px;
        }
        
        .nav-item {
            padding: 6px 12px;
            font-size: 12px;
        }
        
        .main-header {
            padding: 15px 12px;
        }
        
        .header-title {
            font-size: 1.6rem !important;
        }
        
        .features-grid {
            grid-template-columns: repeat(3, 1fr);
        }
    }
    
    /* Apple-style Frosted Glass Effect for Chat Input */
    [data-testid="stChatInput"] {
        position: sticky !important;
        bottom: 0 !important;
        z-index: 999 !important;
        backdrop-filter: blur(40px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(40px) saturate(180%) !important;
        background: rgba(255, 255, 255, 0.08) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.15) !important;
        box-shadow: 0 -8px 32px rgba(0, 0, 0, 0.2),
                    0 -4px 16px rgba(99, 102, 241, 0.15),
                    inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
        padding: 20px !important;
        margin: 0 -30px -30px -30px !important;
    }
    
    /* Chat Input Field Styling */
    [data-testid="stChatInput"] input {
        background: rgba(255, 255, 255, 0.12) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 16px !important;
        padding: 14px 20px !important;
        color: #ffffff !important;
        font-size: 15px !important;
        font-weight: 500 !important;
        transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1) !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1),
                    inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
    }
    
    [data-testid="stChatInput"] input::placeholder {
        color: rgba(255, 255, 255, 0.6) !important;
        font-weight: 400 !important;
    }
    
    [data-testid="stChatInput"] input:hover {
        background: rgba(255, 255, 255, 0.18) !important;
        border-color: rgba(255, 255, 255, 0.35) !important;
        box-shadow: 0 6px 24px rgba(99, 102, 241, 0.25),
                    0 0 0 4px rgba(99, 102, 241, 0.1),
                    inset 0 1px 0 rgba(255, 255, 255, 0.15) !important;
        transform: translateY(-1px) !important;
    }
    
    [data-testid="stChatInput"] input:focus {
        background: rgba(255, 255, 255, 0.22) !important;
        border-color: rgba(139, 92, 246, 0.5) !important;
        outline: none !important;
        box-shadow: 0 8px 32px rgba(139, 92, 246, 0.35),
                    0 0 0 4px rgba(139, 92, 246, 0.15),
                    inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Send Button Styling with Glass Effect */
    [data-testid="stChatInput"] button {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.9), rgba(99, 102, 241, 0.9)) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 12px !important;
        padding: 10px 16px !important;
        transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1) !important;
        box-shadow: 0 4px 16px rgba(139, 92, 246, 0.3),
                    inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
    }
    
    [data-testid="stChatInput"] button:hover {
        background: linear-gradient(135deg, rgba(139, 92, 246, 1), rgba(99, 102, 241, 1)) !important;
        transform: translateY(-2px) scale(1.05) !important;
        box-shadow: 0 8px 24px rgba(139, 92, 246, 0.5),
                    0 0 0 4px rgba(139, 92, 246, 0.2),
                    inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
    }
    
    [data-testid="stChatInput"] button:active {
        transform: translateY(0) scale(1) !important;
    }
    
    /* Chat Message Container Adjustments for Scrolling */
    [data-testid="stChatMessageContainer"] {
        padding-bottom: 120px !important;
    }
</style>

<div id="home" class="section-anchor"></div>

<div class="main-header">
    <h1 class="header-title">🚀 Quantura</h1>
    <p class="header-subtitle">Transform Your Financial Data into Actionable Insights</p>
    <p class="header-tagline">✨ Let's make your financial life hassle-free</p>
    <div class="features-grid">
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <div class="feature-text">Auto-Categorize</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">💰</div>
            <div class="feature-text">Track Budgets</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">📈</div>
            <div class="feature-text">Analyze Trends</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🥧</div>
            <div class="feature-text">Visualize Data</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">📅</div>
            <div class="feature-text">Compare Years</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🌸</div>
            <div class="feature-text">Discover Patterns</div>
        </div>
    </div>
</div>

<div class="nav-container">
    <div class="nav-menu">
        <a href="#home" class="nav-item">🏠 Home</a>
        <a href="#upload" class="nav-item">📤 Upload Data</a>
        <a href="#currency" class="nav-item">💱 Currency</a>
        <a href="#aichat" class="nav-item">🤖 AI Chat</a>
        <a href="#tools" class="nav-item">🪄 Financial Tools</a>
        <a href="#analysis" class="nav-item">📊 Analysis</a>
        <a href="#budget" class="nav-item">💰 Budget</a>
        <a href="#goals" class="nav-item">🎯 Savings Goals</a>
    </div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("🎨 Personalize Dashboard")
    st.markdown("**Choose sections to display:**")
    
    st.session_state.show_company_section = st.checkbox(
        "📊 Company Reports",
        value=st.session_state.show_company_section,
        help="Show corporate financial analysis and comparisons"
    )
    
    st.session_state.show_personal_section = st.checkbox(
        "💰 Personal Spending",
        value=st.session_state.show_personal_section,
        help="Show personal finance analysis and budgets"
    )
    
    st.session_state.show_currency_section = st.checkbox(
        "💱 Currency Converter",
        value=st.session_state.show_currency_section,
        help="Show currency conversion tools"
    )
    
    st.session_state.show_financial_tools = st.checkbox(
        "🪄 Financial Tools",
        value=st.session_state.show_financial_tools,
        help="Show magic of compounding and other financial calculators"
    )
    
    st.session_state.show_stock_analyzer = st.checkbox(
        "📈 Stock Analyzer",
        value=st.session_state.show_stock_analyzer,
        help="AI-powered quantitative stock analysis with Monte Carlo, ARIMA, GARCH, Black-Scholes"
    )

    st.session_state.show_news_section = st.checkbox(
        "📰 Financial News",
        value=st.session_state.show_news_section,
        help="Latest financial news and market updates"
    )

    st.session_state.show_ai_chat = st.checkbox(
        "🤖 AI Chat",
        value=st.session_state.show_ai_chat,
        help="Chat with AI financial assistant"
    )
    
    st.divider()
    
    if st.session_state.show_currency_section:
        st.markdown('<div class="section-anchor" id="currency"></div>', unsafe_allow_html=True)
        st.header("🌍 Currency Settings")
        currencies = list(get_exchange_rates().keys())
        selected_currency = st.selectbox(
            "Data Currency",
            currencies,
            index=0,
            help="Select the currency of ALL uploaded files. All files must be in the same currency. Amounts will be converted to USD for analysis."
        )
        if selected_currency != 'USD':
            st.warning(f"⚠️ Conversion: {selected_currency} → USD (rate: {get_exchange_rates()[selected_currency]})")
        else:
            st.success("✓ Data already in USD")
    else:
        selected_currency = 'USD'
        st.caption("💡 Enable 'Currency Converter' above to change currency settings")
    
    st.divider()
    st.subheader("⚙️ Custom Rules")
    custom_rules = get_custom_rules()
    
    if custom_rules:
        st.write("**Current Rules:**")
        for keyword, category in custom_rules:
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.write(f"{keyword} → {category}")
            with col_b:
                if st.button("🗑️", key=f"del_{keyword}"):
                    success, error = delete_custom_rule(keyword)
                    if success:
                        st.rerun()
                    else:
                        st.error(f"Failed to delete rule: {error}")
    
    st.write("**Add New Rule:**")
    new_keyword = st.text_input("Keyword", key="new_keyword")
    new_category = st.selectbox("Category", ["Income", "Expense", "Investment"], key="new_category")
    if st.button("➕ Add Rule"):
        if new_keyword:
            success, error = add_custom_rule(new_keyword, new_category)
            if success:
                st.success(f"Added rule: {new_keyword} → {new_category}")
                st.rerun()
            else:
                st.error(f"Failed to add rule: {error}")
    
    st.divider()
    st.markdown('<div class="section-anchor" id="budget"></div>', unsafe_allow_html=True)
    st.subheader("💰 Budget Settings")
    
    if 'budget_apply_success' in st.session_state:
        st.success(st.session_state.budget_apply_success)
        del st.session_state.budget_apply_success
    
    st.markdown("#### 🤖 AI Budget Advisor")
    st.caption("Let AI analyze your spending patterns and suggest optimal budgets")
    
    if st.button("✨ Get AI Recommendations", type="primary"):
        if 'processed_df' in st.session_state and st.session_state.processed_df is not None:
            with st.spinner("🧠 AI is analyzing your spending patterns..."):
                recommendations, error = get_ai_budget_recommendations(st.session_state.processed_df)
                
                if error:
                    st.error(f"❌ {error}")
                elif recommendations:
                    st.session_state.ai_budget_recommendations = recommendations
                    st.rerun()
        else:
            st.warning("📊 Please upload your transaction data first to get AI recommendations")
    
    if 'ai_budget_recommendations' in st.session_state and st.session_state.ai_budget_recommendations:
        rec = st.session_state.ai_budget_recommendations
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 15px; border-radius: 10px; color: white; margin-bottom: 10px; margin-top: 10px;">
            <strong>💡 AI Insight:</strong> {rec.get('explanation', 'No explanation available')}
        </div>
        """, unsafe_allow_html=True)
        
        if 'tip' in rec:
            st.info(f"💎 **Pro Tip:** {rec['tip']}")
        
        if 'budgets' in rec:
            render_metric_row([
                {
                    "label": "📥 Income Budget",
                    "value": f"${rec['budgets'].get('Income', 0):,.0f}",
                    "kind": "gain"
                },
                {
                    "label": "📤 Expense Budget",
                    "value": f"${rec['budgets'].get('Expense', 0):,.0f}",
                    "kind": "risk"
                },
                {
                    "label": "📈 Investment Budget",
                    "value": f"${rec['budgets'].get('Investment', 0):,.0f}",
                    "kind": "goal"
                }
            ])
            
            if st.button("✅ Apply AI Recommendations", key="apply_ai_budgets"):
                applied = []
                errors = []
                for cat, amount in rec['budgets'].items():
                    success, error = set_budget(cat, amount)
                    if success:
                        applied.append(cat)
                    else:
                        errors.append(f"{cat}: {error}")
                
                if applied and errors:
                    st.session_state.budget_apply_success = f"⚠️ Partially applied budgets for: {', '.join(applied)}. Failed: {', '.join(errors)}"
                    if 'ai_budget_recommendations' in st.session_state:
                        del st.session_state.ai_budget_recommendations
                    st.rerun()
                elif applied:
                    st.session_state.budget_apply_success = f"✓ Applied AI budgets for: {', '.join(applied)}"
                    if 'ai_budget_recommendations' in st.session_state:
                        del st.session_state.ai_budget_recommendations
                    st.rerun()
                elif errors:
                    st.error(f"❌ Failed to apply budgets: {', '.join(errors)}")
    
    st.divider()
    st.markdown("#### ⚙️ Manual Budget Settings")
    budgets = get_budgets()
    
    categories = ["Income", "Expense", "Investment"]
    for cat in categories:
        current_budget = budgets.get(cat, 0)
        budget_amount = st.text_input(f"{cat} Budget", value=str(int(current_budget)), key=f"budget_{cat}")
        if st.button(f"💾 Set {cat} Budget", key=f"set_budget_{cat}", use_container_width=True):
            try:
                budget_value = float(budget_amount)
                if budget_value != current_budget:
                    success, error = set_budget(cat, budget_value)
                    if success:
                        st.success(f"✓ {cat} budget updated")
                        st.rerun()
                    else:
                        st.error(f"Error: {error}")
            except ValueError:
                st.error("Invalid amount")
    
    # Feedback Widget
    st.divider()
    st.subheader("⭐ Rate Your Experience")
    st.caption("Help us improve Quantura!")
    
    if 'feedback_submitted' not in st.session_state:
        st.session_state.feedback_submitted = False
    
    if not st.session_state.feedback_submitted:
        rating = st.select_slider(
            "How would you rate Quantura?",
            options=["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"],
            value="⭐⭐⭐⭐",
            key="rating_slider"
        )
        
        feedback_text = st.text_area(
            "Any suggestions?",
            placeholder="Share your thoughts...",
            key="feedback_text",
            height=80
        )
        
        if st.button("✅ Submit Feedback", type="primary", use_container_width=True):
            st.session_state.feedback_submitted = True
            st.session_state.user_rating = rating
            st.rerun()
    else:
        st.success(f"🙏 Thank you for your {st.session_state.get('user_rating', '⭐⭐⭐⭐')} rating!")
        if st.button("📝 Submit Another", use_container_width=True):
            st.session_state.feedback_submitted = False
            st.rerun()

# 🪄 Financial Tools Section - Magic of Compounding
if st.session_state.show_financial_tools:
    st.markdown("---")
    st.markdown('<div class="section-anchor" id="tools"></div>', unsafe_allow_html=True)
    st.header("🪄 Financial Tools")
    
    with st.expander("💰 Magic of Compounding - Watch Your Money Grow!", expanded=False):
        st.markdown("**Discover the power of compound interest and see your wealth multiply over time!**")
        
        col_input1, col_input2, col_input3 = st.columns(3)
        
        with col_input1:
            principal = st.number_input("💵 Initial Investment ($)", min_value=0.0, value=10000.0, step=1000.0, help="Starting amount you invest today")
            monthly_contribution = st.number_input("📅 Monthly Addition ($)", min_value=0.0, value=500.0, step=100.0, help="Amount you add each month")
        
        with col_input2:
            annual_rate = st.slider("📈 Annual Interest Rate (%)", min_value=0.0, max_value=20.0, value=8.0, step=0.5, help="Expected annual return rate")
            years = st.slider("⏰ Time Period (Years)", min_value=1, max_value=50, value=20, step=1, help="Investment duration")
        
        with col_input3:
            compound_freq = st.selectbox("🔄 Compounding Frequency", 
                options=["Monthly", "Quarterly", "Annually", "Daily"],
                index=0,
                help="How often interest is calculated and added")
            
            show_inflation = st.checkbox("📊 Adjust for Inflation", value=False)
            if show_inflation:
                inflation_rate = st.slider("Inflation Rate (%)", min_value=0.0, max_value=10.0, value=3.0, step=0.1)
        
        # Calculate compound interest
        freq_map = {"Daily": 365, "Monthly": 12, "Quarterly": 4, "Annually": 1}
        n = freq_map[compound_freq]
        r = annual_rate / 100
        
        # Calculate year-by-year growth
        years_array = list(range(years + 1))
        balances = []
        principal_total = []
        interest_total = []
        
        for t in years_array:
            # Compound interest on principal
            compound_value = principal * (1 + r/n)**(n*t)
            
            # Future value of monthly contributions (annuity)
            if monthly_contribution > 0 and t > 0:
                monthly_rate = r / 12
                months = t * 12
                fv_contributions = monthly_contribution * (((1 + monthly_rate)**months - 1) / monthly_rate)
                total_contributions = monthly_contribution * months
            else:
                fv_contributions = 0
                total_contributions = 0
            
            total_balance = compound_value + fv_contributions
            total_principal = principal + total_contributions
            total_interest = total_balance - total_principal
            
            balances.append(total_balance)
            principal_total.append(total_principal)
            interest_total.append(total_interest)
        
        # Apply inflation adjustment if enabled
        if show_inflation:
            inflation_factor = [(1 / (1 + inflation_rate/100)**t) for t in years_array]
            real_balances = [bal * factor for bal, factor in zip(balances, inflation_factor)]
        else:
            real_balances = balances
        
        # Display Key Metrics with Enhanced Visual Hierarchy
        st.markdown("### 🎯 Your Wealth Projection")
        
        final_balance = balances[-1]
        final_principal = principal_total[-1]
        final_interest = interest_total[-1]
        
        # Calculate when money doubles
        years_to_double = 72 / annual_rate if annual_rate > 0 else 0
        
        metrics_data = [
            {
                "label": "💰 Final Balance",
                "value": f"${final_balance:,.0f}",
                "kind": "goal"
            },
            {
                "label": "📥 Total Invested",
                "value": f"${final_principal:,.0f}",
                "kind": "analytics"
            },
            {
                "label": "✨ Interest Earned",
                "value": f"${final_interest:,.0f}",
                "delta": f"{(final_interest/final_principal*100):.1f}% return",
                "kind": "gain"
            }
        ]
        
        if years_to_double > 0:
            metrics_data.append({
                "label": "⏱️ Money Doubles In",
                "value": f"{years_to_double:.1f} years",
                "kind": "analytics"
            })
        
        render_metric_row(metrics_data)
        
        # Create interactive Plotly chart
        fig_compound = go.Figure()
        
        # Add total balance area
        fig_compound.add_trace(go.Scatter(
            x=years_array,
            y=balances,
            fill='tozeroy',
            name='Total Balance',
            line=dict(color='#10b981', width=3),
            hovertemplate='<b>Year %{x}</b><br>Balance: $%{y:,.0f}<extra></extra>'
        ))
        
        # Add principal line
        fig_compound.add_trace(go.Scatter(
            x=years_array,
            y=principal_total,
            name='Total Invested',
            line=dict(color='#3b82f6', width=2, dash='dash'),
            hovertemplate='<b>Year %{x}</b><br>Invested: $%{y:,.0f}<extra></extra>'
        ))
        
        # Add interest earned area
        fig_compound.add_trace(go.Scatter(
            x=years_array,
            y=interest_total,
            fill='tozeroy',
            name='Interest Earned',
            line=dict(color='#f59e0b', width=2),
            fillcolor='rgba(245, 158, 11, 0.3)',
            hovertemplate='<b>Year %{x}</b><br>Interest: $%{y:,.0f}<extra></extra>'
        ))
        
        fig_compound.update_layout(
            title='🚀 The Magic of Compounding - Your Money Growth Journey',
            xaxis_title='Years',
            yaxis_title='Amount ($)',
            hovermode='x unified',
            template='plotly_white',
            height=500,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            transition_duration=500
        )
        
        st.plotly_chart(add_plotly_animations(fig_compound), use_container_width=True)
        
        # Growth Table - Collapsible
        with st.expander("📊 View Year-by-Year Breakdown", expanded=False):
            growth_data = {
                "Year": years_array[::5] if years > 20 else years_array,  # Show every 5 years if >20
                "Balance": [f"${balances[i]:,.0f}" for i in (range(0, years+1, 5) if years > 20 else range(years+1))],
                "Invested": [f"${principal_total[i]:,.0f}" for i in (range(0, years+1, 5) if years > 20 else range(years+1))],
                "Interest": [f"${interest_total[i]:,.0f}" for i in (range(0, years+1, 5) if years > 20 else range(years+1))]
            }
            st.dataframe(pd.DataFrame(growth_data), use_container_width=True, hide_index=True)
        
        # Wow Factor Insights
        st.markdown("### 💡 Mind-Blowing Insights")
        insight_col1, insight_col2 = st.columns(2)
        
        with insight_col1:
            roi = (final_balance / final_principal - 1) * 100
            st.success(f"🎉 Your {roi:.0f}% return means every dollar you invest grows to **${final_balance/final_principal:.2f}**!")
        
        with insight_col2:
            # Find crossover point where interest > contributions
            for i, (interest, contrib) in enumerate(zip(interest_total, principal_total)):
                if interest > contrib - principal:
                    st.info(f"⚡ By year {i}, your returns (**${interest:,.0f}**) will exceed your contributions (**${contrib - principal:,.0f}**)!")
                    break
    
    # Car Purchase Calculator - 20-5-10 Rule
    with st.expander("🚗 Smart Car Purchase Calculator - 20-5-10 Rule", expanded=False):
        st.markdown("**Make smart car buying decisions using the 20-5-10 rule:**")
        st.info("✅ **20%** down payment | ✅ **5 years** max loan | ✅ EMI ≤ **10%** of monthly salary")
        
        car_col1, car_col2, car_col3 = st.columns(3)
        
        with car_col1:
            car_price = st.number_input("🚗 Car Price ($)", min_value=0.0, value=30000.0, step=1000.0, help="Total on-road price of the car")
            monthly_salary = st.number_input("💰 Monthly Salary ($)", min_value=0.0, value=5000.0, step=500.0, help="Your gross monthly salary")
        
        with car_col2:
            down_payment_pct = st.slider("💵 Down Payment (%)", min_value=0, max_value=50, value=20, step=5, help="Recommended: 20%")
            loan_tenure_years = st.slider("📅 Loan Tenure (Years)", min_value=1, max_value=7, value=5, step=1, help="Recommended: 5 years max")
        
        with car_col3:
            car_interest_rate = st.slider("📈 Interest Rate (%)", min_value=0.0, max_value=15.0, value=7.0, step=0.5, help="Annual interest rate on car loan")
            max_emi_pct = st.slider("🎯 Max EMI (% of salary)", min_value=5, max_value=20, value=10, step=1, help="Recommended: 10% max")
        
        # Calculate loan details
        down_payment = car_price * (down_payment_pct / 100)
        loan_amount = car_price - down_payment
        months = loan_tenure_years * 12
        
        # EMI calculation
        if loan_amount > 0:
            if car_interest_rate > 0:
                # Standard EMI formula: P * r * (1+r)^n / ((1+r)^n - 1)
                monthly_rate = car_interest_rate / (12 * 100)
                emi = loan_amount * monthly_rate * ((1 + monthly_rate) ** months) / (((1 + monthly_rate) ** months) - 1)
                total_payment = emi * months
                total_interest = total_payment - loan_amount
            else:
                # Zero interest: simple amortization
                emi = loan_amount / months
                total_payment = loan_amount
                total_interest = 0
        else:
            emi = 0
            total_payment = 0
            total_interest = 0
        
        # Check affordability
        max_affordable_emi = monthly_salary * (max_emi_pct / 100)
        is_affordable = emi <= max_affordable_emi
        emi_pct_of_salary = (emi / monthly_salary * 100) if monthly_salary > 0 else 0
        
        # Display verdict
        st.markdown("### 🎯 Affordability Check")
        
        if is_affordable and down_payment_pct >= 20 and loan_tenure_years <= 5:
            st.success("✅ **GREAT CHOICE!** This car fits the 20-5-10 rule perfectly!")
        elif is_affordable:
            st.warning("⚠️ **PARTIALLY AFFORDABLE** - EMI is good, but check down payment and tenure")
        else:
            st.error("❌ **NOT RECOMMENDED** - EMI exceeds safe limit for your salary")
        
        # Display metrics with enhanced visual hierarchy
        st.markdown("### 💰 Loan Breakdown")
        
        render_metric_row([
            {
                "label": "💵 Down Payment",
                "value": f"${down_payment:,.0f}",
                "delta": f"{down_payment_pct}% of price",
                "kind": "analytics"
            },
            {
                "label": "📊 Loan Amount",
                "value": f"${loan_amount:,.0f}",
                "kind": "neutral"
            },
            {
                "label": "💳 Monthly EMI",
                "value": f"${emi:,.0f}",
                "delta": f"{emi_pct_of_salary:.1f}% of salary",
                "kind": "risk" if not is_affordable else "gain"
            },
            {
                "label": "💸 Total Interest",
                "value": f"${total_interest:,.0f}",
                "kind": "risk"
            }
        ])
        
        # Visual EMI vs Salary comparison
        st.markdown("### 📊 EMI vs Your Salary")
        
        fig_car = go.Figure()
        
        # Add bars
        fig_car.add_trace(go.Bar(
            x=['Your Monthly EMI', 'Remaining Salary'],
            y=[emi, monthly_salary - emi],
            marker=dict(
                color=['#ef4444' if not is_affordable else '#10b981', '#3b82f6'],
            ),
            text=[f'${emi:,.0f}<br>({emi_pct_of_salary:.1f}%)', f'${monthly_salary - emi:,.0f}'],
            textposition='auto',
            hovertemplate='%{x}: $%{y:,.0f}<extra></extra>'
        ))
        
        # Add max EMI line
        fig_car.add_hline(
            y=max_affordable_emi, 
            line_dash="dash", 
            line_color="orange",
            annotation_text=f"Max Safe EMI: ${max_affordable_emi:,.0f} ({max_emi_pct}%)",
            annotation_position="right"
        )
        
        fig_car.update_layout(
            title='💰 Monthly Budget Impact',
            yaxis_title='Amount ($)',
            showlegend=False,
            template='plotly_white',
            height=400
        )
        
        st.plotly_chart(fig_car, use_container_width=True)
        
        # Payment schedule summary
        st.markdown("### 📅 Payment Summary")
        payment_summary = {
            "Item": ["Down Payment (Upfront)", "Monthly EMI", "Total Loan Payments", "Total Interest Paid", "**Total Car Cost**"],
            "Amount": [
                f"${down_payment:,.0f}",
                f"${emi:,.0f}",
                f"${total_payment:,.0f}",
                f"${total_interest:,.0f}",
                f"**${down_payment + total_payment:,.0f}**"
            ],
            "Details": [
                f"{down_payment_pct}% of ${car_price:,.0f}",
                f"For {months} months ({loan_tenure_years} years)",
                f"{months} payments × ${emi:,.0f}",
                f"{(total_interest/loan_amount*100):.1f}% of loan" if loan_amount > 0 else "0%",
                f"Price + Interest"
            ]
        }
        st.dataframe(pd.DataFrame(payment_summary), use_container_width=True, hide_index=True)
        
        # Recommendations
        st.markdown("### 💡 Smart Recommendations")
        
        rec_col1, rec_col2 = st.columns(2)
        
        with rec_col1:
            if down_payment_pct < 20:
                st.warning(f"🔸 **Increase down payment to 20%**: Save ${car_price * 0.2 - down_payment:,.0f} more")
            else:
                st.success(f"✅ Down payment meets 20% rule!")
            
            if loan_tenure_years > 5:
                st.warning(f"🔸 **Reduce tenure to 5 years**: Saves ${total_interest - (loan_amount * (car_interest_rate/100) * 5 / 2):,.0f} in interest")
            else:
                st.success(f"✅ Loan tenure within 5-year rule!")
        
        with rec_col2:
            if emi_pct_of_salary > max_emi_pct:
                ideal_car_price = (max_affordable_emi * months) / (1 - down_payment_pct/100) if down_payment_pct < 100 else 0
                st.error(f"🔸 **Consider a cheaper car**: Max budget ~${ideal_car_price:,.0f} for your salary")
            else:
                st.success(f"✅ EMI is within {max_emi_pct}% salary rule!")
            
            # Money saved if following all rules
            if not (is_affordable and down_payment_pct >= 20 and loan_tenure_years <= 5):
                st.info(f"💰 Following the 20-5-10 rule could save you from financial stress and hidden costs!")
    
    # Salary Expenditure Planner - Strategic Blueprints
    with st.expander("💼 Salary Expenditure Planner - Build Your Financial Strategy", expanded=False):
        st.markdown("**Choose your financial mindset and get a personalized budget allocation plan!**")
        
        # Plan Definitions
        plans = {
            "🛡️ Stable Plan": {
                "subtitle": "The Safety Fortress",
                "description": "Protect wealth, build security, avoid risk shocks.",
                "ideal_for": "Students, new earners, people in uncertain environments.",
                "allocations": {
                    "Essentials (Rent, Food, Utilities)": (55, 60),
                    "Savings / Emergency Fund": (20, 25),
                    "Investments": (5, 10),
                    "Personal / Discretionary": (10, 10)
                },
                "goal": "Predictable net worth growth with zero risk.",
                "color": "#10b981"
            },
            "⚖️ Balanced Plan": {
                "subtitle": "The Smart Builder",
                "description": "Grow wealth while staying protected.",
                "ideal_for": "Stable income, moderate risk tolerance, medium-term goals.",
                "allocations": {
                    "Essentials": (50, 50),
                    "Savings / Cash Reserve": (15, 20),
                    "Investments": (20, 25),
                    "Personal / Learning / Growth": (5, 10)
                },
                "goal": "Steady growth + flexibility to handle life's shocks.",
                "color": "#3b82f6"
            },
            "🚀 Aggressive Plan": {
                "subtitle": "The Accelerator",
                "description": "Maximize returns, accept volatility.",
                "ideal_for": "High ambition, low dependency, long-term outlook.",
                "allocations": {
                    "Essentials": (40, 45),
                    "Savings": (10, 15),
                    "Investments": (35, 45),
                    "Personal / Risk Ventures": (5, 10)
                },
                "goal": "Double or triple savings growth through compounding + reinvestment.",
                "color": "#f59e0b"
            }
        }
        
        # Plan Selector
        st.markdown("### 🎯 Select Your Financial Mindset")
        selected_plan_name = st.radio(
            "Choose the strategy that matches your goals:",
            options=list(plans.keys()),
            format_func=lambda x: x,
            horizontal=True
        )
        
        selected_plan = plans[selected_plan_name]
        
        # Display plan info
        st.info(f"**{selected_plan['subtitle']}**: {selected_plan['description']}\n\n"
                f"**Ideal For**: {selected_plan['ideal_for']}\n\n"
                f"**Goal**: {selected_plan['goal']}")
        
        # Input Section
        st.markdown("### 💰 Your Financial Details")
        input_col1, input_col2 = st.columns(2)
        
        with input_col1:
            monthly_salary_plan = st.number_input(
                "💵 Monthly Take-Home Salary ($)", 
                min_value=0.0, 
                value=5000.0, 
                step=500.0,
                help="Your after-tax monthly income"
            )
        
        with input_col2:
            projection_months = st.slider(
                "📅 Projection Period (Months)",
                min_value=3,
                max_value=24,
                value=12,
                step=1,
                help="How far ahead do you want to project?"
            )
        
        # Calculate allocations
        st.markdown("### 📊 Recommended Budget Allocation")
        
        allocation_data = []
        total_min = 0
        total_max = 0
        
        for category, (min_pct, max_pct) in selected_plan['allocations'].items():
            mid_pct = (min_pct + max_pct) / 2
            min_amount = monthly_salary_plan * (min_pct / 100)
            max_amount = monthly_salary_plan * (max_pct / 100)
            mid_amount = monthly_salary_plan * (mid_pct / 100)
            
            allocation_data.append({
                "Category": category,
                "% Range": f"{min_pct}% - {max_pct}%",
                "Monthly Amount": f"${min_amount:,.0f} - ${max_amount:,.0f}",
                "Recommended": f"${mid_amount:,.0f}"
            })
            
            total_min += min_pct
            total_max += max_pct
        
        # Display allocation table
        st.dataframe(pd.DataFrame(allocation_data), use_container_width=True, hide_index=True)
        
        # Create pie chart
        fig_allocation = go.Figure(data=[go.Pie(
            labels=[cat for cat in selected_plan['allocations'].keys()],
            values=[(min_pct + max_pct) / 2 for min_pct, max_pct in selected_plan['allocations'].values()],
            hole=0.4,
            marker=dict(colors=['#ef4444', '#10b981', '#3b82f6', '#f59e0b']),
            textinfo='label+percent',
            hovertemplate='<b>%{label}</b><br>%{percent}<br>$%{value:.1f}%<extra></extra>'
        )])
        
        fig_allocation.update_layout(
            title=f'{selected_plan_name} - Budget Distribution',
            showlegend=True,
            height=400
        )
        
        st.plotly_chart(fig_allocation, use_container_width=True)
        
        # Calculate projections
        st.markdown("### 🔮 Financial Projections")
        
        # Get mid-range percentages
        savings_pct = sum([mid for cat, (min_val, max_val) in selected_plan['allocations'].items() 
                          if 'Savings' in cat or 'Cash' in cat for mid in [(min_val + max_val) / 2]])
        investment_pct = sum([mid for cat, (min_val, max_val) in selected_plan['allocations'].items() 
                             if 'Investment' in cat for mid in [(min_val + max_val) / 2]])
        
        monthly_savings = monthly_salary_plan * (savings_pct / 100)
        monthly_investment = monthly_salary_plan * (investment_pct / 100)
        
        # Simple projections (no compounding for savings, 7% annual for investments)
        total_savings_projected = monthly_savings * projection_months
        
        # Investment projection with compound growth (7% annual = ~0.58% monthly)
        monthly_return = 0.07 / 12
        total_investment_projected = 0
        for month in range(projection_months):
            total_investment_projected = (total_investment_projected + monthly_investment) * (1 + monthly_return)
        
        investment_growth = total_investment_projected - (monthly_investment * projection_months)
        total_wealth_projected = total_savings_projected + total_investment_projected
        
        # Display metrics
        proj_col1, proj_col2, proj_col3, proj_col4 = st.columns(4)
        
        with proj_col1:
            st.metric("💰 Savings Goal", f"${total_savings_projected:,.0f}", 
                     delta=f"{projection_months} months")
        with proj_col2:
            st.metric("📈 Investments", f"${total_investment_projected:,.0f}",
                     delta=f"+${investment_growth:,.0f} growth")
        with proj_col3:
            st.metric("🎯 Total Wealth", f"${total_wealth_projected:,.0f}")
        with proj_col4:
            emergency_months = total_savings_projected / (monthly_salary_plan * 0.5) if monthly_salary_plan > 0 else 0
            st.metric("🛡️ Safety Net", f"{emergency_months:.1f} months",
                     help="How many months of essential expenses covered")
        
        # Projection chart
        months_array = list(range(projection_months + 1))
        savings_trajectory = [monthly_savings * m for m in months_array]
        investment_trajectory = []
        
        for m in months_array:
            inv_val = 0
            for month in range(m):
                inv_val = (inv_val + monthly_investment) * (1 + monthly_return)
            investment_trajectory.append(inv_val)
        
        wealth_trajectory = [s + i for s, i in zip(savings_trajectory, investment_trajectory)]
        
        fig_projection = go.Figure()
        
        fig_projection.add_trace(go.Scatter(
            x=months_array,
            y=wealth_trajectory,
            fill='tozeroy',
            name='Total Wealth',
            line=dict(color=selected_plan['color'], width=3),
            hovertemplate='<b>Month %{x}</b><br>Total: $%{y:,.0f}<extra></extra>'
        ))
        
        fig_projection.add_trace(go.Scatter(
            x=months_array,
            y=savings_trajectory,
            name='Savings',
            line=dict(color='#10b981', width=2, dash='dash'),
            hovertemplate='<b>Month %{x}</b><br>Savings: $%{y:,.0f}<extra></extra>'
        ))
        
        fig_projection.add_trace(go.Scatter(
            x=months_array,
            y=investment_trajectory,
            name='Investments',
            line=dict(color='#3b82f6', width=2, dash='dot'),
            hovertemplate='<b>Month %{x}</b><br>Investments: $%{y:,.0f}<extra></extra>'
        ))
        
        fig_projection.update_layout(
            title=f'📈 {projection_months}-Month Wealth Growth Projection',
            xaxis_title='Months',
            yaxis_title='Amount ($)',
            hovermode='x unified',
            template='plotly_white',
            height=450,
            showlegend=True
        )
        
        st.plotly_chart(fig_projection, use_container_width=True)
        
        # AI-Style Insights
        st.markdown("### 💡 Smart Insights")
        insight_col1, insight_col2 = st.columns(2)
        
        with insight_col1:
            if savings_pct >= 20:
                st.success(f"✅ **Excellent saving rate!** At {savings_pct:.0f}% savings, you're building a strong financial foundation.")
            elif savings_pct >= 15:
                st.info(f"💪 **Good progress!** Your {savings_pct:.0f}% savings rate is solid. Consider pushing to 20% for faster growth.")
            else:
                st.warning(f"⚠️ **Room for improvement**: {savings_pct:.0f}% savings might limit emergency fund growth. Aim for 15-20%.")
            
            # Emergency fund timeline
            target_emergency_fund = monthly_salary_plan * 6  # 6 months of salary
            months_to_goal = target_emergency_fund / monthly_savings if monthly_savings > 0 else 0
            if months_to_goal <= 12:
                st.success(f"🎯 You'll reach a 6-month emergency fund in just **{months_to_goal:.1f} months**!")
            else:
                st.info(f"📅 At your current rate, you'll build a 6-month safety net in **{months_to_goal:.1f} months** (~{months_to_goal/12:.1f} years).")
        
        with insight_col2:
            # ROI comparison
            if investment_pct > 0:
                roi_percentage = (investment_growth / (monthly_investment * projection_months) * 100) if monthly_investment > 0 else 0
                st.success(f"📊 Your investments could grow by **{roi_percentage:.1f}%** over {projection_months} months with 7% annual returns!")
            
            # Plan comparison hint
            if selected_plan_name == "🛡️ Stable Plan":
                st.info("💭 **Tip**: Once you build a 6-month emergency fund, consider switching to Balanced Plan for higher growth!")
            elif selected_plan_name == "⚖️ Balanced Plan":
                st.info("💭 **Tip**: Stable job? Consider Aggressive Plan to maximize long-term wealth. Uncertain income? Stable Plan offers more protection.")
            else:
                st.info("💭 **Tip**: Make sure you have at least 3 months emergency fund before staying aggressive!")
    
    # Retirement Planning Calculator
    with st.expander("🏖️ Retirement Planning Calculator - Am I On Track?", expanded=False):
        st.markdown("**Plan your golden years and see if you're saving enough for retirement!**")
        
        ret_col1, ret_col2, ret_col3 = st.columns(3)
        
        with ret_col1:
            current_age = st.number_input("👤 Current Age", min_value=18, max_value=80, value=30, step=1)
            retirement_age = st.number_input("🏖️ Retirement Age", min_value=current_age+1, max_value=90, value=65, step=1)
            current_savings = st.number_input("💰 Current Retirement Savings ($)", min_value=0.0, value=50000.0, step=5000.0)
        
        with ret_col2:
            monthly_contribution_ret = st.number_input("📅 Monthly Contribution ($)", min_value=0.0, value=500.0, step=100.0, key="ret_monthly")
            annual_return_ret = st.slider("📈 Expected Annual Return (%)", min_value=0.0, max_value=15.0, value=7.0, step=0.5)
        
        with ret_col3:
            retirement_monthly_expenses = st.number_input("🏠 Expected Monthly Expenses in Retirement ($)", min_value=0.0, value=4000.0, step=500.0)
            social_security = st.number_input("💵 Expected Social Security/Pension ($/month)", min_value=0.0, value=1500.0, step=100.0)
            retirement_years = st.number_input("⏰ Years in Retirement", min_value=5, max_value=50, value=25, step=5, help="How long you expect to live in retirement")
        
        # Calculate retirement projections
        years_to_retirement = retirement_age - current_age
        months_to_retirement = years_to_retirement * 12
        
        # Future value at retirement
        monthly_rate_ret = annual_return_ret / (12 * 100)
        
        # FV of current savings
        fv_current = current_savings * ((1 + monthly_rate_ret) ** months_to_retirement)
        
        # FV of monthly contributions
        if monthly_contribution_ret > 0 and monthly_rate_ret > 0:
            fv_contributions = monthly_contribution_ret * (((1 + monthly_rate_ret) ** months_to_retirement - 1) / monthly_rate_ret)
        else:
            fv_contributions = monthly_contribution_ret * months_to_retirement
        
        total_at_retirement = fv_current + fv_contributions
        
        # Calculate retirement needs
        monthly_gap = retirement_monthly_expenses - social_security
        total_needed = monthly_gap * 12 * retirement_years
        
        # Calculate if on track
        surplus_or_deficit = total_at_retirement - total_needed
        on_track = surplus_or_deficit >= 0
        
        # How much would last in retirement (withdrawal calculation)
        if monthly_gap > 0:
            years_money_lasts = total_at_retirement / (monthly_gap * 12)
        else:
            years_money_lasts = float('inf')
        
        # Display verdict
        st.markdown("### 🎯 Retirement Readiness")
        
        if on_track:
            st.success(f"✅ **GREAT NEWS!** You're on track for retirement! You'll have **${surplus_or_deficit:,.0f} extra** beyond your needs!")
        else:
            st.error(f"⚠️ **ACTION NEEDED!** You're projected to be **${abs(surplus_or_deficit):,.0f} short** for retirement.")
        
        # Display metrics
        st.markdown("### 💰 Retirement Projection")
        ret_metric1, ret_metric2, ret_metric3, ret_metric4 = st.columns(4)
        
        with ret_metric1:
            st.metric("💼 At Retirement", f"${total_at_retirement:,.0f}", delta=f"In {years_to_retirement} years")
        with ret_metric2:
            st.metric("🎯 Total Needed", f"${total_needed:,.0f}", help=f"{retirement_years} years × ${monthly_gap:,.0f}/mo")
        with ret_metric3:
            if years_money_lasts == float('inf'):
                st.metric("⏰ Money Lasts", "Forever!", delta="Fully covered")
            else:
                color = "normal" if years_money_lasts >= retirement_years else "inverse"
                st.metric("⏰ Money Lasts", f"{years_money_lasts:.1f} years", delta_color=color)
        with ret_metric4:
            monthly_income_retirement = social_security + (total_at_retirement / (retirement_years * 12) if retirement_years > 0 else 0)
            st.metric("💵 Monthly Income", f"${monthly_income_retirement:,.0f}", help="Social Security + portfolio withdrawals")
        
        # Visualization
        st.markdown("### 📊 Savings Growth to Retirement")
        
        years_array_ret = list(range(years_to_retirement + 1))
        savings_trajectory_ret = []
        
        for yr in years_array_ret:
            months = yr * 12
            fv_curr = current_savings * ((1 + monthly_rate_ret) ** months)
            if monthly_contribution_ret > 0 and monthly_rate_ret > 0:
                fv_cont = monthly_contribution_ret * (((1 + monthly_rate_ret) ** months - 1) / monthly_rate_ret)
            else:
                fv_cont = monthly_contribution_ret * months
            savings_trajectory_ret.append(fv_curr + fv_cont)
        
        ages_array = [current_age + yr for yr in years_array_ret]
        
        fig_retirement = go.Figure()
        
        # Savings trajectory
        fig_retirement.add_trace(go.Scatter(
            x=ages_array,
            y=savings_trajectory_ret,
            fill='tozeroy',
            name='Projected Savings',
            line=dict(color='#10b981', width=3),
            hovertemplate='<b>Age %{x}</b><br>Savings: $%{y:,.0f}<extra></extra>'
        ))
        
        # Target line
        fig_retirement.add_hline(
            y=total_needed,
            line_dash="dash",
            line_color="orange",
            annotation_text=f"Target: ${total_needed:,.0f}",
            annotation_position="right"
        )
        
        fig_retirement.update_layout(
            title='🚀 Path to Retirement',
            xaxis_title='Age',
            yaxis_title='Savings ($)',
            hovermode='x unified',
            template='plotly_white',
            height=450
        )
        
        st.plotly_chart(fig_retirement, use_container_width=True)
        
        # Breakdown table
        st.markdown("### 📋 Retirement Income Breakdown")
        retirement_breakdown = {
            "Income Source": ["Social Security/Pension", "Portfolio Withdrawals", "**Total Monthly Income**"],
            "Amount": [
                f"${social_security:,.0f}",
                f"${monthly_gap if total_at_retirement > 0 else 0:,.0f}",
                f"**${monthly_income_retirement:,.0f}**"
            ],
            "Annual": [
                f"${social_security * 12:,.0f}",
                f"${(monthly_gap * 12) if total_at_retirement > 0 else 0:,.0f}",
                f"**${monthly_income_retirement * 12:,.0f}**"
            ]
        }
        st.dataframe(pd.DataFrame(retirement_breakdown), use_container_width=True, hide_index=True)
        
        # Smart Insights
        st.markdown("### 💡 Retirement Insights")
        ret_insight1, ret_insight2 = st.columns(2)
        
        with ret_insight1:
            if on_track:
                st.success(f"🎉 **On Track!** Keep contributing ${monthly_contribution_ret:,.0f}/month and you'll have a comfortable retirement!")
            else:
                # Calculate needed monthly contribution
                needed_fv = total_needed
                if monthly_rate_ret > 0:
                    additional_monthly = (needed_fv - fv_current) / (((1 + monthly_rate_ret) ** months_to_retirement - 1) / monthly_rate_ret)
                else:
                    additional_monthly = (needed_fv - fv_current) / months_to_retirement if months_to_retirement > 0 else 0
                increase_needed = additional_monthly - monthly_contribution_ret
                if increase_needed > 0:
                    st.warning(f"📈 **Action**: Increase monthly contribution by **${increase_needed:,.0f}** to meet your retirement goal!")
                else:
                    st.info(f"💰 **Consider**: Reducing expenses in retirement or increasing Social Security benefits.")
        
        with ret_insight2:
            # Retirement age adjustment
            if not on_track and monthly_contribution_ret > 0:
                # Calculate retirement age needed to meet goal
                years_needed = 0
                for test_years in range(1, 50):
                    test_months = test_years * 12
                    test_fv_curr = current_savings * ((1 + monthly_rate_ret) ** test_months)
                    if monthly_rate_ret > 0:
                        test_fv_cont = monthly_contribution_ret * (((1 + monthly_rate_ret) ** test_months - 1) / monthly_rate_ret)
                    else:
                        test_fv_cont = monthly_contribution_ret * test_months
                    if test_fv_curr + test_fv_cont >= total_needed:
                        years_needed = test_years
                        break
                
                if years_needed > 0:
                    adjusted_retirement_age = current_age + years_needed
                    st.info(f"⏰ **Alternative**: Retire at age **{adjusted_retirement_age}** ({years_needed} years) with current savings rate.")
            else:
                early_retirement_possible = years_money_lasts > retirement_years
                if early_retirement_possible:
                    st.success(f"🎁 **Bonus**: You might be able to retire a few years earlier or enjoy a higher lifestyle!")
    
    # Debt Payoff Planner
    with st.expander("💳 Debt Payoff Planner - Get Out of Debt Faster!", expanded=False):
        st.markdown("**Compare strategies and create a plan to become debt-free!**")
        
        st.info("💡 **Two Popular Strategies**: **Snowball** (pay smallest debt first) vs **Avalanche** (pay highest interest first)")
        
        # Number of debts
        num_debts = st.number_input("📝 How many debts do you have?", min_value=1, max_value=10, value=3, step=1)
        
        # Debt inputs
        debts = []
        st.markdown("### 📋 Enter Your Debts")
        
        for i in range(num_debts):
            with st.expander(f"Debt #{i+1}", expanded=True):
                col_debt1, col_debt2, col_debt3 = st.columns(3)
                with col_debt1:
                    debt_name = st.text_input(f"Name", value=f"Debt {i+1}", key=f"debt_name_{i}")
                    balance = st.number_input(f"Balance ($)", min_value=0.0, value=5000.0, step=100.0, key=f"debt_balance_{i}")
                with col_debt2:
                    interest = st.number_input(f"Interest Rate (%)", min_value=0.0, max_value=30.0, value=15.0, step=0.5, key=f"debt_interest_{i}")
                    min_payment = st.number_input(f"Minimum Payment ($)", min_value=0.0, value=100.0, step=10.0, key=f"debt_min_{i}")
                with col_debt3:
                    st.metric("Monthly Interest", f"${balance * (interest/100/12):,.2f}")
                    st.metric("Payoff Years (min only)", f"{(balance/min_payment/12):.1f}" if min_payment > 0 else "∞")
                
                debts.append({
                    "name": debt_name,
                    "balance": balance,
                    "interest": interest,
                    "min_payment": min_payment
                })
        
        # Extra payment
        st.markdown("### 💰 Extra Payment Strategy")
        extra_payment = st.number_input("💸 Extra Monthly Payment (beyond minimums)", min_value=0.0, value=200.0, step=50.0)
        
        # Calculate both strategies
        def calculate_payoff(debts_list, strategy, extra):
            debts_copy = [d.copy() for d in debts_list]
            total_paid = 0
            months = 0
            payoff_order = []
            
            # Sort based on strategy
            if strategy == "snowball":
                debts_copy.sort(key=lambda x: x["balance"])
            else:  # avalanche
                debts_copy.sort(key=lambda x: -x["interest"])
            
            while any(d["balance"] > 0 for d in debts_copy):
                months += 1
                if months > 600:  # Safety limit
                    break
                
                # Apply minimum payments to all debts
                for debt in debts_copy:
                    if debt["balance"] > 0:
                        monthly_interest = debt["balance"] * (debt["interest"] / 100 / 12)
                        payment = min(debt["min_payment"], debt["balance"] + monthly_interest)
                        principal = payment - monthly_interest
                        debt["balance"] -= principal
                        total_paid += payment
                        
                        if debt["balance"] <= 0:
                            debt["balance"] = 0
                            if debt["name"] not in payoff_order:
                                payoff_order.append((debt["name"], months))
                
                # Apply extra payment to target debt
                target_debt = next((d for d in debts_copy if d["balance"] > 0), None)
                if target_debt and extra > 0:
                    monthly_interest = target_debt["balance"] * (target_debt["interest"] / 100 / 12)
                    extra_to_principal = min(extra, target_debt["balance"])
                    target_debt["balance"] -= extra_to_principal
                    total_paid += extra_to_principal
                    
                    if target_debt["balance"] <= 0:
                        target_debt["balance"] = 0
                        if target_debt["name"] not in [p[0] for p in payoff_order]:
                            payoff_order.append((target_debt["name"], months))
            
            return months, total_paid, payoff_order
        
        # Calculate both strategies
        snowball_months, snowball_total, snowball_order = calculate_payoff(debts, "snowball", extra_payment)
        avalanche_months, avalanche_total, avalanche_order = calculate_payoff(debts, "avalanche", extra_payment)
        
        # Display comparison
        st.markdown("### 🔥 Strategy Comparison")
        
        strategy_col1, strategy_col2 = st.columns(2)
        
        with strategy_col1:
            st.markdown("#### ❄️ Snowball Method")
            st.info("**Pay smallest balance first** - Quick wins for motivation!")
            st.metric("⏰ Time to Debt-Free", f"{snowball_months} months", delta=f"{snowball_months/12:.1f} years")
            st.metric("💰 Total Paid", f"${snowball_total:,.0f}")
            st.metric("📊 Total Interest", f"${snowball_total - sum(d['balance'] for d in debts):,.0f}")
        
        with strategy_col2:
            st.markdown("#### 🏔️ Avalanche Method")
            st.info("**Pay highest interest first** - Save the most money!")
            st.metric("⏰ Time to Debt-Free", f"{avalanche_months} months", delta=f"{avalanche_months/12:.1f} years")
            st.metric("💰 Total Paid", f"${avalanche_total:,.0f}")
            st.metric("📊 Total Interest", f"${avalanche_total - sum(d['balance'] for d in debts):,.0f}")
        
        # Winner banner
        if avalanche_total < snowball_total:
            savings = snowball_total - avalanche_total
            time_saved = snowball_months - avalanche_months
            st.success(f"🏆 **Avalanche Wins!** Saves you **${savings:,.0f}** and **{time_saved} months** compared to Snowball!")
        elif snowball_total < avalanche_total:
            st.success(f"🏆 **Snowball Wins!** Faster payoff with quick wins for motivation!")
        else:
            st.info("Both methods result in the same outcome!")
        
        # Payoff timeline visualization
        st.markdown("### 📅 Debt Payoff Timeline")
        
        fig_debt = go.Figure()
        
        # Create timeline for avalanche (recommended)
        months_timeline = list(range(avalanche_months + 1))
        remaining_debt = []
        
        debts_sim = [d.copy() for d in debts]
        debts_sim.sort(key=lambda x: -x["interest"])  # Avalanche
        
        for month in months_timeline:
            total_remaining = sum(d["balance"] for d in debts_sim)
            remaining_debt.append(total_remaining)
            
            if month < avalanche_months:
                # Apply payments
                for debt in debts_sim:
                    if debt["balance"] > 0:
                        monthly_interest = debt["balance"] * (debt["interest"] / 100 / 12)
                        payment = min(debt["min_payment"], debt["balance"] + monthly_interest)
                        principal = payment - monthly_interest
                        debt["balance"] = max(0, debt["balance"] - principal)
                
                # Apply extra to highest interest
                target = next((d for d in debts_sim if d["balance"] > 0), None)
                if target and extra_payment > 0:
                    extra_to_principal = min(extra_payment, target["balance"])
                    target["balance"] = max(0, target["balance"] - extra_to_principal)
        
        fig_debt.add_trace(go.Scatter(
            x=months_timeline,
            y=remaining_debt,
            fill='tozeroy',
            name='Remaining Debt',
            line=dict(color='#ef4444', width=3),
            hovertemplate='<b>Month %{x}</b><br>Debt: $%{y:,.0f}<extra></extra>'
        ))
        
        fig_debt.update_layout(
            title='🚀 Journey to Debt-Free (Avalanche Method)',
            xaxis_title='Months',
            yaxis_title='Total Debt Remaining ($)',
            hovermode='x unified',
            template='plotly_white',
            height=400
        )
        
        st.plotly_chart(fig_debt, use_container_width=True)
        
        # Payoff order table
        st.markdown("### 📋 Recommended Payoff Order (Avalanche)")
        payoff_table = {
            "Order": [i+1 for i in range(len(avalanche_order))],
            "Debt Name": [p[0] for p in avalanche_order],
            "Payoff Month": [p[1] for p in avalanche_order],
            "Time from Start": [f"{p[1]} months ({p[1]/12:.1f} years)" for p in avalanche_order]
        }
        st.dataframe(pd.DataFrame(payoff_table), use_container_width=True, hide_index=True)
        
        # Smart insights
        st.markdown("### 💡 Debt Freedom Insights")
        debt_insight1, debt_insight2 = st.columns(2)
        
        with debt_insight1:
            total_debt = sum(d["balance"] for d in debts)
            total_min_payments = sum(d["min_payment"] for d in debts)
            
            st.info(f"💰 **Total Debt**: ${total_debt:,.0f}")
            st.info(f"💳 **Minimum Payments**: ${total_min_payments:,.0f}/month")
            
            if extra_payment > 0:
                st.success(f"🚀 **Accelerated Payoff**: With ${extra_payment:,.0f} extra/month, you'll be debt-free in **{avalanche_months} months**!")
            else:
                st.warning("⚠️ **Paying minimums only will take much longer!** Add extra payments to accelerate!")
        
        with debt_insight2:
            avg_interest = sum(d["balance"] * d["interest"] for d in debts) / total_debt if total_debt > 0 else 0
            st.metric("📊 Weighted Avg Interest", f"{avg_interest:.1f}%")
            
            if extra_payment >= total_min_payments * 0.5:
                st.success("🎉 **Aggressive Strategy!** Your extra payment is 50%+ of minimums - excellent!")
            elif extra_payment > 0:
                st.info(f"💪 **Good Start!** Consider increasing extra payment to ${total_min_payments * 0.5:,.0f} for faster results.")
            
            # Freedom date
            import datetime
            freedom_date = datetime.datetime.now() + datetime.timedelta(days=avalanche_months * 30)
            st.success(f"🗓️ **Freedom Date**: {freedom_date.strftime('%B %Y')}!")
    
    # Investment Portfolio Analyzer
    with st.expander("📈 Investment Portfolio Analyzer - Optimize Your Investments", expanded=False):
        st.markdown("**Analyze your portfolio allocation and get diversification recommendations!**")
        
        st.info("💡 **Tip**: A well-diversified portfolio reduces risk. Ideal allocation depends on age and risk tolerance!")
        
        # Input method
        input_method = st.radio("How do you want to enter your portfolio?", ["Manual Entry", "Quick Allocation"], horizontal=True)
        
        if input_method == "Manual Entry":
            st.markdown("### 📋 Enter Your Holdings")
            num_holdings = st.number_input("Number of holdings", min_value=1, max_value=20, value=5, step=1)
            
            holdings = []
            for i in range(num_holdings):
                col_hold1, col_hold2, col_hold3 = st.columns(3)
                with col_hold1:
                    asset_name = st.text_input(f"Asset Name", value=f"Asset {i+1}", key=f"asset_name_{i}")
                with col_hold2:
                    asset_type = st.selectbox(f"Asset Type", 
                                             ["Stocks", "Bonds", "Real Estate", "Cash", "Commodities", "Crypto"],
                                             key=f"asset_type_{i}")
                with col_hold3:
                    amount = st.number_input(f"Value ($)", min_value=0.0, value=10000.0, step=1000.0, key=f"asset_amount_{i}")
                
                holdings.append({
                    "name": asset_name,
                    "type": asset_type,
                    "amount": amount
                })
        
        else:  # Quick Allocation
            st.markdown("### 💰 Quick Portfolio Entry")
            total_portfolio = st.number_input("Total Portfolio Value ($)", min_value=0.0, value=100000.0, step=5000.0)
            
            quick_col1, quick_col2, quick_col3 = st.columns(3)
            
            with quick_col1:
                stocks_pct = st.slider("📊 Stocks (%)", 0, 100, 60, 5)
                bonds_pct = st.slider("🏦 Bonds (%)", 0, 100, 20, 5)
            with quick_col2:
                real_estate_pct = st.slider("🏠 Real Estate (%)", 0, 100, 10, 5)
                cash_pct = st.slider("💵 Cash (%)", 0, 100, 5, 5)
            with quick_col3:
                commodities_pct = st.slider("⚡ Commodities (%)", 0, 100, 3, 1)
                crypto_pct = st.slider("₿ Crypto (%)", 0, 100, 2, 1)
            
            total_pct = stocks_pct + bonds_pct + real_estate_pct + cash_pct + commodities_pct + crypto_pct
            
            if total_pct != 100:
                st.warning(f"⚠️ Total allocation is {total_pct}%. Please adjust to 100%.")
            
            holdings = [
                {"name": "Stocks", "type": "Stocks", "amount": total_portfolio * (stocks_pct / 100)},
                {"name": "Bonds", "type": "Bonds", "amount": total_portfolio * (bonds_pct / 100)},
                {"name": "Real Estate", "type": "Real Estate", "amount": total_portfolio * (real_estate_pct / 100)},
                {"name": "Cash", "type": "Cash", "amount": total_portfolio * (cash_pct / 100)},
                {"name": "Commodities", "type": "Commodities", "amount": total_portfolio * (commodities_pct / 100)},
                {"name": "Crypto", "type": "Crypto", "amount": total_portfolio * (crypto_pct / 100)}
            ]
            holdings = [h for h in holdings if h["amount"] > 0]  # Remove zero allocations
        
        # Calculate totals by type
        total_value = sum(h["amount"] for h in holdings)
        
        if total_value > 0:
            allocation_by_type = {}
            for h in holdings:
                if h["type"] not in allocation_by_type:
                    allocation_by_type[h["type"]] = 0
                allocation_by_type[h["type"]] += h["amount"]
            
            # Display current allocation
            st.markdown("### 📊 Current Portfolio Allocation")
            
            alloc_col1, alloc_col2 = st.columns(2)
            
            with alloc_col1:
                st.metric("💰 Total Portfolio Value", f"${total_value:,.0f}")
                st.metric("🎯 Number of Holdings", len(holdings))
                
                # Diversification score (simple version)
                num_types = len(allocation_by_type)
                concentration = max(allocation_by_type.values()) / total_value * 100
                
                if concentration < 40 and num_types >= 3:
                    diversification_score = 90
                    score_label = "Excellent"
                    score_color = "normal"
                elif concentration < 60 and num_types >= 2:
                    diversification_score = 70
                    score_label = "Good"
                    score_color = "normal"
                else:
                    diversification_score = 40
                    score_label = "Needs Improvement"
                    score_color = "inverse"
                
                st.metric("🎯 Diversification Score", f"{diversification_score}/100", delta=score_label, delta_color=score_color)
            
            with alloc_col2:
                # Pie chart
                fig_portfolio = go.Figure(data=[go.Pie(
                    labels=list(allocation_by_type.keys()),
                    values=list(allocation_by_type.values()),
                    hole=0.4,
                    marker=dict(colors=['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']),
                    textinfo='label+percent',
                    hovertemplate='<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>'
                )])
                
                fig_portfolio.update_layout(
                    title='Asset Allocation',
                    showlegend=True,
                    height=300,
                    margin=dict(t=30, b=0, l=0, r=0)
                )
                
                st.plotly_chart(fig_portfolio, use_container_width=True)
            
            # Allocation table
            st.markdown("### 📋 Detailed Breakdown")
            breakdown_data = {
                "Asset Type": list(allocation_by_type.keys()),
                "Value": [f"${v:,.0f}" for v in allocation_by_type.values()],
                "Percentage": [f"{(v/total_value*100):.1f}%" for v in allocation_by_type.values()],
                "Risk Level": ["High" if k in ["Stocks", "Crypto"] else "Medium" if k in ["Real Estate", "Commodities"] else "Low" for k in allocation_by_type.keys()]
            }
            st.dataframe(pd.DataFrame(breakdown_data), use_container_width=True, hide_index=True)
            
            # Recommendations based on age (ask user)
            st.markdown("### 💡 Personalized Recommendations")
            
            rec_col1, rec_col2 = st.columns(2)
            
            with rec_col1:
                user_age = st.number_input("👤 Your Age (for personalized advice)", min_value=18, max_value=90, value=35, step=1)
                risk_tolerance = st.select_slider("📊 Risk Tolerance", options=["Conservative", "Moderate", "Aggressive"], value="Moderate")
            
            with rec_col2:
                # Rule of thumb: stocks = 100 - age
                recommended_stocks = 100 - user_age
                recommended_bonds = user_age
                
                # Adjust for risk tolerance
                if risk_tolerance == "Aggressive":
                    recommended_stocks = min(90, recommended_stocks + 15)
                    recommended_bonds = max(5, recommended_bonds - 15)
                elif risk_tolerance == "Conservative":
                    recommended_stocks = max(20, recommended_stocks - 15)
                    recommended_bonds = min(70, recommended_bonds + 15)
                
                current_stocks = allocation_by_type.get("Stocks", 0) / total_value * 100
                current_bonds = allocation_by_type.get("Bonds", 0) / total_value * 100
                
                st.metric("📈 Recommended Stocks", f"{recommended_stocks:.0f}%", delta=f"Current: {current_stocks:.0f}%")
                st.metric("🏦 Recommended Bonds", f"{recommended_bonds:.0f}%", delta=f"Current: {current_bonds:.0f}%")
            
            # Rebalancing suggestions
            st.markdown("### 🔄 Rebalancing Suggestions")
            
            stocks_diff = current_stocks - recommended_stocks
            bonds_diff = current_bonds - recommended_bonds
            
            if abs(stocks_diff) > 10 or abs(bonds_diff) > 10:
                st.warning("⚠️ **Rebalancing Recommended**: Your allocation differs significantly from recommendations.")
                
                rebal_col1, rebal_col2 = st.columns(2)
                
                with rebal_col1:
                    if stocks_diff > 10:
                        reduce_amount = total_value * (stocks_diff / 100)
                        st.info(f"📉 **Reduce Stocks**: Sell ~${reduce_amount:,.0f} ({stocks_diff:.0f}%)")
                    elif stocks_diff < -10:
                        increase_amount = total_value * (abs(stocks_diff) / 100)
                        st.info(f"📈 **Increase Stocks**: Buy ~${increase_amount:,.0f} ({abs(stocks_diff):.0f}%)")
                
                with rebal_col2:
                    if bonds_diff > 10:
                        reduce_amount = total_value * (bonds_diff / 100)
                        st.info(f"📉 **Reduce Bonds**: Sell ~${reduce_amount:,.0f} ({bonds_diff:.0f}%)")
                    elif bonds_diff < -10:
                        increase_amount = total_value * (abs(bonds_diff) / 100)
                        st.info(f"📈 **Increase Bonds**: Buy ~${increase_amount:,.0f} ({abs(bonds_diff):.0f}%)")
            else:
                st.success("✅ **Well Balanced!** Your portfolio allocation is close to recommendations for your age and risk tolerance.")
            
            # Risk assessment
            st.markdown("### ⚠️ Risk Assessment")
            risk_col1, risk_col2 = st.columns(2)
            
            with risk_col1:
                high_risk = allocation_by_type.get("Stocks", 0) + allocation_by_type.get("Crypto", 0)
                high_risk_pct = high_risk / total_value * 100
                
                if high_risk_pct > 70:
                    st.warning(f"⚡ **High Risk**: {high_risk_pct:.0f}% in volatile assets. Great for long-term growth but prepare for volatility!")
                elif high_risk_pct > 40:
                    st.info(f"⚖️ **Moderate Risk**: {high_risk_pct:.0f}% in growth assets. Balanced approach with decent upside.")
                else:
                    st.success(f"🛡️ **Low Risk**: {high_risk_pct:.0f}% in volatile assets. Conservative and stable.")
            
            with risk_col2:
                # Concentration risk
                if concentration > 60:
                    st.error(f"⚠️ **Concentration Risk**: {concentration:.0f}% in one asset type. Consider diversifying!")
                elif concentration > 40:
                    st.warning(f"📊 **Moderate Concentration**: {concentration:.0f}% in top holding. Room for improvement.")
                else:
                    st.success(f"✅ **Well Diversified**: Largest position is {concentration:.0f}%.")
        else:
            st.warning("⚠️ Please enter your portfolio holdings to see analysis.")
    
    # Rent vs Buy Calculator
    with st.expander("🏠 Rent vs Buy Calculator - Make the Right Housing Decision", expanded=False):
        st.markdown("**Should you rent or buy? Compare total costs and build a smart housing strategy!**")
        
        st.info("💡 **Key Insight**: Buying isn't always better! It depends on home prices, rent costs, how long you'll stay, and opportunity costs.")
        
        # Analysis period
        analysis_years = st.slider("📅 Analysis Period (years)", min_value=1, max_value=30, value=10, step=1,
                                   help="How many years do you plan to stay in this area?")
        
        # Two columns for rent vs buy inputs
        rent_col, buy_col = st.columns(2)
        
        with rent_col:
            st.markdown("### 🏢 Renting Scenario")
            monthly_rent = st.number_input("💵 Monthly Rent ($)", min_value=0.0, value=2000.0, step=100.0)
            annual_rent_increase = st.slider("📈 Annual Rent Increase (%)", 0.0, 10.0, 3.0, 0.5)
            renters_insurance = st.number_input("🛡️ Renter's Insurance ($/month)", min_value=0.0, value=20.0, step=5.0)
            upfront_rent_costs = st.number_input("💰 Upfront Costs (security deposit, moving)", min_value=0.0, value=3000.0, step=500.0)
        
        with buy_col:
            st.markdown("### 🏠 Buying Scenario")
            home_price = st.number_input("🏡 Home Price ($)", min_value=0.0, value=400000.0, step=10000.0)
            down_payment_pct = st.slider("💰 Down Payment (%)", 0, 50, 20, 5)
            mortgage_rate = st.slider("📊 Mortgage Interest Rate (%)", 0.0, 10.0, 6.5, 0.25)
            loan_term_years = st.selectbox("⏰ Loan Term (years)", [15, 20, 30], index=2)
            
            property_tax_rate = st.slider("🏛️ Property Tax Rate (% of home value)", 0.0, 3.0, 1.2, 0.1)
            hoa_fees = st.number_input("🏘️ HOA Fees ($/month)", min_value=0.0, value=100.0, step=50.0)
            home_insurance = st.number_input("🛡️ Home Insurance ($/month)", min_value=0.0, value=150.0, step=25.0)
            maintenance_pct = st.slider("🔧 Maintenance (% of home value/year)", 0.0, 3.0, 1.0, 0.25)
            closing_costs_pct = st.slider("📄 Closing Costs (%)", 0.0, 5.0, 2.5, 0.5)
            home_appreciation = st.slider("📈 Annual Home Appreciation (%)", -5.0, 10.0, 3.0, 0.5)
        
        # Investment return for opportunity cost
        st.markdown("### 💼 Investment Assumptions")
        investment_return = st.slider("📈 Expected Investment Return (% annual)", 0.0, 15.0, 7.0, 0.5,
                                      help="If renting, what return could you earn by investing the difference?")
        
        # Calculate buying costs
        down_payment = home_price * (down_payment_pct / 100)
        loan_amount = home_price - down_payment
        closing_costs = home_price * (closing_costs_pct / 100)
        
        # Monthly mortgage payment (P&I)
        if mortgage_rate > 0 and loan_amount > 0:
            monthly_rate = mortgage_rate / (12 * 100)
            num_payments = loan_term_years * 12
            monthly_mortgage = loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
        else:
            monthly_mortgage = loan_amount / (loan_term_years * 12) if loan_term_years > 0 else 0
        
        # Display initial costs comparison
        st.markdown("### 💰 Initial Costs Comparison")
        init_col1, init_col2 = st.columns(2)
        
        with init_col1:
            st.metric("🏢 Renting - Upfront", f"${upfront_rent_costs:,.0f}")
        with init_col2:
            total_upfront_buy = down_payment + closing_costs
            st.metric("🏠 Buying - Upfront", f"${total_upfront_buy:,.0f}", 
                     delta=f"${total_upfront_buy - upfront_rent_costs:,.0f} more than renting")
        
        # Year-by-year simulation
        years_array = list(range(analysis_years + 1))
        
        # Renting costs over time
        cumulative_rent_cost = [upfront_rent_costs]
        rent_investment_value = [0]  # What if you invested the down payment difference
        current_rent = monthly_rent
        
        for year in range(1, analysis_years + 1):
            # Annual rent cost
            annual_rent = current_rent * 12 + renters_insurance * 12
            cumulative_rent_cost.append(cumulative_rent_cost[-1] + annual_rent)
            
            # Opportunity cost: invest down payment + ongoing savings
            if year == 1:
                invested = total_upfront_buy - upfront_rent_costs
            else:
                invested = rent_investment_value[-1] * (1 + investment_return/100)
            rent_investment_value.append(invested)
            
            # Increase rent
            current_rent = current_rent * (1 + annual_rent_increase / 100)
        
        # Buying costs over time
        cumulative_buy_cost = [total_upfront_buy]
        home_equity = [down_payment]
        home_value_over_time = [home_price]
        remaining_balance = loan_amount
        
        for year in range(1, analysis_years + 1):
            # Monthly costs
            property_tax_annual = home_value_over_time[-1] * (property_tax_rate / 100)
            maintenance_annual = home_value_over_time[-1] * (maintenance_pct / 100)
            insurance_annual = home_insurance * 12
            hoa_annual = hoa_fees * 12
            
            # Principal and interest for the year
            annual_mortgage_payment = monthly_mortgage * 12 if year <= loan_term_years else 0
            
            # Calculate principal and interest paid this year
            if year <= loan_term_years and loan_amount > 0:
                # Interest for the year (on declining balance)
                annual_interest = remaining_balance * (mortgage_rate / 100)
                principal_paid = annual_mortgage_payment - annual_interest
                remaining_balance = max(0, remaining_balance - principal_paid)
            else:
                annual_interest = 0
                principal_paid = 0
            
            # Total annual cost (ONLY true costs, NOT principal which builds equity)
            annual_buy_cost = annual_interest + property_tax_annual + maintenance_annual + insurance_annual + hoa_annual
            cumulative_buy_cost.append(cumulative_buy_cost[-1] + annual_buy_cost)
            
            # Home appreciation
            new_home_value = home_value_over_time[-1] * (1 + home_appreciation / 100)
            home_value_over_time.append(new_home_value)
            
            # Equity = home value - remaining mortgage
            current_equity = new_home_value - remaining_balance
            home_equity.append(current_equity)
        
        # Net worth comparison (rent + investments vs buy equity)
        rent_net_worth = [rent_investment_value[i] - cumulative_rent_cost[i] for i in range(len(years_array))]
        buy_net_worth = [home_equity[i] - cumulative_buy_cost[i] for i in range(len(years_array))]
        
        # Find break-even point
        break_even_year = None
        for year in range(len(years_array)):
            if buy_net_worth[year] > rent_net_worth[year]:
                break_even_year = year
                break
        
        # Display verdict
        st.markdown("### 🎯 Verdict")
        
        final_rent_cost = cumulative_rent_cost[-1]
        final_buy_cost = cumulative_buy_cost[-1]
        final_home_equity = home_equity[-1]
        final_home_value = home_value_over_time[-1]
        
        # Net position after analysis period
        rent_net_position = rent_investment_value[-1] - final_rent_cost
        buy_net_position = final_home_equity - final_buy_cost
        
        if buy_net_position > rent_net_position:
            advantage = buy_net_position - rent_net_position
            st.success(f"🏠 **BUYING WINS!** After {analysis_years} years, buying gives you **${advantage:,.0f} more net worth** than renting!")
        else:
            advantage = rent_net_position - buy_net_position
            st.warning(f"🏢 **RENTING WINS!** After {analysis_years} years, renting + investing saves you **${advantage:,.0f}** compared to buying!")
        
        # Key metrics
        st.markdown("### 📊 Key Metrics")
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
        with metric_col1:
            st.metric("🏢 Total Rent Paid", f"${final_rent_cost:,.0f}")
            st.metric("💼 Investments (if renting)", f"${rent_investment_value[-1]:,.0f}")
        
        with metric_col2:
            st.metric("🏠 Total Buy Costs", f"${final_buy_cost:,.0f}")
            st.metric("🏡 Home Equity Built", f"${final_home_equity:,.0f}")
        
        with metric_col3:
            monthly_buy_cost_year1 = monthly_mortgage + (property_tax_rate/100 * home_price / 12) + home_insurance + hoa_fees + (maintenance_pct/100 * home_price / 12)
            monthly_rent_cost_year1 = monthly_rent + renters_insurance
            st.metric("💵 Monthly Cost (Rent)", f"${monthly_rent_cost_year1:,.0f}")
            st.metric("💵 Monthly Cost (Buy)", f"${monthly_buy_cost_year1:,.0f}")
        
        with metric_col4:
            st.metric("🏡 Home Value", f"${final_home_value:,.0f}", 
                     delta=f"+${final_home_value - home_price:,.0f}")
            if break_even_year:
                st.metric("⚖️ Break-Even Point", f"{break_even_year} years")
            else:
                st.metric("⚖️ Break-Even Point", "Never" if buy_net_position < rent_net_position else "Immediate")
        
        # Visualization
        st.markdown("### 📈 Net Worth Comparison Over Time")
        
        fig_rent_buy = go.Figure()
        
        # Rent net worth line
        fig_rent_buy.add_trace(go.Scatter(
            x=years_array,
            y=rent_net_worth,
            name='Renting + Investing',
            line=dict(color='#3b82f6', width=3),
            hovertemplate='<b>Year %{x}</b><br>Net Worth: $%{y:,.0f}<extra></extra>'
        ))
        
        # Buy net worth line
        fig_rent_buy.add_trace(go.Scatter(
            x=years_array,
            y=buy_net_worth,
            name='Buying (Home Equity)',
            line=dict(color='#10b981', width=3),
            hovertemplate='<b>Year %{x}</b><br>Net Worth: $%{y:,.0f}<extra></extra>'
        ))
        
        # Break-even point marker
        if break_even_year and break_even_year < len(years_array):
            fig_rent_buy.add_vline(
                x=break_even_year,
                line_dash="dash",
                line_color="orange",
                annotation_text=f"Break-Even: Year {break_even_year}",
                annotation_position="top"
            )
        
        fig_rent_buy.update_layout(
            title=f'Net Worth: Renting vs Buying Over {analysis_years} Years',
            xaxis_title='Years',
            yaxis_title='Net Worth ($)',
            hovermode='x unified',
            template='plotly_white',
            height=450
        )
        
        st.plotly_chart(fig_rent_buy, use_container_width=True)
        
        # Cost breakdown over time
        st.markdown("### 💸 Cumulative Costs Over Time")
        
        fig_costs = go.Figure()
        
        fig_costs.add_trace(go.Scatter(
            x=years_array,
            y=cumulative_rent_cost,
            name='Total Rent Costs',
            fill='tozeroy',
            line=dict(color='#3b82f6', width=2),
            hovertemplate='<b>Year %{x}</b><br>Total: $%{y:,.0f}<extra></extra>'
        ))
        
        fig_costs.add_trace(go.Scatter(
            x=years_array,
            y=cumulative_buy_cost,
            name='Total Buy Costs',
            fill='tozeroy',
            line=dict(color='#10b981', width=2),
            hovertemplate='<b>Year %{x}</b><br>Total: $%{y:,.0f}<extra></extra>'
        ))
        
        fig_costs.update_layout(
            title='Cumulative Costs Comparison',
            xaxis_title='Years',
            yaxis_title='Total Cost ($)',
            hovermode='x unified',
            template='plotly_white',
            height=400
        )
        
        st.plotly_chart(fig_costs, use_container_width=True)
        
        # Smart Insights
        st.markdown("### 💡 Smart Insights")
        insight_col1, insight_col2 = st.columns(2)
        
        with insight_col1:
            if buy_net_position > rent_net_position:
                st.success(f"🏠 **Buying Advantage**: You'll build **${final_home_equity:,.0f}** in home equity!")
                if break_even_year and break_even_year <= 5:
                    st.info(f"⚡ **Quick Break-Even**: Buying becomes profitable in just {break_even_year} years!")
                elif break_even_year:
                    st.info(f"⏰ **Break-Even Timeline**: It takes {break_even_year} years for buying to beat renting.")
            else:
                st.success(f"🏢 **Renting Advantage**: Save **${advantage:,.0f}** by renting and investing!")
                if monthly_rent_cost_year1 < monthly_buy_cost_year1:
                    monthly_savings = monthly_buy_cost_year1 - monthly_rent_cost_year1
                    st.info(f"💰 **Monthly Savings**: Renting saves ${monthly_savings:,.0f}/month you can invest!")
        
        with insight_col2:
            # Opportunity cost analysis
            if down_payment > 0:
                investment_growth = (total_upfront_buy - upfront_rent_costs) * ((1 + investment_return/100) ** analysis_years)
                st.metric("📊 If You Invested Down Payment", f"${investment_growth:,.0f}",
                         help=f"${total_upfront_buy - upfront_rent_costs:,.0f} invested at {investment_return}% for {analysis_years} years")
            
            # Home appreciation insight
            appreciation_gain = final_home_value - home_price
            if appreciation_gain > 0:
                st.success(f"📈 **Home Appreciation**: Your home gained **${appreciation_gain:,.0f}** in value!")
            else:
                st.warning(f"📉 **Home Depreciation**: Your home lost **${abs(appreciation_gain):,.0f}** in value.")
            
            # Flexibility consideration
            if analysis_years < 5 and buy_net_position > rent_net_position:
                st.warning("⚠️ **Short Timeline**: Buying has high upfront costs. Consider renting if you might move soon!")
            elif analysis_years >= 10 and buy_net_position > rent_net_position:
                st.success(f"🎯 **Long-Term Win**: With {analysis_years}+ years, buying builds significant wealth!")
    
    st.markdown("---")

# 📈 Stock Analyzer Section
if st.session_state.show_stock_analyzer:
    st.markdown('<div class="section-anchor" id="stocks"></div>', unsafe_allow_html=True)
    st.header("📈 Global Quantitative Stock Analyzer")
    st.markdown("**🌍 Analyze stocks from ANY country!** AI-powered analysis with Monte Carlo simulations, ARIMA forecasting, GARCH volatility, Black-Scholes options pricing, and risk metrics for US, European, Asian, and emerging markets.")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Single Stock Analysis", "📈 Portfolio Analysis", "⚖️ Options Pricing", "🔬 Advanced Analytics", "🔍 Stock Screener & Batch DCF"])
    
    with tab1:
        st.subheader("Individual Stock Analysis - Global Markets")
        
        st.info("🤖 **AI-Powered: Type ANY company name!** Our AI recognizes thousands of companies worldwide. Examples: Apple, Tesla, Toyota, Samsung, Starbucks, Nike, Walmart, Ferrari, L'Oréal, Spotify, Adidas - and many more!")
        
        # Initialize lookup status states
        if 'lookup_error' not in st.session_state:
            st.session_state.lookup_error = None
        if 'lookup_success' not in st.session_state:
            st.session_state.lookup_success = None
        if 'analysis_success' not in st.session_state:
            st.session_state.analysis_success = None
        
        # Show lookup status messages
        if st.session_state.lookup_error:
            st.error(st.session_state.lookup_error)
        if st.session_state.lookup_success:
            st.info(st.session_state.lookup_success)
        if st.session_state.analysis_success:
            st.success(st.session_state.analysis_success)
        
        # Simple company name input - Streamlit manages state via key
        company_name = st.text_input(
            "Company Name", 
            placeholder="Type company name (e.g., Apple, Tesla, Microsoft, Toyota, Samsung...)",
            help="Just type the company name - no ticker symbols needed!",
            key="company_name_input"
        )
        
        # Store analyzer in session state
        if 'stock_analyzer' not in st.session_state:
            st.session_state.stock_analyzer = None
            st.session_state.stock_quote = None
            st.session_state.stock_metrics = None
            st.session_state.analyzed_symbol = None
        
        if st.button("🔍 Analyze", type="primary"):
            if not company_name or not company_name.strip():
                st.error("❌ Please enter a company name")
                # Clear previous results
                st.session_state.stock_analyzer = None
                st.session_state.stock_quote = None
                st.session_state.stock_metrics = None
                st.session_state.analyzed_symbol = None
            else:
                # Convert company name to ticker symbol
                print(f"[DEBUG] Looking up company: '{company_name}'")
                ticker, message = lookup_company_ticker(company_name)
                print(f"[DEBUG] Lookup result: ticker='{ticker}', message='{message}'")
                
                if not ticker:
                    print(f"[DEBUG] Ticker is empty - clearing state and showing error")
                    # Clear ALL previous data and messages when lookup fails
                    st.session_state.stock_analyzer = None
                    st.session_state.stock_quote = None
                    st.session_state.stock_metrics = None
                    st.session_state.analyzed_symbol = None
                    st.session_state.analyzed_company = None
                    st.session_state.company_name_input = ""  # Clear the text input
                    st.session_state.lookup_error = message
                    st.session_state.lookup_success = None
                    st.session_state.analysis_success = None
                    print(f"[DEBUG] About to call st.rerun()")
                    st.rerun()
                else:
                    print(f"[DEBUG] Ticker found, starting analysis for {ticker}")
                    st.session_state.lookup_error = None
                    st.session_state.lookup_success = message
                    
                    with st.spinner(f"Analyzing {company_name}..."):
                        print(f"[DEBUG] Creating StockAnalyzer for {ticker}")
                        # Use cached data to prevent repeated API calls
                        success, data_df, returns, error = get_cached_stock_data(ticker, period='2y')
                        print(f"[DEBUG] Fetch result: success={success}, error={error}")
                        
                        if success:
                            analyzer = StockAnalyzer(ticker)
                            analyzer.data = data_df
                            analyzer.returns = returns
                        
                        if not success:
                            print(f"[DEBUG] Fetch failed: {error}")
                            st.session_state.lookup_error = f"❌ {error}"
                            st.session_state.stock_analyzer = None
                            st.session_state.lookup_success = None
                            st.session_state.analysis_success = None
                            st.rerun()
                        else:
                            print(f"[DEBUG] Fetch succeeded, getting quote and metrics")
                            st.session_state.analysis_success = f"✅ Analysis complete for {company_name}!"
                            st.session_state.stock_analyzer = analyzer
                            st.session_state.analyzed_symbol = ticker
                            st.session_state.analyzed_company = company_name
                            
                            # Get quote and metrics once
                            quote, _ = analyzer.get_quote()
                            print(f"[DEBUG] Quote: {quote}")
                            st.session_state.stock_quote = quote
                            
                            metrics, _ = analyzer.calculate_metrics(benchmark_symbol='SPY', risk_free_rate=0.04)
                            print(f"[DEBUG] Metrics: {metrics is not None}")
                            st.session_state.stock_metrics = metrics
                            print(f"[DEBUG] About to rerun to display results")
                            st.rerun()
        
        # Display analysis if data exists
        print(f"[DEBUG] Checking display: stock_analyzer={st.session_state.stock_analyzer is not None}")
        if st.session_state.stock_analyzer is not None:
            print(f"[DEBUG] Displaying results for {st.session_state.analyzed_symbol}")
            # Clear temporary status messages when showing results to avoid confusion
            st.session_state.lookup_error = None
            st.session_state.lookup_success = None
            
            analyzer = st.session_state.stock_analyzer
            quote = st.session_state.stock_quote
            metrics = st.session_state.stock_metrics
            stock_symbol = st.session_state.analyzed_symbol
            
            print(f"[DEBUG] Quote exists: {quote is not None}")
            if quote:
                # Enhanced quote metrics with visual hierarchy
                render_metric_row([
                            {
                                "label": "Current Price",
                                "value": f"${quote['price']:.2f}",
                "delta": f"{quote['change_percent']}",
                "kind": "goal"
            },
            {
                "label": "Volume",
                "value": f"{quote['volume']:,}",
                "kind": "analytics"
            },
            {
                "label": "Open",
                "value": f"${quote['open']:.2f}",
                "kind": "analytics"
            },
            {
                "label": "Day Low",
                "value": f"${quote['low']:.2f}",
                "kind": "neutral"
            },
            {
                "label": "Day High",
                "value": f"${quote['high']:.2f}",
                "kind": "neutral"
            }
                ])
                
                st.plotly_chart(add_plotly_animations(create_candlestick_chart(analyzer.data, stock_symbol)), use_container_width=True)
                
                col_left, col_right = st.columns(2)
                
                with col_left:
                    st.markdown("#### 🎲 Monte Carlo Simulation")
                    mc_days = st.slider("Simulation Days", 30, 730, 252, key="mc_days")
                    mc_result, mc_error = analyzer.monte_carlo_simulation(days=mc_days, simulations=1000)
                    
                    if mc_result:
                        render_metric_card(
                            label="Expected Price",
                            value=f"${mc_result['expected_final_price']:.2f}",
                            delta=f"{((mc_result['expected_final_price']/quote['price'])-1)*100:.1f}%",
                            kind="goal"
                        )
                        st.plotly_chart(add_plotly_animations(create_monte_carlo_chart(mc_result, stock_symbol, quote['price'])), use_container_width=True)
                        
                        if st.button("🤖 Explain this graph", key="explain_monte_carlo"):
                            st.session_state.show_mc_explanation = True
                            st.rerun()
                        
                        if st.session_state.get('show_mc_explanation', False):
                            with st.spinner("AI is analyzing..."):
                                p5_value = mc_result['percentiles']['p5'][-1] if 'p5' in mc_result['percentiles'] else 0
                                p95_value = mc_result['percentiles']['p95'][-1] if 'p95' in mc_result['percentiles'] else 0
                                context = f"Stock: {stock_symbol}\nCurrent Price: ${quote['price']:.2f}\nExpected Price ({mc_days} days): ${mc_result['expected_final_price']:.2f}\n5th percentile: ${p5_value:.2f}\n95th percentile: ${p95_value:.2f}"
                                explanation = explain_graph_with_ai("monte_carlo", context)
                                st.info(f"**AI Explanation:**\n\n{explanation}")
                                if st.button("Hide explanation", key="hide_mc"):
                                    st.session_state.show_mc_explanation = False
                                    st.rerun()
                    else:
                        st.error(mc_error)
                
                with col_right:
                    st.markdown("#### 📊 ARIMA Forecast")
                    arima_result, arima_error = analyzer.arima_forecast(order=(5,1,0), days=30)
                    
                    if arima_result:
                        render_metric_card(
                            label="30-Day Forecast",
                            value=f"${arima_result['forecast'][-1]:.2f}",
                            delta=f"{((arima_result['forecast'][-1]/quote['price'])-1)*100:.1f}%",
                            kind="analytics"
                        )
                        st.plotly_chart(add_plotly_animations(create_arima_forecast_chart(analyzer.data, arima_result, stock_symbol)), use_container_width=True)
                        
                        if st.button("🤖 Explain this graph", key="explain_arima"):
                            st.session_state.show_arima_explanation = True
                            st.rerun()
                        
                        if st.session_state.get('show_arima_explanation', False):
                            with st.spinner("AI is analyzing..."):
                                context = f"Stock: {stock_symbol}\nCurrent Price: ${quote['price']:.2f}\n30-Day Forecast: ${arima_result['forecast'][-1]:.2f}\nPredicted Change: {((arima_result['forecast'][-1]/quote['price'])-1)*100:.1f}%"
                                explanation = explain_graph_with_ai("arima_forecast", context)
                                st.info(f"**AI Explanation:**\n\n{explanation}")
                                if st.button("Hide explanation", key="hide_arima"):
                                    st.session_state.show_arima_explanation = False
                                    st.rerun()
                    else:
                        st.error(arima_error)
                
                st.markdown("#### 📉 Risk Metrics & Performance")
                
                if metrics:
                    render_metric_row([
                        {
                            "label": "Sharpe Ratio",
                            "value": f"{metrics['sharpe_ratio']:.3f}",
                            "kind": "gain" if metrics['sharpe_ratio'] > 1 else "analytics"
                        },
                        {
                            "label": "Beta (vs SPY)",
                            "value": f"{metrics['beta']:.3f}",
                            "kind": "analytics"
                        },
                        {
                            "label": "Alpha",
                            "value": f"{metrics['alpha']*100:.2f}%",
                            "kind": "gain" if metrics['alpha'] > 0 else "risk"
                        },
                        {
                            "label": "Volatility",
                            "value": f"{metrics['volatility']*100:.1f}%",
                            "kind": "risk"
                        },
                        {
                            "label": "Correlation",
                            "value": f"{metrics['correlation']:.3f}",
                            "kind": "analytics"
                        }
                    ])
                
                st.markdown("#### 💰 DCF Valuation Analysis - Is This Stock Overvalued?")
                st.markdown("**Discounted Cash Flow (DCF)** calculates the intrinsic value of a stock based on its future cash flows.")
                
                # DCF Input Parameters in an expander
                with st.expander("⚙️ Adjust DCF Assumptions", expanded=False):
                    col_dcf1, col_dcf2, col_dcf3, col_dcf4 = st.columns(4)
                    with col_dcf1:
                        growth_rate = st.slider("FCF Growth Rate (%)", min_value=0, max_value=30, value=8, step=1,
                                               help="Expected annual Free Cash Flow growth rate") / 100
                    with col_dcf2:
                        terminal_growth = st.slider("Terminal Growth (%)", min_value=0, max_value=5, value=3, step=1,
                                                   help="Perpetual growth rate after forecast period") / 100
                    with col_dcf3:
                        discount_rate = st.slider("Discount Rate (%)", min_value=5, max_value=20, value=10, step=1,
                                                 help="Required rate of return (WACC)") / 100
                    with col_dcf4:
                        forecast_years = st.slider("Forecast Years", min_value=3, max_value=10, value=5, step=1,
                                                  help="Number of years to project cash flows")
                
                # Calculate DCF
                dcf_result, dcf_error = analyzer.dcf_valuation(
                    growth_rate=growth_rate,
                    terminal_growth=terminal_growth,
                    discount_rate=discount_rate,
                    years=forecast_years
                )
                
                if dcf_result:
                    # Display valuation status prominently
                    status = dcf_result['valuation_status']
                    if status == "OVERVALUED":
                        status_color = "#ff4444"
                        emoji = "⚠️"
                    elif status == "UNDERVALUED":
                        status_color = "#44ff44"
                        emoji = "✅"
                    else:
                        status_color = "#ffaa44"
                        emoji = "⚖️"
                    
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, {status_color}22 0%, {status_color}11 100%); 
                                padding: 20px; border-radius: 10px; border-left: 5px solid {status_color}; margin: 20px 0;'>
                        <h3 style='margin:0; color:{status_color};'>{emoji} {status}</h3>
                        <p style='font-size: 1.1em; margin: 10px 0;'>{dcf_result['recommendation']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Key metrics
                    col_dcf_m1, col_dcf_m2, col_dcf_m3, col_dcf_m4 = st.columns(4)
                    
                    with col_dcf_m1:
                        render_metric_card(
                            label="Intrinsic Value",
                            value=f"${dcf_result['intrinsic_value_per_share']:.2f}",
                            kind="goal"
                        )
                    
                    with col_dcf_m2:
                        render_metric_card(
                            label="Current Price",
                            value=f"${dcf_result['current_market_price']:.2f}",
                            kind="analytics"
                        )
                    
                    with col_dcf_m3:
                        delta_sign = "+" if dcf_result['overvaluation_pct'] > 0 else ""
                        render_metric_card(
                            label="Over/Under Valued",
                            value=f"{delta_sign}{dcf_result['overvaluation_pct']:.1f}%",
                            kind="risk" if dcf_result['overvaluation_pct'] > 0 else "gain"
                        )
                    
                    with col_dcf_m4:
                        if dcf_result['margin_of_safety'] > 0:
                            render_metric_card(
                                label="Margin of Safety",
                                value=f"{dcf_result['margin_of_safety']:.1f}%",
                                kind="gain"
                            )
                        else:
                            render_metric_card(
                                label="Downside Risk",
                                value=f"{dcf_result['downside_risk']:.1f}%",
                                kind="risk"
                            )
                    
                    # Show step-by-step calculation in expander
                    with st.expander("📋 View Step-by-Step DCF Calculation", expanded=False):
                        st.markdown("### 🧮 Complete DCF Valuation Process")
                        
                        st.markdown(f"""
                        **Step 1️⃣: Current Free Cash Flow (FCF)**
                        - Current FCF: **${dcf_result['fcf_current_billions']:.2f}B**
                        """)
                        
                        st.markdown(f"""
                        **Step 2️⃣: Project Future Cash Flows**
                        - Growth Rate: **{dcf_result['assumptions']['growth_rate']:.1f}%** per year
                        """)
                        
                        # Create table for projected FCFs
                        fcf_data = []
                        for year in range(1, len(dcf_result['projected_fcfs_billions']) + 1):
                            fcf_data.append({
                                'Year': year,
                                'Projected FCF ($B)': f"{dcf_result['projected_fcfs_billions'][year-1]:.2f}",
                                'Discounted PV ($B)': f"{dcf_result['discounted_fcfs_billions'][year-1]:.2f}"
                            })
                        st.table(pd.DataFrame(fcf_data))
                        
                        st.markdown(f"""
                        **Step 3️⃣: Sum of Discounted FCFs**
                        - Total PV of forecasted cash flows: **${dcf_result['sum_discounted_fcfs_billions']:.2f}B**
                        """)
                        
                        st.markdown(f"""
                        **Step 4️⃣: Terminal Value**
                        - Terminal Growth Rate: **{dcf_result['assumptions']['terminal_growth']:.1f}%**
                        - Terminal Value: **${dcf_result['terminal_value_billions']:.2f}B**
                        - Present Value of Terminal: **${dcf_result['pv_terminal_value_billions']:.2f}B**
                        """)
                        
                        st.markdown(f"""
                        **Step 5️⃣: Enterprise Value**
                        - Enterprise Value = Sum of PVs + PV of Terminal Value
                        - **EV = ${dcf_result['enterprise_value_billions']:.2f}B**
                        """)
                        
                        st.markdown(f"""
                        **Step 6️⃣: Adjust for Debt & Cash**
                        - Total Debt: **${dcf_result['total_debt_billions']:.2f}B**
                        - Cash: **${dcf_result['cash_billions']:.2f}B**
                        - Equity Value = EV - Debt + Cash
                        - **Equity Value = ${dcf_result['equity_value_billions']:.2f}B**
                        """)
                        
                        st.markdown(f"""
                        **Step 7️⃣: Intrinsic Value per Share**
                        - Shares Outstanding: **{dcf_result['shares_outstanding_millions']:.0f}M**
                        - **Intrinsic Value = ${dcf_result['intrinsic_value_per_share']:.2f}** per share
                        """)
                        
                        st.markdown(f"""
                        **Step 8️⃣: Compare with Market Price**
                        - Market Price: **${dcf_result['current_market_price']:.2f}**
                        - Intrinsic Value: **${dcf_result['intrinsic_value_per_share']:.2f}**
                        - Difference: **${dcf_result['price_difference']:.2f}** ({dcf_result['overvaluation_pct']:.1f}%)
                        
                        **Verdict: {dcf_result['valuation_status']}** {emoji}
                        """)
                    
                    st.info("💡 **Tip:** Adjust the assumptions above to run sensitivity analysis and see how different scenarios affect valuation.")
                    
                elif dcf_error:
                    # Check if it's a rate limiting error
                    if "Too Many Requests" in str(dcf_error) or "Rate limited" in str(dcf_error):
                        st.warning(f"⚠️ DCF Analysis temporarily unavailable: {dcf_error}")
                        st.info("🕐 **Rate Limit Hit**: Yahoo Finance has blocked too many requests. **Solutions:**\n"
                               "- Wait 2-3 minutes before trying again\n"
                               "- Use the **Stock Screener** tab which has built-in delays\n"
                               "- Analyze fewer stocks at once")
                    else:
                        st.warning(f"⚠️ DCF Analysis not available: {dcf_error}")
                        st.info("💡 DCF valuation requires detailed financial statements. Some stocks (especially small-cap, international, or recently IPO'd) may not have sufficient data available.")
                
                st.markdown("#### 🌊 GARCH Volatility Forecast")
                garch_result, garch_error = analyzer.garch_volatility(p=1, q=1)
                
                if garch_result:
                    st.plotly_chart(add_plotly_animations(create_volatility_chart(garch_result, stock_symbol)), use_container_width=True)
                    
                    if st.button("🤖 Explain this graph", key="explain_garch"):
                        st.session_state.show_garch_explanation = True
                        st.rerun()
                    
                    if st.session_state.get('show_garch_explanation', False):
                        with st.spinner("AI is analyzing..."):
                            context = f"Stock: {stock_symbol}\nCurrent Volatility: {garch_result['current_volatility']:.4f}\n30-Day Forecast Volatility: {garch_result['volatility_forecast'][-1]:.4f}\nTrend: {'Increasing' if garch_result['volatility_forecast'][-1] > garch_result['current_volatility'] else 'Decreasing'}"
                            explanation = explain_graph_with_ai("garch_volatility", context)
                            st.info(f"**AI Explanation:**\n\n{explanation}")
                            if st.button("Hide explanation", key="hide_garch"):
                                st.session_state.show_garch_explanation = False
                                st.rerun()
                else:
                    st.warning(garch_error)
                
                st.markdown("#### 🤖 AI Analysis")
                if quote and metrics:
                    with st.spinner("AI is analyzing..."):
                        ai_analysis, ai_error = get_ai_stock_analysis(stock_symbol, quote, metrics, mc_result, arima_result)
                        
                        if ai_analysis:
                            rating_colors = {
                                "Strong Buy": "🟢", "Buy": "🟢", "Hold": "🟡", 
                                "Sell": "🔴", "Strong Sell": "🔴"
                            }
                            rating = ai_analysis.get('rating', 'Hold')
                            
                            col_ai1, col_ai2, col_ai3 = st.columns(3)
                            with col_ai1:
                                st.markdown(f"### {rating_colors.get(rating, '🟡')} {rating}")
                            with col_ai2:
                                st.metric("Confidence", f"{ai_analysis.get('confidence', 0)}%")
                            with col_ai3:
                                risk_level = ai_analysis.get('risk_level', 'Medium')
                                st.metric("Risk Level", risk_level)
                            
                            st.info(ai_analysis.get('analysis', ''))
                            
                            st.markdown("**Key Insights:**")
                            for insight in ai_analysis.get('key_insights', []):
                                st.markdown(f"- {insight}")
                            
                            st.success(f"**Recommendation:** {ai_analysis.get('recommendation', '')}")
                        else:
                            st.error(ai_error)
    
    with tab2:
        st.subheader("Portfolio Analysis - Global Diversification")
        st.caption("Analyze multiple stocks from any exchange for diversification and correlation")
        
        st.info("💡 **Mix stocks from different countries** for better diversification! Example: `AAPL,7203.T,BP.L,SAP.DE,RELIANCE.NS`")
        
        portfolio_symbols = st.text_input(
            "Enter stock symbols (comma-separated)", 
            value="AAPL,MSFT,GOOGL,7203.T,BP.L", 
            key="portfolio_symbols",
            help="Mix US and international stocks for global diversification. Use ticker suffixes for non-US markets."
        )
        
        if st.button("📊 Analyze Portfolio", type="primary"):
            symbols = [s.strip().upper() for s in portfolio_symbols.split(',')]
            
            if len(symbols) < 2:
                st.error("Please enter at least 2 stock symbols")
            else:
                with st.spinner("Analyzing portfolio..."):
                    stocks_data = []
                    stocks_metrics = []
                    
                    progress_bar = st.progress(0)
                    for i, symbol in enumerate(symbols):
                        # Use cached data to prevent repeated API calls
                        success, data_df, returns, error = get_cached_stock_data(symbol, period='1y')
                        
                        if success and returns is not None:
                            analyzer = StockAnalyzer(symbol)
                            analyzer.data = data_df
                            analyzer.returns = returns
                            metrics, _ = analyzer.calculate_metrics()
                            if metrics:
                                stocks_data.append({'symbol': symbol, 'returns': analyzer.returns})
                                stocks_metrics.append({'symbol': symbol, **metrics})
                        
                        progress_bar.progress((i + 1) / len(symbols))
                    
                    progress_bar.empty()
                    
                    if len(stocks_data) >= 2:
                        st.success(f"✓ Analyzed {len(stocks_data)} stocks")
                        
                        col_port1, col_port2 = st.columns(2)
                        
                        with col_port1:
                            st.markdown("### 🔗 Correlation Matrix")
                            st.plotly_chart(create_correlation_heatmap(stocks_data), use_container_width=True)
                            
                            if st.button("🤖 Explain this graph", key="explain_correlation"):
                                st.session_state.show_corr_explanation = True
                                st.rerun()
                            
                            if st.session_state.get('show_corr_explanation', False):
                                with st.spinner("AI is analyzing..."):
                                    symbols_str = ", ".join([s['symbol'] for s in stocks_data])
                                    context = f"Portfolio stocks: {symbols_str}\nNumber of stocks: {len(stocks_data)}"
                                    explanation = explain_graph_with_ai("correlation_matrix", context)
                                    st.info(f"**AI Explanation:**\n\n{explanation}")
                                    if st.button("Hide explanation", key="hide_corr"):
                                        st.session_state.show_corr_explanation = False
                                        st.rerun()
                        
                        with col_port2:
                            st.markdown("### 📊 Risk-Return Scatter")
                            st.plotly_chart(create_risk_return_scatter(stocks_metrics), use_container_width=True)
                            
                            if st.button("🤖 Explain this graph", key="explain_risk_return"):
                                st.session_state.show_risk_explanation = True
                                st.rerun()
                            
                            if st.session_state.get('show_risk_explanation', False):
                                with st.spinner("AI is analyzing..."):
                                    context_parts = []
                                    for m in stocks_metrics:
                                        sharpe = m.get('sharpe_ratio', 0)
                                        if np.isnan(sharpe):
                                            sharpe = 0
                                        context_parts.append(
                                            f"{m['symbol']}: Return={m['mean_return']*100:.2f}%, "
                                            f"Risk={m['volatility']*100:.2f}%, Sharpe={sharpe:.2f}"
                                        )
                                    context = "\n".join(context_parts)
                                    explanation = explain_graph_with_ai("risk_return_scatter", context)
                                    st.info(f"**AI Explanation:**\n\n{explanation}")
                                    if st.button("Hide explanation", key="hide_risk"):
                                        st.session_state.show_risk_explanation = False
                                        st.rerun()
                        
                        st.markdown("### 🧠 Principal Component Analysis")
                        pca_result, pca_error = StockAnalyzer('').pca_analysis([s['symbol'] for s in stocks_data])
                        
                        if pca_result:
                            st.plotly_chart(create_pca_chart(pca_result), use_container_width=True)
                            st.info(f"💡 **Insight:** First {pca_result['n_components']} components explain {pca_result['cumulative_variance'][-1]*100:.1f}% of portfolio variance")
                            
                            if st.button("🤖 Explain this graph", key="explain_pca"):
                                st.session_state.show_pca_explanation = True
                                st.rerun()
                            
                            if st.session_state.get('show_pca_explanation', False):
                                with st.spinner("AI is analyzing..."):
                                    symbols_str = ", ".join([s['symbol'] for s in stocks_data])
                                    context = f"Portfolio: {symbols_str}\nComponents: {pca_result['n_components']}\nVariance explained: {pca_result['cumulative_variance'][-1]*100:.1f}%"
                                    explanation = explain_graph_with_ai("portfolio_pca", context)
                                    st.info(f"**AI Explanation:**\n\n{explanation}")
                                    if st.button("Hide explanation", key="hide_pca"):
                                        st.session_state.show_pca_explanation = False
                                        st.rerun()
                        
                        st.markdown("### 🤖 AI Portfolio Insights")
                        with st.spinner("Getting AI recommendations..."):
                            portfolio_insights, port_error = get_ai_portfolio_insights(stocks_metrics)
                            
                            if portfolio_insights:
                                col_ins1, col_ins2 = st.columns(2)
                                with col_ins1:
                                    st.metric("Diversification Score", f"{portfolio_insights.get('diversification_score', 0)}/100")
                                with col_ins2:
                                    st.metric("Risk Assessment", portfolio_insights.get('risk_assessment', 'N/A'))
                                
                                st.markdown("**Recommendations:**")
                                for rec in portfolio_insights.get('recommendations', []):
                                    st.markdown(f"- {rec}")
                                
                                st.info(f"**Correlation Insight:** {portfolio_insights.get('correlation_insight', '')}")
                    else:
                        st.error("Could not fetch data for enough stocks")
    
    with tab3:
        st.subheader("⚖️ Black-Scholes Options Pricing")
        st.caption("Calculate option prices and Greeks")
        
        col_opt1, col_opt2, col_opt3 = st.columns(3)
        
        with col_opt1:
            S = st.number_input("Current Stock Price ($)", min_value=0.01, value=100.0, step=1.0)
            K = st.number_input("Strike Price ($)", min_value=0.01, value=100.0, step=1.0)
        
        with col_opt2:
            T = st.number_input("Time to Expiration (years)", min_value=0.01, max_value=10.0, value=1.0, step=0.1)
            r = st.number_input("Risk-Free Rate (%)", min_value=0.0, max_value=20.0, value=4.0, step=0.5) / 100
        
        with col_opt3:
            sigma = st.number_input("Volatility (%)", min_value=0.1, max_value=200.0, value=25.0, step=1.0) / 100
            option_type = st.selectbox("Option Type", ["call", "put"])
        
        if st.button("Calculate Option Price"):
            analyzer = StockAnalyzer('')
            greeks, error = analyzer.black_scholes(S, K, T, r, sigma, option_type)
            
            if greeks:
                st.markdown(f"### {option_type.upper()} Option Results")
                
                col_g1, col_g2, col_g3, col_g4, col_g5 = st.columns(5)
                with col_g1:
                    st.metric("Price", f"${greeks['price']:.2f}")
                with col_g2:
                    st.metric("Delta (Δ)", f"{greeks['delta']:.4f}")
                with col_g3:
                    st.metric("Gamma (Γ)", f"{greeks['gamma']:.4f}")
                with col_g4:
                    st.metric("Vega (ν)", f"{greeks['vega']:.4f}")
                with col_g5:
                    st.metric("Theta (Θ)", f"{greeks['theta']:.4f}")
                
                st.markdown("#### Greeks Sensitivity Analysis")
                price_range = np.linspace(S * 0.7, S * 1.3, 50)
                greeks_data = {'prices': price_range, 'delta': [], 'gamma': [], 'vega': [], 'theta': []}
                
                for price in price_range:
                    g, _ = analyzer.black_scholes(price, K, T, r, sigma, option_type)
                    if g:
                        greeks_data['delta'].append(g['delta'])
                        greeks_data['gamma'].append(g['gamma'])
                        greeks_data['vega'].append(g['vega'])
                        greeks_data['theta'].append(g['theta'])
                
                st.plotly_chart(create_greeks_chart(greeks_data, option_type), use_container_width=True)
            else:
                st.error(error)
    
    with tab4:
        st.subheader("🔬 Advanced Statistical Analysis")
        
        adv_symbol = st.text_input("Stock Symbol", value="AAPL", key="adv_symbol").upper()
        
        if st.button("Run Analysis"):
            with st.spinner("Running advanced analytics..."):
                # Use cached data to prevent repeated API calls
                success, data_df, returns, error = get_cached_stock_data(adv_symbol, period='2y')
                
                if success:
                    analyzer = StockAnalyzer(adv_symbol)
                    analyzer.data = data_df
                    analyzer.returns = returns
                    stats, stats_error = analyzer.statistical_summary()
                    
                    if stats:
                        st.markdown("### 📊 Statistical Summary")
                        
                        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                        with col_s1:
                            st.metric("Mean Return", f"{stats['mean']*100:.3f}%")
                            st.metric("Median", f"{stats['median']*100:.3f}%")
                        with col_s2:
                            st.metric("Std Dev", f"{stats['std']*100:.3f}%")
                            st.metric("Variance", f"{stats['var']:.6f}")
                        with col_s3:
                            st.metric("Skewness", f"{stats['skewness']:.3f}")
                            st.metric("Kurtosis", f"{stats['kurtosis']:.3f}")
                        with col_s4:
                            st.metric("Min Return", f"{stats['min']*100:.2f}%")
                            st.metric("Max Return", f"{stats['max']*100:.2f}%")
                        
                        st.markdown("### 📈 Returns Distribution")
                        fig = go.Figure()
                        fig.add_trace(go.Histogram(x=analyzer.returns*100, nbinsx=50, name='Returns', marker_color='cyan'))
                        fig.update_layout(
                            title=f'{adv_symbol} Daily Returns Distribution',
                            xaxis_title='Return (%)',
                            yaxis_title='Frequency',
                            template='plotly_dark',
                            height=400
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error(error)
    
    with tab5:
        st.subheader("🔍 Stock Screener & Batch DCF Valuation")
        st.markdown("Analyze multiple stocks at once using DCF valuation to find overvalued and undervalued opportunities.")
        
        # Two options: Predefined lists or CSV upload
        screener_option = st.radio(
            "Choose Analysis Method:",
            ["📊 Popular Stocks Screener", "📤 Upload Custom CSV"],
            horizontal=True
        )
        
        if screener_option == "📊 Popular Stocks Screener":
            st.markdown("### Select Stock List to Analyze")
            
            # Predefined stock lists
            stock_lists = {
                "Tech Giants (FAANG+)": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA"],
                "Dow Jones Top 10": ["UNH", "MSFT", "GS", "HD", "CAT", "AMGN", "V", "MCD", "CRM", "BA"],
                "S&P 500 Top 20": ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "BRK-B", "TSLA", "LLY", "V", 
                                  "UNH", "XOM", "JPM", "WMT", "JNJ", "MA", "PG", "AVGO", "HD", "ORCL"],
                "Value Stocks": ["BRK-B", "JNJ", "JPM", "V", "WMT", "PG", "KO", "PEP", "COST", "HD"],
                "High Growth": ["NVDA", "TSLA", "META", "NFLX", "AMD", "CRM", "SHOP", "SQ", "ROKU", "SNAP"],
                "Dividend Aristocrats": ["JNJ", "KO", "PG", "PEP", "WMT", "MCD", "MMM", "CAT", "CVX", "XOM"]
            }
            
            selected_list = st.selectbox("Stock List:", list(stock_lists.keys()))
            tickers_to_analyze = stock_lists[selected_list]
            
            st.info(f"📋 Will analyze: {', '.join(tickers_to_analyze)}")
            
            # Rate limiting warning for large lists
            if len(tickers_to_analyze) > 10:
                est_time_min = (len(tickers_to_analyze)*3) // 60
                est_time_sec = (len(tickers_to_analyze)*3) % 60
                st.warning(f"⏱️ This will analyze {len(tickers_to_analyze)} stocks with 3-second delays (~{est_time_min} min {est_time_sec} sec total). Consider using a smaller list for faster results.")
            
        else:  # CSV Upload
            st.markdown("### Upload Stock List (CSV)")
            st.markdown("Upload a CSV file with stock ticker symbols. File should have a column named 'Ticker' or 'Symbol'")
            
            # Example CSV
            with st.expander("📄 Example CSV Format"):
                st.code("""Ticker
AAPL
MSFT
GOOGL
TSLA
AMZN""")
            
            uploaded_csv = st.file_uploader("Upload CSV file", type=['csv'])
            
            if uploaded_csv:
                try:
                    df_tickers = pd.read_csv(uploaded_csv)
                    
                    # Try to find ticker column
                    ticker_col = None
                    for col in df_tickers.columns:
                        if col.lower() in ['ticker', 'symbol', 'stock']:
                            ticker_col = col
                            break
                    
                    if ticker_col:
                        tickers_to_analyze = df_tickers[ticker_col].str.upper().tolist()
                        st.success(f"✅ Loaded {len(tickers_to_analyze)} tickers from CSV")
                        st.info(f"📋 Tickers: {', '.join(tickers_to_analyze[:10])}{' ...' if len(tickers_to_analyze) > 10 else ''}")
                    else:
                        st.error("❌ CSV must have a column named 'Ticker', 'Symbol', or 'Stock'")
                        tickers_to_analyze = []
                except Exception as e:
                    st.error(f"Error reading CSV: {str(e)}")
                    tickers_to_analyze = []
            else:
                tickers_to_analyze = []
        
        # DCF Parameters
        with st.expander("⚙️ DCF Assumptions (applies to all stocks)", expanded=False):
            col_batch1, col_batch2, col_batch3 = st.columns(3)
            with col_batch1:
                batch_growth = st.slider("FCF Growth Rate (%)", 0, 30, 8, key="batch_growth") / 100
            with col_batch2:
                batch_terminal = st.slider("Terminal Growth (%)", 0, 5, 3, key="batch_terminal") / 100
            with col_batch3:
                batch_discount = st.slider("Discount Rate (%)", 5, 20, 10, key="batch_discount") / 100
        
        # Run Analysis Button
        if st.button("🚀 Run DCF Analysis", type="primary", disabled=len(tickers_to_analyze) == 0):
            results = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Add rate limiting info
            st.info(f"⏳ Analyzing {len(tickers_to_analyze)} stocks with 3-second delays to avoid Yahoo Finance rate limits. Estimated time: ~{len(tickers_to_analyze)*3//60} min {len(tickers_to_analyze)*3%60} sec")
            
            import time
            
            for idx, ticker in enumerate(tickers_to_analyze):
                status_text.text(f"Analyzing {ticker}... ({idx+1}/{len(tickers_to_analyze)})")
                progress_bar.progress((idx + 1) / len(tickers_to_analyze))
                
                # Add delay to avoid rate limiting (except for first request)
                if idx > 0:
                    time.sleep(3)  # 3 second delay between requests to avoid Yahoo Finance rate limits
                
                try:
                    # Use cached data to prevent repeated API calls
                    success, data_df, returns, error = get_cached_stock_data(ticker, period='1y')
                    
                    if success:
                        # Create analyzer with cached data
                        analyzer = StockAnalyzer(ticker)
                        analyzer.data = data_df
                        analyzer.returns = returns
                        dcf_result, dcf_error = analyzer.dcf_valuation(
                            growth_rate=batch_growth,
                            terminal_growth=batch_terminal,
                            discount_rate=batch_discount,
                            years=5
                        )
                        
                        if dcf_result:
                            results.append({
                                'Ticker': ticker,
                                'Current Price': dcf_result['current_market_price'],
                                'Intrinsic Value': dcf_result['intrinsic_value_per_share'],
                                'Difference': dcf_result['price_difference'],
                                'Over/Under %': dcf_result['overvaluation_pct'],
                                'Status': dcf_result['valuation_status'],
                                'Margin of Safety': dcf_result['margin_of_safety'],
                                'Downside Risk': dcf_result['downside_risk']
                            })
                        else:
                            results.append({
                                'Ticker': ticker,
                                'Current Price': None,
                                'Intrinsic Value': None,
                                'Difference': None,
                                'Over/Under %': None,
                                'Status': f"Error: {dcf_error}",
                                'Margin of Safety': None,
                                'Downside Risk': None
                            })
                    else:
                        results.append({
                            'Ticker': ticker,
                            'Current Price': None,
                            'Intrinsic Value': None,
                            'Difference': None,
                            'Over/Under %': None,
                            'Status': f"Data Error: {error}",
                            'Margin of Safety': None,
                            'Downside Risk': None
                        })
                except Exception as e:
                    results.append({
                        'Ticker': ticker,
                        'Current Price': None,
                        'Intrinsic Value': None,
                        'Difference': None,
                        'Over/Under %': None,
                        'Status': f"Error: {str(e)}",
                        'Margin of Safety': None,
                        'Downside Risk': None
                    })
            
            status_text.text("✅ Analysis Complete!")
            progress_bar.empty()
            
            # Display Results
            if results:
                df_results = pd.DataFrame(results)
                
                # Summary metrics
                valid_results = df_results[df_results['Status'].isin(['OVERVALUED', 'UNDERVALUED', 'FAIRLY VALUED'])]
                
                if len(valid_results) > 0:
                    col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
                    
                    with col_sum1:
                        st.metric("✅ Analyzed Successfully", len(valid_results))
                    with col_sum2:
                        undervalued = len(valid_results[valid_results['Status'] == 'UNDERVALUED'])
                        st.metric("📉 Undervalued", undervalued, delta="Buying Opportunity")
                    with col_sum3:
                        overvalued = len(valid_results[valid_results['Status'] == 'OVERVALUED'])
                        st.metric("📈 Overvalued", overvalued, delta="Caution")
                    with col_sum4:
                        fair = len(valid_results[valid_results['Status'] == 'FAIRLY VALUED'])
                        st.metric("⚖️ Fairly Valued", fair)
                    
                    st.markdown("---")
                    
                    # Filter options
                    filter_option = st.selectbox("Filter Results:", ["All", "Undervalued Only", "Overvalued Only", "Fairly Valued Only"])
                    
                    if filter_option == "Undervalued Only":
                        display_df = valid_results[valid_results['Status'] == 'UNDERVALUED']
                    elif filter_option == "Overvalued Only":
                        display_df = valid_results[valid_results['Status'] == 'OVERVALUED']
                    elif filter_option == "Fairly Valued Only":
                        display_df = valid_results[valid_results['Status'] == 'FAIRLY VALUED']
                    else:
                        display_df = df_results
                    
                    # Format the dataframe for display
                    def format_currency(val):
                        if pd.isna(val) or val is None:
                            return "N/A"
                        return f"${val:.2f}"
                    
                    def format_percent(val):
                        if pd.isna(val) or val is None:
                            return "N/A"
                        return f"{val:.1f}%"
                    
                    def color_status(val):
                        if val == 'UNDERVALUED':
                            return 'background-color: #90EE90'
                        elif val == 'OVERVALUED':
                            return 'background-color: #FFB6C6'
                        elif val == 'FAIRLY VALUED':
                            return 'background-color: #FFE4B5'
                        return ''
                    
                    # Display table
                    st.markdown("### 📊 DCF Valuation Results")
                    
                    # Apply formatting
                    styled_df = display_df.style.format({
                        'Current Price': format_currency,
                        'Intrinsic Value': format_currency,
                        'Difference': format_currency,
                        'Over/Under %': format_percent,
                        'Margin of Safety': format_percent,
                        'Downside Risk': format_percent
                    }).applymap(color_status, subset=['Status'])
                    
                    st.dataframe(styled_df, use_container_width=True, height=400)
                    
                    # Download results
                    csv = display_df.to_csv(index=False)
                    from datetime import datetime as dt
                    st.download_button(
                        label="📥 Download Results as CSV",
                        data=csv,
                        file_name=f"dcf_analysis_{dt.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                    
                    # Best opportunities
                    if len(valid_results[valid_results['Status'] == 'UNDERVALUED']) > 0:
                        st.markdown("### 🎯 Top Buying Opportunities (Most Undervalued)")
                        undervalued_sorted = valid_results[valid_results['Status'] == 'UNDERVALUED'].sort_values('Over/Under %')
                        st.dataframe(undervalued_sorted[['Ticker', 'Current Price', 'Intrinsic Value', 'Over/Under %', 'Margin of Safety']].head(5), 
                                    use_container_width=True)
                    
                    if len(valid_results[valid_results['Status'] == 'OVERVALUED']) > 0:
                        st.markdown("### ⚠️ Most Overvalued (Avoid or Sell)")
                        overvalued_sorted = valid_results[valid_results['Status'] == 'OVERVALUED'].sort_values('Over/Under %', ascending=False)
                        st.dataframe(overvalued_sorted[['Ticker', 'Current Price', 'Intrinsic Value', 'Over/Under %', 'Downside Risk']].head(5),
                                    use_container_width=True)
                else:
                    st.warning("⚠️ No valid DCF results. Stocks may not have sufficient financial data.")
                    st.dataframe(df_results, use_container_width=True)
        
        elif len(tickers_to_analyze) == 0 and screener_option == "📤 Upload Custom CSV":
            st.info("👆 Upload a CSV file with stock tickers to begin analysis")
    
    st.markdown("---")

# 📰 Financial News Section
if st.session_state.show_news_section:
    st.markdown('<div class="section-anchor" id="news"></div>', unsafe_allow_html=True)
    st.header("📰 Financial News")
    st.markdown("**Stay updated with the latest market news and stock-specific updates**")

    # Initialize news state
    if 'news_results' not in st.session_state:
        st.session_state.news_results = None
    if 'news_searched_ticker' not in st.session_state:
        st.session_state.news_searched_ticker = None

    # Helper function to fetch and display news
    def fetch_news_for_ticker(ticker_symbol):
        """Fetch news for a given ticker and store in session state"""
        import yfinance as yf
        ticker_obj = yf.Ticker(ticker_symbol.upper())
        news_data = ticker_obj.news
        st.session_state.news_results = news_data
        st.session_state.news_searched_ticker = ticker_symbol.upper()

    def extract_nested_value(data, *keys):
        """Safely extract nested values from dict"""
        for key in keys:
            if isinstance(data, dict):
                data = data.get(key)
            else:
                return None
        return data

    def display_news_articles(news_data, ticker_symbol, max_articles=10):
        """Display news articles in a formatted way"""
        if not news_data or len(news_data) == 0:
            st.warning(f"No news found for {ticker_symbol}. Try a different ticker.")
            return

        st.success(f"Found {len(news_data)} news articles for {ticker_symbol}")

        for article in news_data[:max_articles]:
            # Deep extraction - handle any nested structure
            # Try to find title at any level
            title = None
            link = None
            publisher = None
            pub_date = None

            # Search through all possible paths for title
            if isinstance(article, dict):
                # Direct keys
                title = article.get('title')
                link = article.get('link') or article.get('url')
                publisher = article.get('publisher')
                pub_time = article.get('providerPublishTime')

                # Nested in 'content'
                content = article.get('content', {})
                if isinstance(content, dict):
                    title = title or content.get('title') or content.get('headline')
                    publisher = publisher or extract_nested_value(content, 'provider', 'displayName')
                    pub_time = pub_time or content.get('pubDate') or content.get('publishedAt')
                    link = link or extract_nested_value(content, 'canonicalUrl', 'url')
                    link = link or extract_nested_value(content, 'clickThroughUrl', 'url')

            # Fallback title
            if not title:
                title = str(article)[:100] if article else "News article"

            # Format publish time
            if pub_time:
                try:
                    if isinstance(pub_time, (int, float)):
                        from datetime import datetime
                        pub_date = datetime.fromtimestamp(pub_time).strftime('%b %d, %Y %H:%M')
                    elif isinstance(pub_time, str):
                        from datetime import datetime
                        pub_date = datetime.fromisoformat(pub_time.replace('Z', '+00:00')).strftime('%b %d, %Y %H:%M')
                    else:
                        pub_date = str(pub_time)[:20]
                except:
                    pub_date = "Recent"
            else:
                pub_date = "Recent"

            # Display the article
            with st.container():
                if link and link != '#':
                    st.markdown(f"**[{title}]({link})**")
                else:
                    st.markdown(f"**{title}**")

                st.caption(f"📰 {publisher or 'News'} • 🕐 {pub_date}")
                st.divider()

    # News source selection
    news_tab1, news_tab2 = st.tabs(["🔍 Stock-Specific News", "📊 Market Overview"])

    with news_tab1:
        st.subheader("Search News by Stock")

        # Quick access buttons for popular stocks - BEFORE the search
        st.markdown("**Quick Access:**")
        quick_cols = st.columns(6)
        quick_tickers = ["AAPL", "TSLA", "MSFT", "GOOGL", "AMZN", "NVDA"]

        for i, ticker in enumerate(quick_tickers):
            with quick_cols[i]:
                if st.button(ticker, key=f"quick_news_{ticker}"):
                    with st.spinner(f"Fetching news for {ticker}..."):
                        try:
                            fetch_news_for_ticker(ticker)
                        except Exception as e:
                            st.error(f"Error: {str(e)}")

        st.markdown("---")

        # Manual search
        news_ticker = st.text_input(
            "Or enter any Stock Ticker",
            placeholder="e.g., AAPL, TSLA, MSFT, GOOGL",
            help="Enter a stock ticker symbol to get the latest news",
            key="news_ticker_input"
        )

        if st.button("🔍 Get News", type="primary", key="get_news_btn"):
            if news_ticker:
                with st.spinner(f"Fetching news for {news_ticker.upper()}..."):
                    try:
                        fetch_news_for_ticker(news_ticker)
                    except Exception as e:
                        st.error(f"Error fetching news: {str(e)}")
            else:
                st.warning("Please enter a stock ticker symbol")

        # Display results if we have them
        if st.session_state.news_results and st.session_state.news_searched_ticker:
            st.markdown("---")
            display_news_articles(
                st.session_state.news_results,
                st.session_state.news_searched_ticker
            )

    with news_tab2:
        st.subheader("Major Market Indices News")
        st.markdown("Get the latest news for major market indices")

        # Market index proxies (ETFs that track indices)
        market_options = {
            "S&P 500 (SPY)": "SPY",
            "Dow Jones (DIA)": "DIA",
            "NASDAQ (QQQ)": "QQQ",
            "Russell 2000 (IWM)": "IWM"
        }

        selected_index = st.selectbox("Select Index", list(market_options.keys()))

        if st.button("📊 Get Market News", type="primary", key="get_market_news_btn"):
            proxy = market_options[selected_index]
            with st.spinner(f"Fetching {selected_index} news..."):
                try:
                    fetch_news_for_ticker(proxy)
                except Exception as e:
                    st.error(f"Error fetching market news: {str(e)}")

        # Display market news results
        if st.session_state.news_results and st.session_state.news_searched_ticker in ["SPY", "DIA", "QQQ", "IWM"]:
            display_news_articles(
                st.session_state.news_results,
                st.session_state.news_searched_ticker,
                max_articles=8
            )

        # Sector news shortcuts
        st.markdown("---")
        st.markdown("**Sector ETF News:**")
        sector_cols = st.columns(4)
        sectors = {
            "Tech": "XLK",
            "Finance": "XLF",
            "Healthcare": "XLV",
            "Energy": "XLE"
        }

        for i, (sector, etf) in enumerate(sectors.items()):
            with sector_cols[i]:
                if st.button(f"{sector}", key=f"sector_news_{etf}"):
                    with st.spinner(f"Fetching {sector} sector news..."):
                        try:
                            fetch_news_for_ticker(etf)
                        except Exception as e:
                            st.error(f"Error: {str(e)}")

        # Display sector results
        if st.session_state.news_results and st.session_state.news_searched_ticker in ["XLK", "XLF", "XLV", "XLE"]:
            display_news_articles(
                st.session_state.news_results,
                st.session_state.news_searched_ticker,
                max_articles=8
            )

    st.markdown("---")

# AI Chat Section
if st.session_state.show_ai_chat:
    st.markdown('<div class="section-anchor" id="aichat"></div>', unsafe_allow_html=True)
    st.header("🤖 AI Financial Assistant")
    st.markdown("**Ask me anything about your finances, budgets, or use our calculators!**")
    
    # Display chat history
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me about your finances..."):
        # Add user message to chat history
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get financial context (will use uploaded data if available)
        try:
            # Try to get context from uploaded data
            context = get_financial_context()
        except:
            context = get_financial_context()
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = chat_with_ai(prompt, context, st.session_state.chat_messages)
                st.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_messages = []
        st.rerun()
    
    st.markdown("---")

st.markdown('<div class="section-anchor" id="upload"></div>', unsafe_allow_html=True)
uploaded_files = st.file_uploader("📁 Upload Financial Data (CSV/Excel)", type=['csv', 'xlsx'], accept_multiple_files=True)

st.markdown('<div class="section-anchor" id="analysis"></div>', unsafe_allow_html=True)
tab1, tab2, tab3, tab4 = st.tabs(["📊 Main Analysis", "🥧 Expense Breakdown", "📅 Year-over-Year", "🌸 Seasonal Trends"])

if not uploaded_files:
    if 'processed_df' in st.session_state:
        del st.session_state.processed_df
    if 'primary_type' in st.session_state:
        del st.session_state.primary_type

if uploaded_files:
    try:
        # Load and detect data types
        all_dfs = []
        data_types = []
        for uploaded_file in uploaded_files:
            with st.spinner(f"Processing {uploaded_file.name}..."):
                custom_rules = get_custom_rules()
                df = load_and_categorize(uploaded_file, custom_rules, selected_currency)
                df['Source'] = uploaded_file.name
                all_dfs.append(df)
                data_types.append(df['data_type'].iloc[0] if 'data_type' in df.columns else 'unknown')
        
        # Check if mixing data types
        unique_types = set(data_types)
        if len(unique_types) > 1:
            st.warning(f"⚠️ Mixed data types detected: {', '.join(unique_types)}. Analyzing files separately.")
        
        # Determine primary data type
        primary_type = data_types[0] if data_types else 'personal_finance'
        
        if primary_type == 'corporate':
            # Corporate data analysis path
            combined_df = all_dfs[0]  # For now, analyze first corporate file
            st.session_state.processed_df = combined_df.copy()
            st.session_state.primary_type = 'corporate'
            st.success(f"✅ Loaded corporate overview data from {uploaded_files[0].name}")
        else:
            # Personal finance analysis path
            finance_dfs = [df for df, dtype in zip(all_dfs, data_types) if dtype == 'personal_finance']
            if finance_dfs:
                combined_df = pd.concat(finance_dfs, ignore_index=True)
                st.session_state.processed_df = combined_df.copy()
                st.session_state.primary_type = 'personal_finance'
                st.success(f"✅ Loaded {len(combined_df)} rows from {len(finance_dfs)} file(s). {len(combined_df[combined_df['Category'] == 'Uncategorized'])} uncategorized (manual review).")
            else:
                st.error("No valid personal finance data found.")
                st.stop()
                
    except ValueError as ve:
        if 'processed_df' in st.session_state:
            del st.session_state.processed_df
        if 'primary_type' in st.session_state:
            del st.session_state.primary_type
        st.error(f"❌ {str(ve)}")
        st.info("💡 **Quick Fix:** Make sure your CSV file has these exact column names: **Date**, **Description**, and **Amount**")
        st.stop()
    except Exception as e:
        if 'processed_df' in st.session_state:
            del st.session_state.processed_df
        if 'primary_type' in st.session_state:
            del st.session_state.primary_type
        st.error(f"❌ Error processing file: {str(e)}")
        st.stop()
    
    # Corporate Data UI
    if primary_type == 'corporate' and not st.session_state.show_company_section:
        st.info("📊 Corporate Reports section is hidden. Enable it in the sidebar to see company analysis.")
    elif primary_type == 'corporate' and st.session_state.show_company_section:
        col_info = analyze_corporate_data(combined_df)
        
        with tab1:
            st.subheader("🏢 Corporate Overview")
            st.dataframe(combined_df, use_container_width=True)
            
            # Corporate PDF Download
            st.subheader("📄 Download Report")
            corporate_pdf = generate_corporate_pdf(combined_df, col_info)
            st.download_button(
                label="📥 Download Corporate PDF Report",
                data=corporate_pdf,
                file_name=f"corporate_report_{combined_df['Source'].iloc[0] if 'Source' in combined_df.columns else 'report'}.pdf",
                mime="application/pdf",
                key="corporate_pdf_download"
            )
            
            st.divider()
            
            if col_info['year_col'] and col_info['revenue_col']:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    latest_year = combined_df[col_info['year_col']].max()
                    latest_revenue = combined_df[combined_df[col_info['year_col']] == latest_year][col_info['revenue_col']].iloc[0]
                    st.metric(f"Latest Revenue ({latest_year})", f"${latest_revenue:.2f}B")
                
                with col2:
                    if col_info['income_col']:
                        latest_income = combined_df[combined_df[col_info['year_col']] == latest_year][col_info['income_col']].iloc[0]
                        st.metric(f"Net Income ({latest_year})", f"${latest_income:.2f}B")
                
                with col3:
                    if col_info['marketcap_col']:
                        latest_cap = combined_df[combined_df[col_info['year_col']] == latest_year][col_info['marketcap_col']].iloc[0]
                        st.metric(f"Market Cap ({latest_year})", f"${latest_cap:.2f}T")
                
                # Revenue trend chart
                st.subheader("📈 Revenue Trend")
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(combined_df[col_info['year_col']], combined_df[col_info['revenue_col']], marker='o', linewidth=2, markersize=8)
                ax.set_xlabel('Year')
                ax.set_ylabel('Revenue (USD Billion)')
                ax.set_title('Revenue Growth Over Time')
                ax.grid(True, alpha=0.3)
                st.pyplot(fig)
                
                st.download_button(
                    label="📥 Download Chart as PNG",
                    data=fig_to_png_download(fig, "revenue_growth"),
                    file_name="revenue_growth.png",
                    mime="image/png",
                    key="download_revenue_chart"
                )
                plt.close(fig)
                
                # Income vs Revenue comparison
                if col_info['income_col']:
                    st.subheader("💰 Income vs Revenue")
                    fig, ax = plt.subplots(figsize=(10, 6))
                    x = combined_df[col_info['year_col']]
                    width = 0.35
                    x_pos = range(len(x))
                    ax.bar([p - width/2 for p in x_pos], combined_df[col_info['revenue_col']], width, label='Revenue', alpha=0.8)
                    ax.bar([p + width/2 for p in x_pos], combined_df[col_info['income_col']], width, label='Net Income', alpha=0.8)
                    ax.set_xlabel('Year')
                    ax.set_ylabel('Amount (USD Billion)')
                    ax.set_title('Revenue vs Net Income Comparison')
                    ax.set_xticks(x_pos)
                    ax.set_xticklabels(x)
                    ax.legend()
                    ax.grid(True, alpha=0.3, axis='y')
                    st.pyplot(fig)
                    
                    st.download_button(
                        label="📥 Download Chart as PNG",
                        data=fig_to_png_download(fig, "revenue_income_comparison"),
                        file_name="revenue_income_comparison.png",
                        mime="image/png",
                        key="download_income_chart"
                    )
                    plt.close(fig)
        
        with tab2:
            st.subheader("👥 Employee Growth")
            if col_info['employees_col'] and col_info['year_col']:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(combined_df[col_info['year_col']], combined_df[col_info['employees_col']], marker='s', linewidth=2, markersize=8, color='green')
                ax.set_xlabel('Year')
                ax.set_ylabel('Number of Employees')
                ax.set_title('Employee Growth Over Time')
                ax.grid(True, alpha=0.3)
                st.pyplot(fig)
                
                st.download_button(
                    label="📥 Download Chart as PNG",
                    data=fig_to_png_download(fig, "employee_growth"),
                    file_name="employee_growth.png",
                    mime="image/png",
                    key="download_employees_chart"
                )
                plt.close(fig)
                
                # Financial Ratios Section
                st.divider()
                st.subheader("📊 Financial Ratios")
                ratios = calculate_financial_ratios(combined_df, col_info)
                
                if ratios:
                    ratio_cols = st.columns(len(ratios))
                    for idx, (ratio_name, ratio_value) in enumerate(ratios.items()):
                        with ratio_cols[idx]:
                            st.metric(ratio_name, f"{ratio_value}")
                else:
                    st.info("Insufficient data for ratio calculations")
            else:
                st.info("Employee data not available")
        
        with tab3:
            # Company Comparison Tab - only show if multiple corporate files uploaded
            if len(all_dfs) > 1 and all('data_type' in df.columns and df['data_type'].iloc[0] == 'corporate' for df in all_dfs):
                st.subheader("🏆 Multi-Company Comparison")
                
                comparison_df = build_company_comparison(all_dfs)
                
                if not comparison_df.empty:
                    st.write("**Side-by-Side Metrics:**")
                    st.dataframe(comparison_df, use_container_width=True)
                    
                    # Comparison chart - Revenue trends (INTERACTIVE PLOTLY)
                    st.divider()
                    st.write("**Interactive Revenue Comparison:**")
                    st.caption("💡 Hover to see exact values, click legend to hide/show companies, zoom and pan")
                    
                    fig_plotly = go.Figure()
                    for df in all_dfs:
                        if 'Source' in df.columns:
                            company_name = df['Source'].iloc[0]
                            col_info_temp = analyze_corporate_data(df)
                            if col_info_temp['year_col'] and col_info_temp['revenue_col']:
                                fig_plotly.add_trace(go.Scatter(
                                    x=df[col_info_temp['year_col']],
                                    y=df[col_info_temp['revenue_col']],
                                    mode='lines+markers',
                                    name=company_name,
                                    hovertemplate='<b>%{fullData.name}</b><br>Year: %{x}<br>Revenue: $%{y:.2f}B<extra></extra>'
                                ))
                    
                    fig_plotly.update_layout(
                        title='Revenue Comparison Across Companies',
                        xaxis_title='Year',
                        yaxis_title='Revenue (USD Billion)',
                        hovermode='x unified',
                        template='plotly_white',
                        height=500
                    )
                    
                    st.plotly_chart(fig_plotly, use_container_width=True)
                else:
                    st.warning("Unable to generate comparison data")
            else:
                st.info("Upload multiple corporate data files to enable company comparison")
        
        with tab4:
            st.info("Seasonal trends available for transaction data only")
    
    # Personal Finance Data UI
    elif primary_type != 'corporate' and not st.session_state.show_personal_section:
        st.info("💰 Personal Spending section is hidden. Enable it in the sidebar to see financial analysis.")
    elif primary_type != 'corporate' and st.session_state.show_personal_section:
        with tab1:
            st.subheader("📊 Data Preview")
            st.dataframe(combined_df.head(10), use_container_width=True)
            
            col_filter1, col_filter2 = st.columns(2)
            with col_filter1:
                start_date = st.date_input("Start Date", value=combined_df['Date'].min())
            with col_filter2:
                end_date = st.date_input("End Date", value=combined_df['Date'].max())
        
        date_range = (pd.to_datetime(start_date), pd.to_datetime(end_date))
        
        if st.button("🔍 Analyze & Generate Report"):
            metrics, monthly, filtered_df = analyze_finances(combined_df, date_range)
            
            # Show currency conversion notice
            if selected_currency != 'USD':
                st.info(f"💱 All values displayed in USD (converted from {selected_currency} at rate {get_exchange_rates()[selected_currency]})")
            
            if len(filtered_df) == 0:
                st.warning("⚠️ No data found in the selected date range. Please adjust your date filters.")
            else:
                budgets = get_budgets()
                
                col3, col4, col5 = st.columns(3)
                with col3:
                    st.subheader("📈 Key Metrics")
                    st.metric("Total Income", f"${metrics['Total Income']:,.2f}")
                    st.metric("Net Profit", f"${metrics['Net Profit']:,.2f}")
                    st.metric("Profit Margin", f"{metrics['Profit Margin (%)']}%")
                
                with col4:
                    st.subheader("💰 Budget Status")
                    for category in ['Income', 'Expense', 'Investment']:
                        if category in budgets and budgets[category] > 0:
                            actual = metrics.get(f'Total {category}' if category == 'Income' else f'Total {category}s' if category == 'Expense' else 'Total Investments', 0)
                            budget = float(budgets[category])
                            pct = (actual / budget * 100) if budget > 0 else 0
                            
                            if category == 'Expense' and pct > 100:
                                st.error(f"⚠️ {category}: ${actual:,.2f} / ${budget:,.2f} ({pct:.1f}%)")
                            elif pct > 90:
                                st.warning(f"⚡ {category}: ${actual:,.2f} / ${budget:,.2f} ({pct:.1f}%)")
                            else:
                                st.success(f"✓ {category}: ${actual:,.2f} / ${budget:,.2f} ({pct:.1f}%)")
                
                with col5:
                    st.subheader("📉 Monthly Trends")
                    if not monthly.empty:
                        st.bar_chart(monthly[['Income', 'Expense']])
                    else:
                        st.info("No trend data available")
                
                chart_url, pdf_buffer = generate_report(metrics, monthly, filtered_df)
                st.image(f"data:image/png;base64,{chart_url}", caption="Visual Report")
                
                col_dl1, col_dl2, col_dl3 = st.columns(3)
                with col_dl1:
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=pdf_buffer.getvalue(),
                        file_name="financial_report.pdf",
                        mime="application/pdf"
                    )
                
                with col_dl2:
                    csv_buffer = BytesIO()
                    filtered_df.to_csv(csv_buffer, index=False)
                    st.download_button(
                        label="📊 Export as CSV",
                        data=csv_buffer.getvalue(),
                        file_name="financial_data.csv",
                        mime="text/csv"
                    )
                
                with col_dl3:
                    excel_buffer = BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        filtered_df.to_excel(writer, sheet_name='Transactions', index=False)
                        monthly.to_excel(writer, sheet_name='Monthly Summary')
                    st.download_button(
                        label="📈 Export as Excel",
                        data=excel_buffer.getvalue(),
                        file_name="financial_data.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                # Smart Insights Panel
                st.subheader("💡 Smart Insights")
                insights = generate_smart_insights(filtered_df, date_range)
                
                if insights:
                    for insight in insights:
                        if insight['type'] == 'success':
                            st.success(f"{insight['icon']} {insight['message']}")
                        elif insight['type'] == 'warning':
                            st.warning(f"{insight['icon']} {insight['message']}")
                        else:
                            st.info(f"{insight['icon']} {insight['message']}")
                else:
                    st.info("📊 Not enough data yet to generate insights. Add more transactions!")
                
                if len(uploaded_files) > 1:
                    st.subheader("📁 File Comparison")
                    file_comparison = combined_df.groupby(['Source', 'Category'])['Amount'].sum().unstack(fill_value=0)
                    st.dataframe(file_comparison)
                
                st.balloons()
        
        with tab2:
            st.subheader("🥧 Expense Breakdown by Subcategory")
            subcategories = get_expense_subcategories(combined_df)
            
            if not subcategories.empty and subcategories.sum() > 0:
                subcategories = subcategories[subcategories > 0]
                
                if not subcategories.empty:
                    col_pie1, col_pie2 = st.columns(2)
                    
                    with col_pie1:
                        fig, ax = plt.subplots(figsize=(8, 8))
                        ax.pie(subcategories.values, labels=subcategories.index, autopct='%1.1f%%', startangle=90)
                        ax.set_title('Expense Distribution by Subcategory')
                        st.pyplot(fig)
                        
                        st.download_button(
                            label="📥 Download Chart",
                            data=fig_to_png_download(fig, "expense_distribution"),
                            file_name="expense_distribution.png",
                            mime="image/png",
                            key="download_expense_pie"
                        )
                        plt.close(fig)
                    
                    with col_pie2:
                        st.write("**Breakdown:**")
                        for subcat, amount in subcategories.items():
                            st.metric(subcat, f"${amount:,.2f}")
                else:
                    st.info("No expense data available for breakdown.")
            else:
                st.info("No expense data available for breakdown.")
        
        with tab3:
            st.subheader("📅 Year-over-Year Comparison")
            yoy_data = year_over_year_analysis(combined_df)
            
            if yoy_data is not None:
                st.dataframe(yoy_data)
                
                years = combined_df['Date'].dt.year.unique()
                if len(years) >= 2:
                    st.write("**Year Comparison:**")
                    for year in sorted(years):
                        year_data = combined_df[combined_df['Date'].dt.year == year]
                        total_income = year_data[year_data['Category'] == 'Income']['Amount'].sum()
                        total_expense = year_data[year_data['Category'] == 'Expense']['Amount'].sum()
                        st.write(f"**{year}:** Income: ${total_income:,.2f}, Expenses: ${total_expense:,.2f}")
            else:
                st.info("Need data from multiple years for year-over-year comparison.")
        
        with tab4:
            st.subheader("🌸 Seasonal Spending Trends")
            seasonal_data = detect_seasonal_trends(combined_df)
            
            if not seasonal_data.empty and seasonal_data.sum() > 0:
                fig, ax = plt.subplots(figsize=(10, 6))
                seasonal_data.plot(kind='bar', ax=ax, color=['skyblue', 'lightgreen', 'coral', 'gold'])
                ax.set_title('Seasonal Expense Patterns')
                ax.set_ylabel('Total Expenses ($)')
                ax.set_xlabel('Season')
                plt.xticks(rotation=45)
                st.pyplot(fig)
                
                st.download_button(
                    label="📥 Download Chart",
                    data=fig_to_png_download(fig, "seasonal_expenses"),
                    file_name="seasonal_expenses.png",
                    mime="image/png",
                    key="download_seasonal_chart"
                )
                plt.close(fig)
                
                st.write("**Seasonal Breakdown:**")
                for season, amount in seasonal_data.items():
                    st.metric(season, f"${amount:,.2f}")
            else:
                st.info("No seasonal data available.")
        
        # Recurring Transactions Section
        st.divider()
        with st.expander("🔄 Recurring Transactions & Subscriptions", expanded=False):
            st.write("**Detect your subscriptions, rent, and regular payments:**")
            recurring_df = detect_recurring_transactions(combined_df)
            
            if not recurring_df.empty:
                st.dataframe(recurring_df, use_container_width=True)
                
                total_recurring = recurring_df['Amount'].sum()
                st.metric("💰 Total Monthly Recurring", f"${total_recurring:,.2f}")
                
                st.write("**Breakdown:**")
                for _, row in recurring_df.iterrows():
                    col_r1, col_r2, col_r3 = st.columns(3)
                    with col_r1:
                        st.write(f"**{row['Description']}**")
                    with col_r2:
                        st.write(f"${row['Amount']:,.2f} - {row['Frequency']}")
                    with col_r3:
                        st.write(f"Next: {row['Next Expected'].strftime('%Y-%m-%d')}")
            else:
                st.info("No recurring transactions detected yet. Upload more data with regular payments!")
        
        # Enhanced Forecasting with What-If Scenarios
        st.divider()
        st.subheader("🔮 Financial Forecasting & What-If Scenarios")
        
        col_forecast1, col_forecast2 = st.columns([2, 1])
        
        with col_forecast2:
            st.write("**Forecast Settings:**")
            forecast_months = st.slider("Forecast Period (months)", 3, 12, 6)
            
            st.write("**What-If Scenarios:**")
            income_change = st.slider("Income Change (%)", -50, 100, 0, step=5,
                                     help="E.g., +20% for a raise, -10% for reduced hours")
            expense_change = st.slider("Expense Change (%)", -50, 100, 0, step=5,
                                       help="E.g., -15% for cost-cutting, +10% for lifestyle changes")
        
        with col_forecast1:
            if len(combined_df) > 3:
                monthly = combined_df.groupby(combined_df['Date'].dt.to_period('M')).agg({
                    'Amount': lambda x: x[combined_df['Category'] == 'Income'].sum()
                }).rename(columns={'Amount': 'Income'})
                monthly['Expense'] = combined_df[combined_df['Category'] == 'Expense'].groupby(
                    combined_df['Date'].dt.to_period('M'))['Amount'].sum()
                
                if len(monthly) > 2:
                    # Forecast income
                    months_num = np.arange(len(monthly)).reshape(-1, 1)
                    income_values = monthly['Income'].fillna(0).values.reshape(-1, 1)
                    expense_values = monthly['Expense'].fillna(0).abs().values.reshape(-1, 1)
                    
                    income_model = LinearRegression().fit(months_num, income_values)
                    expense_model = LinearRegression().fit(months_num, expense_values)
                    
                    future_months = np.arange(len(monthly), len(monthly) + forecast_months).reshape(-1, 1)
                    income_forecast_base = income_model.predict(future_months).flatten()
                    expense_forecast_base = expense_model.predict(future_months).flatten()
                    
                    # Apply what-if adjustments
                    income_forecast = income_forecast_base * (1 + income_change / 100)
                    expense_forecast = expense_forecast_base * (1 + expense_change / 100)
                    
                    # Calculate projected savings
                    monthly_savings = income_forecast - expense_forecast
                    cumulative_savings = np.cumsum(monthly_savings)
                    
                    # Display metrics
                    col_m1, col_m2, col_m3 = st.columns(3)
                    with col_m1:
                        st.metric("Avg Monthly Income (Forecast)", f"${income_forecast.mean():,.0f}",
                                 delta=f"{income_change}%" if income_change != 0 else None)
                    with col_m2:
                        st.metric("Avg Monthly Expenses (Forecast)", f"${expense_forecast.mean():,.0f}",
                                 delta=f"{expense_change}%" if expense_change != 0 else None)
                    with col_m3:
                        st.metric(f"{forecast_months}-Month Projected Savings", f"${cumulative_savings[-1]:,.0f}",
                                 delta="Good" if cumulative_savings[-1] > 0 else "Deficit")
                    
                    # Visualization
                    fig, ax = plt.subplots(figsize=(12, 6))
                    months_labels = [f"Month +{i+1}" for i in range(forecast_months)]
                    
                    ax.plot(months_labels, income_forecast, marker='o', label='Forecasted Income', linewidth=2, color='green')
                    ax.plot(months_labels, expense_forecast, marker='s', label='Forecasted Expenses', linewidth=2, color='red')
                    ax.fill_between(range(forecast_months), income_forecast, expense_forecast,
                                   where=(income_forecast >= expense_forecast), alpha=0.3, color='green', label='Surplus')
                    ax.fill_between(range(forecast_months), income_forecast, expense_forecast,
                                   where=(income_forecast < expense_forecast), alpha=0.3, color='red', label='Deficit')
                    
                    ax.set_xlabel('Forecast Period')
                    ax.set_ylabel('Amount ($)')
                    ax.set_title(f'{forecast_months}-Month Financial Forecast')
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    plt.xticks(rotation=45)
                    st.pyplot(fig)
                    
                    st.download_button(
                        label="📥 Download Forecast Chart",
                        data=fig_to_png_download(fig, "financial_forecast"),
                        file_name="financial_forecast.png",
                        mime="image/png",
                        key="download_forecast_chart"
                    )
                    plt.close(fig)
                    
                    # Insights
                    if cumulative_savings[-1] > 0:
                        st.success(f"✅ With these parameters, you'll save ${cumulative_savings[-1]:,.0f} over {forecast_months} months")
                    else:
                        st.warning(f"⚠️ With these parameters, you'll have a deficit of ${abs(cumulative_savings[-1]):,.0f} over {forecast_months} months")
                else:
                    st.info("Need at least 3 months of data for accurate forecasting")
            else:
                st.info("Upload more transaction data to enable forecasting")
        
        # Savings Goals Tracker
        st.divider()
        st.markdown('<div class="section-anchor" id="goals"></div>', unsafe_allow_html=True)
        st.subheader("🎯 Savings Goals Tracker")
        
        col_goals1, col_goals2 = st.columns([2, 1])
        
        with col_goals1:
            st.write("**Your Savings Goals:**")
            savings_goals = get_savings_goals()
            
            if savings_goals:
                for goal in savings_goals:
                    goal_id, goal_name, target, current, deadline, created_at = goal
                    target = float(target)
                    current = float(current)
                    progress_pct = (current / target * 100) if target > 0 else 0
                    remaining = target - current
                    
                    with st.container():
                        st.write(f"**{goal_name}**")
                        
                        goal_col1, goal_col2, goal_col3, goal_col4 = st.columns([2, 1, 1.2, 0.8])
                        
                        with goal_col1:
                            render_progress_bar(
                                label="",
                                current=current,
                                target=target,
                                kind="goal"
                            )
                        
                        with goal_col2:
                            if deadline:
                                days_left = (deadline - datetime.now().date()).days
                                if days_left > 0 and remaining > 0:
                                    monthly_needed = remaining / (days_left / 30)
                                    st.metric("Monthly Needed", f"${monthly_needed:,.0f}")
                                    st.caption(f"{days_left} days left")
                                elif progress_pct >= 100:
                                    st.success("✅ Completed!")
                                else:
                                    st.warning("⚠️ Overdue")
                            else:
                                st.caption("No deadline set")
                        
                        with goal_col3:
                            new_amount = st.number_input(
                                "Update Progress",
                                min_value=0.0,
                                value=current,
                                step=10.0,
                                key=f"goal_{goal_id}"
                            )
                        
                        with goal_col4:
                            st.write("")  # Spacer to align with number input
                            btn_col1, btn_col2 = st.columns(2)
                            with btn_col1:
                                if st.button("✓", key=f"update_{goal_id}", help="Update", use_container_width=True):
                                    success, error = update_savings_goal(goal_id, new_amount)
                                    if success:
                                        st.success("Updated!")
                                        st.rerun()
                                    else:
                                        st.error(f"Error: {error}")
                            with btn_col2:
                                if st.button("🗑️", key=f"delete_{goal_id}", help="Delete", use_container_width=True):
                                    success, error = delete_savings_goal(goal_id)
                                    if success:
                                        st.success("Deleted!")
                                        st.rerun()
                                    else:
                                        st.error(f"Error: {error}")
                        
                        st.divider()
            else:
                st.info("No savings goals yet. Add one to get started!")
        
        with col_goals2:
            st.write("**Add New Goal:**")
            with st.form("add_goal_form"):
                new_goal_name = st.text_input("Goal Name", placeholder="e.g., Emergency Fund")
                new_target = st.number_input("Target Amount ($)", min_value=0.0, value=1000.0, step=100.0)
                new_current = st.number_input("Current Amount ($)", min_value=0.0, value=0.0, step=100.0)
                new_deadline = st.date_input("Deadline (optional)")
                
                submitted = st.form_submit_button("Add Goal")
                
            if submitted:
                if new_goal_name:
                    success, error = add_savings_goal(new_goal_name, new_target, new_current, new_deadline)
                    if success:
                        st.success(f"Added goal: {new_goal_name}!")
                        st.rerun()
                    else:
                        st.error(f"Error: {error}")
                else:
                    st.warning("Please enter a goal name")
