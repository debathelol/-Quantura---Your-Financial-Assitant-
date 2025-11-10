import os
import json
from openai import OpenAI

def _get_openai_client():
    """Lazy initialization of OpenAI client - works on both Replit and Streamlit Cloud"""
    try:
        # Check for API key in both Replit and Streamlit Cloud formats
        api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return None
        
        base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
        
        if base_url:
            # Replit integration
            return OpenAI(api_key=api_key, base_url=base_url)
        else:
            # Streamlit Cloud or standard OpenAI
            return OpenAI(api_key=api_key)
    except Exception as e:
        return None

def get_ai_stock_analysis(symbol, quote_data, metrics, monte_carlo_results, arima_results):
    """Get AI-powered stock analysis and recommendations"""
    try:
        client = _get_openai_client()
        if client is None:
            return None, "AI service not configured. Please set up OPENAI_API_KEY."
        
        context = f"""
You are a quantitative financial analyst. Analyze this stock data and provide insights.

Symbol: {symbol}
Current Price: ${quote_data.get('price', 0):.2f}
Daily Change: {quote_data.get('change_percent', '0%')}
Volume: {quote_data.get('volume', 0):,}

Risk Metrics:
- Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.3f}
- Beta: {metrics.get('beta', 0):.3f}
- Alpha (annualized): {metrics.get('alpha', 0):.3%}
- Volatility (annualized): {metrics.get('volatility', 0):.3%}
- Correlation with SPY: {metrics.get('correlation', 0):.3f}

Monte Carlo Simulation:
- Expected Price (1 year): ${monte_carlo_results.get('expected_final_price', 0):.2f}
- Current Mean Return: {monte_carlo_results.get('mu', 0):.4%}
- Volatility: {monte_carlo_results.get('sigma', 0):.4%}

ARIMA Forecast:
- 30-day forecast: ${arima_results['forecast'][-1]:.2f}
- AIC: {arima_results.get('aic', 0):.2f}

Provide a JSON response with:
1. "rating": "Strong Buy", "Buy", "Hold", "Sell", or "Strong Sell"
2. "confidence": 0-100 score
3. "analysis": 2-3 sentence summary of key findings
4. "risk_level": "Low", "Medium", or "High"
5. "key_insights": array of 3-4 bullet points
6. "recommendation": actionable advice
"""

        # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "You are an expert quantitative analyst. Provide analysis in valid JSON format."},
                {"role": "user", "content": context}
            ],
            max_completion_tokens=800
        )
        
        content = response.choices[0].message.content
        if not content or content.strip() == "":
            return None, "AI returned empty response. Please check your API key and quota."
        
        content = content.strip()
        
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        if not content:
            return None, "AI response was empty after parsing. Please check your API key."
        
        analysis = json.loads(content)
        
        return analysis, None
        
    except json.JSONDecodeError as e:
        return None, f"Failed to parse AI response: {str(e)}. Check your OpenAI API key in Settings."
    except Exception as e:
        return None, f"AI analysis error: {str(e)}. Verify your OPENAI_API_KEY is set correctly."

def get_ai_portfolio_insights(stocks_data):
    """Get AI insights on portfolio diversification and risk"""
    try:
        client = _get_openai_client()
        if client is None:
            return None, "AI service not configured. Please set up OPENAI_API_KEY."
        
        stocks_summary = []
        for stock in stocks_data:
            stocks_summary.append(f"{stock['symbol']}: Beta={stock.get('beta', 0):.2f}, Sharpe={stock.get('sharpe', 0):.2f}")
        
        context = f"""
Analyze this portfolio composition and provide insights:

Stocks in Portfolio:
{chr(10).join(stocks_summary)}

Provide JSON response with:
1. "diversification_score": 0-100
2. "risk_assessment": overall portfolio risk level
3. "recommendations": array of 3-4 specific actions to improve the portfolio
4. "correlation_insight": how correlated these stocks are
5. "rebalancing_suggestion": specific allocation percentages
"""

        # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "You are a portfolio management expert. Provide analysis in valid JSON format."},
                {"role": "user", "content": context}
            ],
            max_completion_tokens=600
        )
        
        content = response.choices[0].message.content.strip()
        
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        insights = json.loads(content)
        
        return insights, None
        
    except Exception as e:
        return None, f"AI portfolio analysis error: {str(e)}"
