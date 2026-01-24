# Quantura

**Financial analytics built on a simple premise: what if "irrational" behavior is actually optimal under constraints we refuse to see?**

[![Stars](https://img.shields.io/github/stars/debathelol/Quantura-Research?style=flat-square)](https://github.com/debathelol/Quantura-Research/stargazers)
[![Forks](https://img.shields.io/github/forks/debathelol/Quantura-Research?style=flat-square)](https://github.com/debathelol/Quantura-Research/network/members)
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)

---

## The Story

I built Quantura to help retail investors make better decisions. Monte Carlo simulations. GARCH volatility modelling. Black-Scholes options pricing. The algorithms worked beautifully.

Then I watched my uncle ignore every warning to buy a penny stock I had mathematically proven was a trap. He lost six months of wages.

For a year, I called this *irrationality*.

Then I read Mani et al. (2013)—researchers who showed that poverty itself drops cognitive performance by 14 IQ points. Not because poor people are less capable, but because scarcity consumes mental bandwidth. I realised: **I was the irrational one—for assuming my reward function was his.**

That insight became a research question. The research question became a paper.

---

## Research: When Algorithms Learn Humility

**📄 [Read the full paper →](https://drive.google.com/file/d/1y13nxiGvTUIlEy2Ptgbmt6tECafYyjIl/view?usp=sharing)**

I applied Maximum Entropy Inverse Reinforcement Learning to infer hidden reward functions behind decisions conventionally labelled "irrational." Instead of imposing external objectives and calling deviations errors, the framework—**Humbler**—recovers the constraints that make observed behaviour optimal.

### Key Results

| Metric | Value |
|--------|-------|
| Prediction Accuracy | **84.6%** |
| vs. Expected Utility | +41.4 pp |
| vs. Prospect Theory | +22.9 pp |
| False Irrationality Rate | 15.4% (down from 56.8%) |
| Parameter Recovery MAE | 0.04 |

### What the Algorithm Recovers

- **Survival threshold (τ)**: The minimum viable liquidity below which capabilities collapse
- **Social trust weight (w_soc)**: How much network advice matters versus financial signal
- **Dignity state (d_dig)**: Face preservation as a constraint—where reputational costs outweigh immediate utility
- **Scarcity-amplified loss aversion (λ)**: Why poverty makes high-variance bets feel like the only escape

### The Core Insight

> *"I am not trying to fix poor people. I am trying to fix the algorithms that call them broken."*

Cash hoarding despite inflation erosion. Expensive informal credit. Short-horizon planning. These aren't failures of rationality—they're optimal strategies under constraints invisible to standard models.

---

## The Platform

Quantura is also a working financial analytics application—the testing ground where I discovered the problem.

### Features

**📈 Stock Analysis Engine**
- AI-powered company lookup (natural language, no tickers needed)
- Monte Carlo simulations for price predictions
- ARIMA forecasting, GARCH volatility modelling
- Black-Scholes options pricing
- Risk metrics: Sharpe ratio, Beta, Alpha, VaR

**💼 Portfolio Management**
- Multi-asset portfolio analysis
- Efficient frontier visualisation
- Risk-adjusted returns calculation
- AI-powered portfolio insights

**💰 Personal Finance**
- Transaction categorisation
- Budget tracking
- Spending pattern analysis
- PDF report generation

**🤖 AI Assistant**
- Natural language financial queries
- Powered by Claude API

### Platform Preview

![Dashboard](https://github.com/user-attachments/assets/371ba0ed-a7fd-4231-acf0-07f99f4a363e)

![Stock Analysis](https://github.com/user-attachments/assets/470d1435-67c1-4e21-802e-a485cd3f54af)

![Portfolio Analytics](https://github.com/user-attachments/assets/d3f288d9-5ba4-472c-9935-6ec7bc867b08)

<details>
<summary>More screenshots</summary>

![Quantura-images-3](https://github.com/user-attachments/assets/b3a8be96-ed2d-42a9-82d6-de630eadfae2)
![Quantura-images-4](https://github.com/user-attachments/assets/fc10ac23-93f0-4597-ba92-32e8b9bdccc4)
![Quantura-images-5](https://github.com/user-attachments/assets/1bd561db-5a10-4372-889e-f131c602ae3f)
![Quantura-images-6](https://github.com/user-attachments/assets/9d8bf428-fd1d-4b44-9796-68bbde9ff397)
![Quantura-images-7](https://github.com/user-attachments/assets/aed87ebf-3c89-4f54-bda2-cb7a3d556c50)
![Quantura-images-8](https://github.com/user-attachments/assets/022ef70a-6bb4-4d55-b8fc-8dc6503f79b0)
![Quantura-images-9](https://github.com/user-attachments/assets/eec80923-7716-4154-9ac8-9c8ecc9bf038)
![Quantura-images-10](https://github.com/user-attachments/assets/a12f39f5-e34a-4f44-a039-75fd37adfee1)
![Quantura-images-11](https://github.com/user-attachments/assets/00419c71-91b8-4f69-b481-9a8b02a19ea7)
![Quantura-images-12](https://github.com/user-attachments/assets/7c386e7c-1c28-49f3-a22f-e57797f0bec7)
![Quantura-images-13](https://github.com/user-attachments/assets/0c83c96a-1772-4911-9576-9744427c6af3)

</details>

---

## Technology

| Layer | Stack |
|-------|-------|
| **Frontend** | Streamlit |
| **Analysis** | Pandas, NumPy, SciPy |
| **ML/Statistics** | scikit-learn, statsmodels, arch |
| **Visualisation** | Plotly, Matplotlib, Seaborn |
| **Financial Data** | yfinance |
| **AI** | OpenAI API |
| **IRL Implementation** | Custom MaxEnt IRL solver (~500 LOC) |

---

## Installation

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
│   ├── features.py             # Survival-aware feature engineering
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

## Intellectual Foundations

This work draws on:

- **Inverse Reinforcement Learning** — Ng & Russell (2000), Ziebart et al. (2008)
- **Scarcity & Cognitive Bandwidth** — Mullainathan & Shafir (2013), Mani et al. (2013)
- **Prospect Theory** — Kahneman & Tversky (1979)
- **Safety-First Criterion** — Roy (1952), Levy & Levy (2009)
- **Capabilities Approach** — Sen (1999)
- **Social Capital & Debt** — Guerin et al. (2014), Jachimowicz et al. (2021)
- **Microfinance & Borrower Welfare** — Ghatak et al. (LSE), Banerjee et al. (2015)

---

## Origin

I'm a high school student from rural West Bengal, India.

No coding bootcamps. No mentors in finance or machine learning. Just documentation, curiosity, and a question that wouldn't let go.

The Bengali proverb says: *"Pete laathi mene tolay baari"*—a kick to the stomach, a blow from below. Poverty strikes twice. Mani et al. proved this isn't metaphor. Building Quantura taught me it isn't just about cognitive load—it's about reward functions we refuse to see.

---

## Future Work

- [ ] Validation on real-world microfinance data (J-PAL Spandana, BFA Financial Diaries)
- [ ] Ethnographic calibration of dignity transition parameters
- [ ] Human-in-the-loop consent architecture implementation
- [ ] Cross-cultural validation across contexts

---

## Ethics

This framework could be weaponised. The same IRL that enables empathetic tools could decode vulnerability for predatory targeting.

**Proposed safeguards:**
- Human-in-the-loop validation (EU AI Act Article 14 compliance)
- User-facing inference transparency
- No external transmission of constraint profiles
- Opt-out architecture for specific inferences

See paper Section 7 for full dual-use analysis.

---

## License

MIT License. See [LICENSE](LICENSE).

---

## Contact

**Debarghya Pati**  
📧 debarghyapati47@gmail.com  
📍 West Bengal, India

---

<p align="center">
  <i>"The goal is not smarter algorithms.<br>It is algorithms that know what they cannot see—and ask before they assume."</i>
</p>
