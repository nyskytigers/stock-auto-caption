import streamlit as st
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
from keybert import KeyBERT

class ModelLoader:
    """
    Handles loading all AI models and running inference.
    """
    def __init__(self):
        self.processor, self.model = self.load_blip_model()
        self.kw_model = self.load_keybert_model()

    @st.cache_resource
    def load_blip_model(_self):
        """Loads the BLIP model for image captioning."""
        processor = BlipProcessor.from_pretrained(
            "Salesforce/blip-image-captioning-base", 
            use_fast=True
        )
        model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        return processor, model

    @st.cache_resource
    def load_keybert_model(_self):
        """Loads the KeyBERT model for keyword extraction."""
        return KeyBERT(model='all-MiniLM-L6-v2')

    def generate_caption(self, image: Image.Image) -> str:
        """Generates a raw caption for a given PIL image."""
        # Note: BLIP model expects RGB
        rgb_image = image.convert("RGB")
        inputs = self.processor(rgb_image, return_tensors="pt")
        out = self.model.generate(**inputs)
        caption = self.processor.decode(out[0], skip_special_tokens=True)
        return caption.strip().capitalize()

    def refine_caption_and_keywords(self, raw_caption: str, selected_categories: list) -> (str, str):
        """Cleans a caption and extracts keywords using KeyBERT."""
        
        # 1. Clean caption
        caption = raw_caption.strip().capitalize()
        if len(caption) > 150:
            caption = caption[:147] + "..."
        
        # 2. Generate top 25 keywords
        keywords = self.kw_model.extract_keywords(
            caption,
            keyphrase_ngram_range=(1, 2),
            stop_words='english',
            top_n=25
        )
        keyword_list = [kw[0] for kw in keywords]

        # 3. Merge with category choices
        if selected_categories:
            for cat in selected_categories:
                if cat and cat.strip():
                    keyword_list.append(cat.strip())
        
        # 4. Deduplicate & clean
        # Use dict.fromkeys to preserve order and remove duplicates
        keyword_list = list(dict.fromkeys(keyword_list))
        keywords_str = ", ".join(keyword_list)

        return caption, keywords_str

