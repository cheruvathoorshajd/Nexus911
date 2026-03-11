"""Nexus911 — FastAPI Application."""
import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from core.config import settings
from core.incident_graph import incident_manager
from api.routes import router
from fastapi.staticfiles import StaticFiles
from pathlib import Path


logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("nexus911")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Nexus911 v1.0.0")
    yield
    logger.info("Shutting down Nexus911")


app = FastAPI(
    title="Nexus911",
    description="Multi-Agent Emergency Coordination System powered by Gemini Live API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    await websocket.accept()
    incident_manager.add_listener(websocket)
    logger.info("Dashboard client connected")
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "get_all_incidents":
                incidents = {iid: inc.to_dict() for iid, inc in incident_manager.incidents.items()}
                await websocket.send_text(
                    json.dumps({"type": "all_incidents", "data": incidents}, default=str)
                )
    except WebSocketDisconnect:
        incident_manager.remove_listener(websocket)
        logger.info("Dashboard client disconnected")


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "active_incidents": len(incident_manager.get_active_incidents()),
    }


FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


@app.get("/", response_class=HTMLResponse)
async def root():
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
    return HTMLResponse(
        content="<h1>Nexus911</h1><p>Frontend not found. Place your React build in /frontend/index.html</p>"
    )
