import streamlit as st

from utils.llm_helper import get_symptom_guidance

st.page_link("views/dashboard.py", label="Back to Dashboard", icon="🏠")
st.title("🩺 Symptom & Doubt Solver")
st.markdown(
    """
<p style='font-size: 1.1rem; color: #86868b;'>
Are you experiencing new symptoms or side effects after taking your medication?
Log your experience here for AI-driven educational guidance, home remedies, and an emergency risk assessment.
</p>
""",
    unsafe_allow_html=True,
)

st.markdown("---")
st.warning(
    "**Disclaimer:** MedSafe AI provides educational information. It is NOT diagnostic and cannot replace a medical professional. If you are experiencing a severe emergency, call your local emergency services."
)

with st.form("symptom_form"):
    st.markdown("#### Patient Profile")
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Age", min_value=1, max_value=120, value=30, step=1)
    with col2:
        gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"])

    st.markdown("#### Medication History")
    medicines = st.text_input(
        "What medicines have you recently taken? (Comma separated)",
        placeholder="e.g. Paracetamol, Lisinopril",
    )

    st.markdown("#### Your Experience")
    experience = st.text_area(
        "Describe what you are feeling or experiencing in detail.",
        placeholder="e.g. I took my blood pressure medication an hour ago and now I have a mild headache and feel slightly dizzy when I stand up.",
        height=150,
    )

    submit_button = st.form_submit_button("Analyze Symptoms", type="primary")

if submit_button:
    if not experience.strip():
        st.error("Please describe your experience so we can assist you.")
    else:
        with st.spinner("Analyzing symptoms and generating guidance..."):
            guidance, risk_level = get_symptom_guidance(age, gender, medicines, experience)

            st.markdown("---")
            st.subheader("MedSafe AI Analysis")

            # Risk Level Badge
            risk_color = "green"
            if risk_level.upper() == "MEDIUM":
                risk_color = "orange"
            elif risk_level.upper() == "HIGH":
                risk_color = "red"

            st.markdown(
                f"### Emergency Risk Predictor: <span style='color:{risk_color}; font-weight:bold;'>{risk_level.upper()}</span>",
                unsafe_allow_html=True,
            )

            if risk_level.upper() == "HIGH":
                st.error(
                    "🚨 **High Risk Detected:** Your symptoms suggest a potentially serious issue. Please seek professional medical attention or go to an emergency room immediately."
                )

            st.markdown("#### Guidance & Education")
            st.info(guidance)
