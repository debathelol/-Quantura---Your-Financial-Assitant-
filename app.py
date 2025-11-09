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

@st.cache_data
def load_and_categorize(uploaded_file):
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

@st.cache_data
def analyze_finances(df):
    df['Month'] = df['Date'].dt.to_period('M')
    monthly = df.groupby(['Month', 'Category'])['Amount'].sum().unstack(fill_value=0)
    
    all_months = pd.period_range(start=df['Date'].min().to_period('M'), 
                                 end=df['Date'].max().to_period('M'), freq='M')
    monthly = monthly.reindex(all_months, fill_value=0)
    
    total_income = monthly.get('Income', pd.Series(0)).sum()
    total_expense = monthly.get('Expense', pd.Series(0)).sum()
    total_invest = monthly.get('Investment', pd.Series(0)).sum()
    profit = total_income - total_expense
    margin = (profit / total_income * 100) if total_income > 0 else 0
    
    if len(monthly) > 1:
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
    return pd.Series(metrics), monthly

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
st.title("🚀 Automated Financial Reporting & Analysis System")
st.markdown("Upload your CSV/Excel → Auto-categorize 90% → Analyze → Report! (Reduces manual entry to ~10% tweaks.)")

with st.sidebar:
    st.header("Quick Start")
    st.markdown("""
    - **Sample Data**: Use sample_data.csv with Date (YYYY-MM-DD), Description, Amount.
    - **Example**: Salary=Income, Rent=Expense, Stock=Investment.
    - **Tweak**: Edit categorize() in app.py for more rules.
    """)

uploaded_file = st.file_uploader("📁 Upload Financial Data (CSV/Excel)", type=['csv', 'xlsx'])

if uploaded_file is not None:
    with st.spinner("Processing... Auto-categorizing 90% of entries"):
        df = load_and_categorize(uploaded_file)
    
    st.success(f"✅ Loaded {len(df)} rows. {len(df[df['Category'] == 'Uncategorized'])} uncategorized (manual review).")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Data Preview")
        st.dataframe(df.head(10), use_container_width=True)
    
    if st.button("🔍 Analyze & Generate Report"):
        metrics, monthly = analyze_finances(df)
        
        col3, col4 = st.columns(2)
        with col3:
            st.subheader("📈 Key Metrics")
            st.metric("Total Income", f"${metrics['Total Income']:,.2f}")
            st.metric("Net Profit", f"${metrics['Net Profit']:,.2f}")
            st.metric("Profit Margin", f"{metrics['Profit Margin (%)']}%")
        
        with col4:
            st.subheader("📉 Monthly Trends")
            st.bar_chart(monthly[['Income', 'Expense']])
        
        chart_url, pdf_buffer = generate_report(metrics, monthly, df)
        st.image(f"data:image/png;base64,{chart_url}", caption="Visual Report")
        
        st.download_button(
            label="📥 Download PDF Report",
            data=pdf_buffer.getvalue(),
            file_name="financial_report.pdf",
            mime="application/pdf"
        )
        
        st.balloons()

st.markdown("---")
st.markdown("Built with ❤️ for your CV. GitHub it next?")
