# app.py
import streamlit as st
import os
import requests
import json
import base64
from openai import OpenAI
from dotenv import load_dotenv

# Must be the first Streamlit command
st.set_page_config(page_title="Claire Namusoke — Portfolio", layout="wide")

load_dotenv()

# ---------- CONFIG ----------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY") 
ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID")  
CV_FILEPATH = "assets/Claire_CV.pdf"
PROJECTS_FILE = "assets/projects.json"

# ---------- STYLING ----------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #000a14 0%, #001420 25%, #001e2c 50%, #002838 75%, #003244 100%);
        border: 3px solid #000a14;
        border-radius: 15px;
        box-shadow: 0 0 30px rgba(0, 153, 204, 0.6), 0 0 60px rgba(0, 102, 153, 0.4);
        margin: 20px;
        padding: 20px;
    }
    /* White text on darker gradient background */
    .stMarkdown, .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, 
    .stMarkdown h4, .stMarkdown h5, .stMarkdown h6, 
    .stTextInput label, .stButton, p, span, div {
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Helpers ----------
def load_projects():
    if os.path.exists(PROJECTS_FILE):
        with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def provide_cv_download():
    if os.path.exists(CV_FILEPATH):
        with open(CV_FILEPATH, "rb") as f:
            b = f.read()
            b64 = base64.b64encode(b).decode()
            href = f'<a href="data:application/pdf;base64,{b64}" download="Claire_CV.pdf">Download CV (PDF)</a>'
            st.markdown(href, unsafe_allow_html=True)
    else:
        st.info("CV file not found in assets/Claire_CV.pdf")

def add_chat_message(role, text):
    if "messages" not in st.session_state:
        st.session_state.messages = []
    st.session_state.messages.append({"role": role, "content": text})

def openai_chat_completion(system_prompt, messages, model=OPENAI_MODEL):
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role":"system","content":system_prompt}] + messages,
            temperature=0.2,
            max_tokens=800
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"Error contacting OpenAI: {e}"

def eleven_tts_generate(text):
    if not ELEVEN_API_KEY or not ELEVEN_VOICE_ID:
        return None
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID}"
    headers = {"xi-api-key": ELEVEN_API_KEY, "Content-Type": "application/json"}
    body = {"text": text, "model": "eleven_monolingual_v1"}
    try:
        r = requests.post(url, json=body, headers=headers, timeout=30)
        if r.status_code == 200:
            return r.content
        else:
            st.error(f"TTS Error: {r.status_code} {r.text}")
            return None
    except Exception as e:
        st.error(f"TTS Exception: {e}")
        return None

def transcribe_audio(audio_bytes):
    """Transcribe audio using OpenAI Whisper API"""
    if not OPENAI_API_KEY:
        return None
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        # Save audio bytes to a temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_file_path = tmp_file.name
        
        # Transcribe using Whisper
        with open(tmp_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        
        # Clean up temp file
        os.unlink(tmp_file_path)
        return transcript.text
    except Exception as e:
        st.error(f"Transcription error: {e}")
        return None

# ---------- Navigation ----------
page = st.radio("Navigation", ["About","Projects","AI Chatbot","Voice Chat"], horizontal=True, label_visibility="collapsed")

# ---------- About ----------
if page == "About":
    st.header("Welcome to My Portfolio")
    
    # Create columns for image and text
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if os.path.exists("assets/profile.jpg"):
            st.image("assets/profile.jpg", width=100)
        else:
            st.info("Profile image not found")
    
    with col2:
        about = """Hi,  I am a data analytics enthusiast and International Shipping and chartering student at Hochschule Bremen, 
             with practical experience in analyzing shipping data, environmental impacts, and 
             global trade trends. I specialize in transforming complex datasets into actionable 
             insights through SQL, Python, Power BI, and interactive dashboards, while integrating
              AI for smarter analysis. Passionate about applying data to real-world shipping and
              Business environments to drive informed decision-making and sustainability initiatives.   
    """
        st.write(about)
    
    st.markdown("""
    <div style='display: flex; gap: 30px; align-items: start;'>
        <div>
            <h3 style='margin-top: 0; margin-bottom: 16px;'>Certifications</h3>
            <p style='margin-top: 0; margin-bottom: 16px;'>Supply Chain Management and Analytics</p>
            <p style='margin-top: 0; margin-bottom: 16px;'>Introduction to Data Analytics</p>
            <p style='margin-top: 0; margin-bottom: 16px;'>SQL & Databases</p>
            <p style='margin-top: 0; margin-bottom: 16px;'>Power BI</p>
        </div>
        <div>
            <h3 style='margin-top: 0; margin-bottom: 16px; opacity: 0;'>.</h3>
            <p style='margin-top: 0; margin-bottom: 16px;'>Coursera</p>
            <p style='margin-top: 0; margin-bottom: 16px;'>Coursera</p>
            <p style='margin-top: 0; margin-bottom: 16px;'>Udemy</p>
            <p style='margin-top: 0; margin-bottom: 16px;'>Udemy</p>
        </div>
        <div style='margin-left: 300px;'>
            <h3 style='margin-top: 0; margin-bottom: 16px;'>Interests</h3>
            <p style='margin-top: 0; margin-bottom: 16px;'>Data Analysis</p>
            <p style='margin-top: 0; margin-bottom: 16px;'>Logistics and Supply Chain</p>
            <p style='margin-top: 0; margin-bottom: 16px;'>Maritime Analytics</p>
            <p style='margin-top: 0; margin-bottom: 16px;'>Chartering Practises</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("Data Skills")
    
    # Animated skill badges
    st.markdown("""
    <style>
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }
    .skill-badge {
        display: inline-block;
        margin: 5px;
        padding: 8px 15px;
        background: linear-gradient(135deg, #1f5a8a 0%, #14406b 100%);
        color: white;
        border-radius: 20px;
        font-weight: bold;
        animation: pulse 2s ease-in-out infinite;
    }
    .skill-badge:nth-child(2) { animation-delay: 0.2s; }
    .skill-badge:nth-child(3) { animation-delay: 0.4s; }
    .skill-badge:nth-child(4) { animation-delay: 0.6s; }
    .skill-badge:nth-child(5) { animation-delay: 0.8s; }
    .skill-badge:nth-child(6) { animation-delay: 1s; }
    </style>
    <div>
        <span class="skill-badge">🐍 Python</span>
        <span class="skill-badge">🗄️ SQL</span>
        <span class="skill-badge">📊 Power BI</span>
        <span class="skill-badge">⚡ Streamlit</span>
        <span class="skill-badge">📂 Git/GitHub</span>
        <span class="skill-badge">💼 MS Office</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("Contact")
    st.markdown("- **LinkedIn:** [LinkedIn](https://www.linkedin.com/in/namusoke-claire-129711335)")
    st.markdown("- **GitHub:** [claire-namusoke](https://github.com/claire-namusoke)")
    st.markdown("- **Email:** clairenamusoke1@gmail.com")
    provide_cv_download()

# ---------- Projects ----------
elif page == "Projects":
    st.header("Projects")
    projects = load_projects()
    if projects:
        for p in projects:
            st.subheader(f"🔗 [{p.get('title')}]({p.get('link')})")
            st.write(p.get("description"))
            
            # Display tools used
            if p.get("tools"):
                tools_str = " • ".join(p.get("tools"))
                st.markdown(f"<p style='color: #58a6ff;'><strong>Tools:</strong> {tools_str}</p>", unsafe_allow_html=True)
            
            st.markdown("---")
    else:
        st.info("No projects found. Add them in assets/projects.json")

# ---------- AI Chatbot ----------
elif page == "AI Chatbot":
    st.header("AI Interview Assistant")
    st.write("Ask questions about my CV or projects, or practice interview questions.")

    # Load context (CV + projects)
    cv_text = ""
    if os.path.exists("assets/cv.txt"):
        with open("assets/cv.txt","r",encoding="utf-8", errors="ignore") as f:
            cv_text = f.read()
    projects_text = "\n".join([f"{p['title']}: {p['description']}" for p in load_projects()])
    
    # Load FAQ/additional info
    faq_text = ""
    if os.path.exists("assets/faq.json"):
        with open("assets/faq.json", "r", encoding="utf-8") as f:
            faq_data = json.load(f)
            faq_text = json.dumps(faq_data, indent=2)
    
    system_prompt = """You are Claire Namusoke's interview assistant. Answer questions about Claire professionally and concisely.

IMPORTANT INSTRUCTIONS:
- When users ask questions, understand the INTENT and MEANING, not just exact wording
- Match user questions to similar questions in the FAQ data semantically
- For example: "What do you want to achieve?" should match "What are your career goals?"
- "Why analytics?" should match "Why did you choose data analytics?"
- "Tell me about yourself" should use information from the CV and custom Q&A
- Always prioritize answers from the FAQ/custom_qa section when available
- Use CV and project information to supplement your answers
- Be conversational but professional"""

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        if m["role"] == "user":
            st.markdown(f"**You:** {m['content']}")
        else:
            st.markdown(f"**Assistant:** {m['content']}")

    # Voice input option
    st.write("**Ask via text or voice:**")
    audio_input = st.audio_input("Record your question")
    
    prompt = st.text_input("Or type your question:", key="chat_input")
    col1, col2 = st.columns([3, 1])
    with col1:
        send_btn = st.button("Send", key="send_btn")
    with col2:
        clear_btn = st.button("Clear History", key="clear_btn")
    
    if clear_btn:
        st.session_state.messages = []
        st.rerun()
    
    # Handle voice input
    if audio_input is not None:
        with st.spinner("Transcribing your question..."):
            user_msg = transcribe_audio(audio_input.getvalue())
        if user_msg:
            st.success(f"You asked: {user_msg}")
            add_chat_message("user", user_msg)
            context_text = "\n\n".join([cv_text[:4000], projects_text[:3000], faq_text[:2000]])
            messages_for_openai = [{"role":"user","content": f"Context:\n{context_text}\n\nQuestion: {user_msg}"}]
            with st.spinner("Thinking..."):
                answer = openai_chat_completion(system_prompt, messages_for_openai)
            add_chat_message("assistant", answer)
            st.rerun()
    
    # Handle text input
    if send_btn:
        user_msg = prompt.strip()
        if user_msg:
            add_chat_message("user", user_msg)
            context_text = "\n\n".join([cv_text[:4000], projects_text[:3000], faq_text[:2000]])
            messages_for_openai = [{"role":"user","content": f"Context:\n{context_text}\n\nQuestion: {user_msg}"}]
            with st.spinner("Thinking..."):
                answer = openai_chat_completion(system_prompt, messages_for_openai)
            add_chat_message("assistant", answer)
            st.rerun()

    st.markdown("---")
    st.write("Download CV:")
    provide_cv_download()

# ---------- Voice Chat ----------
elif page == "Voice Chat":
    st.header("🎙️ Voice Interview Practice")
    st.write("Ask questions via voice or text and get spoken answers.")

    # Load context (CV + projects)
    cv_text = ""
    if os.path.exists("assets/cv.txt"):
        with open("assets/cv.txt","r",encoding="utf-8", errors="ignore") as f:
            cv_text = f.read()
    projects_text = "\n".join([f"{p['title']}: {p['description']}" for p in load_projects()])
    
    # Voice or text input
    st.subheader("📝 Option 1: Record Your Question")
    st.info("👇 Click the microphone button below to start recording your question")
    audio_input = st.audio_input("🎤 Click to record")
    
    st.markdown("---")
    st.subheader("⌨️ Option 2: Type Your Question")
    q = st.text_input("Type your question here:")
    
    if st.button("🔊 Get Spoken Answer", type="primary"):
        if not OPENAI_API_KEY:
            st.error("OPENAI_API_KEY not set.")
        else:
            # Determine the question source
            question = None
            if audio_input is not None:
                with st.spinner("Transcribing your question..."):
                    question = transcribe_audio(audio_input.getvalue())
                if question:
                    st.success(f"You asked: {question}")
            elif q.strip():
                question = q.strip()
            
            if question:
                # Load FAQ for voice chat too
                faq_text = ""
                if os.path.exists("assets/faq.json"):
                    with open("assets/faq.json", "r", encoding="utf-8") as f:
                        faq_data = json.load(f)
                        faq_text = json.dumps(faq_data, indent=2)
                
                context_text = "\n\n".join([cv_text[:4000], projects_text[:3000], faq_text[:2000]])
                question_with_context = f"Context about Claire Namusoke:\n{context_text}\n\nQuestion: {question}"
                system_prompt = """You are Claire Namusoke's voice assistant. Answer questions professionally and concisely.

IMPORTANT: Match user questions to similar questions in the FAQ data semantically, not just by exact wording.
Use the provided CV, project information, and FAQ responses to give accurate answers."""
                with st.spinner("Generating audio response..."):
                    ans = openai_chat_completion(system_prompt, [{"role":"user","content":question_with_context}])
                    st.write(f"**Answer:** {ans}")
                    audio = eleven_tts_generate(ans)
                if audio:
                    st.audio(audio, format="audio/mpeg", autoplay=True)
                else:
                    st.info("TTS not configured. Set ELEVEN_API_KEY and ELEVEN_VOICE_ID.")
            else:
                st.warning("Please record or type a question first.")

st.markdown("<hr>", unsafe_allow_html=True)
st.caption("Made with Streamlit • Claire Namusoke")
