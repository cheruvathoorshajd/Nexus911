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
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
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
                await websocket.send_text(json.dumps({"type": "all_incidents", "data": incidents}, default=str))
    except WebSocketDisconnect:
        incident_manager.remove_listener(websocket)
        logger.info("Dashboard client disconnected")


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0", "active_incidents": len(incident_manager.get_active_incidents())}


@app.get("/", response_class=HTMLResponse)
async def root():
    return """<html>
    <head><title>Nexus911</title></head>
    <body style="display:flex;justify-content:center;align-items:center;height:100vh;
                 font-family:-apple-system,sans-serif;background:#0a0a0a;color:#fff;">
        <div style="text-align:center">
            <h1 style="font-size:3rem;font-weight:200;">Nexus911</h1>
            <p style="color:#888;">Multi-Agent Emergency Coordination System</p>
            <p style="color:#666;">Powered by Gemini Live API + ADK</p>
            <p><a href="/docs" style="color:#0071e3;">API Documentation &rarr;</a></p>
        </div>
    </body>
    </html>"""
