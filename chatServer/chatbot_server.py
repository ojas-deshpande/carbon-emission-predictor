"""
chatbot_server.py
─────────────────
Zero-dependency local server using Google Gemini Flash API (FREE).

  • Serves index.html at http://localhost:5500
  • Proxies /chat  →  Google Gemini Flash API
  • Keeps your API key server-side (never in the browser)

Why Gemini Flash?
  • Completely FREE — no credit card needed
  • 1,500 requests per day free
  • 1 million tokens per minute free
  • Get key at: https://aistudio.google.com

Usage:
    python chatbot_server.py                         # prompts for API key
    python chatbot_server.py --key AIzaSy...         # pass key directly
    GEMINI_API_KEY=AIzaSy... python chatbot_server.py  # environment variable

Then open: http://localhost:5500
"""

import json
import os
import sys
import argparse
from dotenv import load_dotenv
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

# ── Gemini model to use ────────────────────────────────────────────────────────
# gemini-2.0-flash → Latest stable, free tier, fast
# gemini-2.0-flash-lite → Even lighter/faster free option
GEMINI_MODEL  = "gemini-2.5-flash"
GEMINI_URL    = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
PORT          = 5500

# Resolve paths relative to this script's directory
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_INDEX_HTML = os.path.join(_SCRIPT_DIR, '..', 'frontend', 'index.html')


# ── Resolve API key ────────────────────────────────────────────────────────────
def resolve_api_key() -> str:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--key", default="")
    args, _ = parser.parse_known_args()

    load_dotenv(os.path.join(_SCRIPT_DIR, '..', '.env'))
    key = args.key or os.environ.get("GEMINI_API_KEY", "")
    if not key:
        print("+----------------------------------------------------------+")
        print("|   Carbon Dashboard - AI Chat Server (Gemini Flash)      |")
        print("+----------------------------------------------------------+")
        print()
        print("  Using Google Gemini Flash -- FREE API")
        print("  Get your free key at: https://aistudio.google.com")
        print("  Click 'Get API Key' -> 'Create API Key'")
        print()
        key = input("  Paste your Gemini API Key (AIzaSy...): ").strip()
        if not key:
            print("\n  No API key provided. Exiting.")
            sys.exit(1)
    return key


API_KEY = resolve_api_key()


# ── Convert Anthropic message format → Gemini format ──────────────────────────
def convert_to_gemini(body: dict) -> dict:
    """
    The frontend sends Anthropic-style messages:
    {
        "system": "You are a climate analyst...",
        "messages": [
            {"role": "user",      "content": "Which country emits most?"},
            {"role": "assistant", "content": "China emits the most..."},
            {"role": "user",      "content": "What about India?"}
        ]
    }

    Gemini expects:
    {
        "systemInstruction": { "parts": [{"text": "..."}] },
        "contents": [
            {"role": "user",  "parts": [{"text": "..."}]},
            {"role": "model", "parts": [{"text": "..."}]},
            {"role": "user",  "parts": [{"text": "..."}]}
        ],
        "generationConfig": { "maxOutputTokens": 1024 }
    }

    Key difference: Gemini uses "model" instead of "assistant"
    """

    # Convert messages
    contents = []
    for msg in body.get("messages", []):
        role    = msg["role"]
        content = msg["content"]

        # Gemini uses "model" not "assistant"
        gemini_role = "model" if role == "assistant" else "user"

        contents.append({
            "role":  gemini_role,
            "parts": [{"text": content}]
        })

    gemini_body = {
        "contents": contents,
        "generationConfig": {
            "maxOutputTokens": body.get("max_tokens", 1024),
            "temperature":     0.7,
        }
    }

    # Add system instruction if present
    system_text = body.get("system", "")
    if system_text:
        gemini_body["systemInstruction"] = {
            "parts": [{"text": system_text}]
        }

    return gemini_body


# ── Convert Gemini response → Anthropic response format ───────────────────────
def convert_from_gemini(gemini_response: dict) -> dict:
    """
    Gemini response:
    {
        "candidates": [{
            "content": {
                "parts": [{"text": "China emits the most..."}],
                "role": "model"
            }
        }]
    }

    We convert to Anthropic-style so the frontend works without changes:
    {
        "content": [{"type": "text", "text": "China emits the most..."}]
    }
    """

    try:
        text = gemini_response["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        # Handle blocked or empty response
        finish_reason = ""
        try:
            finish_reason = gemini_response["candidates"][0].get("finishReason", "")
        except (KeyError, IndexError):
            pass

        if finish_reason == "SAFETY":
            text = "I cannot respond to that question due to safety guidelines."
        else:
            text = "Sorry, I could not generate a response. Please try again."

    return {
        "content": [{"type": "text", "text": text}]
    }


# ── HTTP Request Handler ───────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass  # Suppress noisy default logs

    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors()
        self.end_headers()

    # ── GET ──────────────────────────────────────────────────────────────────
    def do_GET(self):
        path = self.path.split("?")[0]

        # Keep dashboard access behind Flask-Login. The chat server only
        # exposes AI endpoints; opening it in a browser sends users to Flask.
        if path in ("/", "/index.html"):
            self.send_response(302)
            self.send_header("Location", "http://localhost:5000/login?next=/")
            self.end_headers()
            return

        # Health check — dashboard uses this to show online/offline dot
        if path == "/ping":
            self._send_json({
                "status": "ok",
                "server": "carbon-chatbot",
                "model":  GEMINI_MODEL,
                "provider": "Google Gemini"
            })
            return

        self._send_json({"error": f"Not found: {path}"}, status=404)

    # ── POST ─────────────────────────────────────────────────────────────────
    def do_POST(self):
        if self.path == "/chat":
            length   = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(length) if length else b"{}"

            try:
                body = json.loads(raw_body)
            except json.JSONDecodeError:
                self._send_json({"error": "Invalid JSON"}, status=400)
                return

            # Convert Anthropic format → Gemini format
            gemini_body = convert_to_gemini(body)

            # Call Gemini API
            url = f"{GEMINI_URL}?key={API_KEY}"
            req = urllib.request.Request(
                url,
                data=json.dumps(gemini_body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    gemini_response = json.loads(resp.read())

                # Convert Gemini response → Anthropic format for frontend
                result = convert_from_gemini(gemini_response)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_cors()
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                print("  [OK] Chat OK -- Gemini Flash responded")

            except urllib.error.HTTPError as e:
                err_body = e.read().decode()
                print(f"  [ERROR] Gemini API error {e.code}: {err_body[:300]}")

                if e.code == 400:
                    msg = f"Bad request — check your message format. Details: {err_body[:200]}"
                elif e.code == 403:
                    msg = "Invalid API key. Get a free key at https://aistudio.google.com"
                elif e.code == 429:
                    try:
                        err_json = json.loads(err_body)
                        api_msg = err_json.get("error", {}).get("message", err_body[:200])
                    except:
                        api_msg = err_body[:200]
                    msg = f"Rate limit hit: {api_msg}"
                else:
                    msg = f"Gemini API error {e.code}: {err_body}"

                self._send_json({"error": msg}, status=e.code)

            except urllib.error.URLError as e:
                print(f"  [ERROR] Network error: {e}")
                self._send_json(
                    {"error": "Cannot reach Gemini API. Check your internet connection."},
                    status=503
                )

            except Exception as e:
                print(f"  [ERROR] Server error: {e}")
                self._send_json({"error": str(e)}, status=500)

            return

        self._send_json({"error": "Unknown endpoint"}, status=404)

    # ── Helper ───────────────────────────────────────────────────────────────
    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_cors()
        self.end_headers()
        self.wfile.write(body)


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    server = HTTPServer(("localhost", PORT), Handler)

    print()
    print("+------------------------------------------------------------+")
    print("|   Carbon Dashboard - AI Chat Server                       |")
    print("+------------------------------------------------------------+")
    print()
    print(f"  [OK] Server running at  ->  http://localhost:{PORT}")
    print(f"  [AI] Model              ->  Google {GEMINI_MODEL} (FREE)")
    print("  [DB] Dashboard          ->  http://localhost:5000/login")
    print()
    print("  Keep this server running, then use the Flask dashboard URL above.")
    print("  Go to the AI Chat tab to start chatting.")
    print()
    print("  Press Ctrl+C to stop the server.")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
        server.server_close()
