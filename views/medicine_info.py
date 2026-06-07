import streamlit as st
from utils.medicine_db import MedicineDatabase

st.page_link("views/dashboard.py", label="Back to Dashboard", icon="🏠")
st.title("🔬 Medicine Information Lookup")
st.markdown(
    "<p style='font-size: 1.1rem; color: #86868b;'>Search any medicine by brand name or active salt to view its uses, interactions, and safety profile.</p>",
    unsafe_allow_html=True,
)
st.markdown("---")


@st.cache_resource
def get_db():
    return MedicineDatabase()

db = get_db()

# Search input
query = st.text_input(
    "Search medicine",
    placeholder="e.g. Aspirin, Ibuprofen, Warfarin, Zoloft",
    label_visibility="collapsed",
)

if query.strip():
    result = db.fuzzy_match_medicine(query.strip())

    if result is None:
        st.warning(
            f"No medicine found matching **'{query}'**.  \n"
            "Try the brand name (e.g. 'Advil'), active salt (e.g. 'Ibuprofen'), or check spelling."
        )
        # Show all available medicines as suggestions
        with st.expander("📋 Browse all medicines in the database"):
            for med in sorted(db.medicines, key=lambda m: m["name"]):
                st.markdown(f"- **{med['name']}** — *{med['active_salt']}*")
    else:
        # Found — display full profile
        interactions = result.get("interactions", [])
        high = [i for i in interactions if i["severity"].lower() == "high"]
        moderate = [i for i in interactions if i["severity"].lower() == "moderate"]
        low = [i for i in interactions if i["severity"].lower() == "low"]

        # Header card
        risk_banner = ""
        if high:
            risk_banner = f"🔴 {len(high)} High-severity interaction(s) known"
        elif moderate:
            risk_banner = f"🟠 {len(moderate)} Moderate-severity interaction(s) known"
        else:
            risk_banner = "🟢 No high-severity interactions in current database"

        st.markdown(f"## 💊 {result['name']}")
        st.markdown(f"**Active Salt:** `{result['active_salt']}`")
        st.markdown(f"**Common Uses:** {result['uses']}")
        st.markdown(f"**Interaction Alert:** {risk_banner}")
        st.markdown("---")

        # Interactions breakdown
        st.subheader(f"⚠️ Known Drug Interactions ({len(interactions)} total)")

        if not interactions:
            st.success("No known interactions recorded for this medicine in the current database.")
        else:
            for group, emoji, color in [
                (high, "🔴", "red"),
                (moderate, "🟠", "orange"),
                (low, "🟡", "#b8860b"),
            ]:
                for interaction in group:
                    sev = interaction["severity"]
                    drug_salt = interaction["interacting_drug_salt"]
                    desc = interaction["description"]

                    # Try to find the brand name for the interacting salt
                    interacting_med = db.get_medicine_by_salt(drug_salt)
                    if interacting_med:
                        brand_label = f"{interacting_med['name']} ({drug_salt})"
                    else:
                        brand_label = drug_salt

                    with st.container():
                        st.markdown(
                            f"{emoji} **Interacts with: {brand_label}**  \n"
                            f"<span style='color:{color}; font-weight:700;'>{sev.upper()}</span> — {desc}",
                            unsafe_allow_html=True,
                        )
                        st.markdown("")

        st.markdown("---")

        # Quick action: jump to checker with this medicine pre-loaded
        if st.button(f"🔍 Check interactions involving {result['name']}", type="primary"):
            st.session_state["medication_inputs"] = [result["name"], ""]
            st.switch_page("views/interaction_checker.py")

else:
    # No query — show browsable list
    st.markdown("#### All medicines in the database")
    cols = st.columns(2)
    for i, med in enumerate(sorted(db.medicines, key=lambda m: m["name"])):
        interaction_count = len(med.get("interactions", []))
        high_count = sum(1 for x in med.get("interactions", []) if x["severity"].lower() == "high")
        badge = f"🔴 {high_count} High" if high_count else f"⚠️ {interaction_count} interactions"
        with cols[i % 2]:
            with st.expander(f"💊 {med['name']}"):
                st.markdown(f"**Salt:** `{med['active_salt']}`")
                st.markdown(f"**Uses:** {med['uses']}")
                st.markdown(f"**Interactions:** {badge}")
