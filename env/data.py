"""Synthetic email dataset for the email triage environment."""

import random
from typing import List, Dict, Any

EMAILS = [
    # URGENT - High priority
    {
        "id": "e001",
        "subject": "URGENT: Production server down - customer impact",
        "sender": "ops-alerts@company.com",
        "body": "Our main production server has been down for 15 minutes. Over 500 customers are affected. We need immediate attention from the on-call engineer.",
        "timestamp": "2024-01-15T09:30:00Z",
        "true_label": "urgent",
        "true_priority": 1,
        "true_category": "incident",
        "requires_reply": True,
    },
    {
        "id": "e002",
        "subject": "Security breach detected - immediate action required",
        "sender": "security@company.com",
        "body": "We have detected unauthorized access to our systems at 09:15 AM. Credentials may be compromised. Please rotate all API keys immediately and notify the security team.",
        "timestamp": "2024-01-15T09:45:00Z",
        "true_label": "urgent",
        "true_priority": 1,
        "true_category": "security",
        "requires_reply": True,
    },
    # HIGH priority
    {
        "id": "e003",
        "subject": "Client complaint - delayed delivery on order #45892",
        "sender": "support@client-corp.com",
        "body": "We placed order #45892 two weeks ago and still haven't received it. This is causing disruption to our operations. We need immediate resolution or we'll have to escalate to management.",
        "timestamp": "2024-01-15T10:00:00Z",
        "true_label": "high",
        "true_priority": 2,
        "true_category": "customer_complaint",
        "requires_reply": True,
    },
    {
        "id": "e004",
        "subject": "Budget approval needed by EOD",
        "sender": "cfo@company.com",
        "body": "The Q1 budget proposal needs your sign-off before end of day today. Please review the attached document and provide approval or feedback. This is time-sensitive.",
        "timestamp": "2024-01-15T10:15:00Z",
        "true_label": "high",
        "true_priority": 2,
        "true_category": "approval",
        "requires_reply": True,
    },
    # MEDIUM priority
    {
        "id": "e005",
        "subject": "Team meeting rescheduled to Thursday 2pm",
        "sender": "assistant@company.com",
        "body": "The weekly team sync has been moved from Wednesday to Thursday at 2:00 PM. Please update your calendars accordingly. Agenda remains the same.",
        "timestamp": "2024-01-15T10:30:00Z",
        "true_label": "medium",
        "true_priority": 3,
        "true_category": "scheduling",
        "requires_reply": False,
    },
    {
        "id": "e006",
        "subject": "Monthly report due next Friday",
        "sender": "manager@company.com",
        "body": "Reminder that the monthly performance report is due next Friday. Please compile your team's metrics and achievements for January. Template is in the shared drive.",
        "timestamp": "2024-01-15T11:00:00Z",
        "true_label": "medium",
        "true_priority": 3,
        "true_category": "task",
        "requires_reply": False,
    },
    # LOW priority
    {
        "id": "e007",
        "subject": "Company newsletter - January edition",
        "sender": "newsletter@company.com",
        "body": "Welcome to our January newsletter! This month we're highlighting our team achievements, upcoming events, and a special message from our CEO. Click to read more.",
        "timestamp": "2024-01-15T11:30:00Z",
        "true_label": "low",
        "true_priority": 4,
        "true_category": "newsletter",
        "requires_reply": False,
    },
    {
        "id": "e008",
        "subject": "Office supplies order - please review catalog",
        "sender": "admin@company.com",
        "body": "We're placing the quarterly office supplies order. Please review the catalog and submit any requests by end of week. Items under $50 can be approved automatically.",
        "timestamp": "2024-01-15T12:00:00Z",
        "true_label": "low",
        "true_priority": 4,
        "true_category": "admin",
        "requires_reply": False,
    },
    # SPAM
    {
        "id": "e009",
        "subject": "You've won a $1000 Amazon gift card!",
        "sender": "prize@totally-legit-deals.com",
        "body": "Congratulations! You've been selected as our monthly winner. Click here to claim your $1000 Amazon gift card. Limited time offer - expires in 24 hours!",
        "timestamp": "2024-01-15T12:30:00Z",
        "true_label": "spam",
        "true_priority": 5,
        "true_category": "spam",
        "requires_reply": False,
    },
    {
        "id": "e010",
        "subject": "Exclusive investment opportunity - 300% returns guaranteed",
        "sender": "invest@rich-quick-scheme.net",
        "body": "Dear valued customer, we have an exclusive investment opportunity that guarantees 300% returns in just 30 days. This offer is only available to select individuals like yourself.",
        "timestamp": "2024-01-15T13:00:00Z",
        "true_label": "spam",
        "true_priority": 5,
        "true_category": "spam",
        "requires_reply": False,
    },
    # More varied examples
    {
        "id": "e011",
        "subject": "API rate limit exceeded - service degradation",
        "sender": "monitoring@company.com",
        "body": "Alert: Our third-party API integration has exceeded rate limits. Response times are degraded. Engineering team needs to implement backoff logic. Estimated impact: 200 users.",
        "timestamp": "2024-01-15T13:30:00Z",
        "true_label": "high",
        "true_priority": 2,
        "true_category": "incident",
        "requires_reply": True,
    },
    {
        "id": "e012",
        "subject": "Job application - Senior Developer position",
        "sender": "applicant@email.com",
        "body": "Dear Hiring Manager, I am applying for the Senior Developer position posted on LinkedIn. I have 8 years of experience in Python and distributed systems. Please find my resume attached.",
        "timestamp": "2024-01-15T14:00:00Z",
        "true_label": "medium",
        "true_priority": 3,
        "true_category": "hr",
        "requires_reply": True,
    },
    {
        "id": "e013",
        "subject": "Happy Birthday wishes",
        "sender": "colleague@company.com",
        "body": "Happy Birthday! Hope you have a wonderful day. The team has organized a small celebration in the break room at 3pm if you're free to join us!",
        "timestamp": "2024-01-15T14:30:00Z",
        "true_label": "low",
        "true_priority": 4,
        "true_category": "personal",
        "requires_reply": False,
    },
    {
        "id": "e014",
        "subject": "Legal notice - contract renewal required",
        "sender": "legal@partner-company.com",
        "body": "This is a formal notice that your service contract expires on February 1st. Failure to renew within 7 days will result in service termination and potential legal action for outstanding invoices.",
        "timestamp": "2024-01-15T15:00:00Z",
        "true_label": "urgent",
        "true_priority": 1,
        "true_category": "legal",
        "requires_reply": True,
    },
    {
        "id": "e015",
        "subject": "Lunch menu for next week",
        "sender": "cafeteria@company.com",
        "body": "Here's the lunch menu for next week. Monday: Pasta, Tuesday: Salad Bar, Wednesday: BBQ, Thursday: Asian Fusion, Friday: Pizza. Vegetarian options available daily.",
        "timestamp": "2024-01-15T15:30:00Z",
        "true_label": "low",
        "true_priority": 4,
        "true_category": "admin",
        "requires_reply": False,
    },
]


def get_task_emails(task_level: str) -> List[Dict[str, Any]]:
    """Return emails appropriate for each task difficulty level."""
    if task_level == "easy":
        # Clear-cut cases: obvious spam vs urgent
        return [e for e in EMAILS if e["id"] in ["e001", "e007", "e009", "e013", "e015"]]
    elif task_level == "medium":
        # Mix of priorities, requires proper triage
        return [e for e in EMAILS if e["id"] in ["e002", "e003", "e005", "e008", "e011", "e012"]]
    elif task_level == "hard":
        # Full inbox with subtle priorities, edge cases
        return EMAILS
    return EMAILS


VALID_LABELS = ["urgent", "high", "medium", "low", "spam"]
VALID_CATEGORIES = ["incident", "security", "customer_complaint", "approval", "scheduling",
                    "task", "newsletter", "admin", "spam", "hr", "personal", "legal"]
