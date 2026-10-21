import streamlit as st
from anthropic import Anthropic
import os
from dotenv import load_dotenv

load_dotenv()

# ── Config ──────────────────────────────────────────────
STUDENT_NAME     = "Pan"
STUDENT_FULLNAME = "Ei Shwe Sin"
NATIVE_LANG      = "Burmese (မြန်မာဘာသာ)"
UNIVERSITY       = "IUHW Otawara"
DEPARTMENT       = "保健医療学部 医学検査学科"

# ── System Prompt ────────────────────────────────────────
SYSTEM_PROMPT = f"""==================================================
AI ASSISTANT SYSTEM INSTRUCTIONS
Target User: {STUDENT_NAME} ({STUDENT_FULLNAME}) — Student at {UNIVERSITY}, {DEPARTMENT}
Target Qualification: Japanese Clinical Laboratory Technologist (臨床検査技師)
Primary Language: {NATIVE_LANG} + Simple English (with accurate Japanese medical terminology in Kanji/Katakana)
==================================================

CORE PERSONA & SENSITIVITY
You are a warm, deeply empathetic, highly competent, and supportive AI academic partner for {STUDENT_NAME}.
Background Context: She is an international student in Japan who sometimes experiences language barriers, feels isolated during real-life Japanese university group projects, and receives minimal explanation from university instructors.
Your Mission: Be her safe space, patient tutor, study group partner, communication bridge, and expert lab report mentor. NEVER judge, criticize, or assume she "should already know" something.
Always address her as "{STUDENT_NAME}" — warm and personal.
Auto-detect stress signals: If she mentions feeling overwhelmed, tired, homesick, or frustrated — even without typing /calm — briefly shift to gentle, encouraging Mode 7 tone before continuing.
Memory & Continuity: Remember her past reports, weak subject areas, and ongoing projects across our conversation. Reference them when relevant.

==================================================
OPERATIONAL MODES
==================================================

MODE 1 — /report — ACADEMIC REPORT GENERATOR
Generate IMRAD-structured medical laboratory reports in natural, human-sounding Japanese academic prose.
Structure: 緒言・目的 → 検査・実験方法 → 結果 → 考察 → 参考文献
Sources: JCCLS, WHO, NIH, PubMed, 日本臨床検査医学会
Writing rules: である・だ style, no AI clichés, varied sentence length, Results = raw data only, Discussion = clinical reasoning

MODE 2 — /bridge — LINE GROUP CHAT BRIDGE
When she pastes a Japanese LINE chat log or professor instructions:
1. Summarize in plain {NATIVE_LANG}
2. Suggest a specific task she can own
3. Write 2–3 natural Japanese sentences she can copy-paste into LINE

MODE 3 — /group — INCLUSIVE STUDY GROUP
Simulate a warm study group: {STUDENT_NAME} + 4 AI classmates. ALL played by you, each with distinct personality and deep medical laboratory knowledge.
- AOI (葵) — Empathetic, visually-minded. Expert: 病理組織学, blood morphology, lab reports. Always: "What do you think, {STUDENT_NAME}?"
- YUTO (雄大) — Analytical, structured. Expert: 臨床化学, enzyme kinetics, LFTs, electrolytes, reference ranges. Sometimes over-explains.
- KEN (健) — Curious, lateral-thinking. Expert: 微生物学, 免疫学, clinical cases, latest guidelines.
- REI (玲) — Evidence-first. Expert: 国家試験 past questions, 検査基準値. Always cites: "According to JCCLS 2024..."
Rules: All four involve {STUDENT_NAME}, validate her answers, natural disagreements happen between characters.

MODE 4 — /teacher — PATIENT PROFESSOR TUTOR
Act as Prof. Takahashi (高橋先生) — patient, encouraging IUHW professor.
Explain: hemodynamics, enzyme kinetics, immunoassays, coagulation cascades, urinalysis, microbial ID, ECG interpretation.
Review: IMRAD drafts, presentation slides — constructive and kind.
Drill: 国家試験 past questions with clear logical reasoning.

MODE 5 — /image — VISUAL & MICROSCOPIC ASSISTANT
Analyze: blood smears, Gram stains, urine sediment, tissue slides, ECGs.
Step 1: Primary features (color, shape, staining, intervals)
Step 2: Differential diagnostic possibilities
Step 3: Clinical markers and pathological significance
Step 4: Common exam questions for this finding

MODE 6 — /study — RELAXED MEMORY MODE (DEFAULT)
Bite-sized micro-learning for 国家試験 retention.
- 1–2 facts at a time, never overwhelming
- Japanese mnemonics (語録), visual analogies, memory hooks
- One question at a time; gentle hints on wrong answers; always praise effort

MODE 7 — /calm — STRESS RESET & CHEERLEADER
Emotional grounding when overwhelmed, homesick, or frustrated.
- Validate feelings; remind her how remarkable her journey is
- Short breathing exercise or sweet motivational note
- No academic content unless she asks
- Also auto-activates on stress signals

==================================================
GENERAL RULES
==================================================
1. Medical terms: Always show Kanji/Katakana + English + {NATIVE_LANG} translation
2. Formatting: Clean markdown, bold key terms, mobile-readable
3. Language: {NATIVE_LANG} for explanations, Japanese for medical terms, English for international refs
4. Never judge; every question is valid
5. References: 日本臨床検査医学会, JCCLS, WHO, NIH, PubMed
6. Remember context: current assignments, weak areas, upcoming deadlines
=================================================="""

# ── Mode definitions ─────────────────────────────────────
MODES = [
    {"id": "study",   "cmd": "/study",   "emoji": "📚", "label": "Study",   "desc": "Relaxed micro-learning"},
    {"id": "report",  "cmd": "/report",  "emoji": "📋", "label": "Report",  "desc": "Write lab report"},
    {"id": "group",   "cmd": "/group",   "emoji": "👥", "label": "Group",   "desc": "Study with classmates"},
    {"id": "teacher", "cmd": "/teacher", "emoji": "🎓", "label": "Teacher", "desc": "Prof. Takahashi"},
    {"id": "image",   "cmd": "/image",   "emoji": "🔬", "label": "Image",   "desc": "Analyze lab images"},
    {"id": "bridge",  "cmd": "/bridge",  "emoji": "💬", "label": "Bridge",  "desc": "LINE chat helper"},
    {"id": "calm",    "cmd": "/calm",    "emoji": "🌸", "label": "Calm",    "desc": "Take a breath"},
]

MODE_COLORS = {
    "study":   "#B85C38",
    "report":  "#B85C38",
    "group":   "#5B4A8A",
    "teacher": "#2E6B9E",
    "image":   "#8A6B2E",
    "bridge":  "#3B7A6E",
    "calm":    "#3B7A6E",
}

MODE_INTROS = {
    "study":   f"Hi {STUDENT_NAME}! 📚 Study mode is on. What subject do you want to work on today? I'll keep it short and easy — one fact at a time!",
    "report":  f"Ready to write your lab report, {STUDENT_NAME}! 📋 Tell me the experiment topic and any results you have, and I'll build the full IMRAD structure for you.",
    "group":   f"Study group time! 👥 AOI, Yuto, Ken, and Rei are here with you, {STUDENT_NAME}. What are we studying today — a case, a past exam question, or a lab topic?",
    "teacher": f"こんにちは、{STUDENT_NAME}さん。高橋先生です。🎓 What would you like me to explain today? Take your time — there are no silly questions.",
    "image":   f"Let's look at it together, {STUDENT_NAME}! 🔬 Upload your image or describe what you see, and I'll walk you through the analysis step by step.",
    "bridge":  f"LINE bridge ready! 💬 Paste your group chat or professor's message here, {STUDENT_NAME}. I'll explain what's going on and write Japanese messages you can send.",
    "calm":    f"Hey {STUDENT_NAME} 🌸 I'm here. Whatever you're feeling right now is completely okay. Take a slow breath with me first... inhale 4 counts... hold 4... exhale 4. You've got this. 💛",
}

# ── Page config ──────────────────────────────────────────
st.set_page_config(
    page_title=f"MedLab AI · {STUDENT_NAME}",
    page_icon="🧬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── CSS ──────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,300&family=DM+Serif+Display:ital@0;1&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', system-ui, sans-serif !important;
}

/* Hide streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; max-width: 720px !important; }

/* Top bar */
.top-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 0 16px;
    border-bottom: 1px solid rgba(128,128,128,.15);
    margin-bottom: 16px;
}
.logo-area { display: flex; align-items: center; gap: 10px; }
.logo-dot {
    width: 32px; height: 32px;
    background: #B85C38;
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
}
.logo-name {
    font-family: 'DM Serif Display', Georgia, serif;
    font-size: 1.1rem;
    font-style: italic;
    color: #B85C38;
}
.logo-sub { font-size: .72rem; opacity: .5; margin-top: -2px; }
.mode-badge {
    font-size: .72rem;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 20px;
    letter-spacing: .05em;
    text-transform: uppercase;
}

/* Mode grid */
.mode-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    margin-bottom: 20px;
}
@media (max-width: 500px) {
    .mode-grid { grid-template-columns: repeat(2, 1fr); }
}
.mode-btn {
    background: rgba(128,128,128,.07);
    border: 1.5px solid transparent;
    border-radius: 10px;
    padding: 10px 6px 8px;
    text-align: center;
    cursor: pointer;
    transition: all .15s;
}
.mode-btn:hover { background: rgba(184,92,56,.08); border-color: rgba(184,92,56,.3); }
.mode-btn.active { background: rgba(184,92,56,.12); border-color: #B85C38; }
.mode-btn-emoji { font-size: 1.4rem; display: block; margin-bottom: 3px; }
.mode-btn-label { font-size: .75rem; font-weight: 600; display: block; }
.mode-btn-desc { font-size: .65rem; opacity: .55; display: block; margin-top: 1px; }

/* Chat messages */
.chat-wrap { display: flex; flex-direction: column; gap: 12px; margin-bottom: 20px; }

.msg-user {
    align-self: flex-end;
    background: #B85C38;
    color: #fff;
    padding: 11px 15px;
    border-radius: 16px 16px 4px 16px;
    max-width: 80%;
    font-size: .9rem;
    line-height: 1.55;
}
.msg-ai {
    align-self: flex-start;
    background: rgba(128,128,128,.08);
    padding: 13px 16px;
    border-radius: 4px 16px 16px 16px;
    max-width: 88%;
    font-size: .88rem;
    line-height: 1.65;
    border: 1px solid rgba(128,128,128,.1);
}
.msg-ai strong { font-weight: 600; }
.msg-ai code {
    background: rgba(128,128,128,.12);
    padding: 1px 5px;
    border-radius: 4px;
    font-size: .82rem;
}

/* Input area */
.stTextArea textarea {
    border-radius: 12px !important;
    font-size: .9rem !important;
    font-family: 'DM Sans', sans-serif !important;
    resize: none !important;
    min-height: 80px !important;
}
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-family: 'DM Sans', sans-serif !important;
    transition: all .15s !important;
}

/* Welcome card */
.welcome-card {
    background: linear-gradient(135deg, rgba(184,92,56,.08), rgba(91,74,138,.06));
    border: 1px solid rgba(184,92,56,.2);
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 20px;
    text-align: center;
}
.welcome-card h2 {
    font-family: 'DM Serif Display', Georgia, serif;
    font-size: 1.4rem;
    font-style: italic;
    color: #B85C38;
    margin-bottom: 6px;
}
.welcome-card p { font-size: .84rem; opacity: .65; line-height: 1.6; }

/* Divider */
.divider { height: 1px; background: rgba(128,128,128,.12); margin: 12px 0; }
</style>
""", unsafe_allow_html=True)

# ── Session state ────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "active_mode" not in st.session_state:
    st.session_state.active_mode = "study"
if "client" not in st.session_state:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    st.session_state.client = Anthropic(api_key=api_key) if api_key else None

def switch_mode(mode_id):
    st.session_state.active_mode = mode_id
    intro = MODE_INTROS.get(mode_id, "")
    st.session_state.messages.append({"role": "assistant", "content": intro})

def send_message(user_text):
    if not user_text.strip():
        return
    # Check if it's a slash command
    for m in MODES:
        if user_text.strip().lower().startswith(m["cmd"]):
            st.session_state.active_mode = m["id"]
            extra = user_text.strip()[len(m["cmd"]):].strip()
            display_text = user_text.strip()
            content_text = user_text.strip()
            break
    else:
        display_text = user_text.strip()
        content_text = user_text.strip()

    st.session_state.messages.append({"role": "user", "content": display_text})

    if st.session_state.client is None:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "⚠️ API key not found. Please add your ANTHROPIC_API_KEY to the `.env` file and restart the app."
        })
        return

    # Build messages for API
    api_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
        if m["role"] in ("user", "assistant")
    ]

    try:
        response = st.session_state.client.messages.create(
            model="claude-opus-4-5",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=api_messages,
        )
        reply = response.content[0].text
    except Exception as e:
        reply = f"⚠️ Error: {e}"

    st.session_state.messages.append({"role": "assistant", "content": reply})

# ── Top bar ──────────────────────────────────────────────
active_mode = next(m for m in MODES if m["id"] == st.session_state.active_mode)
color = MODE_COLORS.get(st.session_state.active_mode, "#B85C38")

st.markdown(f"""
<div class="top-bar">
  <div class="logo-area">
    <div class="logo-dot">🧬</div>
    <div>
      <div class="logo-name">MedLab AI</div>
      <div class="logo-sub">for {STUDENT_NAME} · {DEPARTMENT}</div>
    </div>
  </div>
  <div class="mode-badge" style="background:{'rgba(184,92,56,.12)' if color=='#B85C38' else 'rgba(91,74,138,.12)'}; color:{color};">
    {active_mode['emoji']} {active_mode['label']}
  </div>
</div>
""", unsafe_allow_html=True)

# ── Welcome (only when no messages) ─────────────────────
if not st.session_state.messages:
    st.markdown(f"""
    <div class="welcome-card">
      <h2>こんにちは、{STUDENT_NAME}! 🌸</h2>
      <p>Your personal MedLab AI is ready.<br>
      Choose a mode below or just start typing — I'm here for you.<br>
      <em>ကြိုဆိုပါတယ် · いつでも頼ってね</em></p>
    </div>
    """, unsafe_allow_html=True)

# ── Mode buttons ─────────────────────────────────────────
cols = st.columns(7)
for i, mode in enumerate(MODES):
    with cols[i]:
        is_active = mode["id"] == st.session_state.active_mode
        if st.button(
            f"{mode['emoji']}\n{mode['label']}",
            key=f"mode_{mode['id']}",
            help=mode["desc"],
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            switch_mode(mode["id"])
            st.rerun()

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Chat history ─────────────────────────────────────────
if st.session_state.messages:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div style="display:flex;justify-content:flex-end;margin:4px 0"><div class="msg-user">{msg["content"]}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="display:flex;justify-content:flex-start;margin:4px 0"><div class="msg-ai">{msg["content"]}</div></div>', unsafe_allow_html=True)

# ── Input ────────────────────────────────────────────────
st.markdown("")
with st.form("chat_form", clear_on_submit=True):
    placeholder_map = {
        "study":   "Ask anything — a fact, a term, quiz me...",
        "report":  "Tell me your experiment topic and results...",
        "group":   "Start the discussion — topic or case study...",
        "teacher": "What would you like me to explain?",
        "image":   "Describe what you see in the image...",
        "bridge":  "Paste your LINE chat or professor's message here...",
        "calm":    "Tell me how you're feeling...",
    }
    user_input = st.text_area(
        "Message",
        placeholder=placeholder_map.get(st.session_state.active_mode, "Type your message..."),
        label_visibility="collapsed",
        key="user_input",
    )
    col1, col2, col3 = st.columns([4, 1, 1])
    with col2:
        submitted = st.form_submit_button("Send ➤", use_container_width=True, type="primary")
    with col3:
        cleared = st.form_submit_button("Clear", use_container_width=True)

if submitted and user_input:
    send_message(user_input)
    st.rerun()

if cleared:
    st.session_state.messages = []
    st.rerun()

# ── Bottom hint ──────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;font-size:.72rem;opacity:.4;margin-top:16px;padding-bottom:8px;">
  Type a slash command directly: /study /report /group /teacher /image /bridge /calm<br>
  Made with ❤️ for {STUDENT_FULLNAME} · {UNIVERSITY}
</div>
""", unsafe_allow_html=True)
