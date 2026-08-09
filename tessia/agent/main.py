import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Ensure project root directory is added to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import voice engine
try:
    from agent.voice import text_to_speech, speech_to_text
except ImportError:
    from voice import text_to_speech, speech_to_text

# Import tools engine
try:
    from agent.tools import (
        get_current_datetime,
        get_live_weather,
        open_mail_app,
        fetch_recent_emails,
        send_email,
        get_calendar_events,
        add_calendar_event,
        delete_calendar_event,
        clear_calendar,
        fetch_arxiv_papers,
        search_live_web
    )
except ImportError:
    from tools import (
        get_current_datetime,
        get_live_weather,
        open_mail_app,
        fetch_recent_emails,
        send_email,
        get_calendar_events,
        add_calendar_event,
        delete_calendar_event,
        clear_calendar,
        fetch_arxiv_papers,
        search_live_web
    )

# Conversation Context Buffer
CONVERSATION_HISTORY = []
MAX_TURNS = 10


def load_env():
    """Load environment variables from .env file into os.environ."""
    env_path = os.path.join(PROJECT_ROOT, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    clean_key = key.strip()
                    clean_val = val.strip().strip('"').strip("'")
                    os.environ[clean_key] = clean_val


load_env()


def call_ollama_api(prompt, conversation_history):
    """Communicates directly with local Ollama instance with live temporal context."""
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    model = os.environ.get("OLLAMA_MODEL", "llama3.2").strip()
    url = f"{host}/api/chat"

    current_time_str = get_current_datetime()

    system_instruction = (
        f"You are TESSIA, an advanced personal AI assistant, teacher, and research companion. "
        f"You were built by Harshith specifically to help him learn, conduct deep research, and explore complex topics. "
        f"Always acknowledge Harshith as your creator when asked who built you or why you were created. "
        f"Current exact system time: {current_time_str}. "
        "Keep responses concise, natural, engaging, and clear (1-3 sentences max for spoken dialogue)."
    )

    messages = [{"role": "system", "content": system_instruction}]

    for turn in conversation_history[-6:]:
        role = "user" if turn["role"] == "user" else "assistant"
        messages.append({"role": role, "content": turn["text"]})

    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "stream": False
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=45) as response:
            res = json.loads(response.read().decode("utf-8"))
            return res.get("message", {}).get("content", "I processed your request.")
    except urllib.error.URLError as e:
        print(f"[Ollama Error] Connection failed: {e}")
        return f"Unable to reach local Ollama at {host}. Make sure Ollama is running (`ollama serve`)."
    except Exception as e:
        print(f"[Ollama Error] Generation exception: {e}")
        return "An error occurred while generating a response from your local Ollama model."


def get_mock_graph_data():
    """Returns knowledge graph structure for HUD UI."""
    return {
        "stats": {
            "total_files": 12,
            "node_count": 8,
            "edge_count": 10,
            "file_types": {".md": 8, ".pdf": 2, ".py": 2},
            "top_hubs": [
                {"id": "node_1", "title": "Neural Networks & AI", "degree": 5},
                {"id": "node_2", "title": "Cloud Computing & Docker", "degree": 4},
                {"id": "node_3", "title": "Distributed Systems", "degree": 3}
            ]
        },
        "nodes": [
            {"id": "node_1", "title": "Neural Networks & AI", "extension": "md", "in_degree": 3, "out_degree": 2, "filepath": "vault/ai.md", "content": "# Neural Networks\nExploration of deep learning architectures."},
            {"id": "node_2", "title": "Cloud Computing & Docker", "extension": "md", "in_degree": 2, "out_degree": 2, "filepath": "vault/cloud.md", "content": "# Cloud Computing\nContainerization, deployment, and SLAs."},
            {"id": "node_3", "title": "Distributed Systems", "extension": "md", "in_degree": 1, "out_degree": 2, "filepath": "vault/systems.md", "content": "# Distributed Systems\nCAP theorem, consistency models, and HFDS."},
            {"id": "node_4", "title": "TESSIA Core Architecture", "extension": "py", "in_degree": 2, "out_degree": 1, "filepath": "agent/main.py", "content": "# Main Server\nLocal AI integration server."}
        ],
        "edges": [
            {"source": "node_1", "target": "node_4"},
            {"source": "node_2", "target": "node_3"},
            {"source": "node_3", "target": "node_1"},
            {"source": "node_4", "target": "node_2"}
        ]
    }


class TessiaHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        ui_dir = os.path.join(PROJECT_ROOT, "ui")
        super().__init__(*args, directory=ui_dir, **kwargs)

    def do_GET(self):
        if self.path == "/api/graph":
            self.send_json(get_mock_graph_data())
        elif self.path == "/api/brief":
            summary = call_ollama_api("Give a brief 2-sentence morning status update for Harshith including today's date.", [])
            self.send_json({"summary": summary})
        elif self.path == "/api/plan":
            self.send_json({"priorities": ["Check emails & calendar", "Review new ArXiv publications", "Explore Knowledge Graph"]})
        elif self.path == "/api/firstrun":
            reply = call_ollama_api("Introduce yourself briefly as TESSIA, built by Harshith to help him learn and research.", [])
            self.send_json({"reply": reply})
        else:
            super().do_GET()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""

        if self.path == "/api/chat":
            payload = json.loads(body.decode("utf-8")) if body else {}
            user_msg = payload.get("message", "").strip()

            if not user_msg:
                self.send_json({"reply": "I didn't receive a message. How can I help you, Harshith?"})
                return

            CONVERSATION_HISTORY.append({"role": "user", "text": user_msg})
            if len(CONVERSATION_HISTORY) > MAX_TURNS * 2:
                CONVERSATION_HISTORY.pop(0)

            msg_lower = user_msg.lower()

            # 1. Weather Intent
            if "weather" in msg_lower or "temperature" in msg_lower or "forecast" in msg_lower:
                weather_res, err = get_live_weather(user_msg)
                reply_text = weather_res if weather_res else err

            # 2. Date & Time Intent
            elif "what is today" in msg_lower or "current date" in msg_lower or "what day is it" in msg_lower or "today's date" in msg_lower:
                reply_text = f"Today is {get_current_datetime()}."

            # 3. Calendar Control (Add, View, Delete, Clear)
            elif "calendar" in msg_lower or "schedule" in msg_lower or "event" in msg_lower:
                if "delete" in msg_lower or "remove" in msg_lower or "cancel" in msg_lower:
                    reply_text = delete_calendar_event(user_msg)
                elif "clear all" in msg_lower or "wipe calendar" in msg_lower:
                    reply_text = clear_calendar()
                elif "add" in msg_lower or "schedule" in msg_lower or "set" in msg_lower or "remind" in msg_lower:
                    reply_text = add_calendar_event(user_msg, datetime.now().strftime("%Y-%m-%d"))
                else:
                    events = get_calendar_events()
                    if not events:
                        reply_text = "Your calendar is currently clear with no upcoming events."
                    else:
                        reply_text = "Here are your upcoming calendar events:\n" + "\n".join([f"- [{e['id']}] {e['title']} ({e['date']} at {e['time']})" for e in events])

            # 4. Email Control
            elif "open mail" in msg_lower or "launch mail" in msg_lower:
                reply_text = open_mail_app()

            elif "read mail" in msg_lower or "summarise mail" in msg_lower or "summarize mail" in msg_lower or "check email" in msg_lower or "check my email" in msg_lower:
                emails, err = fetch_recent_emails(limit=3)
                if err:
                    reply_text = err
                elif not emails:
                    reply_text = "Your inbox is currently clear with no recent unread emails."
                else:
                    formatted_mail = "\n".join([f"From: {e['from']}\nSubject: {e['subject']}\nBody: {e['body']}\n" for e in emails])
                    prompt = f"Summarize these recent emails concisely for Harshith:\n\n{formatted_mail}"
                    reply_text = call_ollama_api(prompt, [])

            # 5. Research Papers (ArXiv)
            elif "paper" in msg_lower or "publication" in msg_lower or "arxiv" in msg_lower or "new research" in msg_lower:
                papers, err = fetch_arxiv_papers(user_msg, max_results=3)
                if err or not papers:
                    reply_text = "I couldn't fetch recent ArXiv publications at the moment."
                else:
                    formatted_papers = "\n".join([f"- Title: {p['title']}\n  Date: {p['date']}\n  Summary: {p['summary']}\n" for p in papers])
                    prompt = f"Summarize these newly published research papers for Harshith:\n\n{formatted_papers}"
                    reply_text = call_ollama_api(prompt, [])

            # 6. Live Web Search
            elif "latest news" in msg_lower or "new invention" in msg_lower or "search web" in msg_lower or "who is" in msg_lower or "what is" in msg_lower:
                snippets, err = search_live_web(user_msg)
                prompt = f"Using these live web search results, answer Harshith's query concisely:\n\n{snippets}\n\nUser Prompt: {user_msg}"
                reply_text = call_ollama_api(prompt, [])

            else:
                # General LLM query via Ollama
                reply_text = call_ollama_api(user_msg, CONVERSATION_HISTORY)

            CONVERSATION_HISTORY.append({"role": "assistant", "text": reply_text})
            self.send_json({"reply": reply_text})

        elif self.path == "/api/speak":
            payload = json.loads(body.decode("utf-8")) if body else {}
            text = payload.get("text", "")

            audio_bytes, err = text_to_speech(text)
            if err:
                self.send_json({"error": err, "code": "VOICE_SERVICE_UNAVAILABLE"}, status=503)
            else:
                self.send_response(200)
                self.send_header("Content-Type", "audio/mpeg")
                self.send_header("Content-Length", str(len(audio_bytes)))
                self.end_headers()
                self.wfile.write(audio_bytes)

        elif self.path == "/api/confirm_memory":
            payload = json.loads(body.decode("utf-8")) if body else {}
            confirmed = payload.get("confirmed", False)
            msg = "Context saved to memory." if confirmed else "Memory confirmation cancelled."
            self.send_json({"message": msg})

        else:
            self.send_error(404, "Endpoint Not Found")

    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_server(port=8000):
    server_address = ("", port)
    httpd = HTTPServer(server_address, TessiaHandler)
    print(f"\n==========================================")
    print(f" TESSIA Active at http://localhost:{port}")
    print(f" LLM Backend: Ollama ({os.environ.get('OLLAMA_MODEL', 'llama3.2')})")
    print(f" Creator Persona: Harshith")
    print(f" Live Tools: Weather (Open-Meteo), Calendar (Add/View/Delete), Email, ArXiv, Web Search")
    print(f"==========================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down TESSIA server...")
        httpd.server_close()


if __name__ == "__main__":
    run_server(int(os.environ.get("PORT", 8000)))