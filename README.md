# 📸 Stock Auto Caption Generator

Automatically generate **Shutterstock-ready captions and SEO keywords** from your stock photos — powered by **BLIP** (image captioning) and **KeyBERT** (keyword extraction).  
This app runs **100% locally** — no API key or internet connection required after initial setup.

---

## 🚀 Features
- 🧠 **AI caption generation** using the BLIP model (`Salesforce/blip-image-captioning-base`)
- 🔑 **Keyword extraction** using KeyBERT (`all-MiniLM-L6-v2`)
- 🗂️ **Export to Shutterstock CSV format** (`shutterstock_content_upload.csv`)
- 🎨 **Category and metadata selection** (Editorial, Mature, Illustration)
- 💾 Works completely offline — **no OpenAI or external APIs needed**

---

## 🛠️ Requirements
- Python **3.10+**
- A virtual environment (`venv` recommended)
- Packages listed in [`requirements.txt`](./requirements.txt)

---

## ⚙️ Installation

1. **Clone this repository**
   ```bash
   git clone https://github.com/nyskytigers/stock-auto-caption.git
   cd stock-auto-caption

2. **Create and activate a virtual environment
    python -m venv venv
   - On Windows
    venv\Scripts\activate
   - On macOS/Linux
    # source venv/bin/activate

4. **Install dependencies
    pip install -r requirements.txt

▶️ Run the App
    streamlit run app.py

Then open your browser and go to: 
    http://localhost:8501


🧠 Models Used

BLIP: Bootstrapped Language-Image Pretraining
→ Generates descriptive captions from images.

KeyBERT
→ Extracts SEO-friendly keywords from text using sentence embeddings.


🧩 Future Plans
✏️ Editable keyword fields before export
💬 User feedback saving (learning system)
🔍 CLIP-based similarity search for smarter keyword suggestions
🎨 Improved Streamlit UI
🌐 Public web version hosted via Streamlit Cloud or Hugging Face Spaces

🪪 License
This project is open-source and available under the MIT License.

👤 Author
@NYskytigers
