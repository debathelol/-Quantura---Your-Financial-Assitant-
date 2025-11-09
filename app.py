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
from ui_components.charts import fig_to_png_download

def get_db_connection():
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

def get_custom_rules():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT keyword, category FROM custom_rules")
        rules = cur.fetchall()
        cur.close()
        conn.close()
        return rules
    except Exception as e:
        st.sidebar.error(f"Database error loading rules: {str(e)}")
        return []

def add_custom_rule(keyword, category):
    try:
        conn = get_db_connection()
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
        cur = conn.cursor()
        cur.execute("SELECT category, budget_amount FROM budgets")
        budgets = dict(cur.fetchall())
        cur.close()
        conn.close()
        return budgets
    except Exception as e:
        st.sidebar.warning(f"Database error loading budgets: {str(e)}")
        return {}

def set_budget(category, amount):
    try:
        conn = get_db_connection()
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
        st.error(f"Database error loading savings goals: {str(e)}")
        return []

def add_savings_goal(goal_name, target_amount, current_amount, deadline):
    try:
        conn = get_db_connection()
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

st.set_page_config(page_title="FinAutomate", layout="wide")

# Dashboard Customization State
if 'show_company_section' not in st.session_state:
    st.session_state.show_company_section = True
if 'show_personal_section' not in st.session_state:
    st.session_state.show_personal_section = True
if 'show_currency_section' not in st.session_state:
    st.session_state.show_currency_section = True
if 'show_financial_tools' not in st.session_state:
    st.session_state.show_financial_tools = True

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
</style>

<div class="main-header">
    <h1 class="header-title">🚀 FinAutomate</h1>
    <p class="header-subtitle">Transform Your Financial Data into Actionable Insights</p>
    <p class="header-tagline">✨ Let's make your life hassle-free</p>
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
    
    st.divider()
    
    if st.session_state.show_currency_section:
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
    st.header("Quick Start")
    st.markdown("""
    - **Sample Data**: Use sample_data.csv with Date (YYYY-MM-DD), Description, Amount.
    - **Example**: Salary=Income, Rent=Expense, Stock=Investment.
    - **Tweak**: Add custom rules below!
    """)
    
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
    st.subheader("💰 Budget Settings")
    budgets = get_budgets()
    
    categories = ["Income", "Expense", "Investment"]
    for cat in categories:
        current_budget = budgets.get(cat, 0)
        budget_amount = st.number_input(f"{cat} Budget", value=float(current_budget), min_value=0.0, step=100.0, key=f"budget_{cat}")
        if budget_amount != current_budget:
            if st.button(f"Set {cat} Budget", key=f"set_budget_{cat}"):
                success, error = set_budget(cat, budget_amount)
                if success:
                    st.success(f"Budget set for {cat}")
                    st.rerun()
                else:
                    st.error(f"Failed to set budget: {error}")

# 🪄 Financial Tools Section - Magic of Compounding
if st.session_state.show_financial_tools:
    st.markdown("---")
    st.header("🪄 Financial Tools")
    
    with st.expander("💰 Magic of Compounding - Watch Your Money Grow!", expanded=True):
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
        
        # Display Key Metrics
        st.markdown("### 🎯 Your Wealth Projection")
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
        final_balance = balances[-1]
        final_principal = principal_total[-1]
        final_interest = interest_total[-1]
        
        with metric_col1:
            st.metric("💰 Final Balance", f"${final_balance:,.0f}")
        with metric_col2:
            st.metric("📥 Total Invested", f"${final_principal:,.0f}")
        with metric_col3:
            st.metric("✨ Interest Earned", f"${final_interest:,.0f}", delta=f"{(final_interest/final_principal*100):.1f}% return")
        with metric_col4:
            # Calculate when money doubles
            if annual_rate > 0:
                years_to_double = 72 / annual_rate  # Rule of 72
                st.metric("⏱️ Money Doubles In", f"{years_to_double:.1f} years")
        
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
            )
        )
        
        st.plotly_chart(fig_compound, use_container_width=True)
        
        # Growth Table
        st.markdown("### 📊 Year-by-Year Breakdown")
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
    
    st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Main Analysis", "🥧 Expense Breakdown", "📅 Year-over-Year", "🌸 Seasonal Trends"])

uploaded_files = st.file_uploader("📁 Upload Financial Data (CSV/Excel)", type=['csv', 'xlsx'], accept_multiple_files=True)

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
            st.success(f"✅ Loaded corporate overview data from {uploaded_files[0].name}")
        else:
            # Personal finance analysis path
            finance_dfs = [df for df, dtype in zip(all_dfs, data_types) if dtype == 'personal_finance']
            if finance_dfs:
                combined_df = pd.concat(finance_dfs, ignore_index=True)
                st.success(f"✅ Loaded {len(combined_df)} rows from {len(finance_dfs)} file(s). {len(combined_df[combined_df['Category'] == 'Uncategorized'])} uncategorized (manual review).")
            else:
                st.error("No valid personal finance data found.")
                st.stop()
                
    except ValueError as ve:
        st.error(f"❌ {str(ve)}")
        st.info("💡 **Quick Fix:** Make sure your CSV file has these exact column names: **Date**, **Description**, and **Amount**")
        st.stop()
    except Exception as e:
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
                            st.progress(min(progress_pct / 100, 1.0))
                            st.write(f"${current:,.2f} of ${target:,.2f} ({progress_pct:.1f}%)")
                        
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
