import os
import streamlit as st
import plotly.express as px
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# 1. Page Config
st.set_page_config(page_title="Rubriq AI", page_icon="🎓", layout="wide")

# Custom Visual Styling Injection
st.markdown("""
<style>
    /* Dark Theme Background */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: #f8fafc;
    }
    
    /* Title Styling */
    .main-title {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(90deg, #6366f1, #a855f7, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .sub-title {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-bottom: 25px;
    }
    
    /* Score Metric Box */
    .metric-card {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(168, 85, 247, 0.2));
        border: 1px solid rgba(168, 85, 247, 0.4);
        border-radius: 14px;
        padding: 16px;
        text-align: center;
        margin-bottom: 15px;
    }
    .metric-value {
        font-size: 2.8rem;
        font-weight: 800;
        color: #38bdf8;
    }
    .metric-label {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #cbd5e1;
    }

    /* Gradient Primary Button */
    .stButton>button {
        background: linear-gradient(90deg, #6366f1, #a855f7) !important;
        color: white !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        border: none !important;
        padding: 10px 20px !important;
        box-shadow: 0 4px 14px rgba(168, 85, 247, 0.4) !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🎓 Rubriq AI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Automated Rubric Evaluation & Adaptive Feedback Engine</div>', unsafe_allow_html=True)

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
        
        # Styled Score Card
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Overall Score</div>
            <div class="metric-value">{res.overall_score} / 100</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write(f"**Summary:** {res.summary}")

        # Score Bar Chart with Gradient Coloring & Transparent Background
        names = [c.criterion_name for c in res.criteria_breakdown]
        scores = [c.score for c in res.criteria_breakdown]
        fig = px.bar(
            x=names, 
            y=scores, 
            labels={'x':'Criteria', 'y':'Score'}, 
            range_y=[0, 100],
            color=scores,
            color_continuous_scale=["#ef4444", "#f59e0b", "#10b981"]
        )
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#cbd5e1'),
            coloraxis_showscale=False,
            height=280
        )
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
