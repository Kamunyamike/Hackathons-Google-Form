"""Single source of truth for the registration form."""

from dataclasses import dataclass
import re
from typing import Any


TITLE = "AfriCDSA Community Opportunities Registration"
OPPORTUNITY_SELECTION_TITLE = "Opportunity selection"
AWS_SECTION_TITLE = "AWS Event Interest"
HACKATHON_SECTION_TITLE = "Hackathon Interest"
BOTH_SECTION_TITLE = "AWS Event and Hackathon Interest"
PAGE3_SECTION_TITLE = "Future opportunities and consent"
CONSENT_SECTION_TITLE = "Consent"
FUTURE_QUESTION_LABEL = (
    "Would you like to receive information about future opportunities? Tick all that apply."
)
CONSENT_QUESTION_LABEL = "I agree to be contacted by AfriCDSA regarding:"
CONSENT_HELP_TEXT = "Tick Event Updates to receive the Meetup link and event information."
DESCRIPTION = """AfriCDSA is inviting students and alumni to participate in upcoming learning, innovation, and professional development opportunities.

Current opportunities include:
• AWS Student Builder Group Event - Think Like an Architect, Build Like One
• Hack for Inclusion Hackathon

Complete this short form if you would like to participate in either or both opportunities.
Participants interested in the AWS event will receive the official Meetup registration link after submitting this form.

Takes about 2 minutes. Your details are used only by the AfriCDSA Community Team to coordinate these opportunities and, if you agree, to share future ones."""

OPPORTUNITY_OPTIONS = (
    "AWS Student Builder Group Event",
    "Hack for Inclusion Hackathon",
    "Both",
)

AWS_DESCRIPTION = (
    "AWS Student Builder Group Event: Think Like an Architect, Build Like One. "
    "Thursday 26 November 2026, 10:00 am to 5:00 pm, MKCC. Note: Participants "
    "will receive the official Meetup registration link from the AfriCDSA Community Team."
)
HACKATHON_DESCRIPTION = (
    "Hack for Inclusion Hackathon: 7 to 9 January 2027, building disability-inclusive "
    "solutions. The top five teams receive up to KES 1,000,000 in venture support, a "
    "six-month incubation programme and mentorship. Note: You must also apply through "
    "the official application form by 4 December 2026. We will send you the link and "
    "help you form a team."
)

FUTURE_OPPORTUNITY_OPTIONS = (
    "Training Sessions",
    "Hackathons",
    "Competitions",
    "Mentorship Programs",
    "Scholarships",
    "Internships",
    "Research Projects",
    "Community Leadership Opportunities",
)
CONSENT_OPTIONS = (
    "Event Updates",
    "Community Opportunities",
    "Future Learning Programs",
)


@dataclass(frozen=True)
class Question:
    key: str
    label: str
    options: tuple[str, ...]


PAGE1_TEXT_FIELDS = (
    ("q1", "Full Name", None),
    ("q2", "Email Address", None),
    ("q3", "Phone Number", "WhatsApp number preferred, e.g. 0712345678 or +254712345678"),
)
PAGE1_RADIO_QUESTIONS = (
    Question("q4", "Are you a Student or Alumni?", ("Student", "Alumni")),
)
PAGE1_PROGRAM_FIELD = (
    "q5",
    "Current Program or Profession",
    "e.g. Data Science student, or Data Analyst at XYZ Ltd",
)
OPPORTUNITY_QUESTION = Question(
    "q6",
    "Which opportunity are you interested in?",
    OPPORTUNITY_OPTIONS,
)

AWS_QUESTIONS = (
    Question("q7", "Are you available to attend the event?", ("Yes", "No", "Not Sure")),
    Question("q8", "Would you like to join the AfriCDSA AWS participant group?", ("Yes", "No")),
    Question(
        "q9",
        "What interests you most?",
        (
            "Cloud Computing",
            "Artificial Intelligence",
            "AWS Technologies",
            "DevOps",
            "Networking",
            "Career Growth",
        ),
    ),
    Question(
        "q10",
        "After submitting this form, are you willing to complete the official Meetup registration?",
        ("Yes", "No"),
    ),
)
HACKATHON_QUESTIONS = (
    Question("q11", "Have you participated in a hackathon before?", ("Yes", "No")),
    Question("q12", "Would you like to join a team?", ("Yes", "No")),
    Question(
        "q13",
        "Which area interests you?",
        (
            "AI",
            "Data Science",
            "Accessibility Solutions",
            "Software Development",
            "Innovation & Entrepreneurship",
        ),
    ),
    Question("q14", "Do you already have a project idea?", ("Yes", "No")),
)

BRANCH_QUESTIONS = {
    OPPORTUNITY_OPTIONS[0]: AWS_QUESTIONS,
    OPPORTUNITY_OPTIONS[1]: HACKATHON_QUESTIONS,
    OPPORTUNITY_OPTIONS[2]: AWS_QUESTIONS + HACKATHON_QUESTIONS,
}

EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)
PHONE_PATTERN = re.compile(r"^\+?[0-9 ]{10,15}$")
REQUIRED_ERROR = "This is a required question"


def visible_question_keys(opportunity: str) -> tuple[str, ...]:
    return tuple(question.key for question in BRANCH_QUESTIONS.get(opportunity, ()))


def validate_page1(answers: dict[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}
    for key in ("q1", "q2", "q3", "q5", "q6", "q4"):
        value = answers.get(key)
        if not value or (isinstance(value, str) and not value.strip()):
            errors[key] = REQUIRED_ERROR
    email = str(answers.get("q2", "")).strip()
    if email and not EMAIL_PATTERN.fullmatch(email):
        errors["q2"] = "Enter a valid email address."
    phone = str(answers.get("q3", ""))
    if phone and not PHONE_PATTERN.fullmatch(phone):
        errors["q3"] = "Enter a valid phone number."
    return errors


def validate_event(answers: dict[str, Any]) -> dict[str, str]:
    return {
        key: REQUIRED_ERROR
        for key in visible_question_keys(str(answers.get("q6", "")))
        if not answers.get(key)
    }


def validate_consent(answers: dict[str, Any]) -> dict[str, str]:
    return {"q16": REQUIRED_ERROR} if not answers.get("q16") else {}


def clear_hidden_branch_answers(answers: dict[str, Any]) -> dict[str, Any]:
    """Return answers containing only the event fields visible for the saved branch."""
    cleaned = dict(answers)
    opportunity = cleaned.get("q6")
    visible = set(visible_question_keys(str(opportunity)))
    for question in AWS_QUESTIONS + HACKATHON_QUESTIONS:
        if question.key not in visible:
            cleaned[question.key] = ""
    return cleaned
