import unittest
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
from lib.sheets import (
    FORM_HEADERS,
    TRACKER_FOLLOW_UP_HEADERS,
    _record_row,
    _tracker_row,
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


class SheetMappingTests(unittest.TestCase):
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
        class FakeWorksheet:
            def __init__(self):
                self.rows = [FORM_HEADERS]

            def row_values(self, row_number):
                return self.rows[row_number - 1] if len(self.rows) >= row_number else []

            def get_all_values(self):
                return self.rows

            def append_row(self, values, value_input_option=None):
                self.rows.append(values)

            def update(self, range_name, values, value_input_option=None):
                row_number = int(range_name.split(":", 1)[0][1:])
                self.rows[row_number - 1] = values[0]

        class FakeSpreadsheet:
            def __init__(self):
                self.form = FakeWorksheet()

            def worksheet(self, title):
                return self.form

        spreadsheet = FakeSpreadsheet()
        answers = {"q1": "Before", "q6": OPPORTUNITY_OPTIONS[0], "q7": "Yes"}
        with patch("lib.sheets.get_spreadsheet", return_value=spreadsheet):
            save_submission(answers, "response-id", "edit-token", is_edit=False)
            original_timestamp = spreadsheet.form.rows[1][0]
            answers["q1"] = "After"
            save_submission(answers, "response-id", "edit-token", is_edit=True)

        self.assertEqual(len(spreadsheet.form.rows), 2)
        record = dict(zip(FORM_HEADERS, spreadsheet.form.rows[1]))
        self.assertEqual(record["Full Name"], "After")
        self.assertEqual(record["Timestamp"], original_timestamp)
        self.assertEqual(record["Response ID"], "response-id")

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


if __name__ == "__main__":
    unittest.main()
