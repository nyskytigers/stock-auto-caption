import streamlit as st
from models import ModelLoader
from exporters import ShutterstockExporter, AdobeStockExporter, IStockExporter

class StockImageApp:
    """
    The main Streamlit application class.
    
    It orchestrates the UI and wires together the models and exporters.
    """
    def __init__(self):
        # Load models once.
        self.models = ModelLoader()
        
        # Define all available exporters
        self.exporters = {
            "Shutterstock": ShutterstockExporter(),
            "Adobe Stock": AdobeStockExporter(),
            "iStock": IStockExporter()
        }

    def _draw_header(self):
        """Sets page config and draws the main title."""
        st.set_page_config(page_title="Stock Image Metadata Generator")
        
        # Load Google Font
        st.markdown("""
            <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600&display=swap" rel="stylesheet">
        """, unsafe_allow_html=True)

        # Load external CSS
        try:
            with open("style.css", encoding="utf-8") as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        except FileNotFoundError:
            st.warning("style.css not found. Skipping CSS load.")

        st.title("StockWords AI")
        st.write("AI-powered captions and keywords for creators.")

    def _draw_footer(self):
        """Draws the footer links."""
        st.caption("💡 Uses BLIP for captioning and KeyBERT for keyword generation.")
        st.caption("Developed by 🌐[NYskytigers](https://nyskytigers.com) | 🫙[GitHub](https://github.com/nyskytigers/stock-auto-caption) | 🍵[Buy me a coffee](https://www.buyme-acoffee.com/nyskytigers)")
        st.caption("© 2025 NYskytigers. All rights reserved.")

    def run(self):
        """Runs the main application loop."""
        self._draw_header()

        uploaded_files = st.file_uploader(
            "Upload your stock images to automatically generate metadata:",
            type=["jpg", "png", "jpeg"],
            accept_multiple_files=True
        )

        if not uploaded_files:
            st.info("Upload one or more images above to begin.")
            self._draw_footer()
            return # Stop execution if no files

        # Create tabs based on the exporter names
        tab_list = st.tabs(self.exporters.keys())

        # Iterate over the tabs and exporters together
        for tab, (site_name, exporter) in zip(tab_list, self.exporters.items()):
            with tab:
                try:
                    # 1. Draw config and get selections
                    config = exporter.draw_config_options()
                    
                    # 2. Draw batch controls (now inherited by exporter)
                    exporter.draw_batch_controls(uploaded_files)
                    
                    # 3. Draw image editors (pass models and config)
                    exporter.draw_image_editors(uploaded_files, config, self.models)
                    
                    # 4. Draw export button
                    exporter.draw_export_button(uploaded_files, config)
                
                except Exception as e:
                    st.error(f"An error occurred in the {site_name} tab: {e}")
                    st.exception(e) # Show full traceback for debugging

        self._draw_footer()


if __name__ == "__main__":
    app = StockImageApp()
    app.run()

