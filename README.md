# Quantura

**Quantitative finance analytics platform with a Maximum Entropy Inverse Reinforcement Learning (MaxEnt IRL) engine for inferring latent reward functions from observed financial behaviour.**

![Python](https://img.shields.io/badge/Python-100%25-blue)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B)
![License: MIT](https://img.shields.io/badge/License-MIT-green)

---

## Overview

Quantura consists of two components:

1. **Analytics platform** — a Streamlit application for equity analysis, portfolio management, and personal finance, built on standard quantitative methods: Monte Carlo simulation, GARCH volatility modelling, ARIMA forecasting, and Black-Scholes options pricing.
2. **Humbler (research module)** — a MaxEnt IRL framework that, given observed decision trajectories, recovers the latent reward function under which that behaviour is optimal — rather than scoring behaviour against an externally imposed objective and labelling deviations as error.

---

## Research: Humbler — MaxEnt IRL for Behavioural Finance

Classical decision models (Expected Utility, Prospect Theory) fix a reward function in advance and classify deviations from its predictions as irrationality. Humbler inverts the problem: it treats observed behaviour as approximately optimal and uses Maximum Entropy Inverse Reinforcement Learning (Ziebart et al., 2008) to infer the constraint set and feature weights that rationalise it.

**📄 [Read the full paper →](https://drive.google.com/file/d/1y13nxiGvTUIlEy2Ptgbmt6tECafYyjIl/view?usp=sharing)**

### Recovered latent parameters

| Parameter | Interpretation |
|-----------|----------------|
| `τ` | Liquidity floor — minimum viable capital threshold below which the agent's feasible action set collapses |
| `w_soc` | Weight on social/network signal relative to direct financial signal |
| `d_dig` | Reputational-cost state — where signalling costs dominate immediate utility |
| `λ` | State-dependent loss-aversion coefficient |

### Benchmarks

| Metric | Value |
|--------|-------|
| Prediction accuracy | **84.6%** |
| vs. Expected Utility baseline | +41.4 pp |
| vs. Prospect Theory baseline | +22.9 pp |
| False "irrationality" classification rate | 15.4% (down from 56.8%) |
| Parameter recovery MAE | 0.04 |

Evaluation performed on synthetic agent populations with known ground-truth reward parameters; see the paper for the full protocol.

---

## Platform Features

**📈 Stock Analysis Engine**
- Natural-language company lookup — no tickers required
- Monte Carlo simulation for price-path forecasting
- ARIMA forecasting and GARCH volatility modelling
- Black-Scholes options pricing
- Risk metrics: Sharpe ratio, Beta, Alpha, VaR

**💼 Portfolio Management**
- Multi-asset portfolio analysis
- Efficient-frontier visualisation
- Risk-adjusted return calculation
- AI-generated portfolio insights

**💰 Personal Finance**
- Transaction categorisation and budget tracking
- Spending-pattern analysis
- PDF report generation

**🤖 AI Assistant**
- Natural-language financial queries via LLM API

---

## Screenshots

<!-- Paste your existing screenshot attachment links here -->

---

## Tech Stack

| Layer | Stack |
|-------|-------|
| **Frontend** | Streamlit |
| **Analysis** | Pandas, NumPy, SciPy |
| **ML / Statistics** | scikit-learn, statsmodels, arch |
| **Visualisation** | Plotly, Matplotlib, Seaborn |
| **Market data** | yfinance |
| **AI** | OpenAI API |
| **IRL** | Custom MaxEnt IRL solver (~500 LOC) |

---

## Quick Start

```bash
# Clone
git clone https://github.com/debathelol/Quantura-Research.git
cd Quantura-Research

# Install
pip install -r requirements-github.txt

# Configure (create .streamlit/secrets.toml)
# OPENAI_API_KEY = "your-key"

# Run
streamlit run app.py
```

---

## Project Structure

```
Quantura-Research/
├── app.py                      # Main application
├── humbler/                    # IRL research implementation
│   ├── maxent_irl.py           # MaxEnt IRL solver
│   ├── features.py             # Constraint-aware feature engineering
│   └── agents.py               # Synthetic agent simulation
├── services/
│   ├── stock_analyzer.py       # Quantitative analysis
│   ├── stock_ai_analyzer.py    # AI-powered insights
│   └── company_lookup.py       # NLP company resolution
├── ui_components/
│   └── ...                     # Visualisation components
└── paper/
    └── humbler_paper.pdf       # Research paper
```

---

## References

- Ng & Russell (2000) — *Algorithms for Inverse Reinforcement Learning*
- Ziebart et al. (2008) — *Maximum Entropy Inverse Reinforcement Learning*
- Kahneman & Tversky (1979) — *Prospect Theory: An Analysis of Decision under Risk*
- Roy (1952) — *Safety First and the Holding of Assets*

---

## Roadmap

- [ ] Validation on real-world household-finance datasets
- [ ] Empirical calibration of latent-parameter priors
- [ ] Human-in-the-loop inference validation
- [ ] Cross-domain robustness testing

---

## Responsible Use

Inferring latent behavioural constraints from decision data carries dual-use risk: the same machinery that enables adaptive tools could be used to target users based on inferred vulnerability. Design safeguards include user-facing inference transparency, no external transmission of inferred constraint profiles, per-inference opt-out, and human-in-the-loop validation. See Section 7 of the paper for the full analysis.

---

## License

MIT — see [LICENSE](LICENSE).

---

## Contact

**Debarghya Pati**
📧 debarghyapati47@gmail.com
🔗 [github.com/debathelol](https://github.com/debathelol)
