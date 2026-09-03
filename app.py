import os
import streamlit as st
import plotly.express as px
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# 1. Page Config
st.set_page_config(page_title="Rubriq AI", page_icon="🎓", layout="wide")
st.title("🎓 Rubriq AI")
st.caption("Automated Rubric Evaluation & Adaptive Feedback Engine")

# Sidebar for API Key
st.sidebar.header("Settings")
api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")

if not api_key:
    st.info("👈 Enter your Gemini API Key in the sidebar to get started.")
    st.stop()



client = genai.Client(api_key=api_key)

# 2. Data Models
class RubricCriteriaScore(BaseModel):
    criterion_name: str = Field(description="Name of the rubric criterion")
    score: int = Field(description="Score out of 100")
    feedback: str = Field(description="Specific feedback for this criterion")

class EvaluationResponse(BaseModel):
    overall_score: int = Field(description="Overall weighted score out of 100")
    summary: str = Field(description="Summary of submission performance")
    strengths: list[str] = Field(description="Key strengths identified")
    conceptual_gaps: list[str] = Field(description="Identified conceptual gaps")
    criteria_breakdown: list[RubricCriteriaScore] = Field(description="Breakdown per criterion")
    practice_question: str = Field(description="Targeted practice question based on weaknesses")

# 3. Main Interface Layout
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Setup Rubric")
    rubric_input = st.text_area(
        "Rubric Criteria:",
        height=150,
        value="1. Clarity & Structure (30%)\n2. Technical Accuracy (40%)\n3. Critical Analysis & Evidence (30%)"
    )
    st.subheader("2. Student Submission")
    submission_input = st.text_area("Paste Submission Text:", height=200)
    evaluate_btn = st.button("🚀 Analyze Submission", type="primary", use_container_width=True)

with col2:
    st.subheader("3. Evaluation Dashboard")
    if evaluate_btn and submission_input.strip():
        with st.spinner("Analyzing against rubric criteria..."):
            try:
                prompt = f"Analyze the following submission against the rubric.\nRUBRIC:\n{rubric_input}\nSUBMISSION:\n{submission_input}"
                response = client.models.generate_content(
                    model='gemini-3.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=EvaluationResponse,
                        temperature=0.2
                    ),
                )
                st.session_state['eval_result'] = EvaluationResponse.model_validate_json(response.text)
            except Exception as e:
                st.error(f"Error: {e}")

    if 'eval_result' in st.session_state:
        res = st.session_state['eval_result']
        st.metric("Overall Score", f"{res.overall_score} / 100")
        st.write(f"**Summary:** {res.summary}")

        # Score Bar Chart
        names = [c.criterion_name for c in res.criteria_breakdown]
        scores = [c.score for c in res.criteria_breakdown]
        fig = px.bar(x=names, y=scores, labels={'x':'Criteria', 'y':'Score'}, range_y=[0, 100])
        st.plotly_chart(fig, use_container_width=True)

        # Strengths & Gaps
        s_col, g_col = st.columns(2)
        with s_col:
            st.success("🟢 Strengths")
            for item in res.strengths: st.write(f"• {item}")
        with g_col:
            st.warning("🟡 Gaps")
            for item in res.conceptual_gaps: st.write(f"• {item}")

        st.subheader("🎯 Adaptive Practice Question")
        st.info(res.practice_question)
