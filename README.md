<div align="center">
  <img src="https://raw.githubusercontent.com/HarshChoudhary2003/Email-Triage/main/server/static/favicon.ico" alt="Logo" width="80" height="80">

  # 📧 Email Triage OpenEnv
  
  **An OpenEnv-compliant reinforcement learning environment for training AI models and agents on real-world enterprise email triage tasks.**
  
  [![OpenEnv Compliant](https://img.shields.io/badge/OpenEnv-Compliant-success?style=for-the-badge&logo=openai)](https://github.com/techharsh/email-triage-openenv)
  [![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
  [![MCP Ready](https://img.shields.io/badge/MCP-Ready-7c3aed?style=for-the-badge)](#mcp-integration)

  *A robust, interactive AI Sandbox with built-in Agent Chain-of-Thought, beautiful Glassmorphism UI, and Model Context Protocol (MCP) integrations.*
</div>

---

## 🌟 Why Email Triage?

Every modern professional receives over 100+ emails daily. Effective triage — deciding what is urgent, what requires a direct reply, and what can securely wait — is an exponentially high-value productivity skill. 

This environment models triage with **realistic synthetic emails**, dense reward signals, and **advanced agent metrics**. It provides the perfect testing ground for autonomous agents aiming to replicate executive assistant decision-making.

---

## 🏆 Hackathon Winning Features

| Feature | Description |
|---|---|
| **🧠 Agent Chain of Thought** | Native inference uses advanced prompt engineering to enforce a `reasoning` thought-process from the LLM, guaranteeing deeply accurate inferences and transparent action logs. |
| **✨ Auto-Triage Demo Mode** | A zero-click presentation mode located in the dashboard that simulates automatic AI agent decisions live in front of observers. |
| **🎨 2026 Glassmorphism UI** | A completely custom-built, stunning Web Dashboard featuring animated SVG rings, interactive reward history charts, glowing orbs, and fluid CSS transitions. |
| **🔌 MCP Full Support** | The environment natively acts as a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server via the `/mcp` endpoint, unlocking interaction with modern agent ecosystems. |

---

## 🎯 Environment Tasks & Complexity

The environment scales from basic binary classification to complex multi-dimensional triage.

| Task ID | Level | Mails | Objective |
|---------|-------|-------|-----------|
| `task_1_binary_triage` | Easy | 5 | Classify as actionable vs not_actionable |
| `task_2_priority_labeling` | Medium | 6 | Predict 5-class priority + reply detection |
| `task_3_full_triage` | Hard | 15 | Complete triage: Label + Category + Reply required + Action Summary string generation |

<details>
<summary><b>🔍 View State & Observation Specs</b></summary>

### Action Space Schema
```json
{
  "reasoning": "Step-by-step logic detailing why this is urgent...",
  "binary_label": "actionable | not_actionable",
  "priority_label": "urgent | high | medium | low | spam",
  "requires_reply": true,
  "category": "incident | security | hr | personal ...",
  "action_summary": "Short 1-sentence action item",
  "skip": false
}
```

### Observation Space
The environment tracks the entire state machine:
```json
{
  "task_id": "task_3_full_triage",
  "current_email": {
    "id": "e_015",
    "subject": "URGENT: Database deadlock on primary instance",
    "sender": "ops-alerts@company.com",
    "body": "...",
    "timestamp": "2024-03-12T09:30:00Z"
  },
  "emails_remaining": 14,
  "emails_processed": 0,
  "cumulative_score": 0.0,
  "done": false
}
```

</details>

---

## 📈 Reward Function & Evaluation 

The reinforcement learning design provides dense, continuous signals instead of sparse episode-end scoring:
- **Step Reward**: 0.0–1.0 per action. Partial credit is awarded for logically adjacent labels (e.g. labeling `urgent` as `high`).
- **Cumulative Mean**: Running average across the episode drives standard Agent metrics.
- **Skip & False Negative Penalties**: -0.1 penalty for skipping; 0.0 for failing to intercept an `urgent` email appropriately.

---

## 🚀 Setup & Launch

Run the OpenEnv ecosystem locally with Docker or UV.

### 1. Local Quickstart (Python)
```bash
git clone https://github.com/HarshChoudhary2003/Email-Triage
cd Email-Triage
pip install -r requirements.txt

# Bind server to port 7860
python server/app.py
```
> Open `http://localhost:7860` to access the Visual Dashboard Sandbox.

### 2. Auto-eval Baseline Agent
To evaluate against the built-in Chain-of-Thought agent, launch inference:
```bash
export MODEL_NAME="gpt-4o-mini"
export HF_TOKEN="your_key"
python inference.py
```

---

## 📡 API Endpoints

The FastAPI core gracefully handles all OpenEnv validation requirements.

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | `GET` | Serves the interactive Dashboard |
| `/mcp` | `GET` | **MCP Bridge** for Protocol clients |
| `/tasks` | `GET` | Returns task registry schemas |
| `/reset` | `POST` | Resets observation session state |
| `/step` | `POST` | Agent execution endpoint |
| `/health` | `GET` | Liveness checks (`{"status": "healthy"}`) |
| `/schema` | `GET` | Returns observation/action JSON Schema |

---

<div align="center">
  <i>Deployed with ❤️ on Hugging Face Spaces for the OpenEnv Hackathon 2026.</i>
</div>
