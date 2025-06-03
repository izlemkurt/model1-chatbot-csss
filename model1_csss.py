# ✅ PLACE THIS ENTIRE FILE INTO YOUR main.py OR app.py

import streamlit as st
import pandas as pd
import uuid
import os
from datetime import datetime

# Set page config
st.set_page_config(page_title="CSSS Chatbot", layout="centered")

# Likert options
likert_options = ["Never", "Rarely", "Sometimes", "Often", "Very Often"]
likert_map = {opt: i+1 for i, opt in enumerate(likert_options)}

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

survey_questions = [
    ("ease", "How easy was it to interact with this chatbot?"),
    ("natural", "How natural did the conversation feel?"),
    ("understood", "How much did you feel understood by the chatbot?"),
    ("reflection", "How much did this chatbot help you reflect on your feelings?"),
    ("support", "How emotionally supportive did this chatbot feel?"),
    ("open_feedback", "What did you like or dislike about this chatbot experience?")
]

rating_labels = {
    "1": "Very Poor",
    "2": "Poor",
    "3": "Neutral",
    "4": "Good",
    "5": "Excellent"
}

# Session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "step" not in st.session_state:
    st.session_state.step = 0
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "mode" not in st.session_state:
    st.session_state.mode = "questions"
if "survey" not in st.session_state:
    st.session_state.survey = {}

# Styling
st.markdown("""
    <style>
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

# Main container
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
st.markdown("<h4>College Student Stress Chatbot</h4>", unsafe_allow_html=True)

# Survey page
if st.session_state.mode == "survey":
    st.markdown("<div class='bot-msg'>Thanks for completing the questions! Now please share your feedback about the experience:</div>", unsafe_allow_html=True)
    with st.form(key="survey_form"):
        for key, question in survey_questions[:-1]:
            st.session_state.survey[key] = st.radio(
                question,
                [f"{i} ({rating_labels[str(i)]})" for i in range(1, 6)],
                key=key
            )
        st.session_state.survey["open_feedback"] = st.text_area(survey_questions[-1][1], key="open_feedback")
        submitted = st.form_submit_button("Submit Feedback")
        if submitted:
            timestamp = datetime.now().isoformat()
            final_row = {"user_id": st.session_state.session_id, "timestamp": timestamp}
            for q_key, ans in st.session_state.answers.items():
                final_row[q_key] = likert_map[ans]
            final_row.update(st.session_state.survey)
            df = pd.DataFrame([final_row])
            file = "csss_model1_responses_chatbot.csv"
            if os.path.exists(file):
                existing = pd.read_csv(file)
                combined = pd.concat([existing, df], ignore_index=True)
                combined.to_csv(file, index=False)
            else:
                df.to_csv(file, index=False)

            st.success("All responses submitted. Thank you!")

elif st.session_state.mode == "questions":
    # Intro message
    if st.session_state.step == 0:
        st.markdown("<div class='bot-msg'>Hi, I'm here to check in on how you've been feeling lately. Let's go through a few quick questions.</div>", unsafe_allow_html=True)

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

        # Button row
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
            st.session_state.mode = "survey"
            st.rerun()

st.markdown("</div>", unsafe_allow_html=True)
