import streamlit as st
import utils
import pdfplumber
import os
from datetime import datetime

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
.card-box {
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 15px;
    margin: 8px 0;
    background: #fafafa;
}
.result-box {
    background: #f0f8ff;
    border-left: 4px solid #667eea;
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
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
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
    .result-box {
        background: #1e1e2e !important;
        color: #e0e0e0 !important;
        border-left: 4px solid #89b4fa !important;
    }
    .card-box {
        background: #2a2a3e !important;
        color: #e0e0e0 !important;
        border: 1px solid #4a4a6a !important;
    }
    .main-header p {
        color: white !important;
    }
}
</style>
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
    
    // Handle Ctrl+L for Clear history
    if (e.ctrlKey && e.key === 'l') {
        e.preventDefault();
        const clearBtns = Array.from(document.querySelectorAll('button')).filter(btn => 
            btn.textContent.includes('🗑️ Clear') || btn.title.includes('Clear all history')
        );
        if (clearBtns.length > 0) {
            clearBtns[0].click();
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
st.markdown('<p class="shortcut-hint">💡 Keyboard shortcuts: Ctrl+Enter=Generate, Ctrl+S=Sample, Ctrl+L=Clear History, Ctrl+F=Focus Text, Ctrl+P=Focus PDF</p>', unsafe_allow_html=True)

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
    
    st.markdown("### 🎯 Features")
    st.markdown("""
    - 📌 **Summary** — Bullet-point overview
    - 🔑 **Key Points** — Important concepts
    - ❓ **Study Questions** — Test your understanding
    """)
    
    st.markdown("### ⌨️ Shortcuts")
    st.markdown("""
    | Key | Action |
    |---|---|
    | `Ctrl+Enter` | Generate |
    | `Ctrl+S` | Sample text |
    | `Ctrl+L` | Clear history |
    | `Ctrl+F` | Focus text |
    | `Ctrl+P` | Focus PDF |
    """)
    
    st.markdown("---")
    st.markdown("### 📜 History")
    
    # Initialize history if not exists
    if "history" not in st.session_state:
        st.session_state.history = []
    if "pinned_history" not in st.session_state:
        st.session_state.pinned_history = []
    
    # History controls
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        search_term = st.text_input("🔍 Search history", placeholder="Search in history...", key="history_search")
    with col2:
        show_pinned = st.checkbox("📌 Show pinned only", value=False)
    with col3:
        if st.button("🗑️ Clear", help="Clear all history"):
            st.session_state.history = []
            st.session_state.pinned_history = []
            st.rerun()
    
    # Filter history based on search and pinned status
    def matches_search(entry):
        if not search_term:
            return True
        return (search_term.lower() in entry["time"].lower() or 
                search_term.lower() in entry["mode"].lower() or
                search_term.lower() in entry["preview"].lower())
    
    # Get entries to display
    if show_pinned:
        entries_to_show = [e for e in st.session_state.pinned_history if matches_search(e)]
        if not entries_to_show:
            st.caption("No pinned entries match your search.")
    else:
        # Combine pinned and regular history (pinned first)
        regular_entries = [e for e in st.session_state.history if e not in st.session_state.pinned_history]
        entries_to_show = st.session_state.pinned_history + regular_entries[-5:]  # Show last 5 regular
        entries_to_show = [e for e in entries_to_show if matches_search(e)]
        
        if not entries_to_show:
            st.caption("No history entries match your search.")
    
    # Display history entries
    for idx, entry in enumerate(reversed(entries_to_show)):
        # Determine if entry is pinned
        is_pinned = entry in st.session_state.pinned_history
        
        # Create a unique identifier for this entry
        entry_id = f"{entry['time']}_{entry['mode']}_{idx}_{hash(entry['preview']) % 10000}"
        
        with st.container():
            col1, col2, col3 = st.columns([6, 1, 1])
            with col1:
                with st.expander(f"{entry['time']} — {entry['mode']} {'📌' if is_pinned else ''}", expanded=False):
                    st.code(entry["preview"], language="text")
                    if st.button("👁️ View Full", key=f"view_{entry_id}", help="View full result"):
                        st.session_state[f"show_full_{entry_id}"] = True
                        st.rerun()
                    
                    # Show full result if requested
                    if st.session_state.get(f"show_full_{entry_id}", False):
                        # Determine which result to show based on mode and time
                        full_result = None
                        if entry["mode"] == "Summary" and hasattr(st.session_state, 'last_summary') and st.session_state.get('last_summary_time') == entry['time']:
                            full_result = st.session_state.last_summary
                        elif entry["mode"] == "Key Points" and hasattr(st.session_state, 'last_key_points') and st.session_state.get('last_key_points_time') == entry['time']:
                            full_result = st.session_state.last_key_points
                        elif entry["mode"] == "Study Questions" and hasattr(st.session_state, 'last_study_questions') and st.session_state.get('last_study_questions_time') == entry['time']:
                            full_result = st.session_state.last_study_questions
                        
                        if full_result is not None:
                            st.info(f"📝 {entry['mode']}:")
                            st.markdown(full_result)
                        else:
                            st.info("Full result not available in current session (may have been cleared)")
                        
                        if st.button("❌ Close", key=f"close_{entry_id}"):
                            del st.session_state[f"show_full_{entry_id}"]
                            st.rerun()
            
            with col2:
                if not is_pinned:
                    if st.button("📌", key=f"pin_{entry['time']}_{entry['mode']}", help="Pin this entry"):
                        if entry not in st.session_state.pinned_history:
                            st.session_state.pinned_history.append(entry)
                        st.rerun()
                else:
                    if st.button("📌", key=f"unpin_{entry['time']}_{entry['mode']}", help="Unpin this entry"):
                        if entry in st.session_state.pinned_history:
                            st.session_state.pinned_history.remove(entry)
                        st.rerun()
            
            with col3:
                if st.button("🗑️", key=f"del_{entry['time']}_{entry['mode']}", help="Delete this entry"):
                    if entry in st.session_state.history:
                        st.session_state.history.remove(entry)
                    if entry in st.session_state.pinned_history:
                        st.session_state.pinned_history.remove(entry)
                    st.rerun()
            
            st.divider()
    
    # Show stats
    if st.session_state.history or st.session_state.pinned_history:
        st.caption(f"📊 Total: {len(st.session_state.history)} entries, {len(st.session_state.pinned_history)} pinned")
    else:
        st.caption("No history yet.")

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

mode = st.selectbox("What do you want to generate?", ["Summary", "Key Points", "Study Questions"])

if st.button("🚀 Generate", type="primary", use_container_width=True):
    if not API_READY:
        st.error("⚠️ API not configured. Please contact the app owner to set up the Gemini API key.")
    elif not text.strip():
        st.error("Please paste some notes or upload a PDF first.")
    else:
        with st.spinner("Thinking..."):
            try:
                if mode == "Summary":
                    result = utils.generate_summary(text)
                    st.markdown(
                        f'<div class="result-box"><h3>📌 Summary</h3>{result}</div>',
                        unsafe_allow_html=True,
                    )
                    st.download_button(
                        "📥 Download as TXT",
                        data=result,
                        file_name="summary.txt",
                        mime="text/plain",
                    )

                elif mode == "Key Points":
                    result = utils.generate_key_points(text)
                    st.markdown(
                        f'<div class="result-box"><h3>🔑 Key Points</h3>{result}</div>',
                        unsafe_allow_html=True,
                    )
                    st.download_button(
                        "📥 Download as TXT",
                        data=result,
                        file_name="key_points.txt",
                        mime="text/plain",
                    )

                elif mode == "Study Questions":
                    result = utils.generate_study_questions(text)
                    st.markdown(
                        f'<div class="result-box"><h3>❓ Study Questions</h3>{result}</div>',
                        unsafe_allow_html=True,
                    )
                    st.download_button(
                        "📥 Download as TXT",
                        data=result,
                        file_name="study_questions.txt",
                        mime="text/plain",
                    )

                st.session_state.history.append(
                    {
                        "time": datetime.now().strftime("%H:%M"),
                        "mode": mode,
                        "preview": result[:200] + ("..." if len(result) > 200 else ""),
                    }
                )

            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "quota" in error_msg.lower():
                    st.error("""
                    ⚠️ **API Quota Exceeded**
                    
                    You've reached the free tier limit for Gemini API (5 requests per minute).
                    Please wait a moment before trying again, or consider:
                    - Waiting 1-2 minutes before your next request
                    - Using shorter text inputs to reduce API calls
                    - Checking your usage at https://ai.dev/rate-limit
                    
                    The free tier is generous for demo purposes - this limit resets periodically.
                    """)
                else:
                    st.error(f"Something went wrong: {e}")

         # Store results in session state to persist across reruns
        if mode == "Summary":
            st.session_state.last_summary = result
            st.session_state.last_summary_time = datetime.now().strftime("%H:%M")
        elif mode == "Key Points":
            st.session_state.last_key_points = result
            st.session_state.last_key_points_time = datetime.now().strftime("%H:%M")
        elif mode == "Study Questions":
            st.session_state.last_study_questions = result
            st.session_state.last_study_questions_time = datetime.now().strftime("%H:%M")

st.markdown("---")
st.caption("Built with Streamlit + Google Gemini API + pdfplumber")
