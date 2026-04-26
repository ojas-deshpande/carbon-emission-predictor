# 📤 How to Post Your Project on GitHub
## Complete Step-by-Step Guide for Beginners

---

## 🤔 What is GitHub?

GitHub is a website where developers store and share their code.
Think of it like **Google Drive — but for code projects.**

When you put your project on GitHub:
- Anyone can see your work (great for portfolio!)
- You can share a link with your professor
- Your code is safely backed up online
- Other people can use or contribute to it

**Your project will get a URL like:**
`https://github.com/your-username/carbon-emission-dashboard`

---

## 🔧 What You Need

- A computer (Windows / macOS / Linux)
- Internet connection
- 20 minutes

---

## PART 1 — Create a GitHub Account

**Step 1.1** — Go to https://github.com

**Step 1.2** — Click **"Sign up"**

**Step 1.3** — Fill in:
- Username (example: `rahul-sharma` or `john-doe`) — this will be in your URL
- Email address
- Password

**Step 1.4** — Verify your email

**Step 1.5** — You're in! GitHub dashboard opens.

---

## PART 2 — Install Git on Your Computer

Git is the tool that sends your files to GitHub.

### Windows
1. Go to → https://git-scm.com/download/win
2. Download and run the installer
3. Click **Next** on every screen (defaults are fine)
4. At the end, click **Finish**

### macOS
Open Terminal and run:
```bash
git --version
```
If not installed, it will prompt you to install it. Click **Install**.

Or install with Homebrew:
```bash
brew install git
```

### Linux (Ubuntu/Debian)
```bash
sudo apt install git -y
```

**Verify Git is installed:**
```bash
git --version
# Should show: git version 2.x.x
```

---

## PART 3 — Set Up Git With Your Name

This is a one-time setup. Open **Command Prompt** (Windows) or **Terminal** (macOS/Linux) and run:

```bash
git config --global user.name "Your Full Name"
git config --global user.email "your@email.com"
```

Use the **same email** you used for GitHub.

---

## PART 4 — Create a Repository on GitHub

A **repository** (or "repo") is like a folder on GitHub for your project.

**Step 4.1** — Log in to https://github.com

**Step 4.2** — Click the **"+"** button in the top-right corner

**Step 4.3** — Click **"New repository"**

**Step 4.4** — Fill in the form:

| Field | What to Enter |
|---|---|
| Repository name | `carbon-emission-dashboard` |
| Description | `Full-stack ML dashboard for predicting global CO₂ emissions` |
| Visibility | ✅ Public (so professor can see it) |
| Add a README file | ❌ Uncheck this (we have our own) |
| Add .gitignore | ❌ Leave as None |
| License | ❌ Leave as None |

**Step 4.5** — Click **"Create repository"**

You'll see a page with a URL like:
```
https://github.com/your-username/carbon-emission-dashboard
```
**Keep this page open — you'll need the URL in the next step.**

---

## PART 5 — Prepare Your Project Folder

Before uploading, clean up your folder. You don't need to upload everything.

**Your project folder should contain ONLY these files:**

```
carbon-emission-dashboard/
├── README.md                    ✅ Upload
├── HOW_TO_RUN.md                ✅ Upload
├── index.html                   ✅ Upload
├── _template.html               ✅ Upload
├── generate_data.py             ✅ Upload
├── data_pipeline.py             ✅ Upload
├── ml_models.py                 ✅ Upload
├── insights.py                  ✅ Upload
├── chatbot_server.py            ✅ Upload
├── requirements.txt             ✅ Upload
│
└── backend/
    ├── app.py                   ✅ Upload
    ├── models.py                ✅ Upload
    ├── config.py                ✅ Upload
    ├── init_db.py               ✅ Upload
    └── requirements_backend.txt ✅ Upload
```

**DO NOT UPLOAD these (they're auto-generated or private):**
```
venv/                    ❌ Don't upload (too large, private)
__pycache__/             ❌ Don't upload (auto-generated)
dashboard_data.json      ❌ Don't upload (auto-generated)
uploads/                 ❌ Don't upload (user data)
*.pyc files              ❌ Don't upload
```

---

## PART 6 — Create a .gitignore File

A `.gitignore` file tells Git which files to skip automatically.

Create a file called `.gitignore` in your project folder and paste this inside:

```
# Virtual environment
venv/
env/
.env

# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd
*.pycache

# Generated files
dashboard_data.json
uploads/

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store          # macOS
Thumbs.db          # Windows
desktop.ini

# Sensitive files
*.env
secrets.py
```

**Save this file as `.gitignore`** (with the dot at the start, no extension).

---

## PART 7 — Upload Your Project to GitHub

Open **Command Prompt** or **Terminal** and navigate to your project folder:

```bash
# Navigate to your project folder
cd path/to/carbon-emission-dashboard

# Example on Windows:
cd C:\Users\YourName\carbon-emission-dashboard

# Example on macOS/Linux:
cd ~/Documents/carbon-emission-dashboard
```

Now run these commands **one by one:**

```bash
# Step 1: Initialize git in your folder
git init

# Step 2: Connect your folder to your GitHub repository
# (Replace YOUR_USERNAME with your actual GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/carbon-emission-dashboard.git

# Step 3: Tell git to track all your files
git add .

# Step 4: Save your files with a message
git commit -m "Initial commit - Carbon Emission Dashboard"

# Step 5: Send files to GitHub
git push -u origin main
```

**After Step 5**, Git will ask for your GitHub username and password.

> ⚠️ **Important:** GitHub no longer accepts your regular password here.
> You need a **Personal Access Token** instead. See Part 8 below.

---

## PART 8 — Create a Personal Access Token (Password for Git)

GitHub requires a special token instead of your password.

**Step 8.1** — Go to GitHub → Click your profile picture (top-right) → **Settings**

**Step 8.2** — Scroll down the left sidebar → Click **"Developer settings"**

**Step 8.3** — Click **"Personal access tokens"** → **"Tokens (classic)"**

**Step 8.4** — Click **"Generate new token"** → **"Generate new token (classic)"**

**Step 8.5** — Fill in:
- **Note:** `carbon-dashboard-upload`
- **Expiration:** 90 days (or No expiration for your project)
- **Scopes:** Tick ✅ **`repo`** (this gives full repo access)

**Step 8.6** — Click **"Generate token"**

**Step 8.7** — ⚠️ **COPY THE TOKEN NOW** — it shows only once!
It looks like: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx`

**Step 8.8** — When Git asks for your password, paste this token.

> 💡 **Tip:** To avoid typing it every time, run:
> ```bash
> git config --global credential.helper store
> ```
> Then the next time you push, Git saves your token automatically.

---

## PART 9 — Verify It's Online

1. Go to: `https://github.com/YOUR_USERNAME/carbon-emission-dashboard`
2. You should see all your files listed
3. The `README.md` content displays automatically on the page

**🎉 Your project is now live on GitHub!**

---

## PART 10 — How to Update Your Project Later

Whenever you make changes to your code and want to update GitHub:

```bash
# Navigate to your project folder
cd path/to/carbon-emission-dashboard

# Stage all changes
git add .

# Commit with a message describing what you changed
git commit -m "Added compare tab and AI chatbot"

# Push to GitHub
git push
```

That's all. Your GitHub page updates automatically.

---

## PART 11 — Make Your Repository Look Professional

After uploading, do these things on GitHub to make it look great:

### Add Topics/Tags
1. On your repo page, click the ⚙️ gear icon next to **"About"**
2. Add topics like: `machine-learning`, `python`, `flask`, `co2-emissions`, `data-visualization`, `plotly`, `mysql`, `bca-project`
3. Click **Save changes**

### Add a Website Link
If you deploy it online (optional), add the URL in the **About** section.

### Pin the Repository
1. Go to your profile page: `https://github.com/YOUR_USERNAME`
2. Click **"Customize your profile"**
3. Pin this repository so it appears at the top

---

## 🔄 Complete Command Reference

```bash
# ONE-TIME SETUP (do only once)
git config --global user.name "Your Name"
git config --global user.email "your@email.com"

# FIRST UPLOAD (do once per project)
git init
git remote add origin https://github.com/USERNAME/REPONAME.git
git add .
git commit -m "Initial commit"
git push -u origin main

# EVERY TIME YOU UPDATE CODE
git add .
git commit -m "Description of what you changed"
git push

# CHECK STATUS (see which files changed)
git status

# SEE HISTORY OF COMMITS
git log --oneline
```

---

## 🛑 Common Errors and Fixes

### "src refspec main does not match any"
Your branch might be called `master` not `main`. Try:
```bash
git push -u origin master
```

### "failed to push some refs"
Someone else pushed changes (or GitHub has a README). Pull first:
```bash
git pull origin main --allow-unrelated-histories
git push
```

### "remote origin already exists"
```bash
git remote remove origin
git remote add origin https://github.com/USERNAME/REPONAME.git
```

### "Permission denied / Authentication failed"
Make sure you're using a Personal Access Token (not your password). See Part 8.

### Files not showing on GitHub
Make sure you ran `git add .` and `git commit` before `git push`.

---

## 📁 Final Checklist Before Sharing

Before sending the link to your professor, confirm:

- [ ] All Python files are visible on GitHub
- [ ] README.md displays properly (with headings, tables, badges)
- [ ] No `venv/` folder uploaded (it's huge and private)
- [ ] `.gitignore` file is present
- [ ] Repository is set to **Public**
- [ ] Repository description is filled in
- [ ] Topics/tags are added

---

## 📎 Your GitHub Project URL

Once complete, your project will be live at:

```
https://github.com/YOUR_USERNAME/carbon-emission-dashboard
```

Share this link with your professor, add it to your resume, and keep it as portfolio evidence of your work!

---

## 🎓 What GitHub Shows Recruiters/Professors

When someone visits your GitHub project they can see:

1. **README** — Your project description, features, how to run
2. **All source files** — Your actual Python, HTML, CSS, JS code
3. **Commit history** — Proof you built it over time
4. **Languages** — GitHub auto-detects Python, HTML, JavaScript
5. **Stars and forks** — If others find it useful, they can star it

This is exactly why having a clean README and proper folder structure matters — it's your first impression.

---

*Good luck with your project submission! 🚀*
