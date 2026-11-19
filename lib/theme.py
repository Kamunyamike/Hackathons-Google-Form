"""Shared CSS so every input field stays readable on the navy theme."""

import streamlit as st

FIELD_BG = "#141b45"
FIELD_BORDER = "#596078"
FIELD_TEXT = "#ffffff"
PLACEHOLDER = "#b5bad0"
ORANGE = "#f7a51c"

INPUT_CSS = f"""
<style>
/* ---- Text, password, number, textarea and select fields ---- */
[data-baseweb="input"],
[data-baseweb="base-input"],
[data-baseweb="textarea"],
[data-baseweb="select"] > div,
[data-testid="stTextInput"] [data-baseweb="input"] > div,
[data-testid="stNumberInput"] [data-baseweb="input"] > div {{
    background:{FIELD_BG} !important;
    background-color:{FIELD_BG} !important;
    border-radius:10px;
}}
[data-baseweb="input"],
[data-baseweb="textarea"],
[data-baseweb="select"] > div {{
    border:1px solid {FIELD_BORDER} !important;
}}
[data-baseweb="input"]:focus-within,
[data-baseweb="textarea"]:focus-within,
[data-baseweb="select"] > div:focus-within {{
    border-color:{ORANGE} !important;
    box-shadow:0 0 0 1px {ORANGE};
}}
[data-baseweb="input"] input,
[data-baseweb="base-input"] input,
[data-baseweb="textarea"] textarea,
[data-baseweb="select"] div,
[data-baseweb="select"] input {{
    background:transparent !important;
    color:{FIELD_TEXT} !important;
    -webkit-text-fill-color:{FIELD_TEXT} !important;
    caret-color:{ORANGE};
}}
[data-baseweb="input"] input::placeholder,
[data-baseweb="textarea"] textarea::placeholder {{
    color:{PLACEHOLDER} !important;
    -webkit-text-fill-color:{PLACEHOLDER} !important;
    opacity:1;
}}
/* Browser autofill otherwise paints a white/yellow box with invisible text */
input:-webkit-autofill,
input:-webkit-autofill:hover,
input:-webkit-autofill:focus,
textarea:-webkit-autofill {{
    -webkit-box-shadow:0 0 0 1000px {FIELD_BG} inset !important;
    -webkit-text-fill-color:{FIELD_TEXT} !important;
    caret-color:{ORANGE};
    transition:background-color 9999s ease-out 0s;
}}
/* Password "show" eye and number +/- buttons inside the field */
[data-baseweb="input"] button,
[data-testid="stNumberInput"] button {{
    background:transparent !important;
    color:{FIELD_TEXT} !important;
}}
[data-baseweb="input"] button svg {{ fill:{FIELD_TEXT}; }}

/* ---- Secondary buttons (Back, Log in, downloads, Log out) ---- */
div.stButton > button:not([kind="primary"]),
div.stDownloadButton > button,
div[data-testid="stFormSubmitButton"] > button,
a[data-testid="stLinkButton"],
a[data-testid="stBaseLinkButton-secondary"] {{
    background:transparent !important;
    color:{FIELD_TEXT} !important;
    border:1px solid {FIELD_BORDER} !important;
}}
div.stButton > button:not([kind="primary"]):hover,
div.stDownloadButton > button:hover,
div[data-testid="stFormSubmitButton"] > button:hover,
a[data-testid="stLinkButton"]:hover {{
    border-color:{ORANGE} !important;
    color:{ORANGE} !important;
}}
div.stButton > button p,
div.stDownloadButton > button p,
div[data-testid="stFormSubmitButton"] > button p {{ color:inherit !important; }}

/* Admin login form box */
[data-testid="stForm"] {{ border:1px solid {FIELD_BORDER}; border-radius:14px; }}
</style>
"""


def apply_input_styles() -> None:
    st.markdown(INPUT_CSS, unsafe_allow_html=True)
