import streamlit as st
import random

from utils.medicine_db import MedicineDatabase

# Load DB for dynamic stats
@st.cache_resource
def get_db():
    return MedicineDatabase()

db = get_db()
total_drugs = len(db.medicines)
total_interactions = sum(len(m.get("interactions", [])) for m in db.medicines)

# Rotating tips drawn from actual database knowledge
TIPS = [
    "Combining **Aspirin** & **Warfarin** can be highly dangerous — always check before combining!",
    "**Clarithromycin** (antibiotic) can drastically increase statin levels, risking muscle damage.",
    "**Ibuprofen** can reduce the heart-protective effects of Aspirin if taken together.",
    "**Metformin** (diabetes) + **Ibuprofen** can increase the risk of lactic acidosis.",
    "**Clopidogrel** (Plavix) loses effectiveness when combined with **Omeprazole** (Prilosec).",
    "**Sertraline** (antidepressant) + NSAIDs significantly raise GI bleeding risk.",
    "**Digoxin** toxicity risk increases with **Furosemide** — both affect potassium levels.",
    "**Tramadol** + **Sertraline** can trigger serotonin syndrome — a medical emergency.",
    "**Amiodarone** can triple the effect of **Warfarin** — INR must be monitored closely.",
    "**Atenolol** (beta-blocker) can block the rescue effect of **Albuterol** in asthma patients.",
]

tip = random.choice(TIPS)

# Main dashboard UI
st.markdown(f"""
<h1 style="margin-bottom: 0px;">MedSafe AI</h1>
<p style="color: #666; margin-bottom: 1rem; font-weight: 500;">Your Intelligent Healthcare Assistant</p>
<p style="color: #999; font-size: 0.85rem; margin-bottom: 2rem;">
  📚 {total_drugs} medicines tracked &nbsp;·&nbsp; ⚠️ {total_interactions} interactions mapped
</p>

<div class="widget-grid">

<!-- Big Green Tool Card: Interaction Checker -->
<a href="interaction_checker" target="_self" class="card-link widget-full">
<div class="card bg-green" style="flex-direction: row; align-items: center;">
<div style="flex: 1;">
<div class="icon-box">💊</div>
<div class="dash-value" style="font-size: 1.8rem;">Interactions</div>
<div class="dash-sub" style="margin-bottom: 12px; margin-top: 4px;">Check drug-to-drug safety</div>
<span style="border: 1px solid #111; padding: 4px 12px; border-radius: 980px; font-size: 0.8rem; font-weight: 600;">Safety</span>
</div>
<div style="flex: 1; text-align: right; font-size: 4rem; opacity: 0.8;">
🛡️
</div>
</div>
</a>

<!-- Small White Tool Card: OCR -->
<a href="prescription_ocr" target="_self" class="card-link">
<div class="card bg-white">
<div class="icon-box" style="background-color: #f7f9fa; box-shadow: none;">📄</div>
<div class="dash-label">Prescription</div>
<div class="dash-sub">AI Scanner</div>
</div>
</a>

<!-- Small Blue Tool Card: Symptom Solver -->
<a href="symptom_solver" target="_self" class="card-link">
<div class="card bg-blue">
<div class="icon-box" style="background-color: #fff; box-shadow: none;">🩺</div>
<div class="dash-label">Symptoms</div>
<div class="dash-sub">AI Guidance</div>
</div>
</a>

<!-- Small Purple Card: Medicine Info -->
<a href="medicine_info" target="_self" class="card-link">
<div class="card bg-purple">
<div class="icon-box" style="background-color: #fff; box-shadow: none;">🔬</div>
<div class="dash-label">Medicine Info</div>
<div class="dash-sub">Look up any drug</div>
</div>
</a>

<!-- Yellow Info Card: Rotating Tip -->
<div class="card bg-yellow widget-full" style="flex-direction: row; align-items: center; padding: 16px 24px;">
<div class="icon-box" style="width: 48px; height: 48px; margin-right: 12px; font-size: 1.5rem; background-color: #fff; flex-shrink: 0;">💡</div>
<div style="flex: 1;">
<div style="font-weight: 700; font-size: 1.1rem;">Did you know?</div>
<div class="dash-sub">{tip}</div>
</div>
</div>

</div>
""", unsafe_allow_html=True)
