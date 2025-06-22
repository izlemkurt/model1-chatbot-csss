import streamlit as st
import pandas as pd
import uuid
import os
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

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

def generate_question_with_empathy(question):
    prompt = f"""
You are a supportive chatbot helping with a stress questionnaire for college students.
Take this stress question:
"{question}"
1. Rephrase it in a more conversational, natural, and warm way.
2. Add a brief empathetic comment after it.
Return as a single short paragraph.
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def generate_followup(question):
    prompt = f"""
Given this original question: "{question}", write ONE short, simple follow-up question that is also answerable on a Likert scale (Never to Very Often). Make it feel natural and empathetic.
Return only the question.
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def run_chatbot(user_email):
    # Use session state for chat-like experience
    if "m1_step" not in st.session_state:
        st.session_state.m1_step = 0
        st.session_state.m1_responses = []
        st.session_state.m1_followup = False
        st.session_state.m1_followup_q = ""
        st.session_state.m1_followup_idx = None
        st.session_state.m1_paraphrased = []

    st.markdown(
        """
        <style>
        .chat-bubble-bot {background:#e3f2fd; color:#111; margin-bottom:10px; padding:14px 18px;border-radius:18px;font-size:16px;}
        .chat-bubble-user {background:#2196f3;color:#fff;margin-left:auto;font-weight:500;width:fit-content;margin-bottom:12px;padding:14px 18px;border-radius:18px;font-size:16px;}
        </style>
        """, unsafe_allow_html=True
    )

    st.markdown("<h4 style='text-align:center;margin-bottom:2rem;'>College Student Stress Chatbot</h4>", unsafe_allow_html=True)
    st.write("Each question will be phrased in a friendly, conversational way. Please answer using the buttons below.")

    # Paraphrase all questions once per session (and cache for fast re-runs)
    while len(st.session_state.m1_paraphrased) < len(csss_questions):
        with st.spinner("Wording question..."):
            st.session_state.m1_paraphrased.append(
                generate_question_with_empathy(csss_questions[len(st.session_state.m1_paraphrased)])
            )

    # Show previous questions and answers as chat bubbles
    for i, entry in enumerate(st.session_state.m1_responses):
        st.markdown(f"<div class='chat-bubble-bot'>{entry['paraphrased']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='chat-bubble-user'>{entry['response']}</div>", unsafe_allow_html=True)
        if 'follow_up' in entry:
            st.markdown(f"<div class='chat-bubble-bot'>{entry['follow_up']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='chat-bubble-user'>{entry['follow_up_response']}</div>", unsafe_allow_html=True)

    # Ask follow-up if needed
    if st.session_state.m1_followup:
        st.markdown(f"<div class='chat-bubble-bot'>{st.session_state.m1_followup_q}</div>", unsafe_allow_html=True)
        fup_ans = st.radio(
            "Your answer:", likert_options, key=f"fup_{st.session_state.m1_followup_idx}", index=None
        )
        if fup_ans:
            # Save followup answer
            st.session_state.m1_responses[st.session_state.m1_followup_idx]["follow_up"] = st.session_state.m1_followup_q
            st.session_state.m1_responses[st.session_state.m1_followup_idx]["follow_up_response"] = fup_ans
            st.session_state.m1_followup = False
            st.session_state.m1_step += 1
            st.rerun()
        st.stop()

    # Main question loop
    if st.session_state.m1_step < len(csss_questions):
        i = st.session_state.m1_step
        paraphrased = st.session_state.m1_paraphrased[i]
        st.markdown(f"<div class='chat-bubble-bot'>{paraphrased}</div>", unsafe_allow_html=True)
        answer = st.radio(
            "Your answer:", likert_options, key=f"main_{i}", index=None
        )
        if answer:
            entry = {
                "question": csss_questions[i],
                "paraphrased": paraphrased,
                "response": answer
            }
            st.session_state.m1_responses.append(entry)
            # If answer is Often/Very Often, ask follow-up
            if answer in ["Often", "Very Often"]:
                followup_q = generate_followup(csss_questions[i])
                st.session_state.m1_followup = True
                st.session_state.m1_followup_q = followup_q
                st.session_state.m1_followup_idx = i
                st.rerun()
            else:
                st.session_state.m1_step += 1
                st.rerun()
        st.stop()

    # Finish and submit
    st.success("You've completed all questions! Click below to submit your responses.")
    if st.button("Submit Survey"):
        df = pd.DataFrame(st.session_state.m1_responses)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = str(uuid.uuid4())
        filename = f"model1_{session_id}.csv"
        df["email"] = user_email
        df.to_csv(filename, index=False)
        st.success("Responses submitted and saved successfully.")
        st.write(f"Saved as: {filename}")
        # Optionally clear state for new run
        st.session_state.m1_step = 0
        st.session_state.m1_responses = []
        st.session_state.m1_followup = False
        st.session_state.m1_followup_q = ""
        st.session_state.m1_followup_idx = None
        st.session_state.m1_paraphrased = []