# app.py
import streamlit as st
import os
import requests
import json
import base64
from openai import OpenAI

# Must be the first Streamlit command
st.set_page_config(page_title="Claire Namusoke — Portfolio", layout="wide")

# ---------- CONFIG ----------
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")
OPENAI_MODEL = st.secrets.get("OPENAI_MODEL", "gpt-4o-mini")  
ELEVEN_API_KEY = st.secrets.get("ELEVEN_API_KEY") 
ELEVEN_VOICE_ID = st.secrets.get("ELEVEN_VOICE_ID")  
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
    body = {
        "text": text,
        "model": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.7,
            "similarity_boost": 0.8
        }
    }
    try:
        r = requests.post(url, json=body, headers=headers, timeout=30)
        if r.status_code == 200:
            # Check if response is valid audio
            if r.content and len(r.content) > 1000:
                return r.content
            else:
                st.error("TTS API returned success but no valid audio data.")
                st.info(f"Debug: Response length={len(r.content)}; Content-Type={r.headers.get('Content-Type')}")
                return None
        else:
            st.error(f"TTS Error: {r.status_code} {r.text}")
            st.info(f"Debug: Response headers={r.headers}")
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

def add_chatbot_icon():
    """Add floating chatbot icon in bottom corner"""
    if 'show_chat' not in st.session_state:
        st.session_state.show_chat = False
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    
    # Unified AI chat and voice widget at the bottom of the page
    st.markdown("""
    <style>
    .unified-chat-widget {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100vw;
        background: #1a1a2e;
        border-top: 2px solid #58a6ff;
        box-shadow: 0 -2px 12px rgba(0,0,0,0.2);
        z-index: 9999;
        padding: 16px 0 8px 0;
    }
    .unified-chat-content {
        max-width: 600px;
        margin: 0 auto;
        color: #fff;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='unified-chat-widget'><div class='unified-chat-content'>", unsafe_allow_html=True)
    # Show small floating profile picture instead of 💬 icon
    profile_img_html = ""
    if os.path.exists("assets/profile.jpg"):
        import base64
        with open("assets/profile.jpg", "rb") as img_file:
            img_data = base64.b64encode(img_file.read()).decode()
        profile_img_html = f"<img src='data:image/jpeg;base64,{img_data}' alt='Profile' style='width:36px;height:36px;border-radius:50%;margin-right:8px;vertical-align:middle;border:2px solid #58a6ff;box-shadow:0 0 8px #58a6ff;'>"
    st.markdown(f"### {profile_img_html} Talk To Claire", unsafe_allow_html=True)

    # User chooses response type
    response_type = st.session_state.get("response_type_radio")

    # Display messages
    if response_type == "Speech only":
        # Only play the latest assistant speech response, no text
        warning_shown = False
        for i, msg in enumerate(reversed(st.session_state.chat_messages)):
            if msg.get("role") == "assistant":
                audio_bytes = msg.get("audio")
                if audio_bytes:
                    import base64
                    b64_audio = base64.b64encode(audio_bytes).decode()
                    st.markdown(f"""
                    <audio id='ai_audio_{i}' src='data:audio/wav;base64,{b64_audio}' autoplay>
                        Your browser does not support the audio element.
                    </audio>
                    <script>
                    var audio = document.getElementById('ai_audio_{i}');
                    if (audio) {{ audio.play(); }}
                    </script>
                    """, unsafe_allow_html=True)
                else:
                    # Show visible warning if no audio generated
                    st.warning("No audio was generated for the last response. Please check your ElevenLabs API settings or try again.")
                    warning_shown = True
                break
    else:
        for i, msg in enumerate(st.session_state.chat_messages):
            if msg["role"] == "user":
                st.markdown(f"**You:** {msg['content']}")
            else:
                st.markdown(f"**AI:** {msg['content']}")
                if msg.get("audio"):
                    import base64
                    audio_bytes = msg["audio"]
                    if audio_bytes:
                        b64_audio = base64.b64encode(audio_bytes).decode()
                        st.markdown(f"""
                        <audio id='ai_audio_{i}' src='data:audio/wav;base64,{b64_audio}' autoplay>
                            Your browser does not support the audio element.
                        </audio>
                        <script>
                        var audio = document.getElementById('ai_audio_{i}');
                        if (audio) {{ audio.play(); }}
                        </script>
                        """, unsafe_allow_html=True)

    # Clear button for text responses
    if st.button("Clear Text Responses", key="chat_clear"):
        st.session_state.chat_messages = []
        st.rerun()

    # User chooses response type
    response_type = st.radio(
        "Choose response type:",
        ["Text only", "Speech only", "Text & Speech"],
        index=0,
        horizontal=True,
        key="response_type_radio"
    )

    # Text input
    user_msg = st.text_input("Type your question...", key="chat_input", on_change=None)
    # Send message when Enter is pressed (Streamlit reruns on input change)
    if user_msg.strip():
        # Prevent duplicate sends by checking last user message
        last_user_msg = next((m for m in reversed(st.session_state.chat_messages) if m["role"] == "user"), None)
        last_assistant_msg = next((m for m in reversed(st.session_state.chat_messages) if m["role"] == "assistant"), None)
        # Only respond if this user_msg hasn't already received an assistant reply
        if not last_user_msg or last_user_msg["content"] != user_msg or not last_assistant_msg or last_assistant_msg.get("user_msg") != user_msg:
            st.session_state.chat_messages.append({"role": "user", "content": user_msg})
            # Load context
            cv_text = ""
            if os.path.exists("assets/cv.txt"):
                with open("assets/cv.txt","r",encoding="utf-8", errors="ignore") as f:
                    cv_text = f.read()
            projects_text = "\n".join([f"{p['title']}: {p['description']}" for p in load_projects()])
            faq_text = ""
            if os.path.exists("assets/faq.json"):
                with open("assets/faq.json", "r", encoding="utf-8") as f:
                    faq_data = json.load(f)
                    faq_text = json.dumps(faq_data, indent=2)
            context = "\n\n".join([cv_text[:4000], projects_text[:3000], faq_text[:2000]])
            system_prompt = (
                "You are Claire's AI assistant. Respond with warmth, empathy, and a positive tone. "
                "Always consider the FAQ data provided below and use it to answer questions when relevant. "
                "If a question matches or relates to the FAQ, use the FAQ answer, but feel free to add a personal, sentimental touch. "
                "If the FAQ does not cover the question, answer thoughtfully and helpfully.\n\nFAQ Data:\n" + faq_text
            )
            api_key = st.secrets.get("OPENAI_API_KEY")
            if api_key:
                with st.spinner("Thinking..."):
                    answer = openai_chat_completion(system_prompt, [{"role":"user","content": f"Context:\n{context}\n\nQuestion: {user_msg}"}], model=OPENAI_MODEL)
                # Only append one assistant response, then rerun
                if response_type == "Text only":
                    st.session_state.chat_messages.append({"role": "assistant", "content": answer, "audio": None, "user_msg": user_msg})
                elif response_type == "Speech only":
                    audio = eleven_tts_generate(answer)
                    st.session_state.chat_messages.append({"role": "assistant", "content": None, "audio": audio if audio else None, "user_msg": user_msg})
                elif response_type == "Text & Speech":
                    audio = eleven_tts_generate(answer)
                    st.session_state.chat_messages.append({"role": "assistant", "content": answer, "audio": audio if audio else None, "user_msg": user_msg})
            else:
                st.session_state.chat_messages.append({"role": "assistant", "content": "API key not configured. Please check your Streamlit secrets file and restart the app.", "audio": None, "user_msg": user_msg})
                st.rerun()

    st.markdown("</div></div>", unsafe_allow_html=True)

# ---------- Helper: AI Assistant Widget ----------
def show_ai_assistant():
    """Display floating AI assistant on the page"""
    # Initialize session state for AI assistant visibility and chat
    if 'show_assistant' not in st.session_state:
        st.session_state.show_assistant = False
    if 'ai_messages' not in st.session_state:
        st.session_state.ai_messages = []
    
    # Add custom CSS for floating assistant with profile picture
    st.markdown("""
    <style>
    .ai-assistant-float {
        position: fixed;
        bottom: 30px;
        right: 30px;
        z-index: 999;
    }
    .ai-assistant-avatar {
        position: relative;
        cursor: pointer;
        transition: transform 0.3s ease;
    }
    .ai-assistant-avatar:hover {
        transform: scale(1.1);
    }
    .ai-assistant-avatar img {
        width: 70px;
        height: 70px;
        border-radius: 50%;
        border: 3px solid #58a6ff;
        box-shadow: 0 0 20px rgba(88,166,255,0.8);
        object-fit: cover;
    }
    .microphone-badge {
        position: absolute;
        bottom: -5px;
        right: -5px;
        background: linear-gradient(135deg, #58a6ff 0%, #3b8dd9 100%);
        border-radius: 50%;
        width: 28px;
        height: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        border: 2px solid white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        animation: pulse-mic 2s ease-in-out infinite;
    }
    @keyframes pulse-mic {
        0%, 100% { transform: scale(1); box-shadow: 0 2px 8px rgba(0,0,0,0.3); }
        50% { transform: scale(1.1); box-shadow: 0 4px 12px rgba(88, 166, 255, 0.6); }
    }
    .ai-chat-window {
        position: fixed;
        bottom: 120px;
        right: 30px;
        width: 350px;
        max-height: 500px;
        background: #1a1a2e;
        border-radius: 15px;
        border: 2px solid #58a6ff;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        z-index: 998;
        padding: 15px;
        overflow-y: auto;
    }
    /* Make floating picture clickable */
    .ai-assistant-float {
        cursor: pointer;
        pointer-events: auto;
    }
    .ai-assistant-float:active {
        transform: scale(0.95);
    }
    /* Style the button to look like the floating image */
    button[key*="avatar_btn_"] {
        position: fixed !important;
        bottom: 30px !important;
        right: 30px !important;
        width: 70px !important;
        height: 70px !important;
        border-radius: 50% !important;
        background: transparent !important;
        border: 3px solid #58a6ff !important;
        padding: 0 !important;
        z-index: 1002 !important;
        cursor: pointer !important;
        min-height: 0 !important;
        box-shadow: 0 0 20px rgba(88, 166, 255, 0.8) !important;
        color: white !important;
        font-size: 20px !important;
    }
    button[key*="avatar_btn_"]:hover {
        transform: scale(1.1) !important;
        box-shadow: 0 0 25px rgba(88, 166, 255, 1) !important;
    }
    button[key*="avatar_btn_"]:focus {
        background: transparent !important;
        outline: none !important;
    }
    /* Hide the image div since button will show */
    .ai-assistant-float {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Display clickable floating profile picture
    if os.path.exists("assets/profile.jpg"):
        import base64
        with open("assets/profile.jpg", "rb") as img_file:
            img_data = base64.b64encode(img_file.read()).decode()
        
        # Clickable button first (will be positioned over the image with CSS)
        if st.button("💬 Chat", key=f"avatar_btn_{page}"):
            st.session_state.show_assistant = not st.session_state.show_assistant
            st.rerun()
        
        # Create the floating avatar display below the button
        st.markdown(f"""
        <div class="ai-assistant-float">
            <div class="ai-assistant-avatar">
                <img src="data:image/jpeg;base64,{img_data}" alt="AI Chatbot">
                <div class="microphone-badge">💬</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Show AI chat interface when activated
    if st.session_state.show_assistant:
        with st.container():
            st.markdown("### 🤖 AI Assistant")
            
            # Display chat history
            for msg in st.session_state.ai_messages:
                if msg["role"] == "user":
                    st.markdown(f"**You:** {msg['content']}")
                else:
                    st.markdown(f"**AI:** {msg['content']}")
            
            # Input area
            col1, col2 = st.columns([3, 1])
            with col1:
                user_input = st.text_input("Ask me anything...", key=f"ai_input_{page}", label_visibility="collapsed")
            with col2:
                send_btn = st.button("Send", key=f"send_{page}")
            
            col3, col4 = st.columns(2)
            with col3:
                if st.button("Clear Chat", key=f"clear_{page}"):
                    st.session_state.ai_messages = []
                    st.rerun()
            with col4:
                if st.button("Close", key=f"close_{page}"):
                    st.session_state.show_assistant = False
                    st.rerun()
            
            # Process question
            if send_btn and user_input.strip():
                question = user_input.strip()
                st.session_state.ai_messages.append({"role": "user", "content": question})
                if not OPENAI_API_KEY:
                    st.session_state.ai_messages.append({"role": "assistant", "content": "OpenAI API key not configured."})
                else:
                    # Load context
                    cv_text = ""
                    if os.path.exists("assets/cv.txt"):
                        with open("assets/cv.txt","r",encoding="utf-8", errors="ignore") as f:
                            cv_text = f.read()
                    projects_text = "\n".join([f"{p['title']}: {p['description']}" for p in load_projects()])
                    faq_text = ""
                    if os.path.exists("assets/faq.json"):
                        with open("assets/faq.json", "r", encoding="utf-8") as f:
                            faq_data = json.load(f)
                            faq_text = json.dumps(faq_data, indent=2)
                    context_text = "\n\n".join([cv_text[:4000], projects_text[:3000], faq_text[:2000]])
                    system_prompt = """You are Claire Namusoke's AI assistant. Answer questions professionally and concisely.\nMatch user questions to FAQ data semantically. Prioritize FAQ answers when available."""
                    with st.spinner("Thinking..."):
                        answer = openai_chat_completion(system_prompt, [{"role":"user","content": f"Context:\n{context_text}\n\nQuestion: {question}"}])
                    # Only append one assistant response, then rerun
                    st.session_state.ai_messages.append({"role": "assistant", "content": answer})
                st.rerun()

# ---------- Navigation ----------
page = st.radio("Navigation", ["About","Projects"], horizontal=True, label_visibility="collapsed")

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
        about = """Hi,  I am Claire, a data analytics enthusiast and International Shipping and chartering student at Hochschule Bremen, 
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
    # Add bottom AI chat widget with options
    add_chatbot_icon()

# ---------- Projects ----------
elif page == "Projects":
    st.header("Projects")
    projects = load_projects()
    if projects:
        for p in projects:
            st.subheader(f"🔗 [{p.get('title')}]({p.get('link')})")
            # Description is hidden in UI, but available for AI
            # st.write(p.get("description"))
            # Display tools used
            if p.get("tools"):
                tools_str = " • ".join(p.get("tools"))
                st.markdown(f"<p style='color: #58a6ff;'><strong>Tools:</strong> {tools_str}</p>", unsafe_allow_html=True)
            st.markdown("---")
    else:
        st.info("No projects found. Add them in assets/projects.json")
    # Add bottom AI chat widget with options
    add_chatbot_icon()

st.markdown("<hr>", unsafe_allow_html=True)
st.caption("Made with Streamlit • Claire Namusoke")
