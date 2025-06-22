import streamlit as st
import pandas as pd
import uuid
import os
import json
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import traceback

# ==== GOOGLE SHEETS SETUP ====
import gspread
from oauth2client.service_account import ServiceAccountCredentials

GOOGLE_SHEET_ID = "1l0dL4yBqG6wmXAB-ZNApnQUlgmybczHmTl8qAmRgYtI"


# Write Google credentials from Streamlit secrets to file
if "GOOGLE_SERVICE_ACCOUNT" in st.secrets:
    with open("csss-chatbots-6effcd218e02.json", "w") as f:
        f.write(st.secrets["GOOGLE_SERVICE_ACCOUNT"])

def get_gsheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "csss-chatbots-6effcd218e02.json", scope
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1  # first worksheet
    return sheet

# def save_to_gsheet(row_dict):
#     sheet = get_gsheet()
#     existing = sheet.get_all_records()
#     if not existing:  # Sheet is empty, set headers as first row
#         sheet.insert_row(list(row_dict.keys()), 1)
#     sheet.append_row(list(row_dict.values()))



def save_to_gsheet(row_dict):
    try:
        st.write("🔍 Saving to Google Sheet...")
        st.write("Row to save:", row_dict)

        sheet = get_gsheet()
        st.write("✅ Google Sheet loaded")

        existing = sheet.get_all_records()
        st.write(f"📄 Existing rows: {len(existing)}")

        if not existing:
            sheet.insert_row(list(row_dict.keys()), 1)
            st.write("📝 Header row inserted")

        sheet.append_row(list(row_dict.values()))
        st.success("✅ Row successfully saved to Google Sheet")

    except Exception as e:
        st.error("❌ Error saving to Google Sheet")
        st.text(traceback.format_exc())


# --- Setup OpenAI ---
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

csss_questions = [
    "Felt anxious or distressed about personal relationships",
    "Felt anxious or distressed about family matters",
    "Felt anxious or distressed about financial matters",
    "Felt anxious or distressed about academic matters",
    "Felt anxious or distressed about housing matters",
    "Felt anxious or distressed about being away from home",
    "Questioned your ability to handle difficulties in your life",
    "Questioned your ability to attain your personal goals",
    "Felt anxious or distressed because events were not going as planned",
    "Felt as though you were NO longer in control of your life",
    "Felt overwhelmed by difficulties in your life"
]
likert_options = ["Never", "Rarely", "Sometimes", "Often", "Very Often"]

def generate_question_paraphrased(question):
    prompt = f"""
You are a supportive chatbot helping with a stress questionnaire for college students.
Take this stress question:
"{question}"
Rephrase it in a more conversational, natural, and warm way. Do not add an empathy sentence here.
Return as a single short paragraph.
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def generate_followup_with_empathy(question, user_answer):
    prompt = f"""
You are a supportive, creative chatbot for college students.
Given the main question: "{question}"
And the user's answer: "{user_answer}"
Write a single message that contains:
- First, a brief, warm, empathetic sentence acknowledging the user's answer. If the answer is positive ("Never", "Rarely"), use a positive/encouraging empathy ("I'm glad to hear this isn't a source of stress for you.", "It's good this doesn't often affect you.", etc). For "Sometimes", use a neutral empathy ("It's understandable to feel this way from time to time."). If negative ("Often", "Very Often"), be supportive/compassionate ("Dealing with this often can be very difficult to manage.", "I'm sorry to hear this is such a frequent struggle for you.", etc).
- Then, in the same message, a varied, supportive follow-up question that is answerable on the Likert scale (Never, Rarely, Sometimes, Often, Very Often). Avoid always using "How often"; ask about impact, frequency, coping, or related feelings, but always use the Likert response style.
Blend the empathy and the question smoothly in one message block, not as separate sentences.
Return only the message.
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def generate_empathy_plus_next_question(prev_question, user_answer, next_question):
    prompt = f"""
You are a supportive chatbot for college students. The user just answered a stress question: "{prev_question}" with "{user_answer}".
Write a single message that:
- Starts with a brief, warm, empathetic sentence acknowledging the user's answer (positive for "Never"/"Rarely", neutral for "Sometimes", supportive for "Often"/"Very Often").
- Then, in the same message (new sentence), smoothly transition to the next question: "{next_question}" (make it conversational, not robotic).
Do NOT ask for a Likert scale in the text, just present the question.
Return only the message.
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# --- Session state defaults ---
for key, default in {
    "session_id": str(uuid.uuid4()),
    "page": "intro",
    "participant_info": {},
    "main_step": 0,
    "chat_history": [],
    "paraphrased_questions": [],
    "awaiting_followup": False,
    "followup_question": "",
    "followup_for": None,
    "awaiting_next_with_empathy": False,
    "next_empathy_plus_question": "",
    "chat_answers": [],
    "chatbot_start_time": None,
    "chatbot_end_time": None,
    "chatbot_duration_seconds": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# --- CSS Styling ---
st.markdown("""
    <style>
        html, body, .main {
            background: linear-gradient(135deg, #f8f6fc 0%, #f5f7fa 98%) !important;
        }
        .chat-container {
            max-width: 650px;
            margin: 36px auto 24px auto;
            background: #fff;
            border-radius: 18px;
            border: 1.5px solid #ece7fa;
            box-shadow: 0 4px 24px rgba(130,100,220,0.08);
            padding: 36px 28px 40px 28px;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        .chat-header-title {
            color: #111111 !important;
            font-weight: 800;
            letter-spacing: -.5px;
            text-align: center;
            font-size: 1.35rem;
            margin-bottom: 10px;
        }
        .chat-container:empty {
            padding: 0;
            margin: 0;
            min-height: 0;
        }
        .chat-header-title:empty {
            padding: 0;
            margin: 0;
            min-height: 0;
        }
        .bot-msg, .user-msg {
            margin: 14px 0;
            padding: 14px 18px;
            border-radius: 18px;
            font-size: 15.6px;
            line-height: 1.5;
        }
        .bot-msg {
            background-color: #e3f2fd;
            text-align: left;
            color: #111111;
            font-weight: 500;
            box-shadow: 0 1px 8px rgba(33,150,243,0.04);
        }
        .user-msg {
            background-color: #2196f3;
            color: white;
            text-align: left;
            margin-left: auto;
            font-weight: 500;
            border: 1px solid transparent;
            width: fit-content;
            box-shadow: 0 1px 8px rgba(33,150,243,0.05);
        }
        .likert-row {
            display: flex;
            justify-content: flex-end;
            gap: 15px;
            margin-top: 20px;
        }
        .likert-row button {
            background-color: white;
            color: #2196f3;
            border: 2.5px solid #2196f3;
            border-radius: 22px;
            padding: 8.5px 18px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.16s, color 0.16s;
        }
        .likert-row button:hover {
            background-color: #2196f3;
            color: white;
        }
        .survey-container {
            max-width: 650px;
            margin: 36px auto 24px auto;
            background: #fff;
            border-radius: 18px;
            border: 1.5px solid #ece7fa;
            box-shadow: 0 4px 24px rgba(130,100,220,0.08);
            padding: 36px 28px 40px 28px;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        .survey-container:empty {
            padding: 0;
            margin: 0;
            min-height: 0;
        }
        .survey-section-title {
            font-size: 1.15rem;
            font-weight: 700;
            color: #2c3a4e;
            margin-top: 32px;
            margin-bottom: 10px;
        }
        .survey-question {
            font-size: 1.04rem;
            font-weight: 500;
            color: #222;
            margin-bottom: 2px;
            margin-top: 22px;
        }
        .survey-likert-row label {
            margin-right: 22px !important;
            font-size: 0.99rem !important;
        }
        .stRadio [data-baseweb="radio"] {
            margin-right: 18px;
        }
        hr.survey-divider {
            border: none;
            border-top: 1.5px solid #f0f2f8;
            margin: 34px 0 18px 0;
        }
        @media (prefers-color-scheme: dark) {
            .chat-header-title,
            .survey-section-title,
            .survey-question,
            .intro-message {
                color: #f0f0f0 !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

# === INTRO PAGE ===
if st.session_state.page == "intro":
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    st.markdown("<div class='chat-header-title'>Welcome to the Stress Chatbot Study</div>", unsafe_allow_html=True)
    st.write("""
    <div class="intro-message">
    This study compares two chatbot designs to understand how students respond to stress-related questions.<br>
    Your responses will help improve support tools for student wellbeing.<br><br>
    <b>Participation takes about <span style="color:#2196f3;">10-15 minutes</span>.</b>
    </div>
    """, unsafe_allow_html=True)
    email = st.text_input(
        "* Email address",
        key="email_input",
        placeholder="your@email.com"
    )
    st.markdown(
        "<div style='color:#111111;font-size:1.01rem;margin-top:0.05rem;margin-bottom:15px;background:#e3f2fd;padding:8px 16px;border-radius:5px;'>"
        "We require your email to ensure each person only participates once. "
        "<b>Your email will NOT be included in the final research dataset.</b> "
        "Optionally, you may receive a summary of your results by email."
        "</div>",
        unsafe_allow_html=True
    )
    col1, col2 = st.columns(2, gap="small")
    with col1:
        student = st.radio("Are you currently a student?", ["Yes", "No"], key="student_radio")
    with col2:
        age = st.number_input("What is your age?", min_value=18, max_value=100, step=1, key="age_input")
    consent = st.checkbox("I consent to my responses being used for research purposes.")

    if st.button("Start Chatbot", use_container_width=True):
        if not consent:
            st.warning("Please provide consent to continue.")
        elif not email or "@" not in email or "." not in email:
            st.warning("Please enter a valid email address to participate.")
        else:
            st.session_state.participant_info = {
                "student": student,
                "age": age,
                "consent": True,
                "email": email
            }
            st.session_state.page = "chat"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# === CHATBOT PAGE ===
elif st.session_state.page == "chat":
    if st.session_state["chatbot_start_time"] is None:
        st.session_state["chatbot_start_time"] = datetime.now()

    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    st.markdown("<div class='chat-header-title'>College Student Stress Chatbot</div>", unsafe_allow_html=True)

    # Paraphrase and cache all questions up front
    while len(st.session_state.paraphrased_questions) < len(csss_questions):
        with st.spinner("Wording question..."):
            st.session_state.paraphrased_questions.append(
                generate_question_paraphrased(csss_questions[len(st.session_state.paraphrased_questions)])
            )

    # ---- Render chat history ----
    for entry in st.session_state.chat_history:
        if entry["type"] in ["main_q", "empathy_plus_next_q"]:
            st.markdown(f"<div class='bot-msg'>{entry['text']}</div>", unsafe_allow_html=True)
        elif entry["type"] == "main_a":
            st.markdown(f"<div class='user-msg'>{entry['text']}</div>", unsafe_allow_html=True)
        elif entry["type"] == "followup_q":
            st.markdown(f"<div class='bot-msg'>{entry['text']}</div>", unsafe_allow_html=True)
        elif entry["type"] == "followup_a":
            st.markdown(f"<div class='user-msg'>{entry['text']}</div>", unsafe_allow_html=True)

    # Empathy+Next-Question block
    if st.session_state.get("awaiting_next_with_empathy", False):
        msg = st.session_state.next_empathy_plus_question
        st.markdown(f"<div class='bot-msg'>{msg}</div>", unsafe_allow_html=True)
        st.markdown('<div class="likert-row">', unsafe_allow_html=True)
        cols = st.columns(len(likert_options))
        for i, opt in enumerate(likert_options):
            with cols[i]:
                if st.button(opt, key=f"main_{st.session_state.main_step}_{opt}"):
                    st.session_state.chat_history.append({"type": "empathy_plus_next_q", "text": msg})
                    st.session_state.chat_history.append({"type": "main_a", "text": opt})

                    # --- Save the main question and answer in chat_answers
                    st.session_state.chat_answers.append({
                        "question": csss_questions[st.session_state.main_step],
                        "paraphrased": st.session_state.paraphrased_questions[st.session_state.main_step],
                        "answer": opt,
                        "followup": None,
                        "followup_answer": None,
                    })

                    if opt in ["Often", "Very Often"]:
                        followup_q = generate_followup_with_empathy(
                            csss_questions[st.session_state.main_step], opt
                        )
                        st.session_state.followup_question = followup_q
                        st.session_state.followup_for = st.session_state.main_step
                        st.session_state.awaiting_followup = True
                        st.session_state.awaiting_next_with_empathy = False
                        st.rerun()
                    else:
                        if st.session_state.main_step + 1 < len(csss_questions):
                            next_question = st.session_state.paraphrased_questions[st.session_state.main_step + 1]
                            empathy_plus = generate_empathy_plus_next_question(
                                csss_questions[st.session_state.main_step], opt, next_question
                            )
                            st.session_state.next_empathy_plus_question = empathy_plus
                            st.session_state.main_step += 1
                            st.rerun()
                        else:
                            st.session_state.main_step += 1
                            st.session_state.awaiting_next_with_empathy = False
                            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    # If awaiting followup, ask it
    if st.session_state.awaiting_followup:
        followup_q = st.session_state.followup_question
        st.markdown(f"<div class='bot-msg'>{followup_q}</div>", unsafe_allow_html=True)
        st.markdown('<div class="likert-row">', unsafe_allow_html=True)
        cols = st.columns(len(likert_options))
        for i, opt in enumerate(likert_options):
            with cols[i]:
                if st.button(opt, key=f"followup_{st.session_state.followup_for}_{opt}"):
                    st.session_state.chat_history.append({"type": "followup_q", "text": followup_q})
                    st.session_state.chat_history.append({"type": "followup_a", "text": opt})

                    # --- Save the followup and answer in the last chat_answers entry
                    if len(st.session_state.chat_answers) > 0:
                        st.session_state.chat_answers[-1]["followup"] = followup_q
                        st.session_state.chat_answers[-1]["followup_answer"] = opt

                    st.session_state.awaiting_followup = False
                    st.session_state.followup_question = ""
                    st.session_state.followup_for = None
                    st.session_state.main_step += 1
                    if st.session_state.main_step < len(csss_questions):
                        next_question = st.session_state.paraphrased_questions[st.session_state.main_step]
                        empathy_plus = generate_empathy_plus_next_question(
                            csss_questions[st.session_state.main_step - 1], opt, next_question
                        )
                        st.session_state.next_empathy_plus_question = empathy_plus
                        st.session_state.awaiting_next_with_empathy = True
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    # First question
    if st.session_state.main_step == 0 and not st.session_state.chat_history:
        question = st.session_state.paraphrased_questions[0]
        st.markdown(f"<div class='bot-msg'>{question}</div>", unsafe_allow_html=True)
        st.markdown('<div class="likert-row">', unsafe_allow_html=True)
        cols = st.columns(len(likert_options))
        for i, opt in enumerate(likert_options):
            with cols[i]:
                if st.button(opt, key=f"main_0_{opt}"):
                    st.session_state.chat_history.append({"type": "main_q", "text": question})
                    st.session_state.chat_history.append({"type": "main_a", "text": opt})

                    # --- Save the main question and answer in chat_answers
                    st.session_state.chat_answers.append({
                        "question": csss_questions[0],
                        "paraphrased": st.session_state.paraphrased_questions[0],
                        "answer": opt,
                        "followup": None,
                        "followup_answer": None,
                    })
                    if opt in ["Often", "Very Often"]:
                        followup_q = generate_followup_with_empathy(
                            csss_questions[0], opt
                        )
                        st.session_state.followup_question = followup_q
                        st.session_state.followup_for = 0
                        st.session_state.awaiting_followup = True
                        st.rerun()
                    else:
                        if len(csss_questions) > 1:
                            next_question = st.session_state.paraphrased_questions[1]
                            empathy_plus = generate_empathy_plus_next_question(
                                csss_questions[0], opt, next_question
                            )
                            st.session_state.next_empathy_plus_question = empathy_plus
                            st.session_state.awaiting_next_with_empathy = True
                            st.session_state.main_step = 1
                            st.rerun()
                        else:
                            st.session_state.main_step = 1
                            st.session_state.awaiting_next_with_empathy = False
                            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    # End of questions
    st.markdown("<div class='bot-msg'>That's all the questions! Click below to continue.</div>", unsafe_allow_html=True)
    if st.button("Go to Feedback Survey", use_container_width=True):
        st.session_state["chatbot_end_time"] = datetime.now()
        st.session_state["chatbot_duration_seconds"] = (
            st.session_state["chatbot_end_time"] - st.session_state["chatbot_start_time"]
        ).total_seconds()
        st.session_state.page = "survey"
        st.session_state._survey_scroll_fix = True
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# === SURVEY PAGE ===
elif st.session_state.page == "survey":
    # Ensure duration is set (robust for refresh/direct)
    if st.session_state["chatbot_end_time"] is None and st.session_state["chatbot_start_time"] is not None:
        st.session_state["chatbot_end_time"] = datetime.now()
        st.session_state["chatbot_duration_seconds"] = (
            st.session_state["chatbot_end_time"] - st.session_state["chatbot_start_time"]
        ).total_seconds()

    st.markdown('<div class="survey-container">', unsafe_allow_html=True)
    st.markdown('<div class="chat-header-title">Final Survey: Chatbot Experience Evaluation</div>', unsafe_allow_html=True)
    st.write('Please answer the following questions based on your experience with the chatbot you just used. (1 = Strongly Disagree, 5 = Strongly Agree)')
    likert = [
        "1 – Strongly Disagree", 
        "2 – Disagree", 
        "3 – Neutral", 
        "4 – Agree", 
        "5 – Strongly Agree"
    ]

    survey_data = {}

    # Section A – Likeability
    st.markdown('<div class="survey-section-title">Section A – Likeability</div>', unsafe_allow_html=True)
    likeability_qs = [
        "I enjoyed using the chatbot.",
        "I would use this chatbot again.",
        "I would recommend this chatbot to others."
    ]
    for idx, q in enumerate(likeability_qs):
        st.markdown(f'<div class="survey-question">{q}</div>', unsafe_allow_html=True)
        survey_data[q] = st.radio(
            q, options=likert, key=f"like_{idx}", horizontal=True, label_visibility="hidden", index=None
        )

    # Section B – Conversation Quality
    st.markdown('<hr class="survey-divider"/><div class="survey-section-title">Section B – Conversation Quality</div>', unsafe_allow_html=True)
    convo_qs = [
        "The chatbot’s responses were easy to understand.",
        "The chatbot understood me well.",
        "Chatbot responses were useful and appropriate.",
        "The conversation felt natural."
    ]
    for idx, q in enumerate(convo_qs):
        st.markdown(f'<div class="survey-question">{q}</div>', unsafe_allow_html=True)
        survey_data[q] = st.radio(
            q, options=likert, key=f"convo_{idx}", horizontal=True, label_visibility="hidden", index=None
        )

    # Section C – Functional Quality
    st.markdown('<hr class="survey-divider"/><div class="survey-section-title">Section C – Functional Quality</div>', unsafe_allow_html=True)
    func_qs = [
        "The chatbot was very easy to use.",
        "Communicating with the chatbot was clear.",
        "It would be easy to get confused when using the chatbot."
    ]
    for idx, q in enumerate(func_qs):
        st.markdown(f'<div class="survey-question">{q}</div>', unsafe_allow_html=True)
        survey_data[q] = st.radio(
            q, options=likert, key=f"func_{idx}", horizontal=True, label_visibility="hidden", index=None
        )

    # Section D – Data Quality (Perceived)
    st.markdown('<hr class="survey-divider"/><div class="survey-section-title">Section D – Data Quality</div>', unsafe_allow_html=True)
    data_qs = [
        "I feel like the chatbot’s responses were accurate.",
        "The chatbot seemed reliable."
    ]
    for idx, q in enumerate(data_qs):
        st.markdown(f'<div class="survey-question">{q}</div>', unsafe_allow_html=True)
        survey_data[q] = st.radio(
            q, options=likert, key=f"data_{idx}", horizontal=True, label_visibility="hidden", index=None
        )

    # Section E – Design-Oriented
    st.markdown('<hr class="survey-divider"/><div class="survey-section-title">Section E – Design-Oriented</div>', unsafe_allow_html=True)
    design_qs = [
        "The chatbot seemed too robotic.",
        "The chatbot’s personality was realistic and engaging.",
        "The chatbot adapted to my responses."
    ]
    for idx, q in enumerate(design_qs):
        st.markdown(f'<div class="survey-question">{q}</div>', unsafe_allow_html=True)
        survey_data[q] = st.radio(
            q, options=likert, key=f"design_{idx}", horizontal=True, label_visibility="hidden", index=None
        )

    # Section F – Open Feedback
    st.markdown('<hr class="survey-divider"/>', unsafe_allow_html=True)
    st.write("### Section F – Open Feedback")
    open_feedback_1 = st.text_area("What did you like most about this chatbot?", placeholder="Share what you enjoyed...", height=80, key="feedback_like")
    open_feedback_2 = st.text_area("What did you find frustrating or confusing?", placeholder="Share anything that didn't work or was unclear...", height=80, key="feedback_frustrating")
    open_feedback_3 = st.text_area("Do you have any suggestions to improve this chatbot?", placeholder="Share improvements or ideas...", height=80, key="feedback_suggestions")

    missing = [q for q, v in survey_data.items() if not v]
    if st.button("Submit Survey", use_container_width=True):
        if missing or not open_feedback_1.strip() or not open_feedback_2.strip() or not open_feedback_3.strip():
            st.warning("Please answer all questions and fill all feedback boxes before submitting.")
        else:
            timestamp = datetime.now().isoformat()
            row = {
                "user_id": st.session_state.session_id,
                "timestamp": timestamp,
                "chatbot_duration_seconds": st.session_state.chatbot_duration_seconds,
                **st.session_state.participant_info,
                "chatbot_conversation": json.dumps(st.session_state.chat_answers),
                **survey_data,
                "What did you like most about this chatbot?": open_feedback_1,
                "What did you find frustrating or confusing?": open_feedback_2,
                "Do you have any suggestions to improve this chatbot?": open_feedback_3,
                "model": "model1"
            }
            df = pd.DataFrame([row])
            file = "csss_model1_responses_chatbot.csv"
            if os.path.exists(file):
                pd.concat([pd.read_csv(file), df], ignore_index=True).to_csv(file, index=False)
            else:
                df.to_csv(file, index=False)

            # === GOOGLE SHEETS SAVE ===
            try:
                save_to_gsheet(row)
            except Exception as e:
                st.error(f"Could not save to Google Sheet: {e}")

            st.success("Survey submitted. Thank you!")
            st.session_state.page = "thankyou"
            st.session_state.main_step = 0
            st.session_state.chat_history = []
            st.session_state.participant_info = {}
            st.session_state.paraphrased_questions = []
            st.session_state.awaiting_followup = False
            st.session_state.followup_question = ""
            st.session_state.followup_for = None
            st.session_state.chat_answers = []
            st.session_state.chatbot_start_time = None
            st.session_state.chatbot_end_time = None
            st.session_state.chatbot_duration_seconds = None
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# === THANK YOU PAGE ===
elif st.session_state.page == "thankyou":
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    st.markdown('<div class="chat-header-title">Thank You!</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="bot-msg">Your responses have been recorded.<br>Thank you for participating in this study.<br>Feel free to close this page.</div>',
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)