import streamlit as st
import utils
import pdfplumber
import os

st.set_page_config(page_title="AI Notes Summarizer+", page_icon="📝", layout="centered", initial_sidebar_state="expanded")

# Automatically configure API key from secrets or environment variable
api_key = None
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    utils.configure_api(api_key)
except (KeyError, FileNotFoundError):
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        utils.configure_api(api_key)

API_READY = api_key is not None

st.markdown(
    """
<style>
.main-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 20px;
    border-radius: 12px;
    color: white;
    text-align: center;
    margin-bottom: 30px;
}
.main-header h1 { margin: 0; font-size: 2em; }
.main-header p { margin: 5px 0 0; opacity: 0.9; }
.result-box {
    background: #ffffff;
    border: 1px solid #e8e8e8;
    border-left: 4px solid #667eea;
    border-radius: 10px;
    padding: 24px 28px;
    margin: 16px 0;
    font-size: 1.05em;
    line-height: 1.7;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.result-box ul, .result-box ol {
    padding-left: 1.5em;
    margin: 8px 0;
}
.result-box li {
    margin-bottom: 8px;
}
.result-box h3 {
    margin-top: 0;
    color: #1a1a2e;
}
div[data-testid="stButton"] button {
    border-radius: 20px;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}
.stTabs [data-baseweb="tab"] {
    height: 40px;
    padding-left: 20px;
    padding-right: 20px;
}
.shortcut-hint {
    font-size: 0.8em;
    color: #666;
    font-style: italic;
}</style>
""",
    unsafe_allow_html=True,
)

# Add JavaScript for keyboard shortcuts
st.markdown(
    """
<script>
document.addEventListener('keydown', function(e) {
    // Handle Ctrl+Enter for Generate button
    if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault();
        const generateBtn = document.querySelector('button[kind="primary"]');
        if (generateBtn && !generateBtn.disabled) {
            generateBtn.click();
        }
    }
    
    // Handle Ctrl+S for Sample data
    if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        const sampleBtns = Array.from(document.querySelectorAll('button')).filter(btn => 
            btn.textContent.includes('📝 Sample') || btn.title.includes('Load sample text')
        );
        if (sampleBtns.length > 0) {
            sampleBtns[0].click();
        }
    }
    
    // Handle Ctrl+F for Focus on text input
    if (e.ctrlKey && e.key === 'f') {
        e.preventDefault();
        const textAreas = document.querySelectorAll('textarea');
        if (textAreas.length > 0) {
            textAreas[0].focus();
        }
    }
    
    // Handle Ctrl+P for Focus on PDF uploader
    if (e.ctrlKey && e.key === 'p') {
        e.preventDefault();
        const fileUploaders = document.querySelectorAll('input[type="file"]');
        if (fileUploaders.length > 0) {
            fileUploaders[0].focus();
        }
    }
});
</script>
""",
    unsafe_allow_html=True,
)

# Add keyboard shortcut hints
st.markdown('<p class="shortcut-hint">💡 Keyboard shortcuts: Ctrl+Enter=Generate, Ctrl+S=Sample, Ctrl+F=Focus Text, Ctrl+P=Focus PDF</p>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center; padding:10px; background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius:10px; color:white; margin-bottom:15px;">
            <h3 style="margin:0;">📝 AI Notes Summarizer</h3>
            <p style="margin:5px 0 0; font-size:0.85em; opacity:0.9;">Paste notes → Get insights</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    st.markdown("### 💡 How to Use")
    st.markdown("""
    1. **Paste notes** or **upload a PDF**
    2. Choose output type
    3. Click **Generate** (or `Ctrl+Enter`)
    4. Download or save results
    """)

st.markdown(
    '<div class="main-header"><h1>📝 AI Notes Summarizer+</h1><p>Summarize, extract key points, and generate study questions from your notes</p></div>',
    unsafe_allow_html=True,
)

input_tab, pdf_tab = st.tabs(["📝 Paste Text", "📄 Upload PDF"])

text = ""

with input_tab:
    # Sample data button
    col1, col2 = st.columns([4, 1])
    with col1:
        text = st.text_area(
            "Your Notes",
            height=200,
            placeholder="Paste your class notes, textbook excerpts, or study material here...",
            key="text_input",
        )
    with col2:
        st.write("")  # For vertical alignment
        st.write("")  # For vertical alignment
        if st.button("📝 Sample", help="Load sample text to test the app (Ctrl+S)"):
            text = """Artificial Intelligence (AI) is a branch of computer science that aims to create intelligent machines capable of performing tasks that typically require human intelligence. These tasks include learning, reasoning, problem-solving, perception, and language understanding.

Machine Learning is a subset of AI that focuses on the development of algorithms that can learn from and make predictions on data. Instead of being explicitly programmed, machine learning systems learn patterns from data.

Deep Learning is a subset of machine learning that uses neural networks with many layers (deep neural networks) to analyze various factors of data. It has been particularly successful in areas such as image and speech recognition.

Natural Language Processing (NLP) is a field of AI that focuses on the interaction between computers and humans through natural language. The ultimate objective of NLP is to read, decipher, understand, and make sense of human language in a valuable way."""
            st.rerun()

with pdf_tab:
    uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
    if uploaded_file:
        # Show file info
        st.info(f"📄 File: {uploaded_file.name} ({uploaded_file.size} bytes)")
        
        # Progress bar for PDF processing
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("🔄 Opening PDF...")
            progress_bar.progress(10)
            
            # Extract text with progress updates
            text = ""
            with pdfplumber.open(uploaded_file) as pdf:
                total_pages = len(pdf.pages)
                status_text.text(f"📖 Processing {total_pages} pages...")
                progress_bar.progress(20)
                
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    
                    # Update progress
                    progress_percent = 20 + int(60 * (i + 1) / total_pages)
                    progress_bar.progress(progress_percent)
                    status_text.text(f"📖 Processing page {i+1} of {total_pages}...")
                
                progress_bar.progress(90)
                status_text.text("🧹 Finalizing text extraction...")
            
            progress_bar.progress(100)
            
            if text.strip():
                st.success(f"✅ Extracted {len(text)} characters from {total_pages} pages")
                with st.expander("Preview extracted text"):
                    preview_text = text[:1000] + ("..." if len(text) > 1000 else "")
                    st.text(preview_text)
                    
                # Show stats
                word_count = len(text.split())
                line_count = len(text.split('\n'))
                st.caption(f"📊 Stats: {word_count} words, {line_count} lines")
            else:
                st.error("❌ Could not extract text from this PDF. The PDF might be image-based or encrypted.")
                progress_bar.empty()
                status_text.empty()
        except Exception as e:
            st.error(f"❌ Error processing PDF: {str(e)}")
            progress_bar.empty()
            status_text.empty()

col1, col2, col3 = st.columns(3)
with col1:
    mode = st.selectbox("What to generate", ["Summary", "Key Points", "Study Questions"])
with col2:
    detail = st.selectbox("Detail level", ["Brief", "Normal", "Detailed"])
with col3:
    lang = st.selectbox("Language", ["English", "Chinese"])

if st.button("🚀 Generate", type="primary", use_container_width=True):
    if not API_READY:
        st.error("⚠️ API not configured. Please contact the app owner to set up the Gemini API key.")
    elif not text.strip():
        st.error("Please paste some notes or upload a PDF first.")
    else:
        with st.spinner("Thinking..."):
            try:
                    if mode == "Summary":
                        result = utils.generate_summary(text, detail, lang)
                        title = "📌 Summary"
                        filename = f"summary_{detail}_{lang}.txt"
                    elif mode == "Key Points":
                        result = utils.generate_key_points(text, detail, lang)
                        title = "🔑 Key Points"
                        filename = f"key_points_{detail}_{lang}.txt"
                    else:
                        result = utils.generate_study_questions(text, detail, lang)
                        title = "❓ Study Questions"
                        filename = f"study_questions_{detail}_{lang}.txt"

                    st.markdown(
                        f'<div class="result-box"><h3>{title}</h3>{result}</div>',
                        unsafe_allow_html=True,
                    )
                    st.download_button(
                        "📥 Download as TXT",
                        data=result,
                        file_name=filename,
                        mime="text/plain",
                    )

            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "quota" in error_msg.lower():
                    st.error("""
                    ⚠️ **API Quota Exceeded**
                    
                    Your Gemini API free tier quota has been exhausted.
                    Solutions:
                    1. **Get a new free API Key** → https://aistudio.google.com/apikey
                    2. The app uses **Gemini 2.5 Flash** (free tier), so rate limits are unlikely
                    
                    After getting a new key, update `.streamlit/secrets.toml` and restart the app.
                    """)
                else:
                    st.error(f"Something went wrong: {e}")

st.markdown("---")
st.caption("Built with Streamlit + Google Gemini API + pdfplumber")
