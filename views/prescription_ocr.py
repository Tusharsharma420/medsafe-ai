import streamlit as st
import os

from utils.ocr_helper import extract_prescription_data

st.page_link("views/dashboard.py", label="Back to Dashboard", icon="🏠")
st.title("📄 Prescription OCR Reader")
st.markdown(
    """
<p style='font-size: 1.1rem; color: #86868b;'>
Upload a clear photo or scanned image of your prescription. 
MedSafe AI uses state-of-the-art Generative AI Vision to extract the medicine names and their probable active salts to help you understand what you've been prescribed.
</p>
""",
    unsafe_allow_html=True,
)
st.markdown("---")

uploaded_file = st.file_uploader("Upload Prescription Image", type=["jpg", "jpeg", "png", "webp"])

if uploaded_file is not None:
    # Display the uploaded image
    st.image(uploaded_file, caption="Uploaded Prescription", use_container_width=True)

    if st.button("Extract Medicines", type="primary"):
        with st.spinner("Analyzing image using MedSafe AI Vision..."):

            # Save the file temporarily to pass to the OCR helper
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Perform extraction
            extraction_result = extract_prescription_data(temp_path)

            # Cleanup temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

            if "error" in extraction_result:
                st.error(extraction_result["error"])
            else:
                st.success("Extraction Complete!")
                st.subheader("Extracted Medicines")

                # Display results nicely
                if isinstance(extraction_result, list) and len(extraction_result) > 0:
                    for i, med in enumerate(extraction_result):
                        with st.expander(
                            f"💊 Medicine {i+1}: {med.get('name', 'Unknown')}", expanded=True
                        ):
                            st.markdown(f"**Prescribed Name:** {med.get('name', 'N/A')}")
                            st.markdown(f"**Active Salt Data:** {med.get('active_salt', 'N/A')}")

                    st.info(
                        "Tip: You can take these names and enter them into the **Interaction Checker** tool on the left to check for safety."
                    )
                else:
                    st.warning(
                        "Could not clearly identify any medicines from this image. Please ensure the handwriting is legible or try a clearer photo."
                    )
                    st.json(extraction_result)  # Display raw JSON for debugging if needed
