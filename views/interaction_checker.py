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

# Load stats for display
total_drugs = len(db.medicines)
total_interactions = sum(len(m.get("interactions", [])) for m in db.medicines)
st.caption(f"📚 Database: **{total_drugs} medicines** tracked · **{total_interactions} interactions** mapped")

# Session state — pre-populate from OCR if available
if "medication_inputs" not in st.session_state:
    st.session_state.medication_inputs = ["", ""]


def add_med():
    st.session_state.medication_inputs.append("")


def remove_med(index):
    if len(st.session_state.medication_inputs) > 2:
        st.session_state.medication_inputs.pop(index)


def clear_all():
    st.session_state.medication_inputs = ["", ""]


col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    st.markdown("#### Your Medicines")
with col2:
    st.write("")
    st.button("➕ Add Medicine", on_click=add_med, use_container_width=True)
with col3:
    st.write("")
    st.button("🗑 Clear All", on_click=clear_all, use_container_width=True)

# Render input fields dynamically
medicines_entered = []
for i, val in enumerate(st.session_state.medication_inputs):
    cols = st.columns([10, 1])
    with cols[0]:
        med = st.text_input(
            f"Medicine {i+1}",
            value=val,
            key=f"med_{i}",
            placeholder="e.g. Aspirin, Advil, Lisinopril, Warfarin",
        )
        if med:
            medicines_entered.append(med)
    with cols[1]:
        if i >= 2:
            st.button(
                "❌",
                key=f"del_{i}",
                on_click=remove_med,
                args=(i,),
                help="Remove this medicine",
            )

st.markdown("---")
if st.button("🔍 Check Interactions", type="primary"):
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

            # Show resolution results
            if identified_meds:
                st.success(
                    f"✅ Resolved **{len(identified_meds)}** medicine(s): "
                    + " · ".join([f"**{m['name']}** ({m['active_salt']})" for m in identified_meds])
                )
            if unidentified:
                st.warning(
                    f"❓ Could not identify: **{', '.join(unidentified)}**  \n"
                    "Check the spelling, or try using the active salt name (e.g. 'Ibuprofen' instead of 'Advil')."
                )

            # Step 2: Check interactions
            interactions = db.check_interactions(identified_meds)

            st.subheader("Interaction Analysis Results")

            if not interactions:
                st.success(
                    "✅ No known interactions found between the identified medicines in our database.  \n"
                    "*Always consult your doctor or pharmacist before combining medications.*"
                )
            else:
                # Summary header
                high_count = sum(1 for i in interactions if i["severity"].lower() == "high")
                mod_count = sum(1 for i in interactions if i["severity"].lower() == "moderate")
                low_count = sum(1 for i in interactions if i["severity"].lower() == "low")

                summary_parts = []
                if high_count:
                    summary_parts.append(f"🔴 **{high_count} High**")
                if mod_count:
                    summary_parts.append(f"🟠 **{mod_count} Moderate**")
                if low_count:
                    summary_parts.append(f"🟡 **{low_count} Low**")

                st.error(
                    f"⚠️ Found **{len(interactions)} interaction(s)**: {' · '.join(summary_parts)}"
                )

                for idx, interaction in enumerate(interactions):
                    sev = interaction["severity"].lower()
                    color = "red" if sev == "high" else ("orange" if sev == "moderate" else "#b8860b")
                    sev_emoji = "🔴" if sev == "high" else ("🟠" if sev == "moderate" else "🟡")

                    st.markdown(f"#### {sev_emoji} {interaction['med1']} + {interaction['med2']}")
                    st.markdown(
                        f"**Severity:** <span style='color:{color}; font-weight:bold;'>{interaction['severity'].upper()}</span>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"**Clinical Note:** {interaction['description']}")

                    # Use Gemini to generate patient-friendly summary
                    summary = summarize_interaction(
                        interaction["med1"],
                        interaction["med2"],
                        interaction["severity"],
                        interaction["description"],
                    )
                    st.info(f"**AI Guidance:**\n{summary}")
                    st.markdown("---")
