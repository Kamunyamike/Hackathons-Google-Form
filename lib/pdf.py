"""PDF report and receipt generation."""

from fpdf import FPDF
from fpdf.enums import MethodReturnValue


def _pdf_text(value) -> str:
    return str(value or "").encode("latin-1", "replace").decode("latin-1")


def _new_pdf(title: str) -> FPDF:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()
    pdf.set_text_color(7, 13, 43)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 9, _pdf_text(title))
    pdf.ln(3)
    return pdf


def _table(pdf: FPDF, headers: list[str], rows: list[list[str]]):
    widths = [190 / len(headers)] * len(headers)

    def draw_row(values, fill=False):
        line_height = 5
        heights = [
            pdf.multi_cell(
                width - 4,
                line_height,
                _pdf_text(value),
                dry_run=True,
                output=MethodReturnValue.HEIGHT,
            )
            for width, value in zip(widths, values)
        ]
        height = max(7, max(heights, default=7) + 4)
        if pdf.get_y() + height > pdf.page_break_trigger:
            pdf.add_page()
            draw_header()
        y = pdf.get_y()
        x = pdf.l_margin
        for width, value in zip(widths, values):
            pdf.set_fill_color(109, 60, 240) if fill else None
            pdf.rect(x, y, width, height, style="DF" if fill else "D")
            pdf.set_xy(x + 2, y + 2)
            pdf.multi_cell(width - 4, line_height, _pdf_text(value))
            x += width
        pdf.set_xy(pdf.l_margin, y + height)

    def draw_header():
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(255, 255, 255)
        draw_row(headers, fill=True)
        pdf.set_text_color(7, 13, 43)

    pdf.set_font("Helvetica", "B", 8)
    draw_header()
    pdf.set_text_color(7, 13, 43)
    pdf.set_font("Helvetica", size=8)
    for row in rows:
        draw_row(row)


def summary_pdf(counts: dict[str, int], rows: list[dict]) -> bytes:
    pdf = _new_pdf("AfriCDSA Community Opportunities Registration - Summary")
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Registration counts", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=9)
    for label, count in counts.items():
        pdf.cell(0, 6, _pdf_text(f"{label}: {count}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Registrants", new_x="LMARGIN", new_y="NEXT")
    headers = ["Full Name", "Email Address", "Opportunity"]
    table_rows = [
        [
            record.get("Full Name", ""),
            record.get("Email Address", ""),
            record.get("Which opportunity are you interested in?", ""),
        ]
        for record in rows
    ]
    if table_rows:
        _table(pdf, headers, table_rows)
    else:
        pdf.set_font("Helvetica", size=9)
        pdf.cell(0, 7, "No registrations yet.")
    return bytes(pdf.output())


def receipt_pdf(record: dict) -> bytes:
    pdf = _new_pdf("AfriCDSA Community Opportunities Registration - Receipt")
    pdf.set_font("Helvetica", size=10)
    fields = [
        ("Full Name", "Full Name"),
        ("Email Address", "Email Address"),
        ("Phone Number", "Phone Number"),
        ("Are you a Student or Alumni?", "Are you a Student or Alumni?"),
        ("Current Program or Profession", "Current Program or Profession"),
        ("Which opportunity are you interested in?", "Which opportunity are you interested in?"),
    ]
    for label, key in fields:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 6, _pdf_text(label))
        pdf.set_font("Helvetica", size=9)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 6, _pdf_text(record.get(key, "")))
        pdf.ln(1)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 7, "Event interests")
    pdf.set_font("Helvetica", size=9)
    for key, value in record.items():
        if key.startswith(("AWS Event Interest - ", "Hackathon Interest - ", "AWS Event and Hackathon Interest - ")):
            if value:
                pdf.set_x(pdf.l_margin)
                pdf.multi_cell(0, 6, _pdf_text(f"{key.split(' - ', 1)[1]}: {value}"))
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 6, _pdf_text(f"Future opportunities: {record.get('Would you like to receive information about future opportunities? Tick all that apply.', '')}"))
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 6, _pdf_text(f"Consent: {record.get('I agree to be contacted by AfriCDSA regarding:', '')}"))
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 6, _pdf_text(f"Response ID: {record.get('Response ID', '')}"))
    return bytes(pdf.output())
