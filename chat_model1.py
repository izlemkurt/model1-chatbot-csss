import streamlit as st
import pandas as pd
import uuid
import os
from datetime import datetime

st.set_page_config(page_title="CSSS Chatbot Experiment", layout="centered")

for key, default in {
    "session_id": str(uuid.uuid4()),
    "page": "intro",
    "step": 0,
    "answers": {},
    "history": [],
    "participant_info": {},
    "mode": "model1"
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

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
likert_map = {opt: i+1 for i, opt in enumerate(likert_options)}

# --- CSS
st.markdown("""
    <style>
        .big-title {
            font-size: 2.2rem !important;
            font-weight: 800;
            margin-bottom: 0.5rem;
            margin-top: 1rem;
            color: #111 !important;
        }
        .intro-box {
            max-width: 700px;
            margin: 0 auto;
            padding-top: 20px;
        }
        .survey-container {
            max-width: 650px;
            margin: 40px auto 32px auto;
            background: #FCFBFF;
            border-radius: 18px;
            padding: 16px 30px 24px 30px;
            border: 1px solid #E2DDF6;
            box-shadow: 0 3px 18px rgba(130,100,220,0.12);
        }
        .survey-container:empty {
            padding: 0; margin: 0; min-height: 0;
        }
        .survey-title {
            font-size: 2.2rem !important;
            font-weight: 900;
            color: #111 !important;
            text-align: center;
            margin-bottom: 0.35em;
        }
        .survey-desc {
            text-align: center;
            font-size: 1.13rem;
            margin-bottom: 1.1em;
            color: #333;
        }
        .survey-section {
            font-size: 1.18rem;
            font-weight: 700;
            color: #111 !important;
            margin-top: 2.2em;
            margin-bottom: 0.3em;
        }
        .survey-question {
            font-size: 1.07rem;
            font-weight: 500;
            margin-bottom: 0.07em;
            color: #2d224c;
        }
        .survey-radio .stRadio {
            margin-bottom: 1.25em;
        }
        .survey-feedback-section {
            font-size: 1.18rem;
            font-weight: 700;
            color: #7c5fd9 !important;
            margin-top: 2.2em;
            margin-bottom: 0.3em;
        }
        .survey-comments > label, .stTextArea label {
            font-size: 1.07rem !important;
            font-weight: 500;
            color: #7c5fd9 !important;
        }
        .stButton button {
            background: linear-gradient(90deg,#7c5fd9 0,#a389f4 100%);
            color: white;
            font-weight: 700;
            border-radius: 10px;
            padding: 0.5rem 1.25rem;
        }
        .thankyou-container {
            max-width: 600px;
            margin: 70px auto 0 auto;
            background: #f7f7fb;
            border-radius: 18px;
            padding: 44px 36px 44px 36px;
            border: 1px solid #e2ddf6;
            box-shadow: 0 3px 18px rgba(130,100,220,0.10);
            text-align: center;
        }
        .thankyou-container:empty {
            padding: 0; margin: 0; min-height: 0;
        }
        .thankyou-title {
            font-size: 2.2rem !important;
            font-weight: 900;
            color: #111 !important;
            margin-bottom: 1.3rem;
        }
        .thankyou-message {
            font-size: 1.15rem;
            color: #222;
            margin-bottom: 1rem;
        }
        .chat-container {
            max-width: 600px;
            margin: 20px auto;
            background: white;
            border-radius: 16px;
            border: 1px solid #ddd;
            box-shadow: 0 4px 12px rgba(0,0,0,0.06);
            padding: 20px 20px 30px;
            font-family: Arial, sans-serif;
        }
        .chat-container:empty {
            padding: 0; margin: 0; min-height: 0;
        }
        .bot-msg, .user-msg {
            margin: 12px 0;
            padding: 12px 16px;
            border-radius: 18px;
            font-size: 15px;
            line-height: 1.4;
        }
        .bot-msg {
            background-color: #f1f1f1;
            text-align: left;
        }
        .user-msg {
            background-color: #9147ff;
            color: white;
            text-align: left;
            margin-left: auto;
            font-weight: 500;
            border: 1px solid transparent;
            width: fit-content;
        }
        .likert-row {
            display: flex;
            justify-content: flex-end;
            gap: 12px;
            margin-top: 16px;
        }
        .likert-row button {
            background-color: white;
            color: #9147ff;
            border: 2px solid #9147ff;
            border-radius: 20px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
        }
        .likert-row button:hover {
            background-color: #9147ff;
            color: white;
        }
        h4 {
            text-align: center;
            margin-top: 0;
        }
    </style>
""", unsafe_allow_html=True)

# === INTRO PAGE
if st.session_state.page == "intro":
    st.markdown("<div class='intro-box'>", unsafe_allow_html=True)
    st.markdown("<div class='big-title'>Welcome to the Stress Chatbot Study</div>", unsafe_allow_html=True)
    st.write("""
    This study compares two chatbot designs to understand how students respond to stress-related questions.
    Your responses will help improve support tools for student wellbeing.

    **The session takes about 5–10 minutes.**
    """)

    student = st.radio("Are you currently a student?", ["Yes", "No"])
    age = st.number_input("What is your age?", min_value=18, max_value=100, step=1)
    consent = st.checkbox("I consent to my anonymous responses being used for research purposes.")

    if st.button("Start Chatbot"):
        if not consent:
            st.warning("Please provide consent to continue.")
        else:
            st.session_state.participant_info = {"student": student, "age": age, "consent": True}
            st.session_state.page = "chat"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# === CHATBOT PAGE
elif st.session_state.page == "chat":
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    st.markdown("<h4>College Student Stress Chatbot</h4>", unsafe_allow_html=True)

    # Show previous questions and user answers
    for i in range(st.session_state.step):
        st.markdown(f"<div class='bot-msg'>{csss_questions[i]}</div>", unsafe_allow_html=True)
        answer = st.session_state.answers.get(f"Q{i+1}", "")
        if answer:
            st.markdown(f"<div class='user-msg'>{answer}</div>", unsafe_allow_html=True)

    # Show current question and likert options
    if st.session_state.step < len(csss_questions):
        idx = st.session_state.step
        question = csss_questions[idx]
        st.markdown(f"<div class='bot-msg'>{question}</div>", unsafe_allow_html=True)

        st.markdown('<div class="likert-row">', unsafe_allow_html=True)
        cols = st.columns(len(likert_options))
        for i, opt in enumerate(likert_options):
            with cols[i]:
                if st.button(opt, key=f"{idx}_{opt}"):
                    st.session_state.answers[f"Q{idx+1}"] = opt
                    st.session_state.step += 1
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Submit screen
    elif st.session_state.step == len(csss_questions):
        st.markdown("<div class='bot-msg'>That's all the questions! Click below to continue.</div>", unsafe_allow_html=True)
        if st.button("Go to Feedback Survey"):
            st.session_state.page = "survey"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# === SURVEY PAGE
elif st.session_state.page == "survey":
    # Scroll to top when survey page loads
    st.markdown("""
        <script>
            window.parent.document.querySelector('section.main').scrollTo(0, 0);
        </script>
    """, unsafe_allow_html=True)

    st.markdown('<div class="survey-container">', unsafe_allow_html=True)
    st.markdown('<div class="survey-title">Final Survey: Chatbot Experience Evaluation</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="survey-desc">Please answer the following questions based on your experience with the chatbot you just used.<br>'
        '<span style="color:#7c5fd9;">(1 = Strongly Disagree, 5 = Strongly Agree)</span></div>',
        unsafe_allow_html=True
    )

    likert = [
        "1 – Strongly Disagree", 
        "2 – Disagree", 
        "3 – Neutral", 
        "4 – Agree", 
        "5 – Strongly Agree"
    ]

    section_a = [
        "The chatbot was able to carry out the intended functions.",
        "I felt the chatbot’s capabilities matched my expectations.",
        "The chatbot helped me complete the task successfully.",
        "The chatbot responded in a timely and efficient manner.",
        "The chatbot was easy to use.",
        "Overall, the chatbot worked as I expected.",
    ]
    section_b = [
        "The chatbot’s responses were easy to understand.",
        "The flow of the conversation felt natural.",
        "I felt like I was having a real conversation.",
    ]
    section_c = [
        "I enjoyed interacting with the chatbot.",
        "The chatbot felt friendly during the conversation.",
        "I would like to use this chatbot again.",
        "I felt comfortable talking to the chatbot.",
        "The chatbot’s personality was pleasant.",
        "I felt engaged while interacting with the chatbot.",
        "I would recommend this chatbot to others.",
        "I found the experience satisfying.",
        "I felt the chatbot was likable.",
    ]


    survey_data = {}

    st.markdown('<div class="survey-section">Section A – Functional Quality</div>', unsafe_allow_html=True)
    for idx, q in enumerate(section_a):
        st.markdown(f'<div class="survey-question">{q}</div>', unsafe_allow_html=True)
        survey_data[q] = st.radio(
            label="",
            options=likert,
            key=f"func_{idx}",
            horizontal=True,
            label_visibility="collapsed"
        )

    st.markdown('<div class="survey-section">Section B – Conversation Quality</div>', unsafe_allow_html=True)
    for idx, q in enumerate(section_b):
        st.markdown(f'<div class="survey-question">{q}</div>', unsafe_allow_html=True)
        survey_data[q] = st.radio(
            label="",
            options=likert,
            key=f"conv_{idx}",
            horizontal=True,
            label_visibility="collapsed"
        )

    st.markdown('<div class="survey-section">Section C – Likeability / Enjoyment</div>', unsafe_allow_html=True)
    for idx, q in enumerate(section_c):
        st.markdown(f'<div class="survey-question">{q}</div>', unsafe_allow_html=True)
        survey_data[q] = st.radio(
            label="",
            options=likert,
            key=f"like_{idx}",
            horizontal=True,
            label_visibility="collapsed"
        )

    st.markdown('<div class="survey-feedback-section">Section D – Open Feedback</div>', unsafe_allow_html=True)
    open_feedback_1 = st.text_area(
        "What did you like most about this chatbot?",
        placeholder="Share what you enjoyed...",
        height=80,
        key="feedback_like"
    )
    open_feedback_2 = st.text_area(
        "What did you find frustrating or confusing?",
        placeholder="Share anything that didn't work or was unclear...",
        height=80,
        key="feedback_frustrating"
    )
    open_feedback_3 = st.text_area(
        "Do you have any suggestions to improve this chatbot?",
        placeholder="Share improvements or ideas...",
        height=80,
        key="feedback_suggestions"
    )

    # All likert questions required, all text areas required
    missing = [q for q, v in survey_data.items() if not v]
    if st.button("Submit Survey"):
        if (
            missing or
            not open_feedback_1.strip() or
            not open_feedback_2.strip() or
            not open_feedback_3.strip()
        ):
            st.warning("Please answer all questions and fill all feedback boxes before submitting.")
        else:
            timestamp = datetime.now().isoformat()
            row = {
                "user_id": st.session_state.session_id,
                "timestamp": timestamp,
                **st.session_state.participant_info,
                **{f"Q{i+1}": st.session_state.answers.get(f"Q{i+1}", "") for i in range(len(csss_questions))},
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

            st.success("Survey submitted. Thank you!")
            st.session_state.page = "thankyou"
            st.session_state.step = 0
            st.session_state.answers = {}
            st.session_state.history = []
            st.session_state.participant_info = {}
            st.session_state.mode = "model1"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# === THANK YOU PAGE
elif st.session_state.page == "thankyou":
    st.markdown('<div class="thankyou-container">', unsafe_allow_html=True)
    st.markdown('<div class="thankyou-title">Thank You!</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="thankyou-message">Your responses have been recorded.<br>Thank you for participating in this study.<br>Feel free to close this page.</div>',
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)