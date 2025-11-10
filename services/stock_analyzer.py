import os
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from scipy import stats
from scipy.optimize import minimize
import yfinance as yf
from statsmodels.tsa.arima.model import ARIMA
from arch import arch_model
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression
import json

ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY', '')

class StockAnalyzer:
    def __init__(self, symbol):
        self.symbol = symbol.upper()
        self.data = None
        self.returns = None
        
    def fetch_data_alpha_vantage(self, outputsize='compact'):
        """Fetch stock data from Alpha Vantage (compact=100 days, full=20 years)"""
        try:
            url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={self.symbol}&outputsize={outputsize}&apikey={ALPHA_VANTAGE_API_KEY}'
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if 'Time Series (Daily)' not in data:
                error_msg = data.get('Note', data.get('Error Message', 'Unknown error'))
                return False, error_msg
            
            df = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            
            df.columns = ['open', 'high', 'low', 'close', 'adjusted_close', 'volume', 'dividend', 'split']
            df = df.astype(float)
            
            self.data = df
            self.returns = df['adjusted_close'].pct_change().dropna()
            
            return True, "Data fetched successfully"
        except Exception as e:
            return False, str(e)
    
    def fetch_data_yfinance(self, period='1y'):
        """Fetch stock data from Yahoo Finance as fallback"""
        try:
            ticker = yf.Ticker(self.symbol)
            df = ticker.history(period=period)
            
            if df.empty:
                return False, "No data found for symbol"
            
            df.columns = [col.lower() for col in df.columns]
            df['adjusted_close'] = df['close']
            
            self.data = df
            self.returns = df['adjusted_close'].pct_change().dropna()
            
            return True, "Data fetched successfully"
        except Exception as e:
            return False, str(e)
    
    def get_quote(self):
        """Get real-time quote from Alpha Vantage"""
        try:
            url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={self.symbol}&apikey={ALPHA_VANTAGE_API_KEY}'
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if 'Global Quote' not in data:
                return None, data.get('Note', 'Unable to fetch quote')
            
            quote = data['Global Quote']
            return {
                'symbol': quote.get('01. symbol', self.symbol),
                'price': float(quote.get('05. price', 0)),
                'change': float(quote.get('09. change', 0)),
                'change_percent': quote.get('10. change percent', '0%'),
                'volume': int(float(quote.get('06. volume', 0))),
                'latest_trading_day': quote.get('07. latest trading day', ''),
                'previous_close': float(quote.get('08. previous close', 0)),
                'open': float(quote.get('02. open', 0)),
                'high': float(quote.get('03. high', 0)),
                'low': float(quote.get('04. low', 0))
            }, None
        except Exception as e:
            return None, str(e)
    
    def monte_carlo_simulation(self, days=252, simulations=1000):
        """Run Monte Carlo simulation for future price predictions"""
        if self.returns is None or len(self.returns) < 2:
            return None, "Insufficient data for Monte Carlo simulation"
        
        try:
            last_price = self.data['adjusted_close'].iloc[-1]
            mu = self.returns.mean()
            sigma = self.returns.std()
            
            simulated_paths = np.zeros((simulations, days))
            
            for i in range(simulations):
                prices = [last_price]
                for _ in range(days - 1):
                    price = prices[-1] * np.exp(np.random.normal(mu, sigma))
                    prices.append(price)
                simulated_paths[i] = prices
            
            percentiles = {
                'p5': np.percentile(simulated_paths, 5, axis=0),
                'p25': np.percentile(simulated_paths, 25, axis=0),
                'p50': np.percentile(simulated_paths, 50, axis=0),
                'p75': np.percentile(simulated_paths, 75, axis=0),
                'p95': np.percentile(simulated_paths, 95, axis=0),
            }
            
            return {
                'paths': simulated_paths,
                'percentiles': percentiles,
                'final_prices': simulated_paths[:, -1],
                'expected_final_price': np.mean(simulated_paths[:, -1]),
                'days': days,
                'mu': mu,
                'sigma': sigma
            }, None
        except Exception as e:
            return None, str(e)
    
    def black_scholes(self, S, K, T, r, sigma, option_type='call'):
        """Calculate Black-Scholes option price and Greeks"""
        try:
            d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            
            if option_type == 'call':
                price = S * stats.norm.cdf(d1) - K * np.exp(-r * T) * stats.norm.cdf(d2)
                delta = stats.norm.cdf(d1)
            else:
                price = K * np.exp(-r * T) * stats.norm.cdf(-d2) - S * stats.norm.cdf(-d1)
                delta = -stats.norm.cdf(-d1)
            
            gamma = stats.norm.pdf(d1) / (S * sigma * np.sqrt(T))
            vega = S * stats.norm.pdf(d1) * np.sqrt(T) / 100
            theta_call = -(S * stats.norm.pdf(d1) * sigma) / (2 * np.sqrt(T)) - r * K * np.exp(-r * T) * stats.norm.cdf(d2)
            theta_put = -(S * stats.norm.pdf(d1) * sigma) / (2 * np.sqrt(T)) + r * K * np.exp(-r * T) * stats.norm.cdf(-d2)
            theta = theta_call / 365 if option_type == 'call' else theta_put / 365
            
            rho_call = K * T * np.exp(-r * T) * stats.norm.cdf(d2) / 100
            rho_put = -K * T * np.exp(-r * T) * stats.norm.cdf(-d2) / 100
            rho = rho_call if option_type == 'call' else rho_put
            
            return {
                'price': price,
                'delta': delta,
                'gamma': gamma,
                'vega': vega,
                'theta': theta,
                'rho': rho,
                'd1': d1,
                'd2': d2
            }, None
        except Exception as e:
            return None, str(e)
    
    def arima_forecast(self, order=(5, 1, 0), days=30):
        """ARIMA time series forecasting"""
        if self.data is None or len(self.data) < 50:
            return None, "Insufficient data for ARIMA forecasting"
        
        try:
            prices = self.data['adjusted_close']
            
            model = ARIMA(prices, order=order)
            fitted_model = model.fit()
            
            forecast = fitted_model.forecast(steps=days)
            conf_int = fitted_model.get_forecast(steps=days).conf_int()
            
            return {
                'forecast': forecast.values,
                'lower_bound': conf_int.iloc[:, 0].values,
                'upper_bound': conf_int.iloc[:, 1].values,
                'aic': fitted_model.aic,
                'bic': fitted_model.bic,
                'days': days
            }, None
        except Exception as e:
            return None, str(e)
    
    def garch_volatility(self, p=1, q=1):
        """GARCH volatility modeling"""
        if self.returns is None or len(self.returns) < 100:
            return None, "Insufficient data for GARCH modeling"
        
        try:
            returns_percent = self.returns * 100
            
            model = arch_model(returns_percent, vol='GARCH', p=p, q=q)
            fitted_model = model.fit(disp='off')
            
            forecast = fitted_model.forecast(horizon=30)
            volatility_forecast = np.sqrt(forecast.variance.values[-1, :])
            
            return {
                'current_volatility': fitted_model.conditional_volatility.iloc[-1],
                'volatility_forecast': volatility_forecast,
                'aic': fitted_model.aic,
                'bic': fitted_model.bic,
                'params': fitted_model.params.to_dict()
            }, None
        except Exception as e:
            return None, str(e)
    
    def calculate_metrics(self, benchmark_symbol='SPY', risk_free_rate=0.04):
        """Calculate risk metrics: Sharpe, Beta, Alpha, correlation"""
        if self.returns is None or len(self.returns) < 30:
            return None, "Insufficient data for metric calculation"
        
        try:
            benchmark = StockAnalyzer(benchmark_symbol)
            success, _ = benchmark.fetch_data_yfinance(period='1y')
            
            if not success or benchmark.returns is None:
                return None, "Unable to fetch benchmark data"
            
            aligned_returns = pd.concat([self.returns, benchmark.returns], axis=1, join='inner')
            aligned_returns.columns = ['stock', 'benchmark']
            
            stock_returns = aligned_returns['stock']
            benchmark_returns = aligned_returns['benchmark']
            
            sharpe_ratio = (stock_returns.mean() - risk_free_rate/252) / stock_returns.std() * np.sqrt(252)
            
            covariance = stock_returns.cov(benchmark_returns)
            benchmark_variance = benchmark_returns.var()
            beta = covariance / benchmark_variance
            
            alpha = (stock_returns.mean() - risk_free_rate/252) - beta * (benchmark_returns.mean() - risk_free_rate/252)
            alpha_annualized = alpha * 252
            
            correlation = stock_returns.corr(benchmark_returns)
            
            volatility_annualized = stock_returns.std() * np.sqrt(252)
            
            downside_returns = stock_returns[stock_returns < 0]
            sortino_ratio = (stock_returns.mean() - risk_free_rate/252) / downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
            
            return {
                'sharpe_ratio': sharpe_ratio,
                'beta': beta,
                'alpha': alpha_annualized,
                'correlation': correlation,
                'volatility': volatility_annualized,
                'sortino_ratio': sortino_ratio,
                'mean_return': stock_returns.mean() * 252,
                'std_return': stock_returns.std() * np.sqrt(252)
            }, None
        except Exception as e:
            return None, str(e)
    
    def pca_analysis(self, stock_symbols):
        """Principal Component Analysis on multiple stocks"""
        try:
            returns_df = pd.DataFrame()
            
            for symbol in stock_symbols:
                analyzer = StockAnalyzer(symbol)
                success, _ = analyzer.fetch_data_yfinance(period='1y')
                if success and analyzer.returns is not None:
                    returns_df[symbol] = analyzer.returns
            
            if returns_df.empty or len(returns_df.columns) < 2:
                return None, "Need at least 2 valid stocks for PCA"
            
            returns_df = returns_df.dropna()
            
            pca = PCA()
            pca.fit(returns_df)
            
            return {
                'explained_variance_ratio': pca.explained_variance_ratio_,
                'components': pca.components_,
                'n_components': pca.n_components_,
                'feature_names': returns_df.columns.tolist(),
                'cumulative_variance': np.cumsum(pca.explained_variance_ratio_)
            }, None
        except Exception as e:
            return None, str(e)
    
    def statistical_summary(self):
        """Comprehensive statistical summary"""
        if self.returns is None or len(self.returns) < 2:
            return None, "Insufficient data"
        
        try:
            return {
                'mean': self.returns.mean(),
                'std': self.returns.std(),
                'min': self.returns.min(),
                'max': self.returns.max(),
                'skewness': stats.skew(self.returns),
                'kurtosis': stats.kurtosis(self.returns),
                'median': self.returns.median(),
                'var': self.returns.var(),
                'percentile_25': self.returns.quantile(0.25),
                'percentile_75': self.returns.quantile(0.75),
                'count': len(self.returns)
            }, None
        except Exception as e:
            return None, str(e)
