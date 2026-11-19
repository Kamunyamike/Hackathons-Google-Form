"""Supabase persistence for form submissions and the admin tracker."""

from datetime import datetime, timezone
import json
from zoneinfo import ZoneInfo

import httpx
import streamlit as st
from postgrest.exceptions import APIError
from supabase import Client, create_client

from lib.form import (
    AWS_QUESTIONS,
    CONSENT_QUESTION_LABEL,
    FUTURE_QUESTION_LABEL,
    HACKATHON_QUESTIONS,
    OPPORTUNITY_OPTIONS,
)

PAGE1_HEADERS = (
    "Full Name",
    "Email Address",
    "Phone Number",
    "Are you a Student or Alumni?",
    "Current Program or Profession",
    "Which opportunity are you interested in?",
)


def _branch_headers(prefix: str, questions: tuple) -> list[str]:
    return [f"{prefix} - {question.label}" for question in questions]


FORM_HEADERS = (
    ["Timestamp"]
    + list(PAGE1_HEADERS)
    + _branch_headers("AWS Event Interest", AWS_QUESTIONS)
    + _branch_headers("Hackathon Interest", HACKATHON_QUESTIONS)
    + _branch_headers("AWS Event and Hackathon Interest", AWS_QUESTIONS + HACKATHON_QUESTIONS)
    + [
        FUTURE_QUESTION_LABEL,
        CONSENT_QUESTION_LABEL,
        "Response ID",
        "Edit Token",
        "Last edited",
    ]
)

TRACKER_HEADERS = (
    ["Timestamp"]
    + list(PAGE1_HEADERS)
    + [question.label for question in AWS_QUESTIONS + HACKATHON_QUESTIONS]
    + [
        FUTURE_QUESTION_LABEL,
        CONSENT_QUESTION_LABEL,
        "Response ID",
        "Last edited",
        "AWS status",
        "In AWS participant group",
        "Hackathon status",
        "Hackathon team",
        "Shared learnings after event",
    ]
)
TRACKER_FOLLOW_UP_HEADERS = TRACKER_HEADERS[-5:]


class StorageError(Exception):
    """An expected configuration or Supabase API error."""


SheetsError = StorageError


def _supabase_credentials() -> tuple[str, str]:
    try:
        settings = st.secrets["supabase"]
    except (KeyError, FileNotFoundError):
        settings = {}

    missing = [
        f"supabase.{key}"
        for key in ("url", "service_role_key")
        if not str(settings.get(key, "")).strip()
    ]
    if missing:
        raise StorageError(
            "Supabase is not configured. In Streamlit Cloud open "
            "App settings → Secrets and add: " + ", ".join(missing) + "."
        )

    return (
        str(settings["url"]).strip(),
        str(settings["service_role_key"]).strip(),
    )


@st.cache_resource
def get_client() -> Client:
    url, service_role_key = _supabase_credentials()
    try:
        return create_client(url, service_role_key)
    except (ValueError, httpx.HTTPError, httpx.InvalidURL) as error:
        raise StorageError(
            "Supabase client initialization failed. Check supabase.url and "
            "supabase.service_role_key in Streamlit secrets."
        ) from error


def _execute(query):
    try:
        response = query.execute()
    except APIError as error:
        code = str(getattr(error, "code", ""))
        if code in ("401", "403", "42501", "PGRST301"):
            message = (
                "Supabase rejected the request. Check the service_role_key in "
                "Streamlit secrets and confirm it is the service-role key."
            )
        else:
            message = (
                "Supabase could not complete the request. Confirm "
                "supabase/schema.sql has been applied and try again."
            )
        raise StorageError(message) from error
    except (httpx.HTTPError, httpx.InvalidURL, OSError) as error:
        raise StorageError(
            "Supabase is temporarily unavailable. Please try again shortly."
        ) from error
    return response.data or []


def _local_timestamp() -> str:
    return datetime.now(ZoneInfo("Africa/Nairobi")).strftime("%d/%m/%Y %H:%M:%S")


def _csv_value(value) -> str:
    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(item) for item in value)
    return "" if value is None else str(value)


def _record_row(answers: dict, response_id: str, edit_token: str, timestamp: str):
    opportunity = answers.get("q6", "")
    aws_visible = opportunity in (OPPORTUNITY_OPTIONS[0], OPPORTUNITY_OPTIONS[2])
    hack_visible = opportunity in (OPPORTUNITY_OPTIONS[1], OPPORTUNITY_OPTIONS[2])
    row = [
        timestamp,
        answers.get("q1", ""),
        answers.get("q2", ""),
        answers.get("q3", ""),
        answers.get("q4", ""),
        answers.get("q5", ""),
        opportunity,
    ]
    row += [answers.get(question.key, "") if aws_visible else "" for question in AWS_QUESTIONS]
    row += [answers.get(question.key, "") if hack_visible else "" for question in HACKATHON_QUESTIONS]
    row += [
        answers.get(question.key, "")
        for question in AWS_QUESTIONS + HACKATHON_QUESTIONS
    ] if opportunity == OPPORTUNITY_OPTIONS[2] else [""] * 8
    row += [
        _csv_value(answers.get("q15", [])),
        _csv_value(answers.get("q16", [])),
        response_id,
        edit_token,
        _local_timestamp(),
    ]
    return row


def _json_object(value) -> dict:
    if value is None:
        return {}
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as error:
            raise StorageError("Supabase returned invalid JSON data.") from error
    return dict(value) if isinstance(value, dict) else {}


def _record_from_row(row: dict) -> dict | None:
    if not isinstance(row, dict):
        return None

    record = _json_object(row.get("record"))
    record.pop("Edit Token", None)
    response_id = row.get("response_id")
    if response_id is not None:
        record["Response ID"] = str(response_id)
    elif "Response ID" not in record:
        return None
    return record


@st.cache_data(ttl=30)
def get_response_records() -> list[dict]:
    rows = _execute(
        get_client()
        .table("responses")
        .select("response_id,record")
        .order("created_at", desc=False)
    )
    records = []
    for row in rows:
        record = _record_from_row(row)
        if record is not None:
            records.append(record)
    return records


@st.cache_data(ttl=30)
def get_tracker_records() -> list[dict]:
    rows = _execute(
        get_client()
        .table("responses")
        .select("response_id,record,follow_up")
        .order("created_at", desc=False)
    )
    records = []
    for row in rows:
        record = _record_from_row(row)
        if record is None:
            continue
        records.append(
            dict(
                zip(
                    TRACKER_HEADERS,
                    _tracker_row(record, _json_object(row.get("follow_up"))),
                )
            )
        )
    return records


def get_response_by_edit_token(edit_token: str):
    rows = _execute(
        get_client()
        .table("responses")
        .select("response_id,record")
        .eq("edit_token", edit_token)
        .limit(1)
    )
    for row in rows:
        record = _record_from_row(row)
        if record is not None:
            record["Edit Token"] = edit_token
            return record
    return None


def save_submission(
    answers: dict,
    response_id: str,
    edit_token: str,
    is_edit: bool,
):
    client = get_client()
    follow_up = {header: "" for header in TRACKER_FOLLOW_UP_HEADERS}
    timestamp = _local_timestamp()

    if is_edit:
        existing_rows = _execute(
            client.table("responses")
            .select("record,follow_up")
            .eq("response_id", response_id)
            .eq("edit_token", edit_token)
            .limit(1)
        )
        existing_row = next(
            (row for row in existing_rows if isinstance(row, dict)),
            None,
        )
        if existing_row is None:
            raise StorageError("This edit link is invalid or has expired.")
        existing_record = _json_object(existing_row.get("record"))
        timestamp = existing_record.get("Timestamp") or timestamp
        follow_up = _json_object(existing_row.get("follow_up")) or follow_up

    record_values = _record_row(answers, response_id, edit_token, timestamp)
    record = dict(zip(FORM_HEADERS, record_values))
    record.pop("Edit Token", None)

    if is_edit:
        updated_rows = _execute(
            client.table("responses")
            .update(
                {
                    "record": record,
                    "follow_up": follow_up,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            .eq("response_id", response_id)
            .eq("edit_token", edit_token)
            .select("response_id")
        )
        if not any(isinstance(row, dict) for row in updated_rows):
            raise StorageError("This edit link is invalid or has expired.")
    else:
        _execute(
            client.table("responses").insert(
                {
                    "response_id": response_id,
                    "edit_token": edit_token,
                    "record": record,
                    "follow_up": follow_up,
                }
            )
        )

    get_response_records.clear()
    get_tracker_records.clear()


def _tracker_row(record: dict, follow_up: dict):
    opportunity = record.get("Which opportunity are you interested in?", "")
    if opportunity == OPPORTUNITY_OPTIONS[2]:
        event_answers = [
            record.get(f"AWS Event and Hackathon Interest - {question.label}", "")
            for question in AWS_QUESTIONS + HACKATHON_QUESTIONS
        ]
    elif opportunity == OPPORTUNITY_OPTIONS[0]:
        event_answers = [
            record.get(f"AWS Event Interest - {question.label}", "")
            for question in AWS_QUESTIONS
        ] + [""] * len(HACKATHON_QUESTIONS)
    elif opportunity == OPPORTUNITY_OPTIONS[1]:
        event_answers = [""] * len(AWS_QUESTIONS) + [
            record.get(f"Hackathon Interest - {question.label}", "")
            for question in HACKATHON_QUESTIONS
        ]
    else:
        event_answers = [""] * 8

    return (
        [record.get("Timestamp", "")]
        + [record.get(header, "") for header in PAGE1_HEADERS]
        + event_answers
        + [
            record.get(FORM_HEADERS[-5], ""),
            record.get(FORM_HEADERS[-4], ""),
            record.get("Response ID", ""),
            record.get("Last edited", ""),
        ]
        + [follow_up.get(header, "") for header in TRACKER_FOLLOW_UP_HEADERS]
    )


def rebuild_tracker():
    get_response_records.clear()
    get_tracker_records.clear()
    return len(get_response_records())
