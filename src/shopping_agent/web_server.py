"""All-in-one demo web server.

Serves:
  - The UCP mock endpoints (re-uses routes from mock_server.app)
  - A static HTML/JS/CSS frontend at /
  - /api/chat — proxies a single shopping-agent turn to Claude
  - /api/chat/reset — clears the agent's conversation history
  - /api/health — quick liveness check used by the frontend's "Run Demo" button

Run with: python -m shopping_agent.web_server
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .agent import ShoppingAgent
from .config import Config
from .mock_server import PRODUCTS, app

WEB_DIR = Path(__file__).parent / "web"

_agent: ShoppingAgent | None = None
_agent_lock = asyncio.Lock()
_agent_error: str | None = None


async def _get_agent() -> ShoppingAgent:
    """Lazily build a single ShoppingAgent instance.

    Initialised on first /api/chat call so the rest of the demo (products,
    cart, checkout) still works without an ANTHROPIC_API_KEY.
    """
    global _agent, _agent_error
    async with _agent_lock:
        if _agent is None:
            try:
                config = Config.load()
            except ValueError as e:
                _agent_error = str(e)
                raise HTTPException(status_code=503, detail=str(e))
            # Point the agent at this same process's UCP routes.
            config.ucp_base_url = "http://localhost:8000"
            _agent = ShoppingAgent(config)
    return _agent


class ChatRequest(BaseModel):
    message: str


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "ucp": "online",
        "products": len(PRODUCTS),
        "agent_configured": _agent is not None or _agent_error is None,
    }


@app.post("/api/chat")
async def chat(req: ChatRequest):
    agent = await _get_agent()
    try:
        reply = await agent.chat(req.message)
    except Exception as e:  # surface upstream errors to the UI
        raise HTTPException(status_code=500, detail=str(e))
    return {"reply": reply}


@app.post("/api/chat/reset")
async def reset_chat():
    if _agent is not None:
        _agent.messages.clear()
    return {"status": "cleared"}


# Static assets live under /static/*; index.html is served at /.
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@app.get("/")
def index():
    index_path = WEB_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend assets not found")
    return FileResponse(index_path)


def run():
    import uvicorn

    print("Starting Shopping Agent Web Demo on http://localhost:8000")
    print("Open http://localhost:8000 in your browser.")
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run()
