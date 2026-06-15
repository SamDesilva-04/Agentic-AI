# 🤖 JARVIS — Local AI Desktop Assistant

A fully local, self-learning AI assistant that runs on your laptop with no token limits, no usage caps, and full desktop access. Built with Flask and powered by Ollama.

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

## 🛠️ Tech Stack

- **Backend:** Python, Flask
- **LLM Engine:** Ollama (llama3.2 / mistral / phi3)
- **Web Search:** DuckDuckGo (no API key needed)
- **System Monitoring:** psutil
- **Desktop Control:** pyautogui
- **Frontend:** HTML, CSS, JavaScript (served via Flask)

---

## 🚀 Setup

### Step 1 — Install Python
Download from https://python.org (3.10 or higher)

### Step 2 — Install Ollama
Download from https://ollama.com and install it.

Then pull a model:
```bash
ollama pull llama3.2          # Recommended — fast, smart
ollama pull mistral           # Alternative
ollama pull phi3              # Lightweight, great for low-RAM machines
```

Start Ollama:
```bash
ollama serve
```

### Step 3 — Run JARVIS

**Windows:**
