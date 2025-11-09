import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import re
from io import BytesIO
import base64
from sklearn.linear_model import LinearRegression
import psycopg2
import os
from datetime import datetime

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

def load_and_categorize(uploaded_file, custom_rules=None):
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
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
    
    return df

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
    total_expense = monthly['Expense'].sum() if 'Expense' in monthly.columns else 0
    total_invest = monthly['Investment'].sum() if 'Investment' in monthly.columns else 0
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

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #7c3aed 50%, #ec4899 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 20px 60px rgba(124, 58, 237, 0.3);
        position: relative;
        overflow: hidden;
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
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 0.5; }
        50% { transform: scale(1.1); opacity: 0.8; }
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
        transition: all 0.3s ease;
        font-family: 'Inter', sans-serif;
    }
    
    .feature-card:hover {
        background: rgba(255, 255, 255, 0.25);
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
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
</style>

<div class="main-header">
    <h1 class="header-title">🚀 FinAutomate</h1>
    <p class="header-subtitle">Transform Your Financial Data into Actionable Insights</p>
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

tab1, tab2, tab3, tab4 = st.tabs(["📊 Main Analysis", "🥧 Expense Breakdown", "📅 Year-over-Year", "🌸 Seasonal Trends"])

uploaded_files = st.file_uploader("📁 Upload Financial Data (CSV/Excel)", type=['csv', 'xlsx'], accept_multiple_files=True)

if uploaded_files:
    all_dfs = []
    for uploaded_file in uploaded_files:
        with st.spinner(f"Processing {uploaded_file.name}..."):
            custom_rules = get_custom_rules()
            df = load_and_categorize(uploaded_file, custom_rules)
            df['Source'] = uploaded_file.name
            all_dfs.append(df)
    
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    st.success(f"✅ Loaded {len(combined_df)} rows from {len(uploaded_files)} file(s). {len(combined_df[combined_df['Category'] == 'Uncategorized'])} uncategorized (manual review).")
    
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
                            budget = budgets[category]
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
                
                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_buffer.getvalue(),
                    file_name="financial_report.pdf",
                    mime="application/pdf"
                )
                
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
            plt.close(fig)
            
            st.write("**Seasonal Breakdown:**")
            for season, amount in seasonal_data.items():
                st.metric(season, f"${amount:,.2f}")
        else:
            st.info("No seasonal data available.")
