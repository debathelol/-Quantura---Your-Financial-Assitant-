# 🔄 Keep Your App Always Online (Free Solutions)

Your Streamlit app goes to sleep after 7 days of inactivity on the free tier. Here are FREE ways to keep it awake:

---

## Solution 1: UptimeRobot (RECOMMENDED - 100% FREE) ⭐

**UptimeRobot** automatically pings your app every 5 minutes to keep it awake.

### Setup (Takes 2 minutes):

1. **Sign Up**
   - Go to [uptimerobot.com](https://uptimerobot.com)
   - Create a free account (no credit card needed)

2. **Add New Monitor**
   - Click **"+ Add New Monitor"**
   - Settings:
     - **Monitor Type:** HTTP(s)
     - **Friendly Name:** Quantura Financial App
     - **URL:** `https://your-app-url.streamlit.app`
     - **Monitoring Interval:** 5 minutes
   - Click **"Create Monitor"**

3. **Done!**
   - Your app will be pinged every 5 minutes
   - It will NEVER go to sleep
   - Completely free forever (up to 50 monitors)

**Result:** Your app stays online 24/7! ✅

---

## Solution 2: Cron-job.org (Also FREE)

Another reliable service:

1. Go to [cron-job.org](https://cron-job.org)
2. Create free account
3. Add new cronjob:
   - **Title:** Keep Quantura Alive
   - **URL:** `https://your-app-url.streamlit.app`
   - **Schedule:** Every 5 minutes
4. Save and activate

---

## Solution 3: GitHub Actions (For Developers)

Use GitHub's free CI/CD to ping your app:

1. Create `.github/workflows/keepalive.yml` in your repo:

```yaml
name: Keep App Alive

on:
  schedule:
    # Run every 4 hours
    - cron: '0 */4 * * *'
  workflow_dispatch:

jobs:
  keep-alive:
    runs-on: ubuntu-latest
    steps:
      - name: Ping App
        run: |
          curl -I https://your-app-url.streamlit.app
          echo "App pinged successfully"
```

2. Commit and push
3. Enable Actions in your GitHub repo settings
4. Your app gets pinged every 4 hours automatically!

---

## Solution 4: Deploy to Always-On Platform (Alternative)

If you want TRUE always-on (no sleeping ever), use these platforms:

### A. Railway.app
- **Free Tier:** $5 credit/month (enough for small apps)
- **No Sleep:** Always online
- **Setup:**
  1. Go to [railway.app](https://railway.app)
  2. Sign in with GitHub
  3. Deploy from your repo
  4. Add `OPENAI_API_KEY` environment variable
  5. Done! Always online.

### B. Render.com
- **Free Tier:** Available (spins down after 15 min inactivity)
- **Paid:** $7/month for always-on
- **Setup:**
  1. Go to [render.com](https://render.com)
  2. New Web Service → Connect GitHub
  3. Build: `pip install -r requirements.txt`
  4. Start: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
  5. Add environment variable: `OPENAI_API_KEY`

### C. Fly.io
- **Free Tier:** Good allowance
- **Always On:** Yes, on free tier
- **Setup:**
  1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
  2. Run: `fly launch`
  3. Deploy: `fly deploy`
  4. Set secrets: `fly secrets set OPENAI_API_KEY=your-key`

---

## Solution 5: Streamlit Cloud Paid ($20/month)

If you want the simplest solution:

- **Cost:** $20/month
- **Benefits:**
  - No sleep ever
  - Priority support
  - More resources
  - Private apps
  - Custom domains

**Upgrade:** Settings → Billing in Streamlit Cloud dashboard

---

## 📊 Comparison Table

| Solution | Cost | Setup Time | Reliability | Always-On? |
|----------|------|------------|-------------|------------|
| **UptimeRobot** | FREE | 2 min | ⭐⭐⭐⭐⭐ | ✅ Yes |
| **Cron-job.org** | FREE | 3 min | ⭐⭐⭐⭐⭐ | ✅ Yes |
| **GitHub Actions** | FREE | 5 min | ⭐⭐⭐⭐ | ✅ Yes |
| **Railway.app** | $5/mo credit | 5 min | ⭐⭐⭐⭐⭐ | ✅ Yes |
| **Render.com** | $7/mo | 10 min | ⭐⭐⭐⭐⭐ | ✅ Yes (paid) |
| **Streamlit Paid** | $20/mo | 1 min | ⭐⭐⭐⭐⭐ | ✅ Yes |

---

## 🎯 My Recommendation

**For Your School Project:**

1. **FREE Option:** Use **UptimeRobot** (takes 2 minutes, works perfectly)
2. **Best Long-term:** Deploy to **Railway.app** ($5/month credit is free, always-on)

**Quick Win:** Set up UptimeRobot right now while keeping your Streamlit deployment. Takes literally 2 minutes and your app will never sleep again!

---

## 🔧 How to Find Your App URL

Your Streamlit app URL is shown in the Streamlit Cloud dashboard:
- Format: `https://[username]-[repo-name].streamlit.app`
- Example: `https://debathelol-quantura.streamlit.app`

Copy this URL and use it in UptimeRobot or whichever solution you choose.

---

## ⚡ Quick Setup: UptimeRobot (Step-by-Step)

1. Open [uptimerobot.com](https://uptimerobot.com) in new tab
2. Click "Get Started for Free"
3. Enter your email and create password
4. Verify your email
5. Click "+ Add New Monitor"
6. Fill in:
   ```
   Monitor Type: HTTP(s)
   Friendly Name: Quantura App
   URL: https://your-streamlit-app-url.streamlit.app
   Monitoring Interval: 5 minutes
   ```
7. Click "Create Monitor"

**Done!** Your app will be pinged every 5 minutes and stay awake forever! 🎉

---

## 📱 Bonus: Get Alerts

UptimeRobot can also alert you if your app goes down:

1. In UptimeRobot dashboard, click "Alert Contacts"
2. Add your email or phone number
3. Get notified instantly if your app has issues

---

## 🆘 Troubleshooting

**Q: My app still went to sleep with UptimeRobot**
- Check that the monitor is active (green checkmark)
- Verify the URL is correct
- Make sure monitoring interval is 5 minutes or less

**Q: Does this cost me anything?**
- No! UptimeRobot free tier allows 50 monitors
- Streamlit Cloud free tier is still free
- No extra charges

**Q: Will this use my OpenAI credits?**
- Pings don't trigger AI features
- They just load the homepage
- Your API usage stays the same

---

**Recommended Action:** Set up UptimeRobot NOW (2 minutes) and your app will never sleep again! 🚀
