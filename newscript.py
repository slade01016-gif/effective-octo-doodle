from flask import Flask, request, Response, send_from_directory
import requests, json, itertools

app = Flask(__name__)

# ══ All 10 NVIDIA NIM keys — round-robin rotation ══
NV_KEYS = [
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
]
_key_cycle = itertools.cycle(NV_KEYS)
def next_key(): return next(_key_cycle)

NIM_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

@app.route("/")
def index():
    return send_from_directory(".", "newchat.html")

@app.route("/chat", methods=["POST"])
def chat():
    body       = request.get_json(force=True)
    model      = body.get("model", "deepseek-ai/deepseek-v3.2").strip()
    messages   = body.get("messages", [])
    max_tokens = int(body.get("max_tokens", 4096))

    headers = {"Authorization": f"Bearer {next_key()}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens, "stream": True}

    def generate():
        try:
            with requests.post(NIM_URL, headers=headers, json=payload, stream=True, timeout=180) as r:
                if not r.ok:
                    err = r.json()
                    yield f"data: {json.dumps({'error': err.get('detail') or str(err)})}\n\n"
                    return
                for line in r.iter_lines():
                    if not line: continue
                    text = line.decode("utf-8") if isinstance(line, bytes) else line
                    text = text.strip()
                    if not text.startswith("data: "): continue
                    payload_str = text[6:]
                    if payload_str == "[DONE]":
                        yield "data: [DONE]\n\n"
                        return
                    try:
                        chunk = json.loads(payload_str)
                        delta = chunk["choices"][0]["delta"].get("content")
                        if delta:
                            yield f"data: {json.dumps({'content': delta})}\n\n"
                    except Exception:
                        continue
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

if __name__ == "__main__":
    print("╔══════════════════════════════════════╗")
    print("║  NewChat — NVIDIA NIM · 10 Keys      ║")
    print("║  Model choosable per message         ║")
    print("║  http://localhost:5001               ║")
    print("╚══════════════════════════════════════╝")
    app.run(debug=True, port=5001)
