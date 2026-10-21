import streamlit as st
import google.generativeai as genai
import PIL.Image
import io

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
==================================================""".strip()

# ── Mode definitions ─────────────────────────────────────
MODES = [
    {"id": "study",   "emoji": "📚", "label": "Study",   "desc": "Relaxed micro-learning"},
    {"id": "report",  "emoji": "📋", "label": "Report",  "desc": "Write lab report"},
    {"id": "group",   "emoji": "👥", "label": "Group",   "desc": "Study with classmates"},
    {"id": "teacher", "emoji": "🎓", "label": "Teacher", "desc": "Prof. Takahashi"},
    {"id": "image",   "emoji": "🔬", "label": "Image",   "desc": "Analyze lab images"},
    {"id": "bridge",  "emoji": "💬", "label": "Bridge",  "desc": "LINE chat helper"},
    {"id": "calm",    "emoji": "🌸", "label": "Calm",    "desc": "Take a breath"},
]

MODE_INTROS = {
    "study":   f"Hi {STUDENT_NAME}! 📚 Study mode — what subject do you want to review today? I'll keep it short and easy, one fact at a time.",
    "report":  f"Ready to write your lab report! 📋 Tell me the experiment topic and any results you have. I'll build the full IMRAD structure for you.",
    "group":   f"Study group time! 👥 AOI, Yuto, Ken, and Rei are here with you, {STUDENT_NAME}. What are we studying today — a case, a past exam question, or a lab topic?",
    "teacher": f"こんにちは、{STUDENT_NAME}さん。高橋先生です。🎓 What would you like me to explain today? Take your time — there are no silly questions.",
    "image":   f"Let's look at it together! 🔬 Upload your image or describe what you see, and I'll walk you through the analysis step by step.",
    "bridge":  f"LINE bridge ready! 💬 Paste your group chat or professor's message, and I'll explain what's going on and write Japanese replies you can send.",
    "calm":    f"Hey {STUDENT_NAME} 🌸 I'm here. Whatever you're feeling right now is completely okay. Take a slow breath with me... inhale 4... hold 4... exhale 4. You've got this. 💛",
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
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display:ital@0;1&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', system-ui, sans-serif !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; max-width: 720px !important; }

.top-bar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 0 16px; border-bottom: 1px solid rgba(128,128,128,.15); margin-bottom: 16px;
}
.logo-area { display: flex; align-items: center; gap: 10px; }
.logo-dot {
    width: 32px; height: 32px; background: #B85C38; border-radius: 8px;
    display: flex; align-items: center; justify-content: center; font-size: 1rem; flex-shrink: 0;
}
.logo-name { font-family: 'DM Serif Display', serif; font-size: 1.1rem; font-style: italic; color: #B85C38; }
.logo-sub { font-size: .72rem; opacity: .5; margin-top: -2px; }

.welcome-card {
    background: linear-gradient(135deg, rgba(184,92,56,.08), rgba(91,74,138,.06));
    border: 1px solid rgba(184,92,56,.2); border-radius: 14px;
    padding: 20px; margin-bottom: 20px; text-align: center;
}
.welcome-card h2 {
    font-family: 'DM Serif Display', serif; font-size: 1.4rem;
    font-style: italic; color: #B85C38; margin-bottom: 6px;
}
.welcome-card p { font-size: .84rem; opacity: .65; line-height: 1.6; }

.divider { height: 1px; background: rgba(128,128,128,.12); margin: 12px 0; }

.stButton > button {
    border-radius: 10px !important; font-weight: 600 !important;
    font-family: 'DM Sans', sans-serif !important;
}
</style>
""", unsafe_allow_html=True)

# ── Gemini API setup ─────────────────────────────────────
@st.cache_resource
def get_model():
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=SYSTEM_PROMPT,
    )

# ── Session state ────────────────────────────────────────
if "active_mode" not in st.session_state:
    st.session_state.active_mode = "study"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None

def reset_chat(mode_id=None):
    if mode_id:
        st.session_state.active_mode = mode_id
    st.session_state.messages = []
    st.session_state.chat_session = None

def get_chat():
    if st.session_state.chat_session is None:
        model = get_model()
        st.session_state.chat_session = model.start_chat(history=[])
    return st.session_state.chat_session

# ── Top bar ──────────────────────────────────────────────
st.markdown(f"""
<div class="top-bar">
  <div class="logo-area">
    <div class="logo-dot">🧬</div>
    <div>
      <div class="logo-name">MedLab AI</div>
      <div class="logo-sub">for {STUDENT_NAME} · {DEPARTMENT}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Welcome card ─────────────────────────────────────────
st.markdown(f"""
<div class="welcome-card">
  <h2>こんにちは、{STUDENT_NAME}! 🌸</h2>
  <p>Your personal AI study companion for 医学検査学科.<br>
  Ask anything, upload images or PDFs, chat freely!<br>
  <em>ကြိုဆိုပါတယ် · いつでも頼ってね</em></p>
</div>
""", unsafe_allow_html=True)

# ── Mode buttons ─────────────────────────────────────────
st.markdown("**Choose a mode:**")
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
            reset_chat(mode["id"])
            st.rerun()

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Active mode info ─────────────────────────────────────
active = next(m for m in MODES if m["id"] == st.session_state.active_mode)
col_mode, col_clear = st.columns([5, 1])
with col_mode:
    st.markdown(f"**{active['emoji']} {active['label']} mode** — {active['desc']}")
with col_clear:
    if st.button("🗑️ Clear", help="Clear chat history", use_container_width=True):
        reset_chat()
        st.rerun()

# ── Chat history display ─────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("image"):
            st.image(msg["image"], caption="Uploaded image", use_container_width=True)
        if msg.get("filename"):
            st.caption(f"📎 {msg['filename']}")
        st.markdown(msg["content"])

# Show intro if no messages yet
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown(MODE_INTROS[st.session_state.active_mode])

# ── File uploader ────────────────────────────────────────
with st.expander("📎 Attach a file (image or PDF)", expanded=False):
    uploaded_file = st.file_uploader(
        "Upload image or PDF",
        type=["png", "jpg", "jpeg", "gif", "webp", "pdf"],
        label_visibility="collapsed",
        key="file_upload",
    )
    if uploaded_file:
        st.success(f"Ready: {uploaded_file.name}")

# ── Chat input ────────────────────────────────────────────
placeholder_map = {
    "study":   "Ask anything — a fact, a term, quiz me...",
    "report":  "Tell me your experiment topic and results...",
    "group":   "Start the discussion — topic or case study...",
    "teacher": "What would you like Prof. Takahashi to explain?",
    "image":   "Upload an image above and describe what you see...",
    "bridge":  "Paste your LINE chat or professor's message here...",
    "calm":    "Tell me how you're feeling...",
}

if prompt := st.chat_input(placeholder_map.get(st.session_state.active_mode, "Type your message...")):
    # Build the message parts for Gemini
    parts = []
    image_display = None
    filename_display = None

    # Add mode context to first message
    mode_context = f"[Current mode: {active['label']} — {active['desc']}]\n\n"

    # Handle file if attached
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        fname = uploaded_file.name
        ftype = uploaded_file.type
        filename_display = fname

        if ftype.startswith("image/"):
            img = PIL.Image.open(io.BytesIO(file_bytes))
            image_display = img
            parts.append(img)
        elif ftype == "application/pdf":
            # Upload PDF to Gemini Files API
            with st.spinner("Uploading PDF..."):
                try:
                    import tempfile, os
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(file_bytes)
                        tmp_path = tmp.name
                    uploaded_pdf = genai.upload_file(tmp_path, mime_type="application/pdf")
                    parts.append(uploaded_pdf)
                    os.unlink(tmp_path)
                except Exception as e:
                    st.error(f"Could not upload PDF: {e}")

    parts.append(mode_context + prompt)

    # Show user message
    with st.chat_message("user"):
        if image_display:
            st.image(image_display, caption=filename_display, use_container_width=True)
        elif filename_display:
            st.caption(f"📎 {filename_display}")
        st.markdown(prompt)

    # Store user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "image": image_display,
        "filename": filename_display if not image_display else None,
    })

    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                chat = get_chat()
                response = chat.send_message(parts)
                reply = response.text
            except Exception as e:
                reply = f"⚠️ Error: {e}\n\nPlease check your internet connection and try again."

        st.markdown(reply)

    # Store assistant message
    st.session_state.messages.append({
        "role": "assistant",
        "content": reply,
    })

    st.rerun()

# ── Bottom hint ──────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;font-size:.72rem;opacity:.4;margin-top:24px;padding-bottom:8px;">
  Made with ❤️ for {STUDENT_FULLNAME} · {UNIVERSITY}<br>
  Powered by Google Gemini AI
</div>
""", unsafe_allow_html=True)
