"""Optional local models. No Streamlit, network calls only on explicit construction."""
from functools import lru_cache
from .core import clean_caption, refine_caption


class LocalBackend:
    def __init__(self):
        try:
            from transformers import BlipProcessor, BlipForConditionalGeneration
            from keybert import KeyBERT
        except ImportError as error:
            raise RuntimeError('Local AI dependencies missing; install stock-auto-caption[ai]') from error
        name = "Salesforce/blip-image-captioning-base"
        # Slow processor avoids implicit torchvision dependency.
        self.processor = BlipProcessor.from_pretrained(name, use_fast=False)
        self.model = BlipForConditionalGeneration.from_pretrained(name).eval()
        self.kw_model = KeyBERT(model="all-MiniLM-L6-v2")

    def generate_caption(self, image):
        import torch
        inputs = self.processor(image.convert("RGB"), return_tensors="pt")
        with torch.inference_mode():
            output = self.model.generate(**inputs)
        return clean_caption(self.processor.decode(output[0], skip_special_tokens=True))

    def refine_caption_and_keywords(self, raw_caption, selected_categories):
        # Categories are classification fields, not evidence of visible content.
        return refine_caption(raw_caption, self.kw_model)


@lru_cache(maxsize=1)
def get_local_backend():
    return LocalBackend()
