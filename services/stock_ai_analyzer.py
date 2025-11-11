import os
import json
from openai import OpenAI

# Demo mode data templates - used when AI API is unavailable
DEMO_STOCK_ANALYSIS = {
    "rating": "Hold",
    "confidence": 75,
    "analysis": "⚠️ **Demo Mode** - Based on the current metrics, this stock shows moderate volatility with reasonable risk-adjusted returns. The Sharpe ratio indicates acceptable performance relative to risk.",
    "risk_level": "Medium",
    "key_insights": [
        "Stock demonstrates typical market volatility patterns",
        "Risk-adjusted returns are in line with market expectations",
        "Consider portfolio diversification for optimal risk management",
        "Monitor key support and resistance levels"
    ],
    "recommendation": "⚠️ **Demo Mode** - Maintain current position and monitor market conditions. Consider adding protective stops and regular portfolio rebalancing."
}

DEMO_PORTFOLIO_INSIGHTS = {
    "diversification_score": 68,
    "risk_assessment": "Moderate - Portfolio shows reasonable diversification",
    "recommendations": [
        "Consider adding international exposure for better geographic diversification",
        "Balance growth stocks with some defensive positions",
        "Review correlation between holdings to reduce overlap",
        "Maintain emergency cash reserves outside of portfolio"
    ],
    "correlation_insight": "⚠️ **Demo Mode** - Your stocks show moderate correlation, suggesting some overlap in market exposure. Consider adding uncorrelated assets.",
    "rebalancing_suggestion": "⚠️ **Demo Mode** - Consider a balanced allocation based on your risk tolerance and investment goals."
}

DEMO_GRAPH_EXPLANATIONS = {
    "monte_carlo": "⚠️ **Demo Mode** - This simulation shows a range of possible future prices based on historical patterns. The fan-shaped pattern indicates increasing uncertainty over time, which is normal. The center line represents the most likely path, while the outer edges show best and worst-case scenarios. Remember, these are projections, not guarantees.",
    
    "arima_forecast": "⚠️ **Demo Mode** - This forecast predicts near-term price movements using historical patterns. The upward/downward trend suggests the model's best estimate, but real prices can differ due to unexpected events. Use this as one input among many for decision-making, not as a crystal ball.",
    
    "garch_volatility": "⚠️ **Demo Mode** - This chart shows how much the stock price might swing in the future. Rising lines mean more uncertainty ahead, while falling lines suggest calmer trading. High volatility isn't always bad—it can create opportunities—but it does mean bigger potential swings in your account value.",
    
    "correlation_matrix": "⚠️ **Demo Mode** - This heatmap shows which stocks tend to move together. Dark colors mean stocks move in sync (high correlation), while lighter colors mean they move independently. For a well-diversified portfolio, you want more variety in colors, not all dark.",
    
    "risk_return_scatter": "⚠️ **Demo Mode** - This plot compares risk versus reward for each stock. Stocks in the upper-left offer better returns for less risk (ideal), while lower-right stocks have high risk with lower returns (less ideal). The Sharpe ratio helps identify the best risk-adjusted performers.",
    
    "portfolio_pca": "⚠️ **Demo Mode** - This analysis reveals hidden patterns in how your stocks move together. Clustering indicates similar behavior, while spread-out points suggest good diversification. If all your stocks cluster tightly, you're essentially making one big bet instead of multiple independent ones."
}

def get_demo_graph_explanation(graph_type):
    """Get demo explanation for a specific graph type"""
    return DEMO_GRAPH_EXPLANATIONS.get(graph_type, "⚠️ **Demo Mode** - AI explanation is currently unavailable. This chart provides valuable insights into your financial data. Please try again later for a detailed AI-powered explanation.")

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

        # Using gpt-4o-mini - the latest efficient OpenAI model
        response = client.chat.completions.create(
            model="gpt-4o-mini",
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
        # Fallback to demo mode on parsing error
        print(f"[DEMO MODE] JSON parse error, using demo data: {str(e)}")
        return DEMO_STOCK_ANALYSIS, None
    except Exception as e:
        # Fallback to demo mode on any API error (rate limit, auth, network, etc.)
        print(f"[DEMO MODE] API error, using demo data: {str(e)}")
        return DEMO_STOCK_ANALYSIS, None

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

        # Using gpt-4o-mini - the latest efficient OpenAI model
        response = client.chat.completions.create(
            model="gpt-4o-mini",
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
        # Fallback to demo mode on any error
        print(f"[DEMO MODE] Portfolio analysis error, using demo data: {str(e)}")
        return DEMO_PORTFOLIO_INSIGHTS, None
