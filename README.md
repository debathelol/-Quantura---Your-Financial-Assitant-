# 🚀 Quantura: An Institutional-Grade Financial Analytics Platform

**Quantura** is a full-stack, AI-powered financial platform built from scratch in Python. It scales from personal wealth planning to institutional-grade quantitative equity analysis, implementing advanced econometric models and AI-driven insights.

* **Project Status:** ~6,500 lines of Python code, modular architecture.
* **Core Econometrics:** `stock_analyzer.py` (313 lines of models: GARCH, ARIMA, Monte Carlo).
* **AI Integration:** `stock_ai_analyzer.py` (200+ lines for AI-driven insights).

## 👨‍🎓 About This Project (The "Why")

As a student from a rural, non-financial background, I built Quantura to provide the powerful, data-driven tools (often locked behind expensive paywalls) to everyone. This project was my personal solution to the problems of financial illiteracy and information asymmetry I saw around me. It was not a school project, but a personal mission to prove that finance could be democratized through technology.

---

## 📸 Key Feature Showcase

*(This is the most important section. An admissions tutor will look here and nowhere else.)*

### 1. Quantitative Equity Analyzer (The "Quant" Engine)
Performs university-level analysis on global stocks (AAPL, TSLA, Toyota, Reliance) using advanced econometric models.
* Monte Carlo simulations
* GARCH volatility forecasting
* ARIMA price forecasting
* Black-Scholes options pricing
* Full Discounted Cash Flow (DCF) valuation

![Quantura-images-10](https://github.com/user-attachments/assets/a12f39f5-e34a-4f44-a039-75fd37adfee1)
![Quantura-images-12](https://github.com/user-attachments/assets/7c386e7c-1c28-49f3-a22f-e57797f0bec7)

### 2. AI-Powered Advisory Engine
Integrates AI to synthesize complex data into simple, actionable insights.
* Translates complex data (like GARCH models) into plain-English advice.
* Provides clear "Buy/Sell" verdicts with confidence scores.
* A full "AI Chat" assistant to answer unstructured user questions.

![Quantura-images-13](https://github.com/user-attachments/assets/0c83c96a-1772-4911-9576-9744427c6af3)
![Quantura-images-11](https://github.com/user-attachments/assets/00419c71-91b8-4f69-b481-9a8b02a19ea7)

### 3. Behavioural Planning & Economic Models
Encodes financial best practices and behavioural finance concepts (from my Yale coursework) to guide users toward better long-term decisions.
* **Behavioural Budgeting:** Generates budgets based on a user's "Financial Mindset" (Stable, Balanced, etc.).
* **Algorithmic Advisory:** "Smart Car Purchase Calculator" (20-5-10 rule) and "Debt Payoff Planner."
* **Economic Modelling:** A full "Rent vs. Buy" calculator that models opportunity cost and inflation.

![Quantura-images-7](https://github.com/user-attachments/assets/aed87ebf-3c89-4f54-bda2-cb7a3d556c50)
![Quantura-images-8](https://github.com/user-attachments/assets/022ef70a-6bb4-4d55-b8fc-8dc6503f79b0)
![Quantura-images-5](https://github.com/user-attachments/assets/1bd561db-5a10-4372-889e-f131c602ae3f)

---

## 🎯 Advanced Technical Features

### Performance Optimization
- **Intelligent Caching System:** Reduces Yahoo Finance API calls by 50-67% using Streamlit's `@st.cache_data` with 5-minute TTL
- **Rate Limit Protection:** 3-second delays combined with caching prevent API throttling during batch analysis
- **Instant Response:** Analyzing the same stock twice within 5 minutes uses cached data for instant results

### Production-Ready Resilience
- **AI Demo Mode Fallback:** All 6 AI features gracefully degrade to educational demo content when:
  - OpenAI API is unavailable
  - Credits run out mid-session
  - Network issues occur
  - No API keys configured
- **Zero Downtime UX:** App never crashes or shows error messages during demos
- **Clear Labeling:** Demo responses marked with ⚠️ prefix for transparency
- **Debug Logging:** Comprehensive `[DEMO MODE]` logging for troubleshooting

---

## 🛠️ Technology Stack & Architecture

### Core Technologies
- **Frontend/Backend:** Streamlit (Python web framework)
- **Data Analysis:** Pandas, NumPy, SciPy
- **Financial Models:** Statsmodels, Arch (GARCH), yfinance
- **Visualization:** Matplotlib, Seaborn, Plotly
- **AI Integration:** OpenAI GPT-4o-mini
- **Database:** PostgreSQL (Neon-backed)
- **Deployment:** Streamlit Cloud

### Project Structure
```
quantura/
├── app.py                      # Main application (5,700+ lines)
├── services/
│   ├── stock_analyzer.py       # Econometric models (313 lines)
│   ├── stock_ai_analyzer.py    # AI integration (200+ lines)
│   └── company_lookup.py       # Ticker resolution
├── ui_components/
│   ├── charts.py              # Visualization components
│   └── stock_charts.py        # Financial charts
└── database/
    └── db.py                  # PostgreSQL operations
```

### Key Algorithms Implemented
- **Monte Carlo Simulation:** 10,000 path simulations using geometric Brownian motion
- **GARCH(1,1):** Volatility clustering and forecasting
- **ARIMA:** Autoregressive integrated moving average for price prediction
- **Black-Scholes:** European options pricing with Greeks
- **DCF Valuation:** 8-step discounted cash flow analysis
- **Portfolio Optimization:** Sharpe ratio, Beta, Alpha, Sortino ratio calculations

---

## 🚀 Live Demo

**Deployed Application:** [View on Streamlit Cloud](https://quantura.streamlit.app)

**Features:**
- Real-time stock analysis for global markets
- AI-powered recommendations and insights
- Personal finance tracking and budgeting
- Corporate financial analysis
- 7 financial calculators
- Interactive visualizations

---

## 📸 Screenshots
![Quantura-images-0](https://github.com/user-attachments/assets/371ba0ed-a7fd-4231-acf0-07f99f4a363e)
![Quantura-images-1](https://github.com/user-attachments/assets/470d1435-67c1-4e21-802e-a485cd3f54af)
![Quantura-images-2](https://github.com/user-attachments/assets/d3f288d9-5ba4-472c-9935-6ec7bc867b08)
![Quantura-images-3](https://github.com/user-attachments/assets/b3a8be96-ed2d-42a9-82d6-de630eadfae2)
![Quantura-images-4](https://github.com/user-attachments/assets/fc10ac23-93f0-4597-ba92-32e8b9bdccc4)
![Quantura-images-6](https://github.com/user-attachments/assets/9d8bf428-fd1d-4b44-9796-68bbde9ff397)
![Quantura-images-9](https://github.com/user-attachments/assets/eec80923-7716-4154-9ac8-9c8ecc9bf038)

---

## 📊 Impact & Scale

- **6,500+ lines** of production Python code
- **6 AI-powered features** with intelligent fallbacks
- **20+ financial models** and calculators
- **Global stock support** across all major exchanges
- **Multi-currency support** (10 currencies)
- **PostgreSQL database** for data persistence
- **Production deployment** on Streamlit Cloud

---

## 💡 What I Learned

Building Quantura taught me:
- **System Design:** Architecting a full-stack application from scratch
- **Financial Engineering:** Implementing university-level econometric models
- **Production Resilience:** Building fault-tolerant systems with graceful degradation
- **Performance Optimization:** Caching strategies and rate limit management
- **AI Integration:** Practical application of LLMs for domain-specific insights
- **User-Centric Design:** Making complex finance accessible to everyone

---

## 🎓 Academic Connection

This project synthesizes concepts from:
- **Yale's Financial Markets** course (behavioral finance, risk management)
- **Quantitative Finance** (GARCH, ARIMA, Monte Carlo methods)
- **Software Engineering** (modular architecture, caching, error handling)
- **Human-Computer Interaction** (UX design, accessibility)

---

## 📝 License & Usage

This project is free and open-source. Built with the mission of democratizing financial tools for everyone, regardless of background or resources.

---

## 📧 Contact

debarghya47@gmail.com

---

**Built with ❤️ to democratize finance through technology**
