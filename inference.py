"""
Baseline inference script for Email Triage OpenEnv.
Uses OpenAI client against a compatible LLM endpoint.

Required env vars:
  API_BASE_URL  - LLM API endpoint
  MODEL_NAME    - model identifier
  HF_TOKEN      - Hugging Face / API key

Usage:
  python inference.py
"""

import os
import json
import time
import sys
from openai import OpenAI

# ─── Environment setup ───────────────────────────────────────────────────────
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.environ.get("HF_TOKEN", os.environ.get("OPENAI_API_KEY", ""))

if not HF_TOKEN:
    print("[WARN] HF_TOKEN or OPENAI_API_KEY not set — proceeding with empty token.", file=sys.stderr)

client = OpenAI(api_key=HF_TOKEN, base_url=API_BASE_URL)

# ─── Import environment ───────────────────────────────────────────────────────
from env import EmailTriageEnv, Action
from env.tasks import TASKS

TASKS_TO_RUN = list(TASKS.keys())


def build_prompt_task1(obs_dict: dict) -> str:
    email = obs_dict.get("current_email", {})
    return f"""You are an email triage assistant. Classify the following email.

Email:
Subject: {email.get('subject', '')}
From: {email.get('sender', '')}
Body: {email.get('body', '')}

Task: {obs_dict.get('task_description', '')}

Respond with a JSON object containing:
- "binary_label": either "actionable" or "not_actionable"

Only output valid JSON. Example: {{"binary_label": "actionable"}}"""


def build_prompt_task2(obs_dict: dict) -> str:
    email = obs_dict.get("current_email", {})
    return f"""You are an email triage assistant. Label the priority of this email.

Email:
Subject: {email.get('subject', '')}
From: {email.get('sender', '')}
Body: {email.get('body', '')}

Task: {obs_dict.get('task_description', '')}

Valid priority labels: urgent, high, medium, low, spam

Respond with a JSON object:
- "priority_label": one of [urgent, high, medium, low, spam]
- "requires_reply": true or false

Only output valid JSON. Example: {{"priority_label": "high", "requires_reply": true}}"""


def build_prompt_task3(obs_dict: dict) -> str:
    email = obs_dict.get("current_email", {})
    return f"""You are a professional email triage assistant. Fully triage this email.

Email:
Subject: {email.get('subject', '')}
From: {email.get('sender', '')}
Body: {email.get('body', '')}

Task: {obs_dict.get('task_description', '')}

Valid priority labels: urgent, high, medium, low, spam
Valid categories: incident, security, customer_complaint, approval, scheduling, task, newsletter, admin, spam, hr, personal, legal

Respond ONLY with a JSON object:
{{
  "priority_label": "<label>",
  "category": "<category>",
  "requires_reply": <true|false>,
  "action_summary": "<one sentence describing what action to take>"
}}"""


PROMPT_BUILDERS = {
    "task_1_binary_triage": build_prompt_task1,
    "task_2_priority_labeling": build_prompt_task2,
    "task_3_full_triage": build_prompt_task3,
}


def _fallback_action() -> dict:
    """Safe default action used when LLM call fails."""
    return {
        "binary_label": "not_actionable",
        "priority_label": "medium",
        "requires_reply": False,
        "category": "admin",
        "action_summary": "Review and handle as appropriate.",
        "skip": False,
    }


def call_llm(prompt: str, task_id: str) -> dict:
    """Call LLM and parse JSON response."""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are an expert email triage assistant. Always respond with valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=300,
        )
        content = response.choices[0].message.content.strip()
        # Strip markdown fences if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content.strip())
    except json.JSONDecodeError as e:
        print(f"  [WARN] JSON parse error: {e}", file=sys.stderr)
        return _fallback_action()
    except Exception as e:
        print(f"  [ERROR] LLM call failed: {e}", file=sys.stderr)
        return _fallback_action()


def run_task(task_id: str) -> float:
    """Run one task and return final score. Emits required log format."""
    env = EmailTriageEnv(task_id=task_id)
    obs = env.reset()
    obs_dict = obs.model_dump()

    prompt_builder = PROMPT_BUILDERS[task_id]
    task_info = TASKS[task_id]

    # ── [START] log ──────────────────────────────────────────────────────────
    print(
        f"[START] task={task_id} model={MODEL_NAME}"
        f" difficulty={task_info['difficulty']} total_emails={obs_dict['total_emails']}",
        flush=True,
    )

    step_num = 0
    all_rewards = []

    while not obs_dict["done"]:
        if obs_dict["current_email"] is None:
            break

        prompt = prompt_builder(obs_dict)
        action_dict = call_llm(prompt, task_id)
        # Only pass fields that the model returned; let Action defaults handle the rest
        valid_fields = {k: v for k, v in action_dict.items() if k in Action.model_fields and v is not None}
        action = Action(**valid_fields)

        obs, reward, done, info = env.step(action)
        obs_dict = obs.model_dump()
        reward_dict = reward.model_dump()
        all_rewards.append(reward_dict["step_reward"])

        # ── [STEP] log ───────────────────────────────────────────────────────
        print(
            f"[STEP] step={step_num}"
            f" reward={reward_dict['step_reward']}"
            f" cumulative_reward={reward_dict['cumulative_reward']}"
            f" done={done}"
            f" email_id={info.get('email_id')}",
            flush=True,
        )

        step_num += 1
        if done:
            break

    final_score = env.get_final_score()

    # ── [END] log ────────────────────────────────────────────────────────────
    print(
        f"[END] task={task_id} score={final_score}"
        f" steps={step_num} model={MODEL_NAME}"
        f" difficulty={task_info['difficulty']}",
        flush=True,
    )

    return final_score


def main():
    print(f"# Email Triage OpenEnv - Baseline Inference", flush=True)
    print(f"# Model: {MODEL_NAME}", flush=True)
    print(f"# Tasks: {TASKS_TO_RUN}", flush=True)
    print(flush=True)

    results = {}
    for task_id in TASKS_TO_RUN:
        score = run_task(task_id)
        results[task_id] = score
        print(flush=True)

    print("# ── FINAL RESULTS ──────────────────────────────────────────", flush=True)
    for task_id, score in results.items():
        task_name = TASKS[task_id]["name"]
        print(f"# {task_name}: {score:.3f}", flush=True)

    overall = sum(results.values()) / len(results)
    print(f"# Overall average score: {overall:.3f}", flush=True)

    return results


if __name__ == "__main__":
    main()
