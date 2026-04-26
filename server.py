import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Depends, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session
import socketio
import uvicorn

from database import engine, get_db, Base
import models
from parser import parse
from hardware import HardwareManager
from chain_executor import parse_command_chain, execute_chain_step, get_chain_status, reset_chain
from visualizer import get_workspace_visualization
from speech import get_transcription_service_status

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="OpenGuy Robot Control API")
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio, app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

robot = HardwareManager()

@sio.on('connect')
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    await sio.emit('status_update', robot.get_status(), room=sid)

async def background_status_updater():
    """Background task to push status to all connected clients."""
    while True:
        status = robot.get_status()
        await sio.emit('status_update', status)
        await asyncio.sleep(1.0) # Update 1 time per second

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_status_updater())

@app.post("/api/parse")
async def api_parse(request: Request):
    data = await request.json()
    command_text = data.get("command", "").strip()
    api_key = data.get("api_key", os.getenv("ANTHROPIC_API_KEY"))
    if not command_text:
        raise HTTPException(status_code=400, detail="Empty command")
    try:
        parsed = parse(command_text, use_ai=True)
        return parsed
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parse error: {str(e)}")

@app.post("/api/execute")
async def api_execute(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    action = data.get("action")
    if not action:
        raise HTTPException(status_code=400, detail="No action specified")
    
    try:
        # Run hardware execute in threadpool to prevent blocking the event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: robot.execute(
                action=action,
                direction=data.get("direction"),
                distance_cm=data.get("distance_cm"),
                angle_deg=data.get("angle_deg")
            )
        )
        
        # Save to DB
        db_history = models.CommandHistory(
            raw_command=data.get("raw", "unknown"),
            parsed_json=data,
            result_json=result
        )
        db.add(db_history)
        db.commit()
        db.refresh(db_history)
        
        # Push update immediately
        await sio.emit('status_update', robot.get_status())
        
        return {
            "success": True,
            "result": result,
            "output": format_sim_result(result),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")

def format_sim_result(result: Dict[str, Any]) -> list[str]:
    lines = []
    if "movement" in result: lines.append(f"[MOVE] {result['movement']}")
    if "rotation" in result: lines.append(f"[ROTATE] {result['rotation']}")
    if "gripper" in result: lines.append(f"[GRIP] {result['gripper']}")
    if "status" in result: lines.append(f"[STATUS] {result['status']}")
    return lines

@app.get("/api/status")
async def api_status():
    return robot.get_status()

@app.post("/api/reset")
async def api_reset():
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, robot.reset)
    await sio.emit('status_update', robot.get_status())
    return {"success": True, "message": "Robot reset to initial state"}

@app.get("/api/history")
async def api_history(db: Session = Depends(get_db)):
    history = db.query(models.CommandHistory).order_by(models.CommandHistory.timestamp.desc()).limit(20).all()
    # Format to match old API structure
    return {"history": [{
        "timestamp": h.timestamp.isoformat(),
        "command": h.raw_command,
        "parsed": h.parsed_json,
        "result": h.result_json,
        "is_chain_step": h.is_chain_step
    } for h in reversed(history)]}

@app.post("/api/history/clear")
async def api_history_clear(db: Session = Depends(get_db)):
    db.query(models.CommandHistory).delete()
    db.commit()
    return {"success": True, "message": "History cleared"}

@app.get("/api/health")
async def api_health():
    return {
        "status": "healthy",
        "robot_status": robot.get_status(),
        "timestamp": datetime.now().isoformat(),
    }

@app.post("/api/chain/parse")
async def api_chain_parse(request: Request):
    data = await request.json()
    command_text = data.get("command", "").strip()
    api_key = data.get("api_key", os.getenv("ANTHROPIC_API_KEY"))
    if not command_text:
        raise HTTPException(status_code=400, detail="Empty command")
    try:
        result = parse_command_chain(command_text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chain parse error: {str(e)}")

@app.get("/api/chain/status")
async def api_chain_status_endpoint():
    return get_chain_status()

@app.post("/api/chain/execute")
async def api_chain_execute(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    action = data.get("action")
    if not action:
        raise HTTPException(status_code=400, detail="No action specified")
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: robot.execute(
                action=action,
                direction=data.get("direction"),
                distance_cm=data.get("distance_cm"),
                angle_deg=data.get("angle_deg")
            )
        )
        chain_result = execute_chain_step(result)
        
        db_history = models.CommandHistory(
            raw_command=data.get("raw", "unknown"),
            parsed_json=data,
            result_json=result,
            is_chain_step=True
        )
        db.add(db_history)
        db.commit()
        
        await sio.emit('status_update', robot.get_status())
        
        return {
            "success": True,
            "result": result,
            "output": format_sim_result(result),
            "chain_progress": chain_result["progress"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")

@app.post("/api/chain/reset")
async def api_chain_reset_endpoint():
    reset_chain()
    return {"success": True, "message": "Chain reset"}

@app.get("/api/visualize")
async def api_visualize():
    svg = get_workspace_visualization(robot.get_status())
    return HTMLResponse(content=svg, status_code=200, headers={"Content-Type": "image/svg+xml"})

@app.get("/api/speech/status")
async def api_speech_status_endpoint():
    return get_transcription_service_status()

# Serve Frontend
@app.get("/")
async def serve_frontend():
    return FileResponse("index.html")

# Fallback for SPA routing if needed
@app.get("/{full_path:path}")
async def serve_static(full_path: str):
    return FileResponse("index.html")

if __name__ == "__main__":
    uvicorn.run("server:socket_app", host="0.0.0.0", port=5000, reload=True)
