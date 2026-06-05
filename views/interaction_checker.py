import streamlit as st

from utils.medicine_db import MedicineDatabase
from utils.llm_helper import summarize_interaction

st.page_link("views/dashboard.py", label="Back to Dashboard", icon="🏠")
st.title("💊 Medicine Interaction Checker")
st.markdown(
    "<p style='font-size: 1.1rem; color: #86868b;'>Enter your medications below to check for potential drug-drug interactions based on active salts.</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# Initialize database
@st.cache_resource
def get_db():
    return MedicineDatabase()


db = get_db()

# Session state to hold our dynamic list of inputs
if "medication_inputs" not in st.session_state:
    st.session_state.medication_inputs = ["", ""]


def add_med():
    st.session_state.medication_inputs.append("")


def remove_med(index):
    if len(st.session_state.medication_inputs) > 2:
        st.session_state.medication_inputs.pop(index)


col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("#### Your Medicines")
with col2:
    st.write("")  # Spacing
    st.button("➕ Add Medicine", on_click=add_med, use_container_width=True)

# Render input fields dynamically
medicines_entered = []
for i, val in enumerate(st.session_state.medication_inputs):
    cols = st.columns([10, 1])
    with cols[0]:
        med = st.text_input(
            f"Medicine {i+1}",
            value=val,
            key=f"med_{i}",
            placeholder="e.g. Aspirin, Advil, Lisinopril",
        )
        if med:
            medicines_entered.append(med)
    with cols[1]:
        # Don't show remove on first two required fields
        if i >= 2:
            st.button(
                "❌",
                key=f"del_{i}",
                on_click=remove_med,
                args=(i,),
                help="Remove this medicine",
            )

st.markdown("---")
if st.button("Check Interactions", type="primary"):
    if len(medicines_entered) < 2:
        st.warning("Please enter at least two medicines to check for interactions.")
    else:
        with st.spinner("Analyzing active salts and cross-checking database..."):
            # Step 1: Fuzzy match user input to known salts/brands
            identified_meds = []
            unidentified = []

            for med in medicines_entered:
                matched = db.fuzzy_match_medicine(med)
                if matched:
                    identified_meds.append(matched)
                else:
                    unidentified.append(med)

            # Show identified vs unidentified
            if identified_meds:
                st.success(
                    f"✅ Identified {len(identified_meds)} medicines: "
                    + ", ".join([f"{m['name']} ({m['active_salt']})" for m in identified_meds])
                )
            if unidentified:
                st.warning(
                    f"❓ Could not identify: {', '.join(unidentified)}. Interactions may be incomplete."
                )

            # Step 2: Check interactions
            interactions = db.check_interactions(identified_meds)

            st.subheader("Interaction Analysis Results")
            if not interactions:
                st.info(
                    "No known interactions found between the identified medicines. However, always consult your doctor."
                )
            else:
                for idx, interaction in enumerate(interactions):
                    # Use Gemini to generate a patient-friendly summary
                    summary = summarize_interaction(
                        interaction["med1"],
                        interaction["med2"],
                        interaction["severity"],
                        interaction["description"],
                    )

                    # Style based on severity
                    color = "red" if interaction["severity"].lower() == "high" else "orange"
                    st.markdown(
                        f"#### ⚠️ {interaction['med1']} + {interaction['med2']}"
                    )
                    st.markdown(
                        f"**Severity:** <span style='color:{color}; font-weight:bold;'>{interaction['severity'].upper()}</span>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"**Medical Note:** {interaction['description']}")
                    st.info(f"**AI Guidance:**\n{summary}")
                    st.markdown("---")
