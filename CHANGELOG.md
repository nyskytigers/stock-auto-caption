# 📜 Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v1.3.0] - 2025-10-16
### 🧩 Added
- “Apply to All” feature for captions and keywords
  - Users can now define a master caption and/or keyword set
  - Automatically applies to all uploaded images
  - Updates both the editable fields and exported CSV
- Persistent session state to retain applied or edited metadata
- Batch editing options integrated into UI for easier workflow

## [v1.2.1] - 2025-10-15
### 🐞 Fixes
- Fixed issue where **edited captions and keywords** were not saved in the exported CSV.  
- Now the app reads updated values from `st.session_state` to ensure user edits are preserved.  

### 💡 Improvements
- Added safer variable initialization (`results = []`) to prevent `NameError` when no file is uploaded.  
- Simplified export logic for better stability and clarity.  

## [v1.2.0] - 2025-10-14
### UI & Feature Updates
- Arranged **Editorial**, **Mature content**, and **Illustration** dropdowns side-by-side.
- Unified **Montserrat font** across all elements for consistent look and feel.
- Refactored CSS into external `style.css` file for modular code organization.

## [1.1.2] – 2025-10-14
### Changed
- UI preview update
- Fixed preview image and centered vertically/horizontally
- Adjusted caption/keyword textarea height for better layout consistency

---
## [v1.1.1] - 2025-10-14
### 🎨 Improved
- Applied Montserrat font globally across all Streamlit UI components (titles, inputs, buttons, dropdowns, text areas)
- Ensured consistent typography in both light and dark themes
- Adjusted title font size for better single-line layout
- Added CSS overrides targeting Streamlit’s internal widget containers for reliable cross-component styling

### 🧱 Maintenance
- Updated inline CSS block in `app.py` to use `data-testid` selectors
- Prepared for future light/dark theme color adjustments

## [v1.1.0] - 2025-10-13
### ✏️ Added
- Editable caption and keyword fields directly in the UI
- “Save edits” logic to ensure exported CSV reflects user changes
- Custom Montserrat font applied to all UI elements
- Compact single-line title and layout refinements

### 🎨 Improved
- Cleaner visual spacing for multiple uploads
- Consistent font styling across Streamlit widgets
- Clearer user guidance for editing metadata before export

---

## [v1.0.0] - 2025-10-12
### 🚀 Initial Release
- Local AI-powered stock caption generator
- BLIP model (`Salesforce/blip-image-captioning-base`) for image captions
- KeyBERT (`all-MiniLM-L6-v2`) for SEO keyword generation
- CSV export formatted for Shutterstock content uploads
- Streamlit UI with category, editorial, mature, and illustration metadata fields
- 100% local workflow — no API keys or external connections required

---

## 🧩 Planned
- Editable keyword preview with “Apply to All” button
- User feedback collection for future self-learning system
- CLIP-based image similarity engine for keyword refinement
- Enhanced layout and theme customization

---

**Author:** [@NYskytigers](https://github.com/nyskytigers)  
💡 Built for creators, photographers, and stock contributors — to simplify metadata generation through local AI.
