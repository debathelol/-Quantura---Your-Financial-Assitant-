import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
from plotly.subplots import make_subplots

def create_candlestick_chart(df, symbol):
    """Create interactive candlestick chart"""
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name=symbol
    )])
    
    fig.update_layout(
        title=f'{symbol} Price Chart',
        yaxis_title='Price ($)',
        xaxis_title='Date',
        template='plotly_dark',
        height=500,
        hovermode='x unified'
    )
    
    return fig

def create_monte_carlo_chart(monte_carlo_results, symbol, current_price):
    """Create Monte Carlo simulation fan chart"""
    days = monte_carlo_results['days']
    percentiles = monte_carlo_results['percentiles']
    
    fig = go.Figure()
    
    x_days = list(range(days))
    
    fig.add_trace(go.Scatter(
        x=x_days,
        y=percentiles['p95'],
        mode='lines',
        name='95th Percentile',
        line=dict(color='rgba(0,255,0,0.3)', width=1),
        fill=None
    ))
    
    fig.add_trace(go.Scatter(
        x=x_days,
        y=percentiles['p75'],
        mode='lines',
        name='75th Percentile',
        line=dict(color='rgba(0,200,0,0.5)', width=1),
        fill='tonexty',
        fillcolor='rgba(0,255,0,0.1)'
    ))
    
    fig.add_trace(go.Scatter(
        x=x_days,
        y=percentiles['p50'],
        mode='lines',
        name='Median (50th)',
        line=dict(color='yellow', width=3)
    ))
    
    fig.add_trace(go.Scatter(
        x=x_days,
        y=percentiles['p25'],
        mode='lines',
        name='25th Percentile',
        line=dict(color='rgba(255,100,0,0.5)', width=1),
        fill='tonexty',
        fillcolor='rgba(255,165,0,0.1)'
    ))
    
    fig.add_trace(go.Scatter(
        x=x_days,
        y=percentiles['p5'],
        mode='lines',
        name='5th Percentile',
        line=dict(color='rgba(255,0,0,0.3)', width=1),
        fill='tonexty',
        fillcolor='rgba(255,0,0,0.1)'
    ))
    
    fig.add_hline(y=current_price, line_dash="dash", line_color="white", 
                  annotation_text=f"Current: ${current_price:.2f}")
    
    fig.update_layout(
        title=f'{symbol} - Monte Carlo Price Simulation ({days} days, 1000 paths)',
        yaxis_title='Price ($)',
        xaxis_title='Days into Future',
        template='plotly_dark',
        height=500,
        hovermode='x unified'
    )
    
    return fig

def create_arima_forecast_chart(df, arima_results, symbol):
    """Create ARIMA forecast chart with confidence intervals"""
    historical_dates = df.index
    last_date = historical_dates[-1]
    
    forecast_dates = pd.date_range(
        start=last_date + pd.Timedelta(days=1),
        periods=arima_results['days']
    )
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=historical_dates[-60:],
        y=df['adjusted_close'][-60:],
        mode='lines',
        name='Historical Price',
        line=dict(color='cyan', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=forecast_dates,
        y=arima_results['forecast'],
        mode='lines',
        name='ARIMA Forecast',
        line=dict(color='yellow', width=2, dash='dash')
    ))
    
    fig.add_trace(go.Scatter(
        x=forecast_dates,
        y=arima_results['upper_bound'],
        mode='lines',
        name='Upper Confidence',
        line=dict(color='rgba(0,255,0,0.3)', width=1),
        fill=None
    ))
    
    fig.add_trace(go.Scatter(
        x=forecast_dates,
        y=arima_results['lower_bound'],
        mode='lines',
        name='Lower Confidence',
        line=dict(color='rgba(255,0,0,0.3)', width=1),
        fill='tonexty',
        fillcolor='rgba(255,255,0,0.1)'
    ))
    
    fig.update_layout(
        title=f'{symbol} - ARIMA Forecast (30 days)',
        yaxis_title='Price ($)',
        xaxis_title='Date',
        template='plotly_dark',
        height=500,
        hovermode='x unified'
    )
    
    return fig

def create_correlation_heatmap(stocks_data):
    """Create correlation heatmap for multiple stocks"""
    returns_df = pd.DataFrame()
    
    for stock in stocks_data:
        returns_df[stock['symbol']] = stock['returns']
    
    correlation_matrix = returns_df.corr()
    
    fig = go.Figure(data=go.Heatmap(
        z=correlation_matrix.values,
        x=correlation_matrix.columns,
        y=correlation_matrix.columns,
        colorscale='RdYlGn',
        zmid=0,
        text=correlation_matrix.values,
        texttemplate='%{text:.2f}',
        textfont={"size": 12},
        colorbar=dict(title="Correlation")
    ))
    
    fig.update_layout(
        title='Stock Returns Correlation Matrix',
        template='plotly_dark',
        height=500,
        width=600
    )
    
    return fig

def create_risk_return_scatter(stocks_metrics):
    """Create risk-return scatter plot"""
    symbols = [m['symbol'] for m in stocks_metrics]
    returns = [m['mean_return'] * 100 for m in stocks_metrics]
    volatilities = [m['volatility'] * 100 for m in stocks_metrics]
    sharpe_ratios = [m['sharpe_ratio'] for m in stocks_metrics]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=volatilities,
        y=returns,
        mode='markers+text',
        marker=dict(
            size=[abs(s) * 20 + 10 for s in sharpe_ratios],
            color=sharpe_ratios,
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title="Sharpe Ratio"),
            line=dict(width=2, color='white')
        ),
        text=symbols,
        textposition='top center',
        textfont=dict(size=12, color='white'),
        name='Stocks'
    ))
    
    fig.update_layout(
        title='Risk-Return Analysis',
        xaxis_title='Volatility (Annualized %)',
        yaxis_title='Return (Annualized %)',
        template='plotly_dark',
        height=500,
        hovermode='closest'
    )
    
    return fig

def create_volatility_chart(garch_results, symbol):
    """Create GARCH volatility forecast chart"""
    days = len(garch_results['volatility_forecast'])
    x_days = list(range(1, days + 1))
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=x_days,
        y=garch_results['volatility_forecast'],
        mode='lines',
        name='Volatility Forecast',
        line=dict(color='orange', width=2),
        fill='tozeroy',
        fillcolor='rgba(255,165,0,0.2)'
    ))
    
    fig.add_hline(
        y=garch_results['current_volatility'],
        line_dash="dash",
        line_color="cyan",
        annotation_text=f"Current: {garch_results['current_volatility']:.2f}%"
    )
    
    fig.update_layout(
        title=f'{symbol} - GARCH Volatility Forecast (30 days)',
        yaxis_title='Volatility (%)',
        xaxis_title='Days Ahead',
        template='plotly_dark',
        height=400
    )
    
    return fig

def create_pca_chart(pca_results):
    """Create PCA explained variance chart"""
    n_components = len(pca_results['explained_variance_ratio'])
    components = list(range(1, n_components + 1))
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Explained Variance by Component', 'Cumulative Variance')
    )
    
    fig.add_trace(
        go.Bar(
            x=components,
            y=pca_results['explained_variance_ratio'] * 100,
            name='Individual',
            marker_color='purple'
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=components,
            y=pca_results['cumulative_variance'] * 100,
            mode='lines+markers',
            name='Cumulative',
            line=dict(color='cyan', width=3),
            marker=dict(size=8)
        ),
        row=1, col=2
    )
    
    fig.update_xaxes(title_text="Component", row=1, col=1)
    fig.update_xaxes(title_text="Component", row=1, col=2)
    fig.update_yaxes(title_text="Variance Explained (%)", row=1, col=1)
    fig.update_yaxes(title_text="Cumulative Variance (%)", row=1, col=2)
    
    fig.update_layout(
        title='PCA Analysis - Portfolio Dimensionality',
        template='plotly_dark',
        height=400,
        showlegend=False
    )
    
    return fig

def create_greeks_chart(greeks_range, option_type='call'):
    """Create option Greeks visualization"""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Delta', 'Gamma', 'Vega', 'Theta')
    )
    
    prices = greeks_range['prices']
    
    fig.add_trace(
        go.Scatter(x=prices, y=greeks_range['delta'], mode='lines', name='Delta', line=dict(color='green', width=2)),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=prices, y=greeks_range['gamma'], mode='lines', name='Gamma', line=dict(color='blue', width=2)),
        row=1, col=2
    )
    
    fig.add_trace(
        go.Scatter(x=prices, y=greeks_range['vega'], mode='lines', name='Vega', line=dict(color='purple', width=2)),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=prices, y=greeks_range['theta'], mode='lines', name='Theta', line=dict(color='red', width=2)),
        row=2, col=2
    )
    
    fig.update_xaxes(title_text="Stock Price", row=1, col=1)
    fig.update_xaxes(title_text="Stock Price", row=1, col=2)
    fig.update_xaxes(title_text="Stock Price", row=2, col=1)
    fig.update_xaxes(title_text="Stock Price", row=2, col=2)
    
    fig.update_layout(
        title=f'{option_type.capitalize()} Option Greeks Sensitivity',
        template='plotly_dark',
        height=600,
        showlegend=False
    )
    
    return fig
