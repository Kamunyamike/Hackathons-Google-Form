from html import escape
from secrets import token_urlsafe
from urllib.parse import quote
from uuid import uuid4

import streamlit as st

from lib.form import (
    AWS_DESCRIPTION,
    AWS_QUESTIONS,
    AWS_SECTION_TITLE,
    BRANCH_QUESTIONS,
    BOTH_SECTION_TITLE,
    CONSENT_OPTIONS,
    CONSENT_HELP_TEXT,
    CONSENT_QUESTION_LABEL,
    CONSENT_SECTION_TITLE,
    DESCRIPTION,
    FUTURE_OPPORTUNITY_OPTIONS,
    FUTURE_QUESTION_LABEL,
    HACKATHON_DESCRIPTION,
    HACKATHON_QUESTIONS,
    HACKATHON_SECTION_TITLE,
    OPPORTUNITY_OPTIONS,
    OPPORTUNITY_QUESTION,
    OPPORTUNITY_SELECTION_TITLE,
    PAGE1_PROGRAM_FIELD,
    PAGE1_RADIO_QUESTIONS,
    PAGE1_TEXT_FIELDS,
    PAGE3_SECTION_TITLE,
    TITLE,
    clear_hidden_branch_answers,
    validate_consent,
    validate_event,
    validate_page1,
)
from lib.sheets import SheetsError, get_response_by_edit_token, save_submission

st.set_page_config(
    page_title=TITLE,
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root { --navy:#070d2b; --orange:#f7a51c; --violet:#6d3cf0; --yellow:#ffc72c; --red:#d32f2f; }
    .stApp { background:var(--navy); color:#fff; }
    [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
    [data-testid="stStatusWidget"], #MainMenu, footer, [data-testid="stDeployButton"],
    button[data-testid="stDeployButton"] { visibility:hidden; display:none; }
    [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display:none; }
    .block-container { max-width:760px; padding:1.1rem 1rem 3rem; }
    h1, h2, h3, p, label { color:#fff; }
    .form-description { color:#20233c; line-height:1.55; }
    .question-card { border:0; border-radius:16px; background:#fff; padding:1rem 1.15rem; margin:.75rem 0; color:#11152d; }
    [data-testid="stVerticalBlockBorderWrapper"] { background:#fff; border:0; border-radius:16px; color:#11152d; padding:.25rem .4rem; }
    [data-testid="stVerticalBlockBorderWrapper"] label,
    [data-testid="stVerticalBlockBorderWrapper"] p,
    [data-testid="stVerticalBlockBorderWrapper"] .stMarkdown { color:#11152d !important; }
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stRadio"] label,
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCheckbox"] label {
        background:#fff; border:1px solid #dfe2eb; border-radius:12px;
        min-height:52px; padding:.75rem .9rem; margin:.35rem 0; width:100%;
        display:flex; align-items:center; box-sizing:border-box; color:#11152d !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stRadio"] > div,
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCheckbox"] > label { width:100%; }
    [data-testid="stVerticalBlockBorderWrapper"] input[type="text"],
    [data-testid="stVerticalBlockBorderWrapper"] input[type="email"] { color:#11152d; }
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stRadio"] label:has(input:checked),
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCheckbox"] label:has(input:checked) {
        border-color:var(--orange); box-shadow:0 0 0 1px var(--orange);
    }
    [data-testid="stProgressBar"] > div > div { background:var(--orange); }
    div.stButton > button { border-radius:12px; min-height:48px; font-weight:700; }
    div.stButton > button[kind="primary"] { background:var(--orange); color:#11152d; border:0; width:100%; }
    a[data-testid="stLinkButton"] { border-radius:12px; min-height:48px; }
    a.whatsapp-link { display:block; text-align:center; text-decoration:none; padding:.8rem 1rem;
        margin:.5rem 0; border-radius:12px; min-height:48px; box-sizing:border-box;
        font-weight:700; color:white; background:#20b858; }
    .required-error { color:#b3261e !important; font-size:.86rem; padding:.1rem .2rem .35rem; }
    .section-description { color:#222641; line-height:1.55; }
    .honeypot, div[data-testid="stTextInput"]:has(input[aria-label="Leave this field empty"]) { display:none !important; }
    @media (max-width:600px) {
        .block-container { padding-left:.75rem; padding-right:.75rem; }
        div.stButton > button { width:100%; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _header():
    st.markdown(
        """
        <div style="width:100%;aspect-ratio:4/1;border-radius:16px;overflow:hidden;margin-bottom:1rem">
          <svg viewBox="0 0 800 200" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="AfriCDSA Community Opportunities 2026">
            <defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#070d2b"/><stop offset="1" stop-color="#242060"/></linearGradient></defs>
            <rect width="800" height="200" fill="url(#bg)"/>
            <g fill="none" stroke-width="2" opacity=".8">
              <path stroke="#f7a51c" d="M56 29l20 12v23L56 76 36 64V41zM126 94l20 12v23l-20 12-20-12v-23zM725 20l22 13v25l-22 13-22-13V33z"/>
              <path stroke="#6d3cf0" d="M694 111l19 11v22l-19 11-19-11v-22zM90 143l16 9v18l-16 9-16-9v-18zM772 91l16 9v18l-16 9-16-9v-18z"/>
            </g>
            <text x="400" y="83" text-anchor="middle" fill="#ffffff" font-family="Arial,sans-serif" font-size="29" font-weight="700">AfriCDSA Community · Opportunities 2026</text>
            <g font-family="Arial,sans-serif" font-size="13" font-weight="700">
              <rect x="248" y="108" width="132" height="30" rx="15" fill="#f7a51c"/><text x="314" y="128" text-anchor="middle" fill="#070d2b">AWS SBG · 26 Nov</text>
              <rect x="393" y="108" width="166" height="30" rx="15" fill="#6d3cf0"/><text x="476" y="128" text-anchor="middle" fill="#fff">Hack for Inclusion · 7–9 Jan</text>
            </g>
          </svg>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _answers():
    return {key: st.session_state.get(key) for key in (
        "q1", "q2", "q3", "q4", "q5", "q6",
        *(question.key for question in AWS_QUESTIONS + HACKATHON_QUESTIONS),
        "q15", "q16",
    )}


def _load_edit_response():
    edit_token = st.query_params.get("edit")
    if not edit_token or st.session_state.get("_loaded_edit_token") == edit_token:
        return
    try:
        record = get_response_by_edit_token(edit_token)
    except SheetsError as error:
        st.error(str(error))
        return
    if not record:
        st.error("This edit link is invalid or has expired.")
        return

    opportunity = record.get("Which opportunity are you interested in?", "")
    values = {
        "q1": record.get("Full Name", ""),
        "q2": record.get("Email Address", ""),
        "q3": record.get("Phone Number", ""),
        "q4": record.get("Are you a Student or Alumni?", ""),
        "q5": record.get("Current Program or Profession", ""),
        "q6": opportunity,
    }
    if opportunity == OPPORTUNITY_OPTIONS[2]:
        prefix = "AWS Event and Hackathon Interest - "
        for question in AWS_QUESTIONS + HACKATHON_QUESTIONS:
            values[question.key] = record.get(prefix + question.label, "")
    elif opportunity == OPPORTUNITY_OPTIONS[0]:
        prefix = "AWS Event Interest - "
        for question in AWS_QUESTIONS:
            values[question.key] = record.get(prefix + question.label, "")
    elif opportunity == OPPORTUNITY_OPTIONS[1]:
        prefix = "Hackathon Interest - "
        for question in HACKATHON_QUESTIONS:
            values[question.key] = record.get(prefix + question.label, "")
    for key in ("q7", "q8", "q9", "q10", "q11", "q12", "q13", "q14"):
        values.setdefault(key, "")
    values["q15"] = [
        value.strip()
        for value in record.get(
            "Would you like to receive information about future opportunities? Tick all that apply.",
            "",
        ).split(",")
        if value.strip()
    ]
    values["q16"] = [
        value.strip()
        for value in record.get("I agree to be contacted by AfriCDSA regarding:", "").split(",")
        if value.strip()
    ]
    for key, value in values.items():
        st.session_state[key] = value
    for key in ("q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8", "q9", "q10", "q11", "q12", "q13", "q14"):
        st.session_state.pop(f"_widget_{key}", None)
    for question_key, options in (("q15", FUTURE_OPPORTUNITY_OPTIONS), ("q16", CONSENT_OPTIONS)):
        for index, _ in enumerate(options):
            st.session_state.pop(f"{question_key}_option_{index}", None)
    st.session_state["response_id"] = record.get("Response ID", "")
    st.session_state["edit_token"] = edit_token
    st.session_state["is_edit"] = True
    st.session_state["page"] = 1
    st.session_state["_loaded_edit_token"] = edit_token


def _required_error(errors, key):
    if key in errors:
        st.markdown(
            f'<div class="required-error">{escape(errors[key])}</div>',
            unsafe_allow_html=True,
        )


def _persist_widget_value(answer_key: str, widget_key: str):
    st.session_state[answer_key] = st.session_state.get(widget_key)


def _persist_checkbox_group(question_key: str, options: tuple[str, ...]):
    st.session_state[question_key] = [
        option
        for index, option in enumerate(options)
        if st.session_state.get(f"{question_key}_option_{index}", False)
    ]


def _text_field(key: str, label: str, help_text: str | None, errors: dict):
    widget_key = f"_widget_{key}"
    widget_exists = widget_key in st.session_state
    kwargs = {} if widget_exists else {"value": st.session_state.get(key, "")}
    with st.container(border=True):
        st.text_input(
            label,
            key=widget_key,
            help=help_text,
            on_change=_persist_widget_value,
            args=(key, widget_key),
            **kwargs,
        )
    st.session_state[key] = st.session_state.get(widget_key, "")
    _required_error(errors, key)


def _radio(question, errors):
    widget_key = f"_widget_{question.key}"
    widget_exists = widget_key in st.session_state
    with st.container(border=True):
        current = st.session_state.get(widget_key, st.session_state.get(question.key))
        index = question.options.index(current) if current in question.options else None
        kwargs = {} if widget_exists else {"index": index}
        st.radio(
            question.label,
            question.options,
            key=widget_key,
            on_change=_persist_widget_value,
            args=(question.key, widget_key),
            **kwargs,
        )
    st.session_state[question.key] = st.session_state.get(widget_key)
    _required_error(errors, question.key)


def _checkbox_group(question_key, label, options, help_text=None):
    with st.container(border=True):
        st.markdown(f"**{label}**")
        if help_text:
            st.caption(help_text)
        for index, option in enumerate(options):
            widget_key = f"{question_key}_option_{index}"
            widget_exists = widget_key in st.session_state
            checkbox_kwargs = (
                {}
                if widget_exists
                else {"value": option in set(st.session_state.get(question_key, []))}
            )
            st.checkbox(
                option,
                key=widget_key,
                on_change=_persist_checkbox_group,
                args=(question_key, options),
                **checkbox_kwargs,
            )
    selected = [
        option for index, option in enumerate(options)
        if st.session_state.get(f"{question_key}_option_{index}", False)
    ]
    st.session_state[question_key] = selected
    return selected


def _init_session():
    st.session_state.setdefault("page", 1)
    st.session_state.setdefault("completed", False)
    st.session_state.setdefault("is_edit", False)


def _page_one():
    st.markdown(f"## {TITLE}")
    st.markdown(
        f'<div class="question-card form-description">{escape(DESCRIPTION).replace(chr(10), "<br>")}</div>',
        unsafe_allow_html=True,
    )
    errors = st.session_state.get("_page1_errors", {})
    for key, label, help_text in PAGE1_TEXT_FIELDS:
        _text_field(key, label, help_text, errors)
    for question in PAGE1_RADIO_QUESTIONS:
        _radio(question, errors)
    _text_field(PAGE1_PROGRAM_FIELD[0], PAGE1_PROGRAM_FIELD[1], PAGE1_PROGRAM_FIELD[2], errors)
    st.markdown(f"### {OPPORTUNITY_SELECTION_TITLE}")
    _radio(OPPORTUNITY_QUESTION, errors)
    if st.button("Next", type="primary", use_container_width=True, key="page1_next"):
        errors = validate_page1(_answers())
        st.session_state["_page1_errors"] = errors
        if not errors:
            st.session_state["page"] = 2
            st.rerun()
        st.rerun()


def _page_two():
    opportunity = st.session_state.get("q6", "")
    if opportunity not in BRANCH_QUESTIONS:
        st.session_state["page"] = 1
        st.rerun()
    st.markdown("## Page 2")
    if opportunity == OPPORTUNITY_OPTIONS[0]:
        st.markdown(f"### {AWS_SECTION_TITLE}")
    elif opportunity == OPPORTUNITY_OPTIONS[1]:
        st.markdown(f"### {HACKATHON_SECTION_TITLE}")
    else:
        st.markdown(f"### {BOTH_SECTION_TITLE}")
    if opportunity in (OPPORTUNITY_OPTIONS[0], OPPORTUNITY_OPTIONS[2]):
        st.markdown(f'<div class="section-description">{escape(AWS_DESCRIPTION)}</div>', unsafe_allow_html=True)
    if opportunity in (OPPORTUNITY_OPTIONS[1], OPPORTUNITY_OPTIONS[2]):
        st.markdown(f'<div class="section-description">{escape(HACKATHON_DESCRIPTION)}</div>', unsafe_allow_html=True)
    errors = st.session_state.get("_event_errors", {})
    for question in BRANCH_QUESTIONS[opportunity]:
        _radio(question, errors)

    back, next_column = st.columns(2)
    with back:
        if st.button("Back", use_container_width=True, key="page2_back"):
            st.session_state["page"] = 1
            st.rerun()
    with next_column:
        if st.button("Next", type="primary", use_container_width=True, key="page2_next"):
            errors = validate_event(_answers())
            st.session_state["_event_errors"] = errors
            if not errors:
                st.session_state["page"] = 3
                st.rerun()
            st.rerun()


def _page_three():
    st.markdown(f"## {PAGE3_SECTION_TITLE}")
    _checkbox_group(
        "q15",
        FUTURE_QUESTION_LABEL,
        FUTURE_OPPORTUNITY_OPTIONS,
    )
    st.markdown(f"### {CONSENT_SECTION_TITLE}")
    _checkbox_group(
        "q16",
        CONSENT_QUESTION_LABEL,
        CONSENT_OPTIONS,
        help_text=CONSENT_HELP_TEXT,
    )
    _required_error(
        {"q16": "This is a required question"}
        if st.session_state.get("_consent_error") and not st.session_state.get("q16")
        else {},
        "q16",
    )
    with st.container():
        st.text_input(
            "Leave this field empty",
            key="honeypot",
            label_visibility="collapsed",
            placeholder="",
        )
    back, submit_column = st.columns(2)
    with back:
        if st.button("Back", use_container_width=True, key="page3_back"):
            st.session_state["page"] = 2
            st.rerun()
    with submit_column:
        if st.button("Submit", type="primary", use_container_width=True, key="submit"):
            errors = validate_consent(_answers())
            st.session_state["_consent_error"] = bool(errors)
            if errors:
                st.rerun()
            answers = clear_hidden_branch_answers(_answers())
            st.session_state.update(answers)
            if st.session_state.get("honeypot"):
                st.query_params.clear()
                st.session_state["_loaded_edit_token"] = None
                st.session_state["completed"] = True
                st.session_state["honeypot_submission"] = True
                st.rerun()

            response_id = st.session_state.setdefault("response_id", str(uuid4()))
            edit_token = st.session_state.setdefault("edit_token", token_urlsafe(32))
            try:
                save_submission(
                    answers,
                    response_id,
                    edit_token,
                    bool(st.session_state.get("is_edit")),
                )
            except SheetsError as error:
                st.error(str(error))
                return
            st.query_params.clear()
            st.session_state["_loaded_edit_token"] = None
            st.session_state["completed"] = True
            st.session_state["_consent_error"] = False
            st.rerun()


def _confirmation():
    st.markdown(f"## {TITLE}")
    if st.session_state.get("honeypot_submission"):
        return
    try:
        public_url = st.secrets["app"]["public_url"].rstrip("/")
    except KeyError:
        st.error("Set app.public_url in Streamlit secrets to display your response links.")
        return

    st.markdown(
        """
Thank you for registering with AfriCDSA. Here is what to do next.

**AWS Student Builder Group Event (Thursday 26 November, 10am to 5pm, MKCC):** Your place is confirmed only after you register on the official Meetup page. Please do it now: [https://www.meetup.com/aws-sbg-at-mount-kenya-university-thika-town-campus/events/3174261](https://www.meetup.com/aws-sbg-at-mount-kenya-university-thika-town-campus/events/3174261) Then reply "REGISTERED" to the AfriCDSA Community Team on WhatsApp. We will add you to the AfriCDSA AWS participant group.

**Hack for Inclusion Hackathon (7 to 9 January 2027):** Submit the official application by 4 December 2026: [https://forms.cloud.microsoft/r/YTeSBsC9rF](https://forms.cloud.microsoft/r/YTeSBsC9rF) We will contact you about teams and support.

Know someone who should join us? Share this form:
        """
    )
    st.code(public_url, language=None)
    whatsapp_url = "https://wa.me/?text=" + quote(
        f"Know someone who should join us? Share this form: {public_url}",
        safe="",
    )
    st.markdown(
        f'<a class="whatsapp-link" href="{escape(whatsapp_url, quote=True)}" target="_blank" rel="noopener noreferrer">Share on WhatsApp</a>',
        unsafe_allow_html=True,
    )
    if st.session_state.get("edit_token"):
        st.link_button(
            "Edit your response",
            f"{public_url}/?edit={quote(st.session_state['edit_token'], safe='')}",
            use_container_width=True,
        )


_init_session()
if st.query_params.get("edit") and st.query_params.get("edit") != st.session_state.get("_loaded_edit_token"):
    st.session_state["completed"] = False
if not st.session_state.get("completed"):
    _load_edit_response()
    _header()
    st.progress(st.session_state["page"] / 3, text=f"Page {st.session_state['page']} of 3")
    if st.session_state["page"] == 1:
        _page_one()
    elif st.session_state["page"] == 2:
        _page_two()
    else:
        _page_three()
else:
    _header()
    _confirmation()
