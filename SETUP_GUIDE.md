# 📚 Setup Guide for School Project

This guide will help you get your Financial Analytics Dashboard from Replit to GitHub and deployed online.

## 🎯 Quick Start (5 Steps)

### Step 1: Download Your Code from Replit

**Option A: Using Git (Recommended)**
```bash
# In Replit Shell
git add .
git commit -m "Prepare for GitHub upload"
```

**Option B: Download as ZIP**
1. Click the three dots menu in Replit
2. Select "Download as zip"
3. Extract the files on your computer

### Step 2: Create GitHub Repository

1. Go to [github.com](https://github.com)
2. Click the "+" icon → "New repository"
3. Name it: `financial-analytics-dashboard`
4. Make it **Public** (required for free hosting)
5. **Don't** initialize with README (we already have one!)
6. Click "Create repository"

### Step 3: Upload Your Code to GitHub

**Option A: Using Git (if you're familiar)**
```bash
git remote add origin https://github.com/YOUR_USERNAME/financial-analytics-dashboard.git
git branch -M main
git push -u origin main
```

**Option B: Upload Files Directly**
1. On your new GitHub repo page, click "uploading an existing file"
2. Drag and drop ALL your project files
3. **Important:** Rename `requirements-github.txt` to `requirements.txt`
4. Add commit message: "Initial commit - Financial Analytics Dashboard"
5. Click "Commit changes"

### Step 4: Deploy to Streamlit Cloud (FREE!)

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "Continue with GitHub"
3. Click "New app"
4. Fill in:
   - Repository: `YOUR_USERNAME/financial-analytics-dashboard`
   - Branch: `main`
   - Main file path: `app.py`
5. Click "Advanced settings"
6. In "Secrets" section, paste:
   ```toml
   OPENAI_API_KEY = "your-openai-key-here"
   ```
   (Get your key from [platform.openai.com](https://platform.openai.com))
7. Click "Deploy"!
8. Wait 2-3 minutes for deployment ☕

### Step 5: Test & Share!

Your app will be live at:
```
https://YOUR_USERNAME-financial-analytics-dashboard.streamlit.app
```

Test all features:
- ✅ Stock analyzer
- ✅ Portfolio analysis
- ✅ Personal finance upload
- ✅ AI chat assistant

---

## 📝 Before You Upload to GitHub

### Required Changes:

1. **Rename this file:**
   - `requirements-github.txt` → `requirements.txt`

2. **Update README.md with your info:**
   ```markdown
   ## 👨‍🎓 Author
   [Your Name]
   [Your School Name]
   [Your Email]
   ```

3. **Update LICENSE:**
   - Replace `[Your Name]` with your actual name

4. **Add your deployed link to README:**
   - After deployment, add the URL to the "Live Demo" section

### Optional Improvements:

1. **Take Screenshots:**
   - Stock analysis results
   - Portfolio dashboard
   - Personal finance charts
   - AI chat interface
   - Add to `screenshots/` folder

2. **Record Demo Video:**
   - Use [Loom](https://loom.com) (free)
   - 2-3 minute walkthrough
   - Add link to README

3. **Add Sample Data:**
   - Include example CSV files
   - Add instructions in README

---

## 🔑 Getting OpenAI API Key

1. Go to [platform.openai.com](https://platform.openai.com)
2. Sign up (free account)
3. You get **$5 free credit** as a new user!
4. Go to "API keys" section
5. Click "Create new secret key"
6. Name it: "Financial Analytics Dashboard"
7. **Copy the key immediately** (you can't see it again!)
8. Save it somewhere safe

**Cost for school demo:**
- Each AI request costs ~$0.001-0.01
- Your $5 credit = 500-5000 requests
- Perfect for school presentations!

---

## 📋 What to Include in GitHub

### ✅ Upload These Files:
- `app.py` (main application)
- `requirements.txt` (renamed from requirements-github.txt)
- `README.md`
- `LICENSE`
- `DEPLOYMENT.md`
- `.gitignore`
- All folders: `services/`, `ui_components/`, `.streamlit/`
- Sample data files: `sample_data.csv`, etc.

### ❌ Don't Upload These:
- `.replit` (Replit-specific)
- `pyproject.toml` (Replit-specific)
- `uv.lock` (Replit-specific)
- `.env` or secrets (security!)
- `__pycache__/` folders
- `.pythonlibs/` folder

**The `.gitignore` file I created handles this automatically!**

---

## 🎓 For Your School Presentation

### Create a Presentation Slide Deck with:

1. **Title Slide**
   - Project name
   - Your name
   - School info

2. **Problem Statement**
   - Why financial analysis tools are important
   - Who needs them

3. **Solution**
   - Your app features
   - Screenshots

4. **Technology Stack**
   - Python, Streamlit, AI, etc.
   - Show you understand modern tech

5. **Demo**
   - Live demo of your deployed app
   - Use the Streamlit Cloud link

6. **Architecture**
   - Show project structure
   - Explain key components

7. **Challenges & Solutions**
   - What you learned
   - Problems you solved

8. **Future Improvements**
   - What you'd add next
   - Show vision

---

## 🐛 Common Issues & Solutions

### "Module not found" error
**Fix:** Make sure `requirements.txt` has all packages listed

### "API key not found" error
**Fix:** Check secrets in Streamlit Cloud settings

### App crashes on startup
**Fix:** Check logs in Streamlit Cloud dashboard

### Charts not showing
**Fix:** This is already fixed! Just deploy the code as-is

---

## 📞 Getting Help

- **Streamlit Docs:** [docs.streamlit.io](https://docs.streamlit.io)
- **GitHub Guides:** [guides.github.com](https://guides.github.com)
- **Python Help:** [stackoverflow.com](https://stackoverflow.com)

---

## ✅ Checklist Before Submitting

- [ ] Code uploaded to GitHub
- [ ] README updated with your info
- [ ] App deployed to Streamlit Cloud
- [ ] Tested all features work
- [ ] OpenAI API key set up
- [ ] Screenshots added (optional)
- [ ] Demo video recorded (optional)
- [ ] Presentation prepared
- [ ] GitHub link ready to share
- [ ] Live demo link ready to share

---

Good luck with your school project! 🎉🚀

You've built something impressive - be proud! 
