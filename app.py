# app.py
import streamlit as st
import pandas as pd
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
from keybert import KeyBERT

# ------------------------------------------------------------
# 1. Load BLIP model (for image captioning)
# ------------------------------------------------------------
@st.cache_resource
def load_blip_model():
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
    return processor, model

processor, model = load_blip_model()

# ------------------------------------------------------------
# 2. Load KeyBERT model (for keyword extraction)
# ------------------------------------------------------------
@st.cache_resource
def load_keybert_model():
    return KeyBERT(model='all-MiniLM-L6-v2')

kw_model = load_keybert_model()

# ------------------------------------------------------------
# 3. Generate image caption using BLIP
# ------------------------------------------------------------
def generate_caption(image):
    inputs = processor(image, return_tensors="pt")
    out = model.generate(**inputs)
    caption = processor.decode(out[0], skip_special_tokens=True)
    return caption.strip().capitalize()

# ------------------------------------------------------------
# 4. Refine caption & extract keywords using KeyBERT
# ------------------------------------------------------------
def refine_caption_and_keywords(raw_caption, selected_categories):
    caption = raw_caption.strip().capitalize()
    if len(caption) > 150:
        caption = caption[:147] + "..."
    
    # Generate top 25 keywords
    keywords = kw_model.extract_keywords(
        caption,
        keyphrase_ngram_range=(1, 2),
        stop_words='english',
        top_n=25
    )
    keyword_list = [kw[0] for kw in keywords]

    # Merge with Shutterstock category choices
    if selected_categories:
        keyword_list.extend(selected_categories)
    
    # Deduplicate & clean
    keyword_list = list(dict.fromkeys(keyword_list))
    keywords_str = ", ".join(keyword_list)

    return caption, keywords_str

# ------------------------------------------------------------
# 5. Streamlit UI
# ------------------------------------------------------------

st.set_page_config(page_title="Shutterstock Keyword Generator")

# Load Google Font separately (since Streamlit blocks @import inside CSS)
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

# Load external CSS file
#def local_css(file_name):
    #with open(file_name) as f:
       # st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Load external CSS file safely (UTF-8 for Windows)
def local_css(file_name):
    with open(file_name, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Apply styles
local_css("style.css")

st.title("Image Captions and Keywords Generator(MVP)")
st.write("Upload your stock images to automatically generate Shutterstock-ready captions and SEO keywords.")

# ------------------------------------------------------------
# 6. Category and metadata controls
# ------------------------------------------------------------
categories_list = [
    "Religion", "Science", "Signs/Symbols", "Sports/Recreation", "Technology", "Transportation", "Vintage",
    "Abstract", "Animals/Wildlife", "Arts", "Backgrounds/Textures", "Beauty/Fashion", "Buildings/Landmarks",
    "Business/Finance", "Celebrities", "Education", "Food and drink", "Healthcare/Medical", "Holidays",
    "Industrial", "Interiors", "Miscellaneous", "Nature", "Objects", "Parks/Outdoor", "People"
]

selected_categories = st.multiselect(
    "Select up to 2 Shutterstock categories:",
    options=categories_list,
    max_selections=2
)

# Three columns for dropdowns (aligned horizontally)
col1, col2, col3 = st.columns(3)

with col1:
    editorial = st.selectbox("Editorial?", ["no", "yes"], key="editorial_select")
with col2:
    mature = st.selectbox("Mature content?", ["no", "yes"], key="mature_select")
with col3:
    illustration = st.selectbox("Illustration?", ["no", "yes"], key="illustration_select")

# ------------------------------------------------------------
# 7. Upload section
# ------------------------------------------------------------
uploaded_files = st.file_uploader(
    "Upload stock images",
    type=["jpg", "png", "jpeg"],
    accept_multiple_files=True
)
results = []

# ------------------------------------------------------------
# 8. Batch Edit: Apply to All Captions / Keywords
# ------------------------------------------------------------
if uploaded_files:
    st.markdown("### ⚙️ Batch Edit Options")

    # Inputs for master caption and keywords
    global_caption_input = st.text_area(
        "✏️ Master Caption (to append)",
        "",
        height=70,
        key="global_caption" # Use key to hold the value
    )
    global_keywords_input = st.text_area(
        "🔑 Master Keywords (to append, comma-separated)",
        "",
        height=90,
        key="global_keywords" # Use key to hold the value
    )

    col_apply1, col_apply2 = st.columns(2)
    with col_apply1:
        # --- CHANGED BUTTON LABEL AND LOGIC ---
        if st.button("➕ Append Caption to All"):
            if global_caption_input.strip():
                # Directly loop and update the session state for each file
                for file in uploaded_files:
                    key = f"caption_{file.name}"
                    original_caption = st.session_state.get(key, "")
                    # Append new caption
                    new_caption = (original_caption + " " + global_caption_input.strip()).strip()
                    st.session_state[key] = new_caption
                st.success("✅ Master caption appended to all images.")
            else:
                st.warning("Master caption is empty.")
                
    with col_apply2:
        # --- CHANGED BUTTON LABEL AND LOGIC ---
        if st.button("➕ Append Keywords to All"):
            master_keywords_str = global_keywords_input.strip()
            if master_keywords_str:
                # Loop and update the session state for each file
                for file in uploaded_files:
                    key = f"keywords_{file.name}"
                    original_keywords_str = st.session_state.get(key, "")
                    
                    # Get original keywords as a clean list
                    original_list = [k.strip() for k in original_keywords_str.split(",") if k.strip()]
                    
                    # Get master keywords as a clean list
                    master_list = [k.strip() for k in master_keywords_str.split(",") if k.strip()]
                    
                    # Combine and deduplicate
                    combined_list = original_list + master_list
                    deduplicated_list = list(dict.fromkeys(combined_list)) # Preserves order
                    
                    # Save back to session state
                    st.session_state[key] = ", ".join(deduplicated_list)
                    
                st.success("✅ Master keywords appended and deduplicated.")
            else:
                st.warning("Master keywords are empty.")

    # ------------------------------------------------------------
    # 9. Generate and Edit Each Image
    # ------------------------------------------------------------
    st.markdown("### Preview & Edit Metadata")
    for idx, uploaded_file in enumerate(uploaded_files):
        image = Image.open(uploaded_file).convert("RGB")
        
        # Define the unique session state keys for this file
        caption_key = f"caption_{uploaded_file.name}"
        keywords_key = f"keywords_{uploaded_file.name}"

        with st.container():
            col1, col2 = st.columns([1, 2], vertical_alignment="center")
            with col1:
                preview_width, preview_height = 220, 220
                image.thumbnail((preview_width, preview_height))
                st.image(image, caption=None, width=220)

            with col2:
                st.text_input("Filename", value=uploaded_file.name, key=f"filename_{uploaded_file.name}", disabled=True)

                # --- This is the new logic ---
                # Only generate if it hasn't been generated before (or applied)
                if caption_key not in st.session_state:
                    with st.spinner("🔎 Generating caption and keywords..."):
                        try:
                            raw_caption = generate_caption(image)
                            caption, keywords = refine_caption_and_keywords(raw_caption, selected_categories)
                            
                            # Store them in session state
                            st.session_state[caption_key] = caption
                            st.session_state[keywords_key] = keywords
                        
                        except Exception as e:
                            st.error(f"Error processing {uploaded_file.name}: {e}")
                            st.session_state[caption_key] = "Error"
                            st.session_state[keywords_key] = "Error"

                # Create widgets using the session state keys.
                # The widget will now always show the value from st.session_state
                st.text_area(
                    "Caption",
                    height=70,
                    key=caption_key # This key binds the widget to the session state
                )

                st.text_area(
                    "Keywords (comma-separated)",
                    height=110,
                    key=keywords_key # This key binds the widget to the session state
                )

            st.markdown("<hr style='border:0.5px solid #3a3a3a; margin:1.5rem 0;'/>", unsafe_allow_html=True)

# ------------------------------------------------------------
# 10. Export to Shutterstock CSV format
# ------------------------------------------------------------
if uploaded_files:
    final_results = []
    for uploaded_file in uploaded_files:
        filename = uploaded_file.name
        
        # Read directly from the session state keys
        caption = st.session_state.get(f"caption_{uploaded_file.name}", "")
        keywords = st.session_state.get(f"keywords_{uploaded_file.name}", "")
        
        final_results.append([
            filename,
            caption.strip(),
            keywords.strip(),
            ",".join(selected_categories),
            editorial,
            mature,
            illustration
        ])

    if final_results:
        df = pd.DataFrame(
            final_results,
            columns=[
                "Filename",
                "Description",
                "Keywords",
                "Categories",
                "Editorial",
                "Mature content",
                "Illustration"
            ]
        )

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download Shutterstock CSV",
            csv,
            "shutterstock_content_upload.csv",
            "text/csv"
        )

# ------------------------------------------------------------
# 11. Footer
# ------------------------------------------------------------
st.caption("💡 Uses BLIP for captioning and KeyBERT for keyword generation.")

st.caption("Developed by 🌐[NYskytigers](https://nyskytigers.com) | 🫙[GitHub](https://github.com/nyskytigers/stock-auto-caption) | 🍵[Buy me a coffee](https://www.buymeacoffee.com/nyskytigers)")
st.caption("© 2025 NYskytigers. All rights reserved.")

