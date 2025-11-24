import streamlit as st
import pandas as pd
import io
import zipfile
import os
from PIL import Image
from models import ModelLoader # Import our model loader

class BaseExporter:
    """
    A base template for all stock site exporters.
    Subclasses must implement these methods.
    """
    def __init__(self, site_name: str):
        self.site_name = site_name
        self.key_prefix = f"{site_name.lower()[:2]}_" # e.g., "ss_" or "as_"

    def draw_config_options(self) -> dict:
        """Draws the config dropdowns (categories, etc.) and returns selections."""
        raise NotImplementedError

    def draw_batch_controls(self, uploaded_files: list):
        """
        Draws the 'Apply to All' buttons and logic.
        This method is now shared by all subclasses.
        """
        st.markdown("### ⚙️ Batch Edit Options")
        
        # --- Master Title/Caption Section ---
        global_caption = st.text_area(
            "✏️ Master Title (to append, optional)", "", height=70, key=f"{self.key_prefix}global_caption"
        )
        cap_btn_col, cap_msg_col = st.columns([1, 2], vertical_alignment="center")
        with cap_btn_col:
            if st.button("➕ Apply to All", key=f"{self.key_prefix}cap_btn"):
                if global_caption.strip():
                    for file in uploaded_files:
                        key = f"{self.key_prefix}caption_{file.name}"
                        original = st.session_state.get(key, "")
                        st.session_state[key] = (original + " " + global_caption.strip()).strip()
                    with cap_msg_col: st.markdown("✅ Titles/Captions appended.")
                else:
                    with cap_msg_col: st.markdown("💔 Master title is empty.")
        
        # --- Master Keywords Section ---
        global_keywords = st.text_area(
            "🔑 Master Keywords (to append, comma-separated, optional)", "", height=90, key=f"{self.key_prefix}global_keywords"
        )
        key_btn_col, key_msg_col = st.columns([1, 2], vertical_alignment="center")
        with key_btn_col:
            if st.button("➕ Apply to All", key=f"{self.key_prefix}key_btn"):
                if global_keywords.strip():
                    for file in uploaded_files:
                        key = f"{self.key_prefix}keywords_{file.name}"
                        original_str = st.session_state.get(key, "")
                        original_list = [k.strip() for k in original_str.split(",") if k.strip()]
                        master_list = [k.strip() for k in global_keywords.split(",") if k.strip()]
                        deduplicated_list = list(dict.fromkeys(original_list + master_list))
                        st.session_state[key] = ", ".join(deduplicated_list)
                    with key_msg_col: st.markdown("✅ Keywords appended.")
                else:
                    with key_msg_col: st.markdown("💔 Master keywords are empty.")
        st.markdown("---")

    def draw_image_editors(self, uploaded_files: list, config: dict, models: ModelLoader):
        """Draws the editor for each individual image."""
        raise NotImplementedError

    def draw_export_button(self, uploaded_files: list, config: dict):
        """Draws the final 'Download CSV' button."""
        raise NotImplementedError


class ShutterstockExporter(BaseExporter):
    """
    Implements the UI and export logic for Shutterstock.
    """
    def __init__(self):
        super().__init__("Shutterstock")

    def draw_config_options(self) -> dict:
        st.subheader("Shutterstock Generator")
        
        categories_list = [
            "Religion", "Science", "Signs/Symbols", "Sports/Recreation", "Technology", "Transportation", "Vintage",
            "Abstract", "Animals/Wildlife", "Arts", "Backgrounds/Textures", "Beauty/Fashion", "Buildings/Landmarks",
            "Business/Finance", "Celebrities", "Education", "Food and drink", "Healthcare/Medical", "Holidays",
            "Industrial", "Interiors", "Miscellaneous", "Nature", "Objects", "Parks/Outdoor", "People"
        ]
        
        selected_categories = st.multiselect(
            "Select up to 2 Shutterstock categories:",
            options=categories_list,
            max_selections=2,
            key=f"{self.key_prefix}categories"
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            editorial = st.selectbox("Editorial?", ["no", "yes"], key=f"{self.key_prefix}editorial_select")
        with col2:
            mature = st.selectbox("Mature content?", ["no", "yes"], key=f"{self.key_prefix}mature_select")
        with col3:
            illustration = st.selectbox("Illustration?", ["no", "yes"], key=f"{self.key_prefix}illustration_select")
            
        return {
            "categories": selected_categories,
            "editorial": editorial,
            "mature": mature,
            "illustration": illustration
        }

    #
    # draw_batch_controls() is now inherited from BaseExporter
    #

    def draw_image_editors(self, uploaded_files: list, config: dict, models: ModelLoader):
        st.markdown("### 🖼️ Preview & Edit Metadata")
        
        selected_categories = config.get("categories", [])
        
        for uploaded_file in uploaded_files:
            image = Image.open(uploaded_file)
            caption_key = f"{self.key_prefix}caption_{uploaded_file.name}"
            keywords_key = f"{self.key_prefix}keywords_{uploaded_file.name}"

            with st.container():
                col1, col2 = st.columns([1, 2], vertical_alignment="center")
                with col1:
                    image.thumbnail((220, 220))
                    st.image(image, caption=None, width=220)
                with col2:
                    st.text_input("Filename", value=uploaded_file.name, key=f"{self.key_prefix}filename_{uploaded_file.name}", disabled=True)
                    
                    if caption_key not in st.session_state:
                        with st.spinner("🔎 Generating metadata..."):
                            try:
                                raw_caption = models.generate_caption(image)
                                caption, keywords = models.refine_caption_and_keywords(raw_caption, selected_categories)
                                st.session_state[caption_key] = caption
                                st.session_state[keywords_key] = keywords
                            except Exception as e:
                                st.error(f"Error processing {uploaded_file.name}: {e}")
                                st.session_state[caption_key] = "Error"
                                st.session_state[keywords_key] = "Error"
                    
                    # Note: Label is "Caption" here
                    st.text_area("Caption", height=70, key=caption_key) 
                    st.text_area("Keywords (comma-separated)", height=110, key=keywords_key)
                st.markdown("<hr style='border:0.5px solid #3a3a3a; margin:1.5rem 0;'/>", unsafe_allow_html=True)

    def draw_export_button(self, uploaded_files: list, config: dict):
        st.markdown("### ⬇️ Export Shutterstock CSV")
        final_results = []
        
        for uploaded_file in uploaded_files:
            # CHANGE: Replace extension with .eps
            filename_eps = os.path.splitext(uploaded_file.name)[0] + ".eps"

            final_results.append([
                filename_eps,
                st.session_state.get(f"{self.key_prefix}caption_{uploaded_file.name}", "").strip(),
                st.session_state.get(f"{self.key_prefix}keywords_{uploaded_file.name}", "").strip(),
                ",".join(config.get("categories", [])),
                config.get("editorial", "no"),
                config.get("mature", "no"),
                config.get("illustration", "no")
            ])
            
        df = pd.DataFrame(
            final_results, 
            columns=["Filename", "Description", "Keywords", "Categories", "Editorial", "Mature content", "Illustration"]
        )
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download Shutterstock CSV", csv, "shutterstock_upload.csv", "text/csv", key=f"{self.key_prefix}download_btn"
        )


class AdobeStockExporter(BaseExporter):
    """
    Implements the UI and export logic for Adobe Stock.
    """
    def __init__(self):
        super().__init__("AdobeStock")
        self.categories_list = [
            "Animals", "Buildings and Architecture", "Business", "Drinks", "The Environment", "States of Mind",
            "Food", "Graphic Resources", "Hobbies and Leisure", "Industry", "Landscapes", "Lifestyle", "People",
            "Plants and Flowers", "Culture and Religion", "Science", "Social Issues", "Sports", "Technology",
            "Transport", "Travel"
        ]
        # Adobe uses a number (1-indexed) for category
        self.category_map = {name: i + 1 for i, name in enumerate(self.categories_list)}

    def draw_config_options(self) -> dict:
        st.subheader("Adobe Stock Generator")
        
        selected_category = st.selectbox(
            "Select 1 Adobe Stock category:",
            options=self.categories_list,
            index=None,
            placeholder="Choose a category",
            key=f"{self.key_prefix}category"
        )
        
        releases_input = st.text_input(
            "Releases (The names you gave to the releases when you uploaded them on Adobe Stock)", 
            key=f"{self.key_prefix}releases"
        )
            
        return {
            "category_name": selected_category,
            "category_id": self.category_map.get(selected_category, ""),
            "releases": releases_input
        }

    #
    # draw_batch_controls() is now inherited from BaseExporter
    #

    def draw_image_editors(self, uploaded_files: list, config: dict, models: ModelLoader):
        st.markdown("### 🖼️ Preview & Edit Metadata")
        
        # Adobe only has one category, pass it as a list for the refiner
        selected_category_name = config.get("category_name")
        category_list = [selected_category_name] if selected_category_name else []
        
        for uploaded_file in uploaded_files:
            image = Image.open(uploaded_file)
            caption_key = f"{self.key_prefix}caption_{uploaded_file.name}"
            keywords_key = f"{self.key_prefix}keywords_{uploaded_file.name}"

            with st.container():
                col1, col2 = st.columns([1, 2], vertical_alignment="center")
                with col1:
                    image.thumbnail((220, 220))
                    st.image(image, caption=None, width=220)
                with col2:
                    st.text_input("Filename", value=uploaded_file.name, key=f"{self.key_prefix}filename_{uploaded_file.name}", disabled=True)
                    
                    if caption_key not in st.session_state:
                        with st.spinner("🔎 Generating metadata..."):
                            try:
                                raw_caption = models.generate_caption(image)
                                caption, keywords = models.refine_caption_and_keywords(raw_caption, category_list)
                                st.session_state[caption_key] = caption
                                st.session_state[keywords_key] = keywords
                            except Exception as e:
                                st.error(f"Error processing {uploaded_file.name}: {e}")
                                st.session_state[caption_key] = "Error"
                                st.session_state[keywords_key] = "Error"
                    
                    # Note: Label is "Title" here
                    st.text_area("Title", height=70, key=caption_key)
                    st.text_area("Keywords (comma-separated)", height=110, key=keywords_key)
                st.markdown("<hr style='border:0.5px solid #3a3a3a; margin:1.5rem 0;'/>", unsafe_allow_html=True)

    def draw_export_button(self, uploaded_files: list, config: dict):
        st.markdown("### ⬇️ Export Adobe Stock CSV")
        final_results = []
        
        for uploaded_file in uploaded_files:
            # CHANGE: Replace extension with .eps
            filename_eps = os.path.splitext(uploaded_file.name)[0] + ".eps"

            final_results.append([
                filename_eps,
                st.session_state.get(f"{self.key_prefix}caption_{uploaded_file.name}", "").strip(),
                st.session_state.get(f"{self.key_prefix}keywords_{uploaded_file.name}", "").strip(),
                config.get("category_id", ""),
                config.get("releases", "").strip()
            ])
            
        df = pd.DataFrame(
            final_results, 
            columns=["Filename", "Title", "Keywords", "Category", "Releases"]
        )
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download Adobe Stock CSV", csv, "adobestock_upload.csv", "text/csv", key=f"{self.key_prefix}download_btn"
        )

class IStockExporter(BaseExporter):
    """
    Implements the UI and export logic for iStock.
    Special feature: Generates individual CSVs per image and zips them.
    """
    def __init__(self):
        super().__init__("iStock")

    def draw_config_options(self) -> dict:
        st.subheader("iStock Generator")
        st.info("ℹ️ iStock does not require specific categories for this tool.")
        return {} # No specific config needed for iStock

    def draw_image_editors(self, uploaded_files: list, config: dict, models: ModelLoader):
        st.markdown("### 🖼️ Preview & Edit Metadata")
        
        for uploaded_file in uploaded_files:
            image = Image.open(uploaded_file)
            caption_key = f"{self.key_prefix}caption_{uploaded_file.name}"
            keywords_key = f"{self.key_prefix}keywords_{uploaded_file.name}"

            with st.container():
                col1, col2 = st.columns([1, 2], vertical_alignment="center")
                with col1:
                    image.thumbnail((220, 220))
                    st.image(image, caption=None, width=220)
                with col2:
                    st.text_input("Filename", value=uploaded_file.name, key=f"{self.key_prefix}filename_{uploaded_file.name}", disabled=True)
                    
                    if caption_key not in st.session_state:
                        with st.spinner("🔎 Generating metadata..."):
                            try:
                                raw_caption = models.generate_caption(image)
                                # Pass empty list as categories
                                caption, keywords = models.refine_caption_and_keywords(raw_caption, [])
                                st.session_state[caption_key] = caption
                                st.session_state[keywords_key] = keywords
                            except Exception as e:
                                st.error(f"Error processing {uploaded_file.name}: {e}")
                                st.session_state[caption_key] = "Error"
                                st.session_state[keywords_key] = "Error"
                    
                    st.text_area("Title/Description", height=70, key=caption_key)
                    st.text_area("Keywords (comma-separated)", height=110, key=keywords_key)
                st.markdown("<hr style='border:0.5px solid #3a3a3a; margin:1.5rem 0;'/>", unsafe_allow_html=True)

    def draw_export_button(self, uploaded_files: list, config: dict):
        st.markdown("### ⬇️ Export iStock CSVs (ZIP)")
        
        # We need to create a ZIP file in memory containing multiple CSVs
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for uploaded_file in uploaded_files:
                # 1. Prepare data for this single image
                filename = uploaded_file.name
                caption = st.session_state.get(f"{self.key_prefix}caption_{filename}", "").strip()
                keywords = st.session_state.get(f"{self.key_prefix}keywords_{filename}", "").strip()

                # CHANGE: Replace extension with .eps for the filename column within the CSV
                name_without_ext = os.path.splitext(filename)[0]
                filename_eps = name_without_ext + ".eps"
                
                # Columns: file name | description | country | title | keywords | color
                row_data = [
                    filename_eps, # <--- Used here
                    caption,    # description
                    "",         # country (empty)
                    caption,    # title (same as description)
                    keywords,   # keywords
                    "yes"       # color (always yes)
                ]
                
                # 2. Create a mini DataFrame for this file
                df = pd.DataFrame([row_data], columns=["file name", "description", "country", "title", "keywords", "color"])
                
                # 3. Convert DataFrame to CSV string
                csv_data = df.to_csv(index=False).encode("utf-8")
                
                # 4. Add to zip
                # The CSV file itself is named "filename.csv"
                csv_filename = f"{name_without_ext}.csv"
                
                zf.writestr(csv_filename, csv_data)
        
        # Finalize zip
        zip_buffer.seek(0)
        
        st.download_button(
            "⬇️ Download All iStock CSVs (ZIP)", 
            zip_buffer, 
            "istock_metadata.zip", 
            "application/zip", 
            key=f"{self.key_prefix}download_btn"
        )