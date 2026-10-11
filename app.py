"""
General Surgery Dice Quiz - shared by you and your friend.

Run:  streamlit run app.py --server.address 0.0.0.0
Put sure.jpg and notsure.jpg in this same folder - they become the
background of the SURE and NOT SURE buttons.
"""

import base64
import glob
import json
import os
import random
import threading
from datetime import datetime

import streamlit as st

# ------------------------------------------------------------------ settings
TITLE = "Ivy's Bitch ass General Surgery Questions 😡!!!!!!!!!!!"

FOLDER = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_FILE = os.path.join(FOLDER, "questions.json")   # the 114 topics
MEMORY_FILE = os.path.join(FOLDER, "shared_state.json")   # shared Sure / Not sure lists
NOTEPAD_FILE = os.path.join(FOLDER, "study_notes.txt")    # the notepad

BUTTON_WIDTH = 350   # width of each picture button in pixels (height follows the picture's shape)
BUTTON_TEXT = "!!!!!!!!!!!"   # added after the words under the buttons

st.set_page_config(page_title="Surgery Dice Quiz", page_icon="🎲", layout="wide")


# ------------------------------------------------------------ load questions
@st.cache_data
def load_questions():
    with open(QUESTIONS_FILE, encoding="utf-8") as f:
        return {q["id"]: q for q in json.load(f)}


@st.cache_resource
def get_lock():
    return threading.Lock()   # stops two people saving at the exact same moment


QUESTIONS = load_questions()
LOCK = get_lock()


# ------------------------------------------------- shared memory (the files)
def load_memory():
    """Returns {"sure": {id: info}, "unsure": {id: info}}"""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"sure": {}, "unsure": {}}


def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=1)
    save_notepad(memory)


def save_notepad(memory):
    """Writes the two lists into study_notes.txt"""
    lines = [f"SAVED {datetime.now():%d %b %Y %H:%M}", ""]
    for key, heading in (("sure", "SURE"), ("unsure", "NOT SURE")):
        lines.append(f"{heading} ({len(memory[key])})")
        lines.append("-" * 30)
        for qid, info in memory[key].items():
            q = QUESTIONS[int(qid)]
            lines.append(f"Q{q['id']}. {q['topic']}  [{q['ref']}]  ({info['at']})")
        lines.append("")
    text = "\n".join(lines)
    with open(NOTEPAD_FILE, "w", encoding="utf-8") as f:
        f.write(text)
    return text


def mark(qid, answer):
    """answer is 'sure' or 'unsure'. A topic can only be in one list."""
    other = "unsure" if answer == "sure" else "sure"
    with LOCK:
        memory = load_memory()
        memory[other].pop(str(qid), None)
        memory[answer][str(qid)] = {"at": datetime.now().strftime("%d %b %H:%M")}
        save_memory(memory)


def remove(qid):
    with LOCK:
        memory = load_memory()
        memory["sure"].pop(str(qid), None)
        memory["unsure"].pop(str(qid), None)
        save_memory(memory)


# ---------------------------------------------- what THIS person is doing now
if "current" not in st.session_state:
    st.session_state.current = None      # the question on the table
    st.session_state.revealed = False    # has the answer been shown?

state = st.session_state


def clear_question():
    state.current = None
    state.revealed = False


# ------------------------------------------------------------------- title
st.title(TITLE)


# ------------------------------------------------------------ the counters
memory = load_memory()
already_sorted = {int(i) for i in memory["sure"]} | {int(i) for i in memory["unsure"]}

pool = [qid for qid in QUESTIONS if qid not in already_sorted]
if not pool:                      # everything sorted -> start revising all topics
    pool = list(QUESTIONS)

a, b, c = st.columns(3)
a.metric("✅ Sure", len(memory["sure"]))
b.metric("❓ Not sure", len(memory["unsure"]))
c.metric("🎲 Left to roll", len(pool))

st.divider()


# ------------------------------------------------------------ the 3 buttons
st.markdown(
    """
    <style>
    /* big Roll button in the middle */
    .st-key-roll_button { max-width: 340px; margin-left: auto; margin-right: auto; }
    .st-key-roll_button button { width: 100%; height: 72px; }
    .st-key-roll_button button p { font-size: 24px; font-weight: bold; }

    /* Reveal + Reset side by side below it (also on phones) */
    .st-key-action_row { max-width: 560px; margin: 0 auto; }
    .st-key-action_row [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; }
    .st-key-action_row [data-testid="stColumn"] { min-width: 0 !important; flex: 1 1 0 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

if st.button("🎲 Roll the dice", key="roll_button", type="primary", use_container_width=True,
             disabled=(state.current is not None or not pool)):
    state.current = random.choice(pool)
    state.revealed = False
    st.rerun()

with st.container(key="action_row"):
    reveal_col, reset_col = st.columns(2)

    if reveal_col.button("👁️ Reveal answer", use_container_width=True,
                         disabled=(state.current is None or state.revealed)):
        state.revealed = True
        st.rerun()

    if reset_col.button("🔄 Reset question", use_container_width=True,
                        disabled=(state.current is None)):
        clear_question()
        st.rerun()


# ------------------------------------------ picture buttons (sure.jpg / notsure.jpg)
def find_picture(name):
    """Finds sure.jpg / Sure.JPG / sure.png ... in this folder (any capital letters)"""
    for file in os.listdir(FOLDER):
        base, ext = os.path.splitext(file)
        if base.lower() == name and ext.lower() in (".jpg", ".jpeg", ".png", ".webp"):
            return os.path.join(FOLDER, file)
    return None


@st.cache_data
def small_picture(path):
    """Shrinks the picture so a big photo does not slow the page down"""
    from PIL import Image
    import io

    img = Image.open(path).convert("RGB")
    img.thumbnail((700, 700))          # keeps the picture's shape, only makes it smaller
    buffer = io.BytesIO()
    img.save(buffer, "JPEG", quality=85)
    return base64.b64encode(buffer.getvalue()).decode(), img.width, img.height


def button_picture_css(key, name):
    """CSS that puts a picture on the st.button that has this key"""
    path = find_picture(name)
    if path is None:
        return ""   # no picture found -> normal button with its text
    data, width, height = small_picture(path)
    return f"""
    .st-key-{key} [data-testid="stButton"] {{ display: flex; justify-content: center; }}
    .st-key-{key} button {{
        background-image: url(data:image/jpeg;base64,{data});
        background-size: 100% 100%;       /* picture fills the button exactly, no cropping */
        background-repeat: no-repeat;
        background-color: transparent;
        border: none;
        padding: 0;
        min-height: 0;
        width: {BUTTON_WIDTH}px;
        max-width: 100%;
        height: auto;
        aspect-ratio: {width} / {height};  /* button has the same shape as your picture */
        border-radius: 14px;
    }}
    .st-key-{key} button:hover {{ filter: brightness(1.15); }}
    .st-key-{key} button p {{ display: none; }}
    """


def show_sort_buttons(locked):
    """The SURE / NOT SURE picture buttons with words under them.
    locked=True shows them greyed out. Returns "sure", "unsure" or None."""
    st.markdown(
        f"""
        <style>
        {button_picture_css("sure_button", "sure")}
        {button_picture_css("unsure_button", "notsure")}
        /* keep the two buttons side by side on phones too */
        .st-key-sort_row [data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap !important; }}
        .st-key-sort_row [data-testid="stColumn"] {{ min-width: 0 !important; flex: 1 1 0 !important; }}
        .st-key-sort_row button:disabled {{ opacity: 0.4; }}
        .word-under {{ text-align: center; font-size: 22px; font-weight: bold; margin-top: 4px; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    answer = None
    with st.container(key="sort_row"):
        sure_col, unsure_col = st.columns(2)

        with sure_col:
            if st.button("Sure", key="sure_button", use_container_width=True, disabled=locked):
                answer = "sure"
            st.markdown(f"<div class='word-under'>Sure{BUTTON_TEXT}</div>", unsafe_allow_html=True)

        with unsure_col:
            if st.button("Not sure", key="unsure_button", use_container_width=True, disabled=locked):
                answer = "unsure"
            st.markdown(f"<div class='word-under'>Not sure{BUTTON_TEXT}</div>", unsafe_allow_html=True)

    for name in ("sure", "notsure"):
        if find_picture(name) is None:
            st.caption(f"⚠️ {name}.jpg not found in the app folder")

    return answer


# --------------------------------------------------------- the question card
if state.current is not None:
    q = QUESTIONS[state.current]

    with st.container(border=True):
        st.caption(f"{q['chapter']}  ·  {q['ref']}")
        st.subheader(f"Q{q['id']}. {q['topic']}")

        if not state.revealed:
            st.write("Think about what you know, then press **Reveal answer**.")
        else:
            st.info(q["answer"])
            st.write("**Did you know it?** Press a picture below.")

# the picture buttons are always visible; they unlock after you reveal the answer
answer = show_sort_buttons(locked=not (state.current is not None and state.revealed))

if answer:
    mark(state.current, answer)
    clear_question()
    st.rerun()

st.divider()


# --------------------------------------- the two columns (refresh every 5s)
@st.fragment(run_every="5s")
def show_lists():
    memory = load_memory()
    left, right = st.columns(2)

    for column, key, heading in ((left, "sure", "✅ Sure"), (right, "unsure", "❓ Not sure")):
        with column:
            st.subheader(f"{heading} ({len(memory[key])})")

            for qid, info in memory[key].items():
                q = QUESTIONS[int(qid)]
                with st.expander(f"Q{q['id']}. {q['topic']}"):
                    st.write(q["answer"])
                    if st.button("Remove from list", key=f"remove_{key}_{qid}"):
                        remove(int(qid))
                        st.rerun()


show_lists()


# ------------------------------------------------------------------- footer
st.markdown(
    "<p style='text-align:center; opacity:0.8; font-size:20px; margin-top:60px;'>"
    "Made with ❤️ by Shrubby<br>#pungu<br>#friendship goals 😉</p>",
    unsafe_allow_html=True,
)
