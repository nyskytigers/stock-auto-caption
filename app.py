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
st.title("Shutterstock_Content_Upload Generator(MVP)")
st.write("Upload your stock images to automatically generate Shutterstock-ready captions and SEO keywords.")

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

uploaded_files = st.file_uploader(
    "Upload stock images",
    type=["jpg", "png", "jpeg"],
    accept_multiple_files=True
)

if uploaded_files:
    results = []
    for uploaded_file in uploaded_files:
        image = Image.open(uploaded_file).convert("RGB")
        st.image(image, caption=uploaded_file.name, use_container_width=True)

        with st.spinner("🔎 Generating caption and keywords..."):
            try:
                raw_caption = generate_caption(image)
                caption, keywords = refine_caption_and_keywords(raw_caption, selected_categories)

                st.success(f"**Caption:** {caption}\n\n**Keywords:** {keywords}")

                results.append([
                    uploaded_file.name,
                    caption,
                    keywords,
                    ",".join(selected_categories),
                    editorial,
                    mature,
                    illustration
                ])
            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {e}")

    # --------------------------------------------------------
    # 6. Export to Shutterstock CSV format
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
# 7. Footer
# ------------------------------------------------------------
st.caption("💡 Uses BLIP for captioning and KeyBERT for keyword generation.")
