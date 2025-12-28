import os
import requests
from openai import OpenAI

def init_openai_client():
    """Initialize OpenAI client - works on both Replit and with standard OpenAI API keys"""
    try:
        # Check for API key in both Replit and standard formats
        api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print(f"[AI Lookup] No API key found in environment variables")
            return None

        base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")

        if base_url:
            # Replit integration
            client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            # Standard OpenAI or Streamlit Cloud
            client = OpenAI(api_key=api_key)

        return client
    except Exception as e:
        print(f"[AI Lookup] Error initializing OpenAI client: {str(e)}")
        return None

POPULAR_COMPANIES = {
    # US Tech Giants
    "apple": "AAPL",
    "microsoft": "MSFT",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "amazon": "AMZN",
    "meta": "META",
    "facebook": "META",
    "tesla": "TSLA",
    "nvidia": "NVDA",
    "netflix": "NFLX",
    
    # US Finance & Others
    "berkshire": "BRK-B",
    "berkshire hathaway": "BRK-B",
    "jpmorgan": "JPM",
    "jp morgan": "JPM",
    "visa": "V",
    "walmart": "WMT",
    "disney": "DIS",
    "coca cola": "KO",
    "coca-cola": "KO",
    "coke": "KO",
    "pepsi": "PEP",
    "mcdonald": "MCD",
    "mcdonalds": "MCD",
    "nike": "NKE",
    "intel": "INTC",
    "amd": "AMD",
    "cisco": "CSCO",
    "oracle": "ORCL",
    "ibm": "IBM",
    "salesforce": "CRM",
    "adobe": "ADBE",
    "paypal": "PYPL",
    "uber": "UBER",
    "airbnb": "ABNB",
    "spotify": "SPOT",
    "zoom": "ZM",
    
    # UK Companies
    "bp": "BP.L",
    "shell": "SHEL.L",
    "hsbc": "HSBA.L",
    "unilever": "ULVR.L",
    "astrazeneca": "AZN.L",
    "diageo": "DGE.L",
    "vodafone": "VOD.L",
    "barclays": "BARC.L",
    "tesco": "TSCO.L",
    "rolls royce": "RR.L",
    "rolls-royce": "RR.L",
    
    # European Companies
    "volkswagen": "VOW3.DE",
    "bmw": "BMW.DE",
    "mercedes": "MBG.DE",
    "mercedes benz": "MBG.DE",
    "mercedes-benz": "MBG.DE",
    "siemens": "SIE.DE",
    "sap": "SAP.DE",
    "adidas": "ADS.DE",
    "lvmh": "MC.PA",
    "hermes": "RMS.PA",
    "l'oreal": "OR.PA",
    "loreal": "OR.PA",
    "total": "TTE.PA",
    "totalenergies": "TTE.PA",
    "airbus": "AIR.PA",
    "danone": "BN.PA",
    "nestle": "NESN.SW",
    "novartis": "NOVN.SW",
    "roche": "ROG.SW",
    
    # Japanese Companies
    "toyota": "7203.T",
    "sony": "6758.T",
    "honda": "7267.T",
    "nissan": "7201.T",
    "panasonic": "6752.T",
    "mitsubishi": "8058.T",
    "nintendo": "7974.T",
    "softbank": "9984.T",
    "canon": "7751.T",
    "mazda": "7261.T",
    
    # Chinese/Hong Kong
    "tencent": "0700.HK",
    "alibaba": "9988.HK",
    "xiaomi": "1810.HK",
    "baidu": "BIDU",
    "jd.com": "JD",
    "jd": "JD",
    "nio": "NIO",
    "byd": "1211.HK",
    
    # Indian Companies
    "reliance": "RELIANCE.NS",
    "reliance industries": "RELIANCE.NS",
    "tcs": "TCS.NS",
    "tata consultancy": "TCS.NS",
    "infosys": "INFY.NS",
    "hdfc": "HDFCBANK.NS",
    "hdfc bank": "HDFCBANK.NS",
    "wipro": "WIPRO.NS",
    "icici": "ICICIBANK.NS",
    "icici bank": "ICICIBANK.NS",
    "bharti airtel": "BHARTIARTL.NS",
    "airtel": "BHARTIARTL.NS",
    "mahindra": "M&M.NS",
    
    # Canadian Companies
    "shopify": "SHOP.TO",
    "royal bank": "RY.TO",
    "rbc": "RY.TO",
    "td bank": "TD.TO",
    "scotiabank": "BNS.TO",
    "enbridge": "ENB.TO",
    
    # Australian Companies
    "bhp": "BHP.AX",
    "commonwealth bank": "CBA.AX",
    "cba": "CBA.AX",
    "westpac": "WBC.AX",
    "nab": "NAB.AX",
    "anz": "ANZ.AX",
    
    # South Korean
    "samsung": "005930.KS",
    "hyundai": "005380.KS",
    "lg": "066570.KS",
    "kia": "000270.KS",
    
    # Brazilian
    "petrobras": "PETR4.SA",
    "vale": "VALE3.SA",
    "itau": "ITUB4.SA",
    "bradesco": "BBDC4.SA",
}


def get_ticker_from_ai(company_name: str) -> tuple[str, str]:
    """
    Use AI to convert company name to ticker symbol.
    
    Args:
        company_name: Company name
    
    Returns:
        tuple: (ticker_symbol, company_full_name) or ("", "") if not found
    """
    try:
        client = init_openai_client()
        if not client:
            print(f"[AI Lookup] OpenAI client initialization failed")
            return "", ""
        
        print(f"[AI Lookup] Looking up company: {company_name}")
        
        prompt = f"""You are a financial expert. Convert the company name to its stock ticker symbol.

Company name: "{company_name}"

Instructions:
1. Identify the correct stock ticker symbol (e.g., AAPL for Apple, TSLA for Tesla)
2. For international stocks, include the exchange suffix:
   - .L for London Stock Exchange (e.g., BP.L)
   - .T for Tokyo Stock Exchange (e.g., 7203.T for Toyota)
   - .HK for Hong Kong (e.g., 0700.HK for Tencent)
   - .NS for India NSE (e.g., RELIANCE.NS)
   - .KS for Korea (e.g., 005930.KS for Samsung)
   - .DE for Frankfurt (e.g., VOW3.DE for Volkswagen)
   - .PA for Paris (e.g., MC.PA for LVMH)
   - .AX for Australia, .TO for Toronto, .SA for Brazil, etc.
3. Return the ticker symbol and the full official company name
4. If you're unsure or the company doesn't exist, return "UNKNOWN"

Respond in this exact format:
TICKER: <ticker_symbol>
NAME: <full company name>

Examples:
- "Apple" → TICKER: AAPL, NAME: Apple Inc.
- "Toyota" → TICKER: 7203.T, NAME: Toyota Motor Corporation
- "BP" → TICKER: BP.L, NAME: BP plc
- "Samsung Electronics" → TICKER: 005930.KS, NAME: Samsung Electronics Co., Ltd.
"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a financial market expert who knows stock ticker symbols for companies worldwide."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=150
        )
        
        result = response.choices[0].message.content.strip()
        print(f"[AI Lookup] AI response: {result}")
        
        # Parse the response
        lines = result.split('\n')
        ticker = ""
        full_name = ""
        
        for line in lines:
            if line.startswith("TICKER:"):
                ticker = line.replace("TICKER:", "").strip()
            elif line.startswith("NAME:"):
                full_name = line.replace("NAME:", "").strip()
        
        # Check if valid
        if ticker and ticker.upper() != "UNKNOWN":
            print(f"[AI Lookup] Success: {company_name} → {ticker} ({full_name})")
            return ticker.upper(), full_name
        
        print(f"[AI Lookup] Failed: AI returned UNKNOWN or invalid response")
        return "", ""
        
    except Exception as e:
        print(f"[AI Lookup] Exception: {str(e)}")
        return "", ""


def lookup_company_ticker(company_name: str) -> tuple[str, str]:
    """
    Convert a company name to its stock ticker symbol using AI.
    
    Args:
        company_name: Company name (e.g., "Apple", "Tesla", "Toyota", "Samsung")
    
    Returns:
        tuple: (ticker_symbol, status_message)
        - ticker_symbol: The stock ticker (e.g., "AAPL", "7203.T")
        - status_message: Success/error message for user
    """
    if not company_name or not company_name.strip():
        return "", "Please enter a company name"
    
    search_term = company_name.strip().lower()
    
    # First check popular companies database (fast cache)
    if search_term in POPULAR_COMPANIES:
        ticker = POPULAR_COMPANIES[search_term]
        return ticker, f"✓ Found {company_name.title()} → {ticker}"
    
    # Use AI to find the ticker (supports unlimited companies!)
    ticker, full_name = get_ticker_from_ai(company_name)
    if ticker:
        return ticker, f"✓ Found {full_name} → {ticker}"
    
    # If AI fails, only accept as ticker if it looks like a real ticker (all caps, short, with optional exchange suffix)
    if len(search_term) <= 6 and search_term.replace('.', '').replace('-', '').isalpha() and company_name.isupper():
        # User entered something like "AAPL" or "BP.L" - use as-is
        ticker = company_name.upper()
        return ticker, f"Using ticker: {ticker}"
    
    # Not found
    return "", f"❌ Company '{company_name}' not recognized. AI couldn't find this company. Please check the spelling or try the exact stock ticker symbol."


def get_company_suggestions(partial_name: str, limit: int = 5) -> list[tuple[str, str]]:
    """
    Get company name suggestions based on partial input.
    
    Args:
        partial_name: Partial company name
        limit: Maximum number of suggestions
    
    Returns:
        list of (company_name, ticker) tuples
    """
    if not partial_name:
        return []
    
    search_term = partial_name.lower()
    suggestions = []
    
    for company, ticker in POPULAR_COMPANIES.items():
        if search_term in company:
            suggestions.append((company.title(), ticker))
            if len(suggestions) >= limit:
                break
    
    return suggestions
