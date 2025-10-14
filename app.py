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

# Custom Montserrat font and layout styling
st.markdown("""
    <style>
    /* Import Montserrat */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600&display=swap');

    /* Universal font across app */
    html, body, [class*="css"] {
        font-family: 'Montserrat', sans-serif !important;
    }

    /* Base typography for Streamlit widgets */
    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stTextInputRoot"] label,
    div[data-testid="stTextAreaRoot"] label,
    div[data-testid="stSelectboxRoot"] label,
    div[data-testid="stMultiSelectRoot"] label,
    div[data-testid="stButton"] button,
    div[data-testid="stDownloadButton"] button,
    input, textarea, select {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 400 !important;
    }

    h1, h2, h3 {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 600 !important;
        line-height: 1.2;
    }

    h1 {
        font-size: 2rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* ✨ Smooth theme transitions */
    * {
      transition: background-color 0.3s ease, color 0.3s ease;
    }        
    

    /* Force col1 width to 240px */
    div[data-testid="column"]:first-of-type {
        flex: 0 0 240px !important;  /* fixed width */
        max-width: 240px !important;
        min-width: 240px !important;
    }

    /* Let col2 fill the rest */
    div[data-testid="column"]:nth-of-type(2) {
        flex: 1 1 auto !important;
    }
            
    /* Force Streamlit text area height overrides */
    div[data-testid="stTextAreaRoot"] textarea {
        min-height: 90px !important;   /* adjust here for 3-line height */
        height: 90px !important;
        line-height: 1.4 !important;
        font-size: 0.9rem !important;
    }


    </style>
""", unsafe_allow_html=True)

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

editorial = st.selectbox("Editorial?", ["no", "yes"])
mature = st.selectbox("Mature content?", ["no", "yes"])
illustration = st.selectbox("Illustration?", ["no", "yes"])

# ------------------------------------------------------------
# 7. Upload section
# ------------------------------------------------------------


uploaded_files = st.file_uploader(
    "Upload stock images",
    type=["jpg", "png", "jpeg"],
    accept_multiple_files=True
)

if uploaded_files:
    results = []

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
                            height=110,  # fits ~3 lines comfortably
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
        df = pd.DataFrame(
            results,
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
st.caption("© 2024 NYskytigers. All rights reserved.")

