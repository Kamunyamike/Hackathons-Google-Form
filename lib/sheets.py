"""Google Sheets persistence for form submissions and the admin tracker."""

from datetime import datetime
from zoneinfo import ZoneInfo

import gspread
import streamlit as st
from google.auth.exceptions import GoogleAuthError
from google.oauth2.service_account import Credentials
from requests.exceptions import RequestException

from lib.form import (
    AWS_QUESTIONS,
    CONSENT_QUESTION_LABEL,
    FUTURE_QUESTION_LABEL,
    HACKATHON_QUESTIONS,
    OPPORTUNITY_OPTIONS,
)

SPREADSHEET_TITLE = "AfriCDSA Opportunities 2026"
FORM_WORKSHEET_TITLE = "Form Responses 1"
TRACKER_WORKSHEET_TITLE = "Tracker"
SCOPES = (
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
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


class SheetsError(Exception):
    """An expected configuration or Google Sheets API error."""


def _retry_api(operation):
    for attempt in range(2):
        try:
            return operation()
        except gspread.exceptions.APIError as error:
            if attempt == 1:
                raise SheetsError(
                    "Google Sheets could not complete the request. Please try again shortly."
                ) from error
        except RequestException as error:
            raise SheetsError(
                "Google Sheets is temporarily unavailable. Please try again shortly."
            ) from error


@st.cache_resource
def get_spreadsheet():
    try:
        service_account = dict(st.secrets["gcp_service_account"])
        spreadsheet_id = st.secrets["sheets"]["spreadsheet_id"]
    except KeyError as error:
        raise SheetsError(
            "Google Sheets is not configured. Add the required secrets in Streamlit settings."
        ) from error

    try:
        credentials = Credentials.from_service_account_info(service_account, scopes=SCOPES)
        client = gspread.authorize(credentials)
        spreadsheet = _retry_api(lambda: client.open_by_key(spreadsheet_id))
        if spreadsheet.title != SPREADSHEET_TITLE:
            raise SheetsError(
                f"The configured spreadsheet must be named '{SPREADSHEET_TITLE}'."
            )
        return spreadsheet
    except (GoogleAuthError, ValueError) as error:
        raise SheetsError(
            "Google Sheets authentication failed. Check the service-account secrets."
        ) from error


def _get_worksheet(title: str, rows: int = 1000, cols: int = 40):
    spreadsheet = get_spreadsheet()
    try:
        return _retry_api(lambda: spreadsheet.worksheet(title))
    except gspread.exceptions.WorksheetNotFound:
        return _retry_api(
            lambda: spreadsheet.add_worksheet(title=title, rows=rows, cols=cols)
        )


def _ensure_form_worksheet():
    worksheet = _get_worksheet(FORM_WORKSHEET_TITLE, cols=len(FORM_HEADERS))
    if not _retry_api(lambda: worksheet.row_values(1)):
        _retry_api(
            lambda: worksheet.update(
                range_name="A1",
                values=[FORM_HEADERS],
                value_input_option="RAW",
            )
        )
    return worksheet


def _ensure_tracker_worksheet():
    worksheet = _get_worksheet(TRACKER_WORKSHEET_TITLE, cols=len(TRACKER_HEADERS))
    if not _retry_api(lambda: worksheet.row_values(1)):
        _retry_api(
            lambda: worksheet.update(
                range_name="A1",
                values=[TRACKER_HEADERS],
                value_input_option="RAW",
            )
        )
    return worksheet


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


def _read_rows(worksheet):
    rows = _retry_api(lambda: worksheet.get_all_values())
    if not rows:
        return []
    names = rows[0]
    return [
        {name: row[index] if index < len(row) else "" for index, name in enumerate(names)}
        for row in rows[1:]
        if any(row)
    ]


@st.cache_data(ttl=30)
def get_response_records():
    worksheet = _ensure_form_worksheet()
    return _read_rows(worksheet)


@st.cache_data(ttl=30)
def get_tracker_records():
    worksheet = _ensure_tracker_worksheet()
    return _read_rows(worksheet)


def get_response_by_edit_token(edit_token: str):
    return next(
        (
            record
            for record in get_response_records()
            if record.get("Edit Token") == edit_token
        ),
        None,
    )


def _find_response_row(worksheet, response_id: str, edit_token: str | None = None):
    rows = _retry_api(lambda: worksheet.get_all_values())
    if not rows:
        return None, None
    headers = rows[0]
    id_column = headers.index("Response ID")
    token_column = headers.index("Edit Token")
    for row_number, row in enumerate(rows[1:], start=2):
        if len(row) > id_column and row[id_column] == response_id:
            if edit_token is None or (
                len(row) > token_column and row[token_column] == edit_token
            ):
                return row_number, row
    return None, None


def save_submission(
    answers: dict,
    response_id: str,
    edit_token: str,
    is_edit: bool,
):
    worksheet = _ensure_form_worksheet()
    row_number, existing_row = _find_response_row(
        worksheet, response_id, edit_token if is_edit else None
    )
    if is_edit and row_number is None:
        raise SheetsError("This edit link is invalid or has expired.")

    original_timestamp = (
        existing_row[0] if existing_row and existing_row[0] else _local_timestamp()
    )
    values = _record_row(answers, response_id, edit_token, original_timestamp)
    if row_number is not None:
        end_column = gspread.utils.rowcol_to_a1(1, len(FORM_HEADERS)).rstrip("1")
        _retry_api(
            lambda: worksheet.update(
                range_name=f"A{row_number}:{end_column}{row_number}",
                values=[values],
                value_input_option="RAW",
            )
        )
    else:
        _retry_api(lambda: worksheet.append_row(values, value_input_option="RAW"))
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
    records = get_response_records()
    old_tracker_rows = get_tracker_records()
    follow_up_by_id = {
        record.get("Response ID", ""): record
        for record in old_tracker_rows
        if record.get("Response ID")
    }

    worksheet = _ensure_tracker_worksheet()
    old_row_count = len(_retry_api(lambda: worksheet.get_all_values()))
    values = [TRACKER_HEADERS] + [
        _tracker_row(
            record,
            follow_up_by_id.get(record.get("Response ID", ""), {}),
        )
        for record in records
    ]
    _retry_api(lambda: worksheet.clear())
    _retry_api(
        lambda: worksheet.update(
            range_name="A1",
            values=values,
            value_input_option="RAW",
        )
    )
    if old_row_count > len(values):
        _retry_api(
            lambda: worksheet.delete_rows(
                len(values) + 1,
                old_row_count,
            )
        )
    get_tracker_records.clear()
    return len(records)


def export_sheet_values():
    form = _ensure_form_worksheet()
    tracker = _ensure_tracker_worksheet()
    return (
        _retry_api(lambda: form.get_all_values()),
        _retry_api(lambda: tracker.get_all_values()),
    )
