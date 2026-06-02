# 📝 AI Notes Summarizer+

An AI-powered tool that helps students summarize notes, extract key points, and generate study questions.

## 🚀 Live Demo

[Click here to try it!](https://ai-notes-summarizer.streamlit.app)

## 🎯 Features

- 📌 **Summary** — Bullet-point overview of your notes
- 🔑 **Key Points** — Extract the most important concepts
- ❓ **Study Questions** — Generate AI-powered questions to test understanding
- 📄 **PDF Support** — Upload and process PDF files
- 📥 **Export** — Download results as TXT files
- 📜 **History** — Search, pin, and manage your past results
- ⌨️ **Keyboard Shortcuts** — Ctrl+Enter (Generate), Ctrl+S (Sample), Ctrl+F (Focus), Ctrl+P (PDF)

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **AI**: Google Gemini API (gemini-2.5-flash)
- **PDF**: pdfplumber

## 📦 Local Development

### Prerequisites
- Python 3.10+
- A Gemini API key (free at https://aistudio.google.com/apikey)

### Setup

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO

# Create secrets file
mkdir -p .streamlit
echo 'GEMINI_API_KEY = "your-api-key-here"' > .streamlit/secrets.toml

# Install dependencies
pip install -r requirements.txt

# Run locally
streamlit run app.py
```

## ☁️ Deploy to Streamlit Cloud (Free)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```

2. **Deploy**
   - Go to https://share.streamlit.io
   - Sign in with GitHub
   - Click **"New app"**
   - Select your repository
   - Set Main file path to `app.py`
   - Click **"Deploy"**

3. **Add API Key**
   - In your app dashboard, go to **Settings → Secrets**
   - Add:
     ```toml
     GEMINI_API_KEY = "your-api-key-here"
     ```
   - Click **Save**
   - Your app will automatically restart

4. **Share**
   - Your app is now live at: `https://YOUR_APP_NAME.streamlit.app`
   - Share this link with anyone!

## 🔒 Security Notes

- The Gemini API key is stored as a **Streamlit Secret** (not in code)
- The `.streamlit/secrets.toml` file is excluded by `.gitignore`
- Users of the deployed app don't need to provide their own API key

## 📝 License

This project was created as a 10th-grade AI project.
