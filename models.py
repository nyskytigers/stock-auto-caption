"""Backward-compatible Streamlit adapter for the optional local backend."""
import streamlit as st
from stock_metadata.backends import LocalBackend


class ModelLoader(LocalBackend):
    def __init__(self):
        backend = self.load_backend()
        self.processor, self.model, self.kw_model = backend.processor, backend.model, backend.kw_model

    @staticmethod
    @st.cache_resource
    def load_backend():
        return LocalBackend()

    def load_blip_model(self):
        return self.processor, self.model

    def load_keybert_model(self):
        return self.kw_model


