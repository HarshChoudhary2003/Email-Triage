"""
Email Triage OpenEnv Environment
Implements the full OpenEnv spec: typed Pydantic models, step/reset/state API.
"""

from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field
import copy
import time

from .data import EMAILS, VALID_LABELS, VALID_CATEGORIES
from .tasks import TASKS, GRADERS


# ─── Typed Models (OpenEnv spec) ────────────────────────────────────────────

class Email(BaseModel):
    id: str
    subject: str
    sender: str
    body: str
    timestamp: str


class Observation(BaseModel):
    """What the agent sees at each step."""
    task_id: str
    task_description: str
    current_email: Optional[Email] = None
    emails_remaining: int = 0
    emails_processed: int = 0
    total_emails: int = 0
    last_action_feedback: Optional[str] = None
    cumulative_score: float = 0.0
    done: bool = False
    valid_labels: List[str] = Field(default_factory=lambda: VALID_LABELS)
    valid_categories: List[str] = Field(default_factory=lambda: VALID_CATEGORIES)


class Action(BaseModel):
    """What the agent can do."""
    # Task 1 fields
    binary_label: Optional[str] = None  # "actionable" | "not_actionable"

    # Task 2 fields
    priority_label: Optional[str] = None  # urgent | high | medium | low | spam
    requires_reply: Optional[bool] = None

    # Task 3 additional fields
    category: Optional[str] = None
    action_summary: Optional[str] = None

    # Meta
    skip: bool = False  # Agent can skip an email (penalized)


class Reward(BaseModel):
    """Reward signal for current step."""
    step_reward: float = Field(ge=0.0, le=1.0)
    cumulative_reward: float
    partial_credits: Dict[str, float] = Field(default_factory=dict)
    feedback: str = ""
    penalty_applied: bool = False


class EnvironmentState(BaseModel):
    """Full internal state."""
    task_id: str
    email_queue: List[Dict]
    current_index: int
    scores: List[float]
    step_count: int
    max_steps: int
    done: bool
    start_time: float


# ─── Environment ─────────────────────────────────────────────────────────────

class EmailTriageEnv:
    """
    OpenEnv-compliant Email Triage Environment.

    Simulates an email inbox where an AI agent must triage emails
    by priority, category, and required actions.
    """

    def __init__(self, task_id: str = "task_1_binary_triage"):
        if task_id not in TASKS:
            raise ValueError(f"Unknown task_id: {task_id}. Choose from: {list(TASKS.keys())}")
        self._task_id = task_id
        self._task_config = TASKS[task_id]
        self._state: Optional[EnvironmentState] = None

    def reset(self) -> Observation:
        """Reset environment to initial state, return first observation."""
        emails = copy.deepcopy(self._task_config["emails"])

        self._state = EnvironmentState(
            task_id=self._task_id,
            email_queue=emails,
            current_index=0,
            scores=[],
            step_count=0,
            max_steps=self._task_config["max_steps"],
            done=False,
            start_time=time.time(),
        )

        return self._make_observation(feedback="Environment reset. Start triaging emails.")

    def step(self, action: Action) -> tuple[Observation, Reward, bool, Dict[str, Any]]:
        """
        Process one agent action.
        Returns: (observation, reward, done, info)
        """
        if self._state is None:
            raise RuntimeError("Call reset() before step()")
        if self._state.done:
            raise RuntimeError("Episode is done. Call reset() to start a new episode.")

        self._state.step_count += 1
        current_email = self._get_current_email()

        # Penalty for skipping
        if action.skip:
            step_reward = 0.1
            feedback = f"Skipped email '{current_email['subject'][:40]}'. Penalty applied."
            penalty = True
        else:
            # Grade the action
            grader = GRADERS[self._task_id]
            action_dict = action.model_dump()
            step_reward, feedback = grader(action_dict, current_email)
            penalty = False

        self._state.scores.append(step_reward)
        self._state.current_index += 1

        # Check termination conditions
        all_emails_done = self._state.current_index >= len(self._state.email_queue)
        step_limit_reached = self._state.step_count >= self._state.max_steps

        if all_emails_done or step_limit_reached:
            self._state.done = True

        cumulative = sum(self._state.scores) / max(len(self._state.scores), 1)

        reward = Reward(
            step_reward=round(step_reward, 3),
            cumulative_reward=round(cumulative, 3),
            feedback=feedback,
            penalty_applied=penalty,
        )

        obs = self._make_observation(feedback=feedback)

        info = {
            "email_id": current_email["id"],
            "true_label": current_email["true_label"],
            "step": self._state.step_count,
            "score": step_reward,
        }

        return obs, reward, self._state.done, info

    def state(self) -> EnvironmentState:
        """Return current internal state (for debugging/logging)."""
        if self._state is None:
            raise RuntimeError("Call reset() before state()")
        return self._state

    def _get_current_email(self) -> Dict:
        """Get the current email to be triaged."""
        idx = self._state.current_index
        if idx >= len(self._state.email_queue):
            return {}
        return self._state.email_queue[idx]

    def _make_observation(self, feedback: str = "") -> Observation:
        """Build an Observation from current state."""
        s = self._state
        current_raw = self._get_current_email()

        current_email = None
        if current_raw:
            current_email = Email(
                id=current_raw["id"],
                subject=current_raw["subject"],
                sender=current_raw["sender"],
                body=current_raw["body"],
                timestamp=current_raw["timestamp"],
            )

        cumulative = sum(s.scores) / max(len(s.scores), 1)

        return Observation(
            task_id=self._task_id,
            task_description=self._task_config["description"],
            current_email=current_email,
            emails_remaining=max(0, len(s.email_queue) - s.current_index),
            emails_processed=s.current_index,
            total_emails=len(s.email_queue),
            last_action_feedback=feedback,
            cumulative_score=round(cumulative, 3),
            done=s.done,
        )

    def get_final_score(self) -> float:
        """Return final normalized score for the episode."""
        if not self._state or not self._state.scores:
            return 0.0
        return round(sum(self._state.scores) / len(self._state.scores), 3)
