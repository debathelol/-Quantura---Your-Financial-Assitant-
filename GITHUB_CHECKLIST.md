# ✅ GitHub Upload Checklist

Use this checklist to make sure you're ready to upload!

## Before Upload

- [ ] I've tested the app and it works
- [ ] All features are working (stock analysis, portfolio, etc.)
- [ ] I've removed any personal API keys from the code
- [ ] I've updated README.md with my name and school info

## Files to Rename/Update

- [ ] Rename `requirements-github.txt` to `requirements.txt`
- [ ] Update `[Your Name]` in LICENSE file
- [ ] Update `[Your Email]` in README.md
- [ ] Add your GitHub username to deployment links

## What to Upload

### ✅ These Files
- [ ] `app.py`
- [ ] `requirements.txt` (renamed!)
- [ ] `README.md`
- [ ] `LICENSE`
- [ ] `DEPLOYMENT.md`
- [ ] `SETUP_GUIDE.md`
- [ ] `.gitignore`
- [ ] `services/` folder (all files)
- [ ] `ui_components/` folder (all files)
- [ ] `.streamlit/` folder
- [ ] `sample_data.csv`
- [ ] `sample_data_multi_year.csv`

### ❌ Don't Upload
- [ ] `.replit` file
- [ ] `pyproject.toml`
- [ ] `uv.lock`
- [ ] Any files with "replit" or "nix" in the name
- [ ] `.env` or `.streamlit/secrets.toml`
- [ ] `__pycache__` folders

## After Upload to GitHub

- [ ] Repository is PUBLIC (required for free hosting)
- [ ] README displays correctly
- [ ] All folders are present
- [ ] requirements.txt is in root directory

## Deployment

- [ ] Created Streamlit Cloud account
- [ ] Connected GitHub repository
- [ ] Added OpenAI API key to secrets
- [ ] App successfully deployed
- [ ] Tested deployed app works
- [ ] Added deployed URL to README

## Final Checks

- [ ] All links in README work
- [ ] Screenshots added (optional but impressive!)
- [ ] Code is clean and commented
- [ ] No errors in the deployed app
- [ ] Prepared presentation/demo

---

## Quick Deploy Command

Once everything is on GitHub:

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. New app → Select your repo → Deploy!
3. Add this to secrets:
   ```
   OPENAI_API_KEY = "your-key-here"
   ```

---

**You're ready to impress your teachers! 🎓**
