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

st.title("Shutterstock Content Upload Generator(MVP)")
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

if uploaded_files:  

    # Section Title (normal font, no emoji)
    st.markdown("Preview & Edit Metadata", unsafe_allow_html=True)

    # Responsive card grid
    for idx, uploaded_file in enumerate(uploaded_files):
        image = Image.open(uploaded_file).convert("RGB")

        with st.container():
      
            # Two-column grid (auto-adjusts on wide screens)
            
            col1, col2 = st.columns([1, 2], vertical_alignment="center")

            # --- Left column (Image) ---
            with col1:
            # Fix preview height (center image vertically)
                preview_width = 220
                preview_height = 220
                image.thumbnail((preview_width, preview_height))

                st.image(image, caption=None, width=220)
              
            # --- Right column (Caption + Keywords) ---
            with col2:
             
                st.text_input(
                    label="Filename",
                    value=uploaded_file.name,
                    key=f"filename_{uploaded_file.name}"
                )
                with st.spinner("🔎 Generating caption and keywords..."):
                    try:
                        raw_caption = generate_caption(image)
                        caption, keywords = refine_caption_and_keywords(raw_caption, selected_categories)

                        st.text_area(
                            "Caption",
                            caption,
                            height=70,
                            key=f"caption_{uploaded_file.name}",
                        )
                        st.text_area(
                            "Keywords (comma-separated)",
                            keywords,
                            height=110,  
                            key=f"keywords_{uploaded_file.name}",
                        )

                        results.append([
                            uploaded_file.name,
                            caption.strip(),
                            keywords.strip(),
                            ",".join(selected_categories),
                            editorial,
                            mature,
                            illustration
                        ])
                    except Exception as e:
                        st.error(f"Error processing {uploaded_file.name}: {e}")

            # --- Divider between image blocks ---
            st.markdown(
                "<hr style='border:0.5px solid #3a3a3a; margin:1.5rem 0;'/>",
                unsafe_allow_html=True
                )


# --------------------------------------------------------
# 8. Export to Shutterstock CSV format
# --------------------------------------------------------
if results:
    # Rebuild results with latest user edits from session_state
    final_results = []
    for uploaded_file in uploaded_files:
        filename = st.session_state.get(f"filename_{uploaded_file.name}", uploaded_file.name)
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
# 9. Footer
# ------------------------------------------------------------
st.caption("💡 Uses BLIP for captioning and KeyBERT for keyword generation.")

st.caption("Developed by 🌐[NYskytigers](https://nyskytigers.com) | 🫙[GitHub](https://github.com/nyskytigers/stock-auto-caption) | 🍵[Buy me a coffee](https://www.buymeacoffee.com/nyskytigers)")
st.caption("© 2025 NYskytigers. All rights reserved.")

