"""
FastAPI server exposing the Email Triage OpenEnv environment.
Deployed on Hugging Face Spaces.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn

import sys
import os
# Ensure the parent directory is in sys.path so 'env' module is found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env import EmailTriageEnv, Action
from env.tasks import TASKS

app = FastAPI(
    title="Email Triage OpenEnv",
    description="An OpenEnv-compliant environment for training AI agents on email triage tasks.",
    version="1.0.0",
)

# In-memory session store (single-session for HF Spaces demo)
_sessions: Dict[str, EmailTriageEnv] = {}


class ResetRequest(BaseModel):
    task_id: str = "task_1_binary_triage"
    session_id: str = "default"


class StepRequest(BaseModel):
    session_id: str = "default"
    action: Dict[str, Any]


@app.get("/")
def root():
    return {
        "name": "email-triage-openenv",
        "version": "1.0.0",
        "tasks": list(TASKS.keys()),
        "endpoints": ["/reset", "/step", "/state", "/health", "/tasks"],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks():
    return {
        task_id: {
            "name": cfg["name"],
            "description": cfg["description"],
            "difficulty": cfg["difficulty"],
            "num_emails": len(cfg["emails"]),
            "max_steps": cfg["max_steps"],
            "success_threshold": cfg.get("success_threshold", 0.0),
        }
        for task_id, cfg in TASKS.items()
    }


@app.post("/reset")
def reset(req: Optional[ResetRequest] = None):
    # Fallback to defaults if body is missing
    r = req or ResetRequest()
    
    if r.task_id not in TASKS:
        raise HTTPException(status_code=400, detail=f"Unknown task_id: {r.task_id}")

    env = EmailTriageEnv(task_id=r.task_id)
    _sessions[r.session_id] = env
    obs = env.reset()

    return {
        "observation": obs.model_dump(),
        "session_id": r.session_id,
        "task_id": r.task_id,
    }


@app.post("/step")
def step(req: StepRequest):
    env = _sessions.get(req.session_id)
    if env is None:
        raise HTTPException(status_code=400, detail=f"No session '{req.session_id}'. Call /reset first.")

    try:
        action = Action(**req.action)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid action: {e}")

    try:
        obs, reward, done, info = env.step(action)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "observation": obs.model_dump(),
        "reward": reward.model_dump(),
        "done": done,
        "info": info,
    }


@app.get("/state")
def get_state(session_id: str = "default"):
    env = _sessions.get(session_id)
    if env is None:
        raise HTTPException(status_code=400, detail=f"No session '{session_id}'. Call /reset first.")
    return env.state().model_dump()


@app.get("/score")
def get_score(session_id: str = "default"):
    env = _sessions.get(session_id)
    if env is None:
        raise HTTPException(status_code=400, detail=f"No session '{session_id}'. Call /reset first.")
    return {
        "session_id": session_id,
        "final_score": env.get_final_score(),
        "step_count": env.state().step_count,
    }


def start():
    """Entry point for the openenv-server script."""
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860, reload=True)


if __name__ == "__main__":
    start()
