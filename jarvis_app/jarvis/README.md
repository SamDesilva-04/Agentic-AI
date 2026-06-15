# 🤖 JARVIS — Local AI Desktop Assistant

A fully local, self-learning AI assistant that runs on your laptop with no token limits, no usage caps, and full desktop access.

---

## ✅ Features

| Feature | Online | Offline |
|---|---|---|
| Full AI chat (LLM) | ✅ | ✅ (needs Ollama) |
| Web search (DuckDuckGo) | ✅ | ❌ |
| Weather | ✅ | ❌ |
| Time & Date | ✅ | ✅ |
| Calculator / Math | ✅ | ✅ |
| System info (CPU/RAM/Disk) | ✅ | ✅ |
| Screenshots | ✅ | ✅ |
| Open files / URLs | ✅ | ✅ |
| Memory across sessions | ✅ | ✅ |
| Self-learning (teach facts) | ✅ | ✅ |
| Internet status notification | ✅ | ✅ |

---

## 🚀 Setup (One-time)

### Step 1 — Install Python
Download from https://python.org (3.10 or higher)

### Step 2 — Install Ollama (for AI chat)
Download from https://ollama.com and install it.

Then pull a model (choose one):
```bash
ollama pull llama3.2          # Recommended — fast, smart
ollama pull mistral           # Alternative
ollama pull phi3              # Lightweight, great for low-RAM machines
```

Then start Ollama:
```bash
ollama serve
```

### Step 3 — Run JARVIS

**Windows:**
```
Double-click start_windows.bat
```

**Linux / macOS:**
```bash
chmod +x start_linux_mac.sh
./start_linux_mac.sh
```

**Or directly:**
```bash
pip install -r requirements.txt
python app.py
```

JARVIS will open automatically at **http://localhost:7777**

---

## 🧠 Teaching JARVIS

You can teach JARVIS facts about you in three ways:

1. **Say it:** "Remember that my name: Sam DeSilva"
2. **Click 📌** in the input bar and fill in a key/value
3. **Say it naturally** and JARVIS will remember across sessions

---

## 💻 Desktop Commands

- `open https://github.com` — opens browser
- `open C:\Users\Sam\Documents` — opens folder
- `take a screenshot` — captures your desktop
- `launch notepad` — opens apps (Windows)

---

## ⚙️ Settings (click ⚙️ in sidebar)

- Switch between models (llama3.2, mistral, phi3, etc.)
- Set how many past messages to remember
- Toggle dark/light theme

---

## 📦 Dependencies

```
flask          — web server
requests       — HTTP calls
psutil         — system metrics
duckduckgo-search — web search (no API key needed)
beautifulsoup4 — web page parsing
pyautogui      — screenshots & desktop control
Pillow         — image processing
```

---

## 🔒 Privacy

Everything runs **100% locally** on your machine. No data is sent to any cloud service (web search queries go to DuckDuckGo anonymously). Your conversations are stored in `memory/conversations.jsonl` on your own disk.

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| "Ollama not running" | Run `ollama serve` in a terminal |
| No models showing | Run `ollama pull llama3.2` |
| Screenshot fails | Run `pip install pyautogui pillow` |
| Port 7777 in use | Edit `port = 7777` in `app.py` |
| Slow responses | Use a smaller model like `phi3` |
