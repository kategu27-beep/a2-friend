# A2 Friend

A2 Friend is a small Flask web app for friendly conversations in simple CEFR A2 English. The chat lives inside a cozy, responsive diary interface. Conversation history stays only in the open browser tab.

## Project files

- `main.py` — Flask routes, input checks, Kie AI request, and response parsing.
- `templates/index.html` — diary page structure.
- `static/style.css` — illustration, layout, animation, and mobile styles.
- `static/script.js` — chat UI, mood display, and short client-side history.
- `requirements.txt` — Python packages.
- `.gitignore` — files that must not be committed.

## Run locally (PowerShell in VS Code)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:KIE_API_KEY="your_key_here"
$env:KIE_API_URL="https://api.kie.ai/api/v1/responses"
$env:KIE_MODEL="your_model_name"
$env:PORT="3000"
python main.py
```

Open `http://127.0.0.1:3000`. Only `KIE_API_KEY` is strictly required; the other settings have defaults. Set `KIE_MODEL` to a model supported by your Kie AI account.

Never put the real API key in HTML, JavaScript, Git, or this README. For local work you may keep it in a `.env` file for reference, but this simple version does not automatically load that file: set it in the terminal as shown above.

## Connect to GitHub

Create an empty repository on GitHub, then run:

```powershell
git init
git add .
git commit -m "Create A2 Friend"
git branch -M main
git remote add origin https://github.com/YOUR_NAME/a2-friend.git
git push -u origin main
```

## Deploy to Bothost

Connect the GitHub repository in Bothost and configure:

- Build/install command: `pip install -r requirements.txt`
- Start command: `python main.py`
- `KIE_API_KEY`: your real Kie AI key (secret)
- `KIE_API_URL`: `https://api.kie.ai/api/v1/responses`
- `KIE_MODEL`: a model name available in your Kie AI account
- `PORT`: use the value provided by the host; the app defaults to `3000`

The server listens on `0.0.0.0`, so it is ready for hosting. No `localhost` URL is hard-coded in the frontend.
