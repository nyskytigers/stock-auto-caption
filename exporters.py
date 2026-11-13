import streamlit as st
from PIL import Image
from models import ModelLoader
from stock_metadata import Metadata, process_image, export_csv, export_istock_zip
from stock_metadata.core import clean_keywords

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
                        deduplicated_list = clean_keywords(original_list + master_list)
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


    def download_metadata(self, uploaded_files, config, marketplace, zipped=False):
        st.caption("Draft CSV only. Review facts, keywords, rights, releases and platform fields before submission.")
        records = []
        try:
            for file in uploaded_files:
                records.append(Metadata(
                    filename=file.name,
                    caption=st.session_state.get(f"{self.key_prefix}caption_{file.name}", ""),
                    keywords=st.session_state.get(f"{self.key_prefix}keywords_{file.name}", ""),
                    categories=config.get("categories", []),
                    category=config.get("category_id", ""),
                    releases=config.get("releases", "").strip(),
                    editorial=config.get("editorial", "no"),
                    mature=config.get("mature", "no"),
                    illustration=config.get("illustration", "no"),
                    country=config.get("country", ""),
                    color=config.get("color", "yes"),
                ))
            data = export_istock_zip(records) if zipped else export_csv(records, marketplace)
        except (ValueError, TypeError) as error:
            st.error(f"Export blocked: {error}. Correct metadata before downloading.")
            return
        extension = "zip" if zipped else "csv"
        st.download_button(
            f"Download {self.site_name} {extension.upper()}", data,
            f"{marketplace}_metadata.{extension}",
            "application/zip" if zipped else "text/csv",
            key=f"{self.key_prefix}download_btn",
        )


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
        
        for uploaded_file in uploaded_files:
            try:
                uploaded_file.seek(0)
                with Image.open(uploaded_file) as source:
                    image = source.copy()
            except Exception as error:
                st.error(f"Cannot decode {uploaded_file.name}: {error}")
                continue
            caption_key = f"{self.key_prefix}caption_{uploaded_file.name}"
            keywords_key = f"{self.key_prefix}keywords_{uploaded_file.name}"

            with st.container():
                col1, col2 = st.columns([1, 2], vertical_alignment="center")
                with col1:
                    preview = image.copy()
                    preview.thumbnail((220, 220))
                    st.image(preview, caption=None, width=220)
                    preview.close()
                with col2:
                    st.text_input("Filename", value=uploaded_file.name, key=f"{self.key_prefix}filename_{uploaded_file.name}", disabled=True)
                    
                    if caption_key not in st.session_state:
                        with st.spinner("🔎 Generating metadata..."):
                            try:
                                uploaded_file.seek(0)
                                record = process_image(uploaded_file, models, filename=uploaded_file.name)
                                caption, keywords = record.caption, ", ".join(record.keywords)
                                st.session_state[caption_key] = caption
                                st.session_state[keywords_key] = keywords
                            except Exception as e:
                                st.error(f"Error processing {uploaded_file.name}: {e}")
                                st.session_state[caption_key] = ""
                                st.session_state[keywords_key] = ""
                                st.caption("Enter reviewed metadata manually or re-upload to retry.")
                    
                    # Note: Label is "Caption" here
                    st.text_area("Caption", height=70, key=caption_key) 
                    st.text_area("Keywords (comma-separated)", height=110, key=keywords_key)
                image.close()
                st.markdown("<hr style='border:0.5px solid #3a3a3a; margin:1.5rem 0;'/>", unsafe_allow_html=True)

    def draw_export_button(self, uploaded_files: list, config: dict):
        self.download_metadata(uploaded_files, config, "shutterstock", False)


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
            "Releases (Exact uploaded JPEG release filename)",
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
        
        for uploaded_file in uploaded_files:
            try:
                uploaded_file.seek(0)
                with Image.open(uploaded_file) as source:
                    image = source.copy()
            except Exception as error:
                st.error(f"Cannot decode {uploaded_file.name}: {error}")
                continue
            caption_key = f"{self.key_prefix}caption_{uploaded_file.name}"
            keywords_key = f"{self.key_prefix}keywords_{uploaded_file.name}"

            with st.container():
                col1, col2 = st.columns([1, 2], vertical_alignment="center")
                with col1:
                    preview = image.copy()
                    preview.thumbnail((220, 220))
                    st.image(preview, caption=None, width=220)
                    preview.close()
                with col2:
                    st.text_input("Filename", value=uploaded_file.name, key=f"{self.key_prefix}filename_{uploaded_file.name}", disabled=True)
                    
                    if caption_key not in st.session_state:
                        with st.spinner("🔎 Generating metadata..."):
                            try:
                                uploaded_file.seek(0)
                                record = process_image(uploaded_file, models, filename=uploaded_file.name)
                                caption, keywords = record.caption, ", ".join(record.keywords)
                                st.session_state[caption_key] = caption
                                st.session_state[keywords_key] = keywords
                            except Exception as e:
                                st.error(f"Error processing {uploaded_file.name}: {e}")
                                st.session_state[caption_key] = ""
                                st.session_state[keywords_key] = ""
                                st.caption("Enter reviewed metadata manually or re-upload to retry.")
                    
                    # Note: Label is "Title" here
                    st.text_area("Title", height=70, key=caption_key)
                    st.text_area("Keywords (comma-separated)", height=110, key=keywords_key)
                image.close()
                st.markdown("<hr style='border:0.5px solid #3a3a3a; margin:1.5rem 0;'/>", unsafe_allow_html=True)

    def draw_export_button(self, uploaded_files: list, config: dict):
        self.download_metadata(uploaded_files, config, "adobe", False)

class IStockExporter(BaseExporter):
    """
    Implements the UI and export logic for iStock.
    Special feature: Generates individual CSVs per image and zips them.
    """
    def __init__(self):
        super().__init__("iStock")

    def draw_config_options(self) -> dict:
        st.subheader("iStock Generator")
        st.info("Legacy Creative Illustration CSV. Verify your ESP template and resolve controlled-vocabulary keywords. Complete country in ESP before submitting.")
        country = st.text_input("Country (confirm against your ESP template)", key=f"{self.key_prefix}country")
        color = st.selectbox("Color illustration?", ["yes", "no"], key=f"{self.key_prefix}color")
        return {"country": country.strip(), "color": color}

    def draw_image_editors(self, uploaded_files: list, config: dict, models: ModelLoader):
        st.markdown("### 🖼️ Preview & Edit Metadata")
        
        for uploaded_file in uploaded_files:
            try:
                uploaded_file.seek(0)
                with Image.open(uploaded_file) as source:
                    image = source.copy()
            except Exception as error:
                st.error(f"Cannot decode {uploaded_file.name}: {error}")
                continue
            caption_key = f"{self.key_prefix}caption_{uploaded_file.name}"
            keywords_key = f"{self.key_prefix}keywords_{uploaded_file.name}"

            with st.container():
                col1, col2 = st.columns([1, 2], vertical_alignment="center")
                with col1:
                    preview = image.copy()
                    preview.thumbnail((220, 220))
                    st.image(preview, caption=None, width=220)
                    preview.close()
                with col2:
                    st.text_input("Filename", value=uploaded_file.name, key=f"{self.key_prefix}filename_{uploaded_file.name}", disabled=True)
                    
                    if caption_key not in st.session_state:
                        with st.spinner("🔎 Generating metadata..."):
                            try:
                                uploaded_file.seek(0)
                                record = process_image(uploaded_file, models, filename=uploaded_file.name)
                                caption, keywords = record.caption, ", ".join(record.keywords)
                                st.session_state[caption_key] = caption
                                st.session_state[keywords_key] = keywords
                            except Exception as e:
                                st.error(f"Error processing {uploaded_file.name}: {e}")
                                st.session_state[caption_key] = ""
                                st.session_state[keywords_key] = ""
                                st.caption("Enter reviewed metadata manually or re-upload to retry.")
                    
                    st.text_area("Title/Description", height=70, key=caption_key)
                    st.text_area("Keywords (comma-separated)", height=110, key=keywords_key)
                image.close()
                st.markdown("<hr style='border:0.5px solid #3a3a3a; margin:1.5rem 0;'/>", unsafe_allow_html=True)

    def draw_export_button(self, uploaded_files: list, config: dict):
        self.download_metadata(uploaded_files, config, "istock", True)
