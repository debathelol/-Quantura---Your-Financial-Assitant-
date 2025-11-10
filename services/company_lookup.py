import os
import requests

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


def lookup_company_ticker(company_name: str) -> tuple[str, str]:
    """
    Convert a company name to its stock ticker symbol.
    
    Args:
        company_name: Company name (e.g., "Apple", "Tesla", "Toyota")
    
    Returns:
        tuple: (ticker_symbol, status_message)
        - ticker_symbol: The stock ticker (e.g., "AAPL", "7203.T")
        - status_message: Success/error message for user
    """
    if not company_name or not company_name.strip():
        return "", "Please enter a company name"
    
    search_term = company_name.strip().lower()
    
    # First check popular companies database
    if search_term in POPULAR_COMPANIES:
        ticker = POPULAR_COMPANIES[search_term]
        return ticker, f"✓ Found {company_name.title()} → {ticker}"
    
    # Try Alpha Vantage API if available
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if api_key:
        try:
            url = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={company_name}&apikey={api_key}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                matches = data.get('bestMatches', [])
                
                if matches:
                    # Get the best match (first result)
                    best_match = matches[0]
                    ticker = best_match.get('1. symbol', '')
                    match_name = best_match.get('2. name', '')
                    
                    if ticker:
                        return ticker, f"✓ Found {match_name} → {ticker}"
        except Exception as e:
            pass
    
    # If not found, try as-is (user might know the ticker)
    if len(search_term) <= 10 and search_term.replace('.', '').replace('-', '').isalnum():
        ticker = company_name.upper()
        return ticker, f"Using ticker: {ticker}"
    
    # Not found
    return "", f"❌ Company '{company_name}' not found. Try: Apple, Tesla, Microsoft, Toyota, Samsung, etc."


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
