"""
General Surgery Dice Quiz - shared by you and your friend.

Run:  streamlit run app.py --server.address 0.0.0.0
Put image1, image2, image3 (png / jpg / jpeg / webp) in this same folder
and they show side by side above the footer.
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
TITLE = "Vaibhavi Ivy's Bitch ass General Surgery Questions 😡!!!!!!!!!!!"

FOLDER = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_FILE = os.path.join(FOLDER, "questions.json")   # the 114 topics
MEMORY_FILE = os.path.join(FOLDER, "shared_state.json")   # shared Sure / Not sure lists
NOTEPAD_FILE = os.path.join(FOLDER, "study_notes.txt")    # the notepad

PICTURES_MAX_WIDTH = 700   # total width of the 3 pictures in pixels

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
roll_col, reveal_col, reset_col = st.columns(3)

if roll_col.button("🎲 Roll the dice", type="primary", use_container_width=True,
                   disabled=(state.current is not None or not pool)):
    state.current = random.choice(pool)
    state.revealed = False
    st.rerun()

if reveal_col.button("👁️ Reveal answer", use_container_width=True,
                     disabled=(state.current is None or state.revealed)):
    state.revealed = True
    st.rerun()

if reset_col.button("🔄 Reset question", use_container_width=True,
                    disabled=(state.current is None)):
    clear_question()
    st.rerun()


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
            st.write("**Did you know it?**")
            sure_col, unsure_col = st.columns(2)

            if sure_col.button("✅ I was SURE", use_container_width=True):
                mark(q["id"], "sure")
                clear_question()
                st.rerun()

            if unsure_col.button("❓ NOT sure", use_container_width=True):
                mark(q["id"], "unsure")
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


# ------------------------------------------- 3 pictures side by side (above footer)
def find_image(name):
    """Looks for image1.png / image1.jpg / image1.jpeg / image1.webp in this folder"""
    for ext in ("png", "jpg", "jpeg", "webp"):
        for path in glob.glob(os.path.join(FOLDER, f"{name}.{ext}")) + \
                    glob.glob(os.path.join(FOLDER, f"{name}.{ext.upper()}")):
            return path
    return None


def image_to_html(path):
    ext = path.rsplit(".", 1)[1].lower().replace("jpg", "jpeg")
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f'<img src="data:image/{ext};base64,{data}">'


st.divider()

pictures = [find_image(name) for name in ("image1", "image2", "image3")]
pictures = [p for p in pictures if p]

if pictures:
    # plain HTML row (not st.columns) so the pictures stay side by side on phones too
    st.markdown(
        f"""
        <style>
        .picture-row {{
            display: flex;
            gap: 10px;
            max-width: {PICTURES_MAX_WIDTH}px;
            margin: 0 auto;
        }}
        .picture-row img {{
            flex: 1;
            min-width: 0;
            width: 100%;
            aspect-ratio: 1 / 1;
            object-fit: contain;
            border-radius: 12px;
        }}
        </style>
        <div class="picture-row">{"".join(image_to_html(p) for p in pictures)}</div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.caption("🖼️ Put image1, image2, image3 (png / jpg) in this folder and they will show here.")


# ------------------------------------------------------------------- footer
st.markdown(
    "<p style='text-align:center; opacity:0.8; font-size:28px;'>Made with ❤️ by Shrubby<br>#pungu</p>",
    unsafe_allow_html=True,
)