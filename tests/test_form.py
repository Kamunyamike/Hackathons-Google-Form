import unittest
from copy import deepcopy
import json
from unittest.mock import patch

from lib.form import (
    AWS_QUESTIONS,
    HACKATHON_QUESTIONS,
    OPPORTUNITY_OPTIONS,
    REQUIRED_ERROR,
    clear_hidden_branch_answers,
    validate_consent,
    validate_event,
    validate_page1,
    visible_question_keys,
)
from lib.storage import (
    FORM_HEADERS,
    TRACKER_HEADERS,
    TRACKER_FOLLOW_UP_HEADERS,
    StorageError,
    _record_row,
    _tracker_row,
    get_client,
    get_response_by_edit_token,
    get_response_records,
    get_tracker_records,
    save_submission,
)
from lib.pdf import receipt_pdf, summary_pdf


class FormBehaviorTests(unittest.TestCase):
    def test_page_one_validation_requires_fields_and_formats(self):
        errors = validate_page1(
            {
                "q1": " ",
                "q2": "not-an-email",
                "q3": "abc",
                "q4": "Student",
                "q5": "Data Science",
                "q6": OPPORTUNITY_OPTIONS[0],
            }
        )
        self.assertEqual(errors["q1"], REQUIRED_ERROR)
        self.assertEqual(errors["q2"], "Enter a valid email address.")
        self.assertEqual(errors["q3"], "Enter a valid phone number.")
        self.assertNotIn("q4", errors)

    def test_branch_validation_and_hidden_answers(self):
        self.assertEqual(
            visible_question_keys(OPPORTUNITY_OPTIONS[0]),
            tuple(question.key for question in AWS_QUESTIONS),
        )
        self.assertEqual(
            visible_question_keys(OPPORTUNITY_OPTIONS[1]),
            tuple(question.key for question in HACKATHON_QUESTIONS),
        )
        self.assertEqual(len(visible_question_keys(OPPORTUNITY_OPTIONS[2])), 8)
        answers = {f"q{number}": f"answer-{number}" for number in range(7, 15)}
        answers["q6"] = OPPORTUNITY_OPTIONS[0]
        cleaned = clear_hidden_branch_answers(answers)
        self.assertEqual(cleaned["q7"], "answer-7")
        self.assertEqual(cleaned["q10"], "answer-10")
        self.assertEqual(cleaned["q11"], "")
        self.assertEqual(cleaned["q14"], "")

    def test_event_and_consent_validation(self):
        self.assertEqual(validate_event({"q6": OPPORTUNITY_OPTIONS[0], "q7": "Yes"}), {
            "q8": REQUIRED_ERROR,
            "q9": REQUIRED_ERROR,
            "q10": REQUIRED_ERROR,
        })
        self.assertEqual(validate_consent({"q16": []}), {"q16": REQUIRED_ERROR})
        self.assertEqual(validate_consent({"q16": ["Event Updates"]}), {})


class StorageMappingTests(unittest.TestCase):
    def test_branch_values_are_written_to_expected_columns(self):
        answers = {
            "q1": "Test Person",
            **{f"q{number}": f"answer-{number}" for number in range(7, 15)},
            "q15": ["Hackathons", "Scholarships"],
            "q16": ["Event Updates"],
        }
        for opportunity in OPPORTUNITY_OPTIONS:
            answers["q6"] = opportunity
            row = _record_row(answers, "response-id", "secret-token", "18/11/2026 12:00:00")
            record = dict(zip(FORM_HEADERS, row))
            for number in range(7, 15):
                if opportunity == OPPORTUNITY_OPTIONS[2]:
                    expected = f"answer-{number}"
                    header = f"AWS Event and Hackathon Interest - {self._question_label(number)}"
                elif opportunity == OPPORTUNITY_OPTIONS[0] and number <= 10:
                    expected = f"answer-{number}"
                    header = f"AWS Event Interest - {self._question_label(number)}"
                elif opportunity == OPPORTUNITY_OPTIONS[1] and number >= 11:
                    expected = f"answer-{number}"
                    header = f"Hackathon Interest - {self._question_label(number)}"
                else:
                    expected = ""
                    header = (
                        f"AWS Event Interest - {self._question_label(number)}"
                        if number <= 10
                        else f"Hackathon Interest - {self._question_label(number)}"
                    )
                self.assertEqual(record[header], expected)
            self.assertEqual(record["Response ID"], "response-id")
            self.assertEqual(record["Edit Token"], "secret-token")
            self.assertEqual(
                record["Would you like to receive information about future opportunities? Tick all that apply."],
                "Hackathons, Scholarships",
            )

    def test_tracker_merges_branch_questions_and_preserves_follow_up(self):
        both_answers = {
            "q1": "Test Person",
            "q6": OPPORTUNITY_OPTIONS[2],
            **{f"q{number}": f"answer-{number}" for number in range(7, 15)},
        }
        row = _record_row(both_answers, "response-id", "secret-token", "18/11/2026 12:00:00")
        record = dict(zip(FORM_HEADERS, row))
        tracker = _tracker_row(record, {header: "retained" for header in TRACKER_FOLLOW_UP_HEADERS})
        self.assertEqual(tracker[7:15], [f"answer-{number}" for number in range(7, 15)])
        self.assertEqual(tracker[-5:], ["retained"] * 5)

    def test_edit_updates_existing_response_row(self):
        client = FakeSupabaseClient()
        answers = {"q1": "Before", "q6": OPPORTUNITY_OPTIONS[0], "q7": "Yes"}
        with patch("lib.storage.get_client", return_value=client):
            save_submission(answers, "response-id", "edit-token", is_edit=False)
            original_timestamp = client.rows[0]["record"]["Timestamp"]
            client.rows[0]["follow_up"]["AWS status"] = "Confirmed"
            answers["q1"] = "After"
            save_submission(answers, "response-id", "edit-token", is_edit=True)

        self.assertEqual(len(client.rows), 1)
        record = client.rows[0]["record"]
        self.assertEqual(record["Full Name"], "After")
        self.assertEqual(record["Timestamp"], original_timestamp)
        self.assertEqual(record["Response ID"], "response-id")
        self.assertIn("Last edited", record)
        self.assertNotIn("Edit Token", record)
        self.assertEqual(client.rows[0]["follow_up"]["AWS status"], "Confirmed")

    def test_invalid_edit_token_raises_storage_error(self):
        client = FakeSupabaseClient()
        with patch("lib.storage.get_client", return_value=client):
            with self.assertRaisesRegex(
                StorageError,
                "This edit link is invalid or has expired.",
            ):
                save_submission(
                    {"q1": "Test", "q6": OPPORTUNITY_OPTIONS[0]},
                    "response-id",
                    "wrong-token",
                    is_edit=True,
                )

    def test_edit_link_lookup_returns_record_with_token(self):
        client = FakeSupabaseClient()
        with patch("lib.storage.get_client", return_value=client):
            save_submission(
                {"q1": "Test", "q6": OPPORTUNITY_OPTIONS[0]},
                "response-id",
                "edit-token",
                is_edit=False,
            )
            record = get_response_by_edit_token("edit-token")

        self.assertEqual(record["Full Name"], "Test")
        self.assertEqual(record["Response ID"], "response-id")
        self.assertEqual(record["Edit Token"], "edit-token")

    def test_missing_supabase_secrets_raise_storage_error(self):
        get_client.clear()
        try:
            with patch("lib.storage.st.secrets", {}):
                with self.assertRaisesRegex(
                    StorageError,
                    "supabase.url, supabase.service_role_key",
                ):
                    get_client()
        finally:
            get_client.clear()

    def test_admin_records_do_not_include_edit_tokens(self):
        client = FakeSupabaseClient()
        get_response_records.clear()
        try:
            with patch("lib.storage.get_client", return_value=client):
                save_submission(
                    {"q1": "Test", "q6": OPPORTUNITY_OPTIONS[0]},
                    "response-id",
                    "private-edit-token",
                    is_edit=False,
                )
                client.rows.append(("not", "a row dict"))
                records = get_response_records()
        finally:
            get_response_records.clear()

        self.assertEqual(len(records), 1)
        self.assertIsInstance(records, list)
        self.assertTrue(all(isinstance(record, dict) for record in records))
        self.assertEqual(records[0]["Full Name"], "Test")
        self.assertIn("Timestamp", records[0])
        self.assertEqual(records[0]["Response ID"], "response-id")
        self.assertNotIn("Edit Token", records[0])

    def test_tracker_records_include_follow_up_columns(self):
        client = FakeSupabaseClient()
        client.rows.append(
            {
                "response_id": "response-id",
                "edit_token": "private-edit-token",
                "record": {
                    "Timestamp": "18/11/2026 12:00:00",
                    "Response ID": "response-id",
                    "Which opportunity are you interested in?": OPPORTUNITY_OPTIONS[0],
                },
                "follow_up": {header: "retained" for header in TRACKER_FOLLOW_UP_HEADERS},
                "created_at": "2026-11-18T12:00:00+00:00",
            }
        )
        get_tracker_records.clear()
        try:
            with patch("lib.storage.get_client", return_value=client):
                records = get_tracker_records()
        finally:
            get_tracker_records.clear()

        self.assertEqual(len(records), 1)
        self.assertEqual(set(records[0]), set(TRACKER_HEADERS))
        self.assertEqual(
            [records[0][header] for header in TRACKER_FOLLOW_UP_HEADERS],
            ["retained"] * len(TRACKER_FOLLOW_UP_HEADERS),
        )

    def test_records_parse_json_string_fields(self):
        client = FakeSupabaseClient()
        client.rows.append(
            {
                "response_id": "response-id",
                "record": json.dumps(
                    {
                        "Timestamp": "18/11/2026 12:00:00",
                        "Full Name": "Test",
                        "Response ID": "response-id",
                        "Which opportunity are you interested in?": OPPORTUNITY_OPTIONS[0],
                    }
                ),
                "follow_up": json.dumps(
                    {header: "retained" for header in TRACKER_FOLLOW_UP_HEADERS}
                ),
            }
        )
        get_response_records.clear()
        get_tracker_records.clear()
        try:
            with patch("lib.storage.get_client", return_value=client):
                response_records = get_response_records()
                tracker_records = get_tracker_records()
        finally:
            get_response_records.clear()
            get_tracker_records.clear()

        self.assertEqual(response_records[0]["Full Name"], "Test")
        self.assertEqual(response_records[0]["Response ID"], "response-id")
        self.assertEqual(
            [tracker_records[0][header] for header in TRACKER_FOLLOW_UP_HEADERS],
            ["retained"] * len(TRACKER_FOLLOW_UP_HEADERS),
        )

    def test_pdf_downloads_return_pdf_documents(self):
        record = {
            "Full Name": "Test Person",
            "Email Address": "test@example.com",
            "Which opportunity are you interested in?": OPPORTUNITY_OPTIONS[0],
            "Response ID": "response-id",
        }
        summary = summary_pdf({"Total": 1, "AWS only": 1}, [record])
        receipt = receipt_pdf(record)
        self.assertTrue(summary.startswith(b"%PDF"))
        self.assertTrue(receipt.startswith(b"%PDF"))

    @staticmethod
    def _question_label(number):
        from lib.form import AWS_QUESTIONS, HACKATHON_QUESTIONS

        questions = AWS_QUESTIONS + HACKATHON_QUESTIONS
        return next(question.label for question in questions if question.key == f"q{number}")


class FakeSupabaseResponse:
    def __init__(self, data):
        self.data = data

    def __iter__(self):
        return iter((("data", self.data),))


class FakeSupabaseClient:
    def __init__(self):
        self.rows = []

    def table(self, name):
        if name != "responses":
            raise AssertionError(f"Unexpected table: {name}")
        return FakeSupabaseQuery(self)


class FakeSupabaseQuery:
    def __init__(self, client):
        self.client = client
        self.action = "select"
        self.filters = []
        self.limit_value = None
        self.payload = None
        self.returning = False

    def select(self, columns):
        self.returning = True
        return self

    def eq(self, column, value):
        self.filters.append((column, value))
        return self

    def limit(self, value):
        self.limit_value = value
        return self

    def order(self, column, desc=False):
        return self

    def insert(self, payload):
        self.action = "insert"
        self.payload = deepcopy(payload)
        return self

    def update(self, payload):
        self.action = "update"
        self.payload = deepcopy(payload)
        return self

    def execute(self):
        if self.action == "insert":
            row = deepcopy(self.payload)
            self.client.rows.append(row)
            return FakeSupabaseResponse([row])

        matched = [
            row
            for row in self.client.rows
            if all(row.get(column) == value for column, value in self.filters)
        ]
        if self.action == "update":
            for row in matched:
                row.update(deepcopy(self.payload))
        if self.limit_value is not None:
            matched = matched[:self.limit_value]
        return FakeSupabaseResponse(deepcopy(matched) if self.returning else [])


if __name__ == "__main__":
    unittest.main()
