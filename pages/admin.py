from hmac import compare_digest
from io import BytesIO

import pandas as pd
import streamlit as st

from lib.form import OPPORTUNITY_OPTIONS
from lib.pdf import receipt_pdf, summary_pdf
from lib.sheets import (
    FORM_HEADERS,
    SheetsError,
    TRACKER_HEADERS,
    get_response_records,
    get_tracker_records,
    rebuild_tracker,
)
from lib.theme import apply_input_styles

st.set_page_config(
    page_title="AfriCDSA Opportunities Admin",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .stApp { background:#070d2b; color:#fff; }
    [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
    [data-testid="stStatusWidget"], #MainMenu, footer, [data-testid="stDeployButton"] { display:none; }
    [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display:none; }
    .block-container { max-width:1400px; }
    h1,h2,h3,p,label { color:#fff; }
    div.stButton > button, div.stDownloadButton > button { border-radius:10px; min-height:44px; }
    </style>
    """,
    unsafe_allow_html=True,
)
apply_input_styles()

st.title("AfriCDSA Opportunities Admin")

if not st.session_state.get("admin_authenticated"):
    with st.form("admin_login"):
        password = st.text_input("Password", type="password")
        login = st.form_submit_button("Log in")
    if login:
        try:
            expected_password = st.secrets["admin"]["password"]
        except KeyError:
            st.error("Admin access is not configured. Set admin.password in Streamlit secrets.")
        else:
            if compare_digest(password, str(expected_password)):
                st.session_state["admin_authenticated"] = True
                st.rerun()
            st.error("Incorrect password.")
    st.stop()

try:
    records = get_response_records()
    tracker_records = get_tracker_records()
except SheetsError as error:
    st.error(str(error))
    st.stop()


def _count_yes(key: str) -> int:
    question_headers = {
        "q7": "AWS Event Interest - Are you available to attend the event?",
        "q8": "AWS Event Interest - Would you like to join the AfriCDSA AWS participant group?",
        "q10": "AWS Event Interest - After submitting this form, are you willing to complete the official Meetup registration?",
        "q12": "Hackathon Interest - Would you like to join a team?",
        "q14": "Hackathon Interest - Do you already have a project idea?",
    }
    both_headers = {
        "q7": "AWS Event and Hackathon Interest - Are you available to attend the event?",
        "q8": "AWS Event and Hackathon Interest - Would you like to join the AfriCDSA AWS participant group?",
        "q10": "AWS Event and Hackathon Interest - After submitting this form, are you willing to complete the official Meetup registration?",
        "q12": "AWS Event and Hackathon Interest - Would you like to join a team?",
        "q14": "AWS Event and Hackathon Interest - Do you already have a project idea?",
    }
    return sum(
        1
        for record in records
        if (
            record.get(both_headers[key], "")
            if record.get("Which opportunity are you interested in?") == OPPORTUNITY_OPTIONS[2]
            else record.get(question_headers[key], "")
        ) == "Yes"
    )


selection_header = "Which opportunity are you interested in?"
total = len(records)
aws_only = sum(record.get(selection_header) == OPPORTUNITY_OPTIONS[0] for record in records)
hackathon_only = sum(record.get(selection_header) == OPPORTUNITY_OPTIONS[1] for record in records)
both = sum(record.get(selection_header) == OPPORTUNITY_OPTIONS[2] for record in records)
aws_interest = aws_only + both
hackathon_interest = hackathon_only + both
counts = {
    "Total": total,
    "AWS only": aws_only,
    "Hackathon only": hackathon_only,
    "Both": both,
    "All AWS interest": aws_interest,
    "All Hackathon interest": hackathon_interest,
    "Yes Q7": _count_yes("q7"),
    "Yes Q8": _count_yes("q8"),
    "Yes Q10": _count_yes("q10"),
    "Yes Q12": _count_yes("q12"),
    "Yes Q14": _count_yes("q14"),
}
st.subheader("Registration counts")
st.dataframe(
    pd.DataFrame([{"Count": key, "Registrants": value} for key, value in counts.items()]),
    hide_index=True,
    use_container_width=True,
)

raw_df = pd.DataFrame(records, columns=[header for header in FORM_HEADERS if header != "Edit Token"])
tracker_df = pd.DataFrame(tracker_records, columns=TRACKER_HEADERS)
st.subheader("Registrants")
search = st.text_input("Search registrants")
if search:
    mask = raw_df.astype(str).apply(
        lambda column: column.str.contains(search, case=False, na=False, regex=False)
    ).any(axis=1)
    visible_df = raw_df[mask]
else:
    visible_df = raw_df
st.dataframe(visible_df, hide_index=True, use_container_width=True)

excel_buffer = BytesIO()
with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
    raw_df.to_excel(writer, sheet_name="Form Responses 1", index=False)
    tracker_df.to_excel(writer, sheet_name="Tracker", index=False)
st.download_button(
    "Download Excel (.xlsx)",
    data=excel_buffer.getvalue(),
    file_name="africdsa-opportunities-2026.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
)
st.download_button(
    "Download CSV (.csv)",
    data=raw_df.to_csv(index=False).encode("utf-8-sig"),
    file_name="africdsa-opportunities-2026.csv",
    mime="text/csv",
    use_container_width=True,
)
st.download_button(
    "Download PDF summary report",
    data=summary_pdf(counts, records),
    file_name="africdsa-opportunities-summary.pdf",
    mime="application/pdf",
    use_container_width=True,
)

if records:
    options = {
        f"{record.get('Full Name', '')} <{record.get('Email Address', '')}> [{record.get('Response ID', '')}]": record
        for record in records
    }
    chosen_label = st.selectbox("Choose a registrant for a PDF receipt", list(options))
    st.download_button(
        "Download PDF receipt",
        data=receipt_pdf(options[chosen_label]),
        file_name="africdsa-registration-receipt.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
else:
    st.info("No registrations yet.")

if st.button("Rebuild Tracker sheet", type="primary"):
    try:
        rebuilt_count = rebuild_tracker()
    except SheetsError as error:
        st.error(str(error))
    else:
        st.success(f"Tracker sheet rebuilt for {rebuilt_count} responses.")
        st.rerun()

if st.button("Log out"):
    st.session_state.pop("admin_authenticated", None)
    st.rerun()
