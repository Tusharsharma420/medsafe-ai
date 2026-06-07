import streamlit as st

st.set_page_config(
    page_title="MedSafe AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Apple-like Light Mode, Bold Typography, Smooth UI, Dashboard)
st.markdown("""
<style>
    /* Base typography targeting Apple constraints */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    
    html, body, [class*="css"], .stMarkdown, .stText {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", "Inter", sans-serif !important;
        background-color: #f7f9fa !important; /* Soft white/gray wave background */
        color: #111111 !important; 
    }
    
    /* Bold, clean headings */
    h1, h2, h3, h4, h5, h6 {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Inter", sans-serif !important;
        color: #111111 !important;
        font-weight: 800 !important;
        letter-spacing: -0.03em !important;
    }
    
    h1 {
        font-weight: 800 !important;
        font-size: 2.8rem !important;
    }
    
    /* Main container padding & invisible wrapper */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 3rem;
        max-width: 480px; /* Force mobile width feeling */
        background-color: transparent !important;
        margin-top: 0rem;
    }

    /* UI Widgets */
    .widget-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
        margin-top: 20px;
    }
    .widget-full {
        grid-column: span 2;
    }
    
    a.card-link {
        text-decoration: none !important;
        color: inherit !important;
        display: block;
        transition: transform 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
    }
    
    a.card-link:hover {
        transform: translateY(-4px) scale(1.01);
    }
    
    .card {
        border-radius: 32px;
        padding: 24px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.03);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        position: relative;
        overflow: hidden;
        height: 100%;
        cursor: pointer;
    }
    
    /* Colors inspired by image */
    .bg-green { background-color: #d1f2cf !important; }
    .bg-blue { background-color: #c9ebf2 !important; }
    .bg-yellow { background-color: #fceea6 !important; }
    .bg-white { background-color: #ffffff !important; }
    .bg-purple { background-color: #e8d5f5 !important; }

    /* Dashboard text */
    .dash-label {
        font-size: 0.9rem;
        font-weight: 600;
        color: rgba(0,0,0,0.6);
        margin-bottom: 4px;
    }
    .dash-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #111;
        letter-spacing: -0.05em;
        line-height: 1.1;
    }
    .dash-sub {
        font-size: 0.8rem;
        font-weight: 500;
        color: rgba(0,0,0,0.5);
    }
    
    /* Icons */
    .icon-box {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background-color: white;
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }

    /* Header Profile */
    .profile-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
    }
    .profile-info {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .profile-img {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        background-color: #eee;
        object-fit: cover;
    }
    
    /* Primary buttons */
    .stButton > button {
        background-color: #111111 !important;
        color: white !important;
        border-radius: 980px !important; 
        border: none !important;
        padding: 0.6rem 1.2rem !important;
        font-weight: 600 !important;
        transition: transform 0.2s !important;
    }
    .stButton > button:hover {
        transform: scale(1.02);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"],
    [data-testid="stSidebarNav"],
    [data-testid="collapsedControl"],
    [data-testid="stHeader"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Setup Sidebar Navigation using Streamlit native pages
pg = st.navigation([
    st.Page("views/dashboard.py", title="Dashboard", icon="🏠", default=True),
    st.Page("views/interaction_checker.py", title="Interaction Checker", icon="💊", url_path="interaction_checker"),
    st.Page("views/prescription_ocr.py", title="Prescription OCR", icon="📄", url_path="prescription_ocr"),
    st.Page("views/symptom_solver.py", title="Symptom Solver", icon="🩺", url_path="symptom_solver"),
    st.Page("views/medicine_info.py", title="Medicine Info", icon="🔬", url_path="medicine_info"),
])
pg.run()

