"""
JARVIS — Local AI Desktop Assistant
Run with: python app.py
Requires Ollama running locally: https://ollama.com
"""

import os, sys, json, math, re, socket, threading, time, datetime, subprocess, platform
import base64, io, hashlib, webbrowser
from pathlib import Path
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import requests
import psutil

# ─── Directories ─────────────────────────────────────────────────────────────
BASE    = Path(__file__).parent
MEMORY  = BASE / "memory"
MEMORY.mkdir(exist_ok=True)
CONV_FILE  = MEMORY / "conversations.jsonl"
FACTS_FILE = MEMORY / "learned_facts.json"
PREFS_FILE = MEMORY / "preferences.json"

# ─── Flask App ────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "jarvis-local-key-2025"

OLLAMA_URL    = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2"

# ─── Utility helpers ──────────────────────────────────────────────────────────

def check_internet(host="8.8.8.8", port=53, timeout=2):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False


def check_ollama():
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        models = [m["name"] for m in r.json().get("models", [])]
        return True, models
    except Exception:
        return False, []


def get_system_info():
    now = datetime.datetime.now()
    bat = psutil.sensors_battery() if hasattr(psutil, "sensors_battery") else None
    return {
        "time"    : now.strftime("%I:%M:%S %p"),
        "date"    : now.strftime("%A, %B %d, %Y"),
        "cpu"     : psutil.cpu_percent(interval=0.2),
        "ram"     : psutil.virtual_memory().percent,
        "ram_used": round(psutil.virtual_memory().used / (1024**3), 1),
        "ram_total": round(psutil.virtual_memory().total / (1024**3), 1),
        "disk"    : psutil.disk_usage("/").percent,
        "platform": platform.system(),
        "hostname": platform.node(),
        "battery" : f"{bat.percent:.0f}% {'charging' if bat.power_plugged else 'discharging'}" if bat else "N/A",
    }


# ─── Memory / Learning ────────────────────────────────────────────────────────

def save_turn(role: str, content: str):
    with open(CONV_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "role": role, "content": content,
            "ts": datetime.datetime.now().isoformat()
        }) + "\n")


def load_recent(n=30):
    if not CONV_FILE.exists():
        return []
    lines = CONV_FILE.read_text(encoding="utf-8").strip().splitlines()
    msgs = []
    for line in lines[-n:]:
        try:
            d = json.loads(line)
            msgs.append({"role": d["role"], "content": d["content"]})
        except Exception:
            pass
    return msgs


def load_facts():
    if not FACTS_FILE.exists():
        return {}
    try:
        return json.loads(FACTS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_fact(key: str, value: str):
    facts = load_facts()
    facts[key] = {"value": value, "updated": datetime.datetime.now().isoformat()}
    FACTS_FILE.write_text(json.dumps(facts, indent=2), encoding="utf-8")


def load_prefs():
    if not PREFS_FILE.exists():
        return {"model": DEFAULT_MODEL, "theme": "dark", "memory_turns": 20}
    try:
        return json.loads(PREFS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"model": DEFAULT_MODEL, "theme": "dark", "memory_turns": 20}


def save_prefs(prefs: dict):
    PREFS_FILE.write_text(json.dumps(prefs, indent=2), encoding="utf-8")


def memory_context() -> str:
    facts = load_facts()
    if not facts:
        return ""
    lines = [f"- {k}: {v['value']}" for k, v in list(facts.items())[-20:]]
    return "Learned facts about the user:\n" + "\n".join(lines)


# ─── Web tools ────────────────────────────────────────────────────────────────

def web_search(query: str, max_results: int = 6):
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return results
    except Exception as e:
        return []


def fetch_url(url: str) -> str:
    try:
        from bs4 import BeautifulSoup
        headers = {"User-Agent": "Mozilla/5.0 (compatible; JARVIS/1.0)"}
        r = requests.get(url, timeout=12, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script","style","nav","footer","header","aside","noscript"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        # Clean up blank lines
        lines = [l for l in text.splitlines() if l.strip()]
        return "\n".join(lines[:300])
    except Exception as e:
        return f"Could not fetch URL: {e}"


def get_weather(city: str = "") -> str:
    try:
        url = f"https://wttr.in/{city.replace(' ','+') if city else ''}?format=3"
        r = requests.get(url, timeout=5)
        return r.text.strip()
    except Exception:
        return "Weather service unavailable."


# ─── Screenshot ───────────────────────────────────────────────────────────────

def take_screenshot():
    try:
        import pyautogui
        from PIL import Image
        screenshot = pyautogui.screenshot()
        buf = io.BytesIO()
        screenshot.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        return None


# ─── Offline query handler ────────────────────────────────────────────────────

MATH_RE = re.compile(r"^[\s\d\+\-\*\/\(\)\.\%\,\^\s]+$")

def handle_offline(query: str):
    q = query.lower().strip()
    now = datetime.datetime.now()

    # Time
    if re.search(r"\btime\b|\bclock\b|\bhour\b|\bminute\b", q):
        return f"⏰ Current time: **{now.strftime('%I:%M:%S %p')}**"

    # Date
    if re.search(r"\bdate\b|\btoday\b|\bday\b|\bmonth\b|\byear\b|\bweek\b", q):
        return (f"📅 Today is **{now.strftime('%A, %B %d, %Y')}**\n"
                f"Week {now.isocalendar()[1]} of {now.year}")

    # Calculator
    expr_match = re.search(r"([\d\.\+\-\*\/\(\)\%\^]+)", query.replace("×","*").replace("÷","/").replace("^","**"))
    if expr_match and re.search(r"calcul|compute|=|\bwhat is\b|\bsolve\b|\bhow much\b|\bmath\b", q):
        try:
            expr = expr_match.group(1).replace("^","**")
            result = eval(expr, {"__builtins__": {}}, {
                "sin": math.sin, "cos": math.cos, "tan": math.tan,
                "sqrt": math.sqrt, "log": math.log, "pi": math.pi, "e": math.e,
                "abs": abs, "round": round,
            })
            return f"🔢 **{expr_match.group(1)} = {round(result, 10)}**"
        except Exception:
            pass

    # System info
    if re.search(r"\bcpu\b|\bram\b|\bmemory\b|\bdisk\b|\bstorage\b|\bsystem\b|\bbattery\b|\bpc\b", q):
        info = get_system_info()
        return (f"💻 **System Info**\n"
                f"- Platform: {info['platform']} ({info['hostname']})\n"
                f"- Date/Time: {info['date']} {info['time']}\n"
                f"- CPU usage: {info['cpu']}%\n"
                f"- RAM: {info['ram']}% used ({info['ram_used']} / {info['ram_total']} GB)\n"
                f"- Disk: {info['disk']}% used\n"
                f"- Battery: {info['battery']}")

    return None  # fallback to LLM


# ─── LLM ──────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are JARVIS, an intelligent local AI desktop assistant running on the user's personal computer.

Capabilities:
- Answer any question or task using your knowledge
- When given web search results, use them to give current, accurate answers
- Remember information across conversations using your memory
- Help with coding, writing, analysis, calculations, and creative tasks
- Control the user's desktop when asked (take screenshots, open apps)
- Learn from the user and adapt to their preferences

Personality:
- Efficient, smart, and proactive
- Give direct answers without unnecessary filler
- Format responses in clean Markdown when it helps readability
- If you learn something important about the user, note it so you can remember it

{memory_context}
"""


def build_messages(user_msg: str, search_results=None, include_history: bool = True):
    prefs   = load_prefs()
    mem_ctx = memory_context()
    sys_msg = SYSTEM_PROMPT.format(memory_context=mem_ctx)

    msgs = [{"role": "system", "content": sys_msg}]

    if include_history:
        history = load_recent(prefs.get("memory_turns", 20))
        msgs.extend(history)

    # Inject search results
    if search_results:
        ctx = "Here are current web search results for this query:\n\n"
        for i, r in enumerate(search_results, 1):
            ctx += f"{i}. **{r.get('title','')}**\n{r.get('body','')}\nSource: {r.get('href','')}\n\n"
        ctx += f"\nUser's question: {user_msg}"
        msgs.append({"role": "user", "content": ctx})
    else:
        msgs.append({"role": "user", "content": user_msg})

    return msgs


def chat_ollama_stream(messages: list, model: str):
    """Yield streamed response tokens from Ollama."""
    try:
        with requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={"model": model, "messages": messages, "stream": True},
            stream=True, timeout=180
        ) as resp:
            for line in resp.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        token = data.get("message", {}).get("content", "")
                        if token:
                            yield token
                        if data.get("done"):
                            break
                    except Exception:
                        pass
    except Exception as e:
        yield f"\n\n⚠️ Ollama error: {e}. Make sure Ollama is running (`ollama serve`)."


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    online         = check_internet()
    ollama_ok, mods = check_ollama()
    prefs          = load_prefs()
    info           = get_system_info()
    return jsonify({
        "internet": online,
        "ollama"  : ollama_ok,
        "models"  : mods,
        "current_model": prefs.get("model", DEFAULT_MODEL),
        "system"  : info,
        "memory_count": sum(1 for _ in open(CONV_FILE) if CONV_FILE.exists()) if CONV_FILE.exists() else 0,
        "facts_count" : len(load_facts()),
    })


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data  = request.json
    query = data.get("message", "").strip()
    if not query:
        return jsonify({"error": "Empty message"}), 400

    prefs = load_prefs()
    model = prefs.get("model", DEFAULT_MODEL)
    online = check_internet()
    ollama_ok, _ = check_ollama()

    # Save user turn
    save_turn("user", query)

    def generate():
        full_response = []

        # 1. Try offline shortcut first
        offline_resp = handle_offline(query)
        if offline_resp and not re.search(r"\bsearch\b|\bweb\b|\binternet\b|\bnews\b|\bweather\b|\blatest\b|\bcurrent\b|\bstock\b", query.lower()):
            save_turn("assistant", offline_resp)
            yield offline_resp
            return

        # 2. Web search if online and query needs current info
        search_results = None
        needs_web = online and re.search(
            r"\bsearch\b|\bweb\b|\bnews\b|\bweather\b|\blatest\b|\bcurrent\b|\bstock\b|\bwho is\b|\bwhat is the\b|\bhow to\b|\bprice\b|\bwhen did\b|\bwhere is\b|\brecipe\b",
            query.lower()
        )
        if needs_web:
            yield "🔍 *Searching the web...*\n\n"
            # Check weather shortcut
            weather_m = re.search(r"weather (?:in |for |at )?(.+)", query, re.I)
            if weather_m:
                w = get_weather(weather_m.group(1))
                search_results = [{"title": "Weather", "body": w, "href": ""}]
            else:
                search_results = web_search(query)

        # 3. If Ollama is running, use it
        if ollama_ok:
            msgs = build_messages(query, search_results)
            for token in chat_ollama_stream(msgs, model):
                full_response.append(token)
                yield token
        else:
            # Offline fallback: handle basic queries without LLM
            if offline_resp:
                full_response.append(offline_resp)
                yield offline_resp
            elif search_results:
                resp = "Here's what I found online:\n\n"
                for r in search_results[:3]:
                    resp += f"**{r.get('title','')}**\n{r.get('body','')}\n\n"
                full_response.append(resp)
                yield resp
            else:
                msg = ("⚠️ **Ollama is not running.**\n\n"
                       "To enable full AI capabilities:\n"
                       "1. Install Ollama: https://ollama.com\n"
                       "2. Run: `ollama serve`\n"
                       "3. Pull a model: `ollama pull llama3.2`\n\n"
                       "I can still help with **time, date, calculations, and system info** while offline.")
                full_response.append(msg)
                yield msg

        if full_response:
            save_turn("assistant", "".join(full_response))

    return Response(stream_with_context(generate()), content_type="text/plain; charset=utf-8")


@app.route("/api/screenshot", methods=["POST"])
def api_screenshot():
    b64 = take_screenshot()
    if b64:
        return jsonify({"image": b64})
    return jsonify({"error": "Screenshot failed. Make sure pyautogui is installed."}), 500


@app.route("/api/system")
def api_system():
    return jsonify(get_system_info())


@app.route("/api/memory", methods=["GET"])
def api_memory():
    history = load_recent(50)
    facts   = load_facts()
    return jsonify({"history": history, "facts": facts})


@app.route("/api/memory/clear", methods=["POST"])
def api_memory_clear():
    if CONV_FILE.exists():
        CONV_FILE.write_text("")
    return jsonify({"ok": True})


@app.route("/api/learn", methods=["POST"])
def api_learn():
    data = request.json
    save_fact(data.get("key",""), data.get("value",""))
    return jsonify({"ok": True})


@app.route("/api/prefs", methods=["GET","POST"])
def api_prefs():
    if request.method == "POST":
        prefs = load_prefs()
        prefs.update(request.json)
        save_prefs(prefs)
        return jsonify({"ok": True})
    return jsonify(load_prefs())


@app.route("/api/open", methods=["POST"])
def api_open():
    """Open a file or URL on the desktop."""
    target = request.json.get("target","")
    try:
        if target.startswith("http"):
            webbrowser.open(target)
        else:
            if platform.system() == "Windows":
                os.startfile(target)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", target])
            else:
                subprocess.Popen(["xdg-open", target])
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/execute", methods=["POST"])
def api_execute():
    """Run a shell command (user-initiated only)."""
    cmd = request.json.get("command","")
    if not cmd:
        return jsonify({"error": "No command"}), 400
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        return jsonify({"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/models", methods=["GET"])
def api_models():
    _, models = check_ollama()
    return jsonify({"models": models})


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = 7777
    print(f"""
╔══════════════════════════════════════╗
║   JARVIS — Local AI Desktop          ║
║   http://localhost:{port}              ║
╚══════════════════════════════════════╝
""")
    # Auto-open browser
    threading.Timer(1.2, lambda: webbrowser.open(f"http://localhost:{port}")).start()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
