import streamlit as st
import os
import tempfile

from utils.ocr_helper import extract_prescription_data

st.page_link("views/dashboard.py", label="Back to Dashboard", icon="🏠")
st.title("📄 Prescription OCR Reader")
st.markdown(
    """
<p style='font-size: 1.1rem; color: #86868b;'>
Upload a clear photo or scanned image of your prescription.
MedSafe AI uses state-of-the-art Generative AI Vision to extract the medicine names and their
probable active salts to help you understand what you've been prescribed.
</p>
""",
    unsafe_allow_html=True,
)
st.markdown("---")

MAX_FILE_SIZE_MB = 10
uploaded_file = st.file_uploader(
    "Upload Prescription Image",
    type=["jpg", "jpeg", "png", "webp"],
    help=f"Maximum file size: {MAX_FILE_SIZE_MB}MB",
)

if uploaded_file is not None:
    # File size validation
    file_size_mb = len(uploaded_file.getbuffer()) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        st.error(f"File too large ({file_size_mb:.1f}MB). Please upload an image under {MAX_FILE_SIZE_MB}MB.")
    else:
        # Display the uploaded image
        st.image(uploaded_file, caption="Uploaded Prescription", use_container_width=True)
        st.caption(f"File size: {file_size_mb:.2f}MB")

        if st.button("Extract Medicines", type="primary"):
            with st.spinner("Analyzing image using MedSafe AI Vision..."):

                # Use a secure temp file instead of writing to cwd
                suffix = os.path.splitext(uploaded_file.name)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded_file.getbuffer())
                    temp_path = tmp.name

                try:
                    extraction_result = extract_prescription_data(temp_path)
                finally:
                    # Always clean up the temp file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

                if isinstance(extraction_result, dict) and "error" in extraction_result:
                    st.error(f"OCR failed: {extraction_result['error']}")
                    st.info("Tips: Ensure the image is well-lit, not blurry, and the text is clearly visible.")
                elif isinstance(extraction_result, list) and len(extraction_result) > 0:
                    st.success(f"✅ Extraction complete — {len(extraction_result)} medicine(s) identified!")
                    st.subheader("Extracted Medicines")

                    extracted_names = []
                    for i, med in enumerate(extraction_result):
                        name = med.get("name", "Unknown")
                        salt = med.get("active_salt", "Unknown")
                        extracted_names.append(name)
                        with st.expander(f"💊 Medicine {i+1}: {name}", expanded=True):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"**Prescribed Name**")
                                st.markdown(f"`{name}`")
                            with col2:
                                st.markdown(f"**Active Salt (Identified)**")
                                st.markdown(f"`{salt}`")

                    st.markdown("---")

                    # Send to Interaction Checker button
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("🔍 Check Interactions for These Medicines", type="primary", use_container_width=True):
                            # Pre-populate the interaction checker via session state
                            st.session_state["ocr_medicines"] = extracted_names
                            st.session_state["medication_inputs"] = extracted_names + [""] if len(extracted_names) < 2 else extracted_names
                            st.switch_page("views/interaction_checker.py")
                    with col_b:
                        st.info(
                            f"Found: **{', '.join(extracted_names)}**. Click the button to check for drug interactions."
                        )
                else:
                    st.warning(
                        "Could not clearly identify any medicines from this image. "
                        "Please ensure the handwriting is legible or try a clearer photo."
                    )
