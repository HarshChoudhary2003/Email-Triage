# 📧 Email Triage OpenEnv

An **OpenEnv-compliant** reinforcement learning environment for training AI agents on real-world **email triage** tasks — one of the most universal and high-value productivity challenges in enterprise AI.

## Why Email Triage?

Every professional receives 100+ emails daily. Effective triage — deciding what's urgent, what needs a reply, and what can wait — is a high-value skill that AI agents can genuinely augment. This environment models that task with realistic emails and nuanced reward signals.

## Environment Overview

The agent receives emails one at a time and must triage them by:
- **Priority**: urgent / high / medium / low / spam
- **Category**: incident, security, customer_complaint, scheduling, etc.
- **Action**: whether a reply is required
- **Summary**: a one-sentence action description

Reward is given per email with partial credit for adjacent priority levels, creating a dense, informative signal throughout the episode.

## Tasks

| Task | Difficulty | Emails | Description |
|------|-----------|--------|-------------|
| `task_1_binary_triage` | Easy | 5 | Classify as actionable vs not_actionable |
| `task_2_priority_labeling` | Medium | 6 | 5-class priority + reply detection |
| `task_3_full_triage` | Hard | 15 | Full triage: label + category + reply + summary |

## Action Space

```json
{
  "binary_label": "actionable | not_actionable",
  "priority_label": "urgent | high | medium | low | spam",
  "requires_reply": true,
  "category": "incident | security | customer_complaint | ...",
  "action_summary": "One sentence describing what to do",
  "skip": false
}
```

## Observation Space

```json
{
  "task_id": "task_1_binary_triage",
  "task_description": "...",
  "current_email": {
    "id": "e001",
    "subject": "URGENT: Production server down",
    "sender": "ops@company.com",
    "body": "...",
    "timestamp": "2024-01-15T09:30:00Z"
  },
  "emails_remaining": 4,
  "emails_processed": 1,
  "total_emails": 5,
  "cumulative_score": 0.8,
  "done": false,
  "valid_labels": ["urgent", "high", "medium", "low", "spam"],
  "valid_categories": ["incident", "security", ...]
}
```

## Reward Function

- **Step reward**: 0.0–1.0 per email, with partial credit for adjacent labels
- **Cumulative reward**: running mean across episode
- **Skip penalty**: 0.1 reward for skipping an email
- **False negative penalty**: missing an urgent email scores 0.0
- **Dense signal**: every step has a meaningful reward

## Setup & Usage

### Local Development

```bash
git clone <repo-url>
cd email-triage-openenv
pip install -r requirements.txt

# Start the API server
python app.py
```

### Docker

```bash
docker build -t email-triage-openenv .
docker run -p 7860:7860 \
  -e API_BASE_URL=https://api.openai.com/v1 \
  -e MODEL_NAME=gpt-4o-mini \
  -e HF_TOKEN=your_key \
  email-triage-openenv
```

### Run Baseline Inference

```bash
export API_BASE_URL=https://api.openai.com/v1
export MODEL_NAME=gpt-4o-mini
export HF_TOKEN=your_openai_key

python inference.py
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Environment info |
| GET | `/health` | Health check |
| GET | `/tasks` | List available tasks |
| POST | `/reset` | Reset environment for a task |
| POST | `/step` | Take an action |
| GET | `/state` | Current environment state |
| GET | `/score` | Final score for session |

### Example: Run via API

```python
import requests

BASE = "http://localhost:7860"

# Start a new episode
obs = requests.post(f"{BASE}/reset", json={
    "task_id": "task_1_binary_triage",
    "session_id": "my_agent"
}).json()

# Step through emails
while not obs["observation"]["done"]:
    action = {"binary_label": "actionable"}  # Your agent's decision
    result = requests.post(f"{BASE}/step", json={
        "session_id": "my_agent",
        "action": action
    }).json()
    obs = result
    print(f"Reward: {result['reward']['step_reward']}")
```

## Baseline Scores

| Task | GPT-4o-mini Score |
|------|------------------|
| task_1_binary_triage (Easy) | ~0.85 |
| task_2_priority_labeling (Medium) | ~0.72 |
| task_3_full_triage (Hard) | ~0.61 |
| **Overall Average** | **~0.73** |

## Project Structure

```
email-triage-openenv/
├── openenv.yaml          # OpenEnv spec metadata
├── Dockerfile            # Container definition
├── README.md             # This file
├── inference.py          # Baseline inference script (root-level, required)
├── app.py                # FastAPI server
├── requirements.txt      # Python dependencies
└── env/
    ├── __init__.py
    ├── environment.py    # Core OpenEnv logic (step/reset/state)
    ├── tasks.py          # Task definitions + graders
    └── data.py           # Synthetic email dataset (15 emails)
```

## OpenEnv Compliance

- ✅ Typed `Observation`, `Action`, `Reward` Pydantic models
- ✅ `step()` → `(observation, reward, done, info)`
- ✅ `reset()` → initial observation
- ✅ `state()` → current internal state
- ✅ `openenv.yaml` with full metadata
- ✅ 3 tasks with difficulty progression (easy → medium → hard)
- ✅ Reward in [0.0, 1.0] range
- ✅ Dense reward (partial credit, not just binary)
- ✅ Baseline `inference.py` with `[START]`/`[STEP]`/`[END]` logging
- ✅ Dockerfile works with `docker build && docker run`
- ✅ Deploys to Hugging Face Spaces on port 7860
