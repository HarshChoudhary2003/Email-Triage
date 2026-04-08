"""Tasks and graders for the email triage OpenEnv environment."""

from typing import Dict, List, Any, Tuple
from .data import get_task_emails, VALID_LABELS, VALID_CATEGORIES


TASKS = {
    "task_1_binary_triage": {
        "id": "task_1_binary_triage",
        "name": "Binary Email Triage (Easy)",
        "description": (
            "Classify each email as either 'actionable' (urgent/high priority, requires "
            "response) or 'not_actionable' (low/spam, no action needed). "
            "This is the simplest form of email triage."
        ),
        "difficulty": "easy",
        "max_steps": 10,
        "emails": get_task_emails("easy"),
        "success_threshold": 0.8,
    },
    "task_2_priority_labeling": {
        "id": "task_2_priority_labeling",
        "name": "Priority Labeling (Medium)",
        "description": (
            "Assign each email one of five priority labels: urgent, high, medium, low, spam. "
            "The agent must also identify whether a reply is required. "
            "Partial credit is given for adjacent priority levels."
        ),
        "difficulty": "medium",
        "max_steps": 15,
        "emails": get_task_emails("medium"),
        "success_threshold": 0.7,
    },
    "task_3_full_triage": {
        "id": "task_3_full_triage",
        "name": "Full Inbox Triage (Hard)",
        "description": (
            "Complete triage of a full inbox: assign priority label, category, "
            "whether a reply is required, and provide a one-sentence action summary. "
            "Agent must handle all 15 emails correctly with nuanced judgment."
        ),
        "difficulty": "hard",
        "max_steps": 30,
        "emails": get_task_emails("hard"),
        "success_threshold": 0.65,
    },
}


def grade_binary_triage(action: Dict, email: Dict) -> Tuple[float, str]:
    """Grade task 1: binary actionable vs not_actionable."""
    predicted = action.get("binary_label", "").lower()
    true_label = email["true_label"]

    # Ground truth mapping
    actionable_labels = {"urgent", "high"}
    is_truly_actionable = true_label in actionable_labels

    if predicted == "actionable" and is_truly_actionable:
        return 1.0, "Correct: actionable email identified"
    elif predicted == "not_actionable" and not is_truly_actionable:
        return 1.0, "Correct: non-actionable email identified"
    elif predicted == "actionable" and not is_truly_actionable:
        # False positive — less bad than missing urgent
        penalty = 0.3 if true_label == "medium" else 0.1
        return penalty, f"False positive: email was {true_label}"
    elif predicted == "not_actionable" and is_truly_actionable:
        # False negative — worse, missed urgent/high
        return 0.0, f"Missed actionable email: was {true_label}"
    else:
        return 0.0, f"Invalid binary_label: {predicted}"


def grade_priority_label(action: Dict, email: Dict) -> Tuple[float, str]:
    """Grade task 2: 5-class priority label + reply detection."""
    predicted_label = action.get("priority_label", "").lower()
    predicted_reply = action.get("requires_reply", None)
    true_label = email["true_label"]
    true_reply = email["requires_reply"]

    label_score = 0.0
    reply_score = 0.0

    # Priority label scoring with adjacency credit
    priority_order = ["urgent", "high", "medium", "low", "spam"]
    if predicted_label not in priority_order:
        label_score = 0.0
    elif predicted_label == true_label:
        label_score = 1.0
    else:
        true_idx = priority_order.index(true_label)
        pred_idx = priority_order.index(predicted_label)
        distance = abs(true_idx - pred_idx)
        if distance == 1:
            label_score = 0.5  # Adjacent level
        elif distance == 2:
            label_score = 0.2
        else:
            label_score = 0.0

    # Reply detection scoring
    if predicted_reply is None:
        reply_score = 0.3  # didn't attempt
    elif bool(predicted_reply) == bool(true_reply):
        reply_score = 1.0
    else:
        reply_score = 0.0

    # Weighted combination
    final_score = 0.7 * label_score + 0.3 * reply_score
    msg = f"Label: {predicted_label} (true: {true_label}, score: {label_score:.1f}), Reply: {predicted_reply} (true: {true_reply}, score: {reply_score:.1f})"
    return round(final_score, 3), msg


def grade_full_triage(action: Dict, email: Dict) -> Tuple[float, str]:
    """Grade task 3: full triage with label + category + reply + summary."""
    scores = {}
    details = []

    # Priority label (40% weight)
    predicted_label = action.get("priority_label", "").lower()
    true_label = email["true_label"]
    priority_order = ["urgent", "high", "medium", "low", "spam"]
    if predicted_label == true_label:
        scores["label"] = 1.0
    elif predicted_label in priority_order:
        distance = abs(priority_order.index(predicted_label) - priority_order.index(true_label))
        scores["label"] = max(0.0, 1.0 - distance * 0.35)
    else:
        scores["label"] = 0.0
    details.append(f"label={scores['label']:.2f}")

    # Category (25% weight)
    predicted_cat = action.get("category", "").lower()
    true_cat = email["true_category"]
    if predicted_cat == true_cat:
        scores["category"] = 1.0
    elif predicted_cat in VALID_CATEGORIES:
        # Partial credit for related categories
        related = {
            "incident": ["security", "task"],
            "security": ["incident"],
            "customer_complaint": ["task"],
            "scheduling": ["task", "admin"],
            "admin": ["scheduling", "task"],
        }
        if true_cat in related.get(predicted_cat, []) or predicted_cat in related.get(true_cat, []):
            scores["category"] = 0.4
        else:
            scores["category"] = 0.0
    else:
        scores["category"] = 0.0
    details.append(f"cat={scores['category']:.2f}")

    # Reply required (20% weight)
    predicted_reply = action.get("requires_reply")
    true_reply = email["requires_reply"]
    if predicted_reply is None:
        scores["reply"] = 0.0
    elif bool(predicted_reply) == bool(true_reply):
        scores["reply"] = 1.0
    else:
        scores["reply"] = 0.0
    details.append(f"reply={scores['reply']:.2f}")

    # Summary quality (15% weight) - basic heuristic check
    summary = action.get("action_summary", "")
    if isinstance(summary, str) and len(summary.strip()) >= 10:
        # Check for key words from email subject/body
        email_text = (email["subject"] + " " + email["body"]).lower()
        summary_words = set(summary.lower().split())
        email_words = set(email_text.split())
        overlap = len(summary_words & email_words)
        scores["summary"] = min(1.0, overlap / 3)  # At least 3 overlapping words = full score
    else:
        scores["summary"] = 0.0
    details.append(f"summary={scores['summary']:.2f}")

    final = (
        0.40 * scores["label"] +
        0.25 * scores["category"] +
        0.20 * scores["reply"] +
        0.15 * scores["summary"]
    )
    return round(final, 3), ", ".join(details)


GRADERS = {
    "task_1_binary_triage": grade_binary_triage,
    "task_2_priority_labeling": grade_priority_label,
    "task_3_full_triage": grade_full_triage,
}
