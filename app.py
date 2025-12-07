import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS
from streamlit_option_menu import option_menu
import requests
import json
from PIL import Image
import PyPDF2
import docx
import re
from typing import Dict, List, Optional

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="MarketingOS | Enterprise Logic",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SESSION STATE INITIALIZATION ---
if 'history' not in st.session_state: st.session_state.history = []
if 'gemini_key' not in st.session_state: st.session_state.gemini_key = ""
if 'perplexity_key' not in st.session_state: st.session_state.perplexity_key = ""
if 'current_analysis' not in st.session_state: st.session_state.current_analysis = None
if 'uploaded_files' not in st.session_state: st.session_state.uploaded_files = []
if 'uploaded_images' not in st.session_state: st.session_state.uploaded_images = []
if 'url_context' not in st.session_state: st.session_state.url_context = ""
if 'chat_mode' not in st.session_state: st.session_state.chat_mode = False
if 'chat_messages' not in st.session_state: st.session_state.chat_messages = []

# --- HYBRID AESTHETIC CSS ---
def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;600;700&display=swap');
        
        /* BASE */
        .stApp { background-color: #fafaf9; color: #1a1f2e; font-family: 'Roboto', sans-serif; }
        
        /* SIDEBAR */
        [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e7e5e4; font-family: 'Roboto', sans-serif; }
        
        /* HEADERS & TEXT */
        .section-header { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; color: #a8a29e; font-weight: 600; margin: 20px 0 8px 0; font-family: 'Roboto', sans-serif; }
        .gradient-text { background: transparent; -webkit-text-fill-color: #1a1f2e; color: #1a1f2e; font-weight: 700; font-size: 2rem; margin-bottom: 0.5rem; letter-spacing: -0.02em; font-family: 'Roboto', sans-serif; }
        
        /* BUTTONS */
        .stButton button[kind="primary"] { background-color: #14b8a6; color: white !important; border: none; width: 100%; border-radius: 8px; padding: 10px 16px; font-weight: 600; font-size: 0.95rem; box-shadow: 0 2px 4px rgba(20, 184, 166, 0.2); transition: all 0.2s ease; }
        .stButton button[kind="primary"]:hover { background-color: #0d9488; box-shadow: 0 4px 12px rgba(20, 184, 166, 0.3); transform: translateY(-1px); }
        .stButton button:not([kind="primary"]) { background-color: #ffffff; color: #1a1f2e; border: 1px solid #e7e5e4; border-radius: 6px; font-weight: 500; padding: 10px 20px; transition: all 0.2s ease; }
        .stButton button:not([kind="primary"]):hover { border-color: #14b8a6; color: #14b8a6; }
        
        /* COMPONENTS */
        iframe[title="streamlit_option_menu.option_menu"] { margin-top: -10px; }
        .streamlit-expanderHeader { font-size: 0.9rem; color: #57534e; background-color: transparent; border: none; }
        [data-testid="stFileUploader"] { border: 1px dashed #e7e5e4; padding: 10px; border-radius: 8px; background-color: #ffffff; }
        
        /* CARDS */
        .ui-card { background-color: #ffffff; border: 1px solid #e7e5e4; border-radius: 8px; padding: 24px; margin-bottom: 16px; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05); transition: all 0.2s ease; }
        .ui-card:hover { box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08); border-color: #d6d3d1; transform: translateY(-1px); }
        
        /* STATUS & DEBATE */
        .status-badge { display: inline-flex; align-items: center; padding: 4px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: 500; background-color: #fafaf9; border: 1px solid #e7e5e4; color: #57534e; margin-right: 8px; font-family: 'Roboto', sans-serif; }
        .dot-online { width: 6px; height: 6px; background-color: #10b981; border-radius: 50%; margin-right: 6px; }
        .dot-offline { width: 6px; height: 6px; background-color: #ef4444; border-radius: 50%; margin-right: 6px; }
        .debate-creator { background-color: #f0fdfa; border-left: 3px solid #14b8a6; padding: 12px 16px; margin: 8px 0; border-radius: 4px; font-size: 0.9em; }
        .debate-critic { background-color: #fef2f2; border-left: 3px solid #ef4444; padding: 12px 16px; margin: 8px 0; border-radius: 4px; font-size: 0.9em; }
        
        /* INPUTS */
        .stTextArea textarea, .stTextInput input { border-radius: 6px; border: 1px solid #e7e5e4; transition: border-color 0.2s ease; font-family: 'Roboto', sans-serif; }
        .stTextArea textarea:focus, .stTextInput input:focus { border-color: #14b8a6; box-shadow: 0 0 0 1px #14b8a6; outline: none; }
        
        /* METRICS & TAGS */
        [data-testid="stMetricValue"] { color: #1a1f2e; font-weight: 600; font-family: 'Roboto', sans-serif; }
        [data-baseweb="tag"] { background-color: #ccfbf1 !important; border: 1px solid #14b8a6 !important; color: #115e59 !important; font-weight: 500; padding: 4px 12px; border-radius: 6px; font-family: 'Roboto', sans-serif; }
        [data-baseweb="tag"] svg { fill: #0d9488 !important; }
        [data-baseweb="tag"]:hover { background-color: #99f6e4 !important; border-color: #0d9488 !important; }
        
        /* CHAT & BADGES */
        .chat-message { padding: 12px 16px; border-radius: 12px; margin: 8px 0; font-size: 0.95rem; line-height: 1.5; }
        .user-message { background-color: #14b8a6; color: white; margin-left: 20%; border-bottom-right-radius: 4px; }
        .agent-message { background-color: #ffffff; border: 1px solid #e7e5e4; margin-right: 20%; border-bottom-left-radius: 4px; }
        .file-badge { display: inline-flex; align-items: center; gap: 6px; padding: 4px 8px; background-color: #f0fdfa; border: 1px solid #14b8a6; border-radius: 4px; font-size: 0.8rem; color: #0f766e; margin-right: 6px; margin-bottom: 6px; }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# --- FILE PROCESSING UTILITIES ---
def clean_markdown(text: str) -> str:
    """Removes code block wrappers and fixes table indentation"""
    text = text.replace("```markdown", "").replace("```", "").strip()
    text = re.sub(r'^##\s', '### ', text, flags=re.MULTILINE)
    return text

def extract_text_from_pdf(file) -> str:
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def extract_text_from_docx(file) -> str:
    try:
        doc = docx.Document(file)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        return f"Error reading DOCX: {str(e)}"

def extract_text_from_txt(file) -> str:
    try:
        return file.read().decode('utf-8')
    except Exception as e:
        return f"Error reading TXT: {str(e)}"

def analyze_image_with_gemini(image_file, prompt: str) -> str:
    """Analyze image using Gemini Vision"""
    try:
        if not st.session_state.gemini_key:
            return "Error: Gemini API key not configured"
        
        genai.configure(api_key=st.session_state.gemini_key)
        img = Image.open(image_file)
        
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content([prompt, img])
        return response.text
    except Exception as e:
        return f"Error analyzing image: {str(e)}"

def fetch_url_content(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        return response.text[:10000]
    except Exception as e:
        return f"Error fetching URL: {str(e)}"

# --- BUILT-IN MAD ENGINE (Enhanced) ---
class MADEngine:
    def __init__(self, gemini_key: str):
        self.gemini_key = gemini_key
        if gemini_key:
            genai.configure(api_key=gemini_key)
    
    def call_creator(self, prompt: str, previous_feedback: str = "", context: str = "") -> str:
        try:
            if not self.gemini_key: return "Error: Gemini API key not configured"
            
            context_str = f"Additional Context from Files/URLs:\n{context}\n" if context else ""
            feedback_str = f"Previous Critic Feedback: {previous_feedback}" if previous_feedback else ""
            
            full_prompt = f"""You are the CREATOR agent in a Multi-Agent Debate system.
            Your role: Generate high-quality marketing content and analysis.
            Task: {prompt}
            
            {context_str}
            {feedback_str}
            
            Provide a comprehensive, well-structured response in markdown format. Be specific, actionable, and data-driven."""
            
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = model.generate_content(full_prompt)
            return response.text
        except Exception as e: return f"Creator Error: {str(e)}"
    
    def call_critic(self, creator_output: str, original_prompt: str) -> Dict[str, any]:
        try:
            if not self.gemini_key: return {"approved": False, "feedback": "Error: Gemini API key not configured"}
            
            critic_prompt = f"""You are the CRITIC agent in a Multi-Agent Debate system.
            Original Task: {original_prompt}
            Creator's Output: {creator_output}
            Evaluate for completeness, accuracy, and actionability.
            Respond in JSON: {{ "approved": true/false, "score": 0-100, "feedback": "Specific feedback", "strengths": [], "weaknesses": [] }}"""
            
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = model.generate_content(critic_prompt)
            try: return json.loads(response.text.strip().replace('```json', '').replace('```', ''))
            except: return {"approved": True, "score": 75, "feedback": response.text}
        except Exception as e: return {"approved": False, "feedback": f"Critic Error: {str(e)}", "score": 0}
    
    def solve_task(self, task: str, max_rounds: int = 3, context: str = "") -> Dict:
        debate_history = []
        creator_output = ""
        for round_num in range(1, max_rounds + 1):
            feedback = debate_history[-1]['feedback'] if debate_history else ""
            creator_output = self.call_creator(task, feedback, context)
            debate_history.append({"round": round_num, "role": "creator", "content": creator_output})
            
            critic_result = self.call_critic(creator_output, task)
            debate_history.append({"round": round_num, "role": "critic", "content": f"Score: {critic_result.get('score', 0)}/100\n\n{critic_result.get('feedback', '')}", "feedback": critic_result.get('feedback', ''), "approved": critic_result.get('approved', False), "score": critic_result.get('score', 0)})
            
            if critic_result.get('approved', False) and critic_result.get('score', 0) >= 80:
                return {"final_answer": creator_output, "rounds_used": round_num, "approved": True, "debate_history": debate_history, "final_score": critic_result.get('score', 0)}
        
        return {"final_answer": creator_output, "rounds_used": max_rounds, "approved": False, "debate_history": debate_history, "final_score": critic_result.get('score', 0)}

    def chat_response(self, user_message: str, conversation_history: List[Dict], analysis_context: str = "") -> str:
        try:
            if not self.gemini_key: return "Error: Gemini API key not configured"
            chat_context = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in conversation_history[-5:]])
            prompt = f"Previous Analysis: {analysis_context}\nConversation: {chat_context}\nUser: {user_message}\nProvide a helpful response."
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = model.generate_content(prompt)
            return response.text
        except Exception as e: return f"Error: {str(e)}"

# --- HELPER FUNCTIONS ---
def check_systems() -> Dict[str, bool]:
    return {"gemini": bool(st.session_state.gemini_key), "mad_engine": bool(st.session_state.gemini_key)}

def display_mad_result(data: Optional[Dict], filename: str = "report.md"):
    if not data or "error" in data:
        st.error(data.get("error", "Unknown error"))
        return
    st.session_state.current_analysis = data['final_answer']
    
    # Use clean_markdown for better formatting
    clean_report = clean_markdown(data['final_answer'])
    
    st.markdown("---")
    with st.expander("📋 **Final Report**", expanded=True):
        st.markdown(clean_report)
        st.markdown(f"\n\n*⚡ Generated via MAD Engine ({data.get('rounds_used', '?')} rounds) | Score: {data.get('final_score', 'N/A')}/100*")
    
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("🔄 Rounds", data.get('rounds_used', 'N/A'))
    with c2: st.metric("Status", "✅ Approved" if data.get('approved') else "⚠️ Max Rounds")
    with c3: st.metric("📊 Final Score", f"{data.get('final_score', 'N/A')}/100")
    
    st.download_button("📥 Download Report", clean_report, file_name=filename, mime="text/markdown")
    
    if st.button("💬 Chat About This Analysis", type="primary"):
        st.session_state.chat_mode = True
        st.session_state.chat_messages = [{"role": "assistant", "content": "Hi! Ask me anything about this analysis."}]
        st.rerun()
        
    with st.expander("🔍 **Debate History**", expanded=False):
        for entry in data.get('debate_history', []):
            role = "🔵 CREATOR" if entry['role'] == "creator" else "🔴 CRITIC"
            st.markdown(f'<div class="debate-{entry["role"]}">{role} (Round {entry["round"]})</div>', unsafe_allow_html=True)
            st.markdown(entry['content'])
            st.divider()

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("""<div style="padding:10px 0 20px 0; display:flex; align-items:center; gap:10px;"><div style="font-size:24px;">⚡</div><div><div style="font-weight:700; font-size:16px; color:#1a1f2e;">MarketingOS</div><div style="font-size:11px; color:#78716c;">Enterprise Edition</div></div></div>""", unsafe_allow_html=True)
    if st.button("➕ New Analysis", type="primary", use_container_width=True):
        st.session_state.current_analysis = None
        st.session_state.chat_mode = False
        st.session_state.uploaded_files = []
        st.session_state.uploaded_images = []
        st.session_state.url_context = ""
        st.rerun()
    
    st.markdown('<div class="section-header">AI AGENTS</div>', unsafe_allow_html=True)
    selected = option_menu(None, ["Audit", "PPC", "SEO", "Social", "Research", "Copy", "Strategy"], icons=["clipboard-data", "currency-dollar", "search", "instagram", "globe", "pencil-square", "diagram-3"], menu_icon="robot", default_index=0, styles={"container": {"padding": "0!important", "background-color": "transparent"}, "icon": {"color": "#14b8a6", "font-size": "16px"}, "nav-link": {"font-size": "14px", "text-align": "left", "margin": "2px 0", "padding": "8px 12px", "color": "#57534e", "font-weight": "400"}, "nav-link-selected": {"background-color": "#f0fdfa", "color": "#0f766e", "font-weight": "600"}})
    
    st.markdown('<div class="section-header">CONTEXT</div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["📄 Docs", "🖼️ Images", "🌐 URL"])
    
    with tab1:
        uploaded_files = st.file_uploader("Attach Documents", type=['pdf', 'csv', 'docx', 'txt'], accept_multiple_files=True, label_visibility="collapsed")
        if uploaded_files: st.session_state.uploaded_files = uploaded_files
    
    with tab2:
        uploaded_images = st.file_uploader("Attach Images", type=['jpg', 'png', 'jpeg'], accept_multiple_files=True, label_visibility="collapsed")
        if uploaded_images: st.session_state.uploaded_images = uploaded_images
        
    with tab3:
        url_input = st.text_input("Analyze URL", placeholder="https://example.com", label_visibility="collapsed")
        if url_input and st.button("Link URL"):
            with st.spinner("Fetching..."):
                st.session_state.url_context = fetch_url_content(url_input)
                st.success("Linked!")
    
    if st.session_state.uploaded_files or st.session_state.uploaded_images or st.session_state.url_context:
        if st.button("🗑️ Clear Context"):
            st.session_state.uploaded_files = []
            st.session_state.uploaded_images = []
            st.session_state.url_context = ""
            st.rerun()

    st.markdown('<div class="section-header">SYSTEM</div>', unsafe_allow_html=True)
    with st.expander("⚙️ Configuration", expanded=False):
        k1 = st.text_input("Gemini API Key", type="password", value=st.session_state.gemini_key)
        if k1: st.session_state.gemini_key = k1
        k2 = st.text_input("Perplexity API Key", type="password", value=st.session_state.perplexity_key)
        if k2: st.session_state.perplexity_key = k2
    
    st.markdown("<br>", unsafe_allow_html=True)
    status = check_systems()
    c1, c2 = st.columns(2)
    with c1: st.markdown(f'<div class="status-badge"><span class="dot-{"online" if status["mad_engine"] else "offline"}"></span>Engine</div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="status-badge"><span class="dot-{"online" if status["gemini"] else "offline"}"></span>Gemini</div>', unsafe_allow_html=True)

# --- MAIN CONTENT ---
if st.session_state.chat_mode:
    st.markdown(f'<h1 class="gradient-text">💬 Chat Analysis</h1>', unsafe_allow_html=True)
    if st.button("⬅️ Back"): st.session_state.chat_mode = False; st.rerun()
    for msg in st.session_state.chat_messages:
        st.markdown(f'<div class="chat-message {"user-message" if msg["role"] == "user" else "agent-message"}">{msg["content"]}</div>', unsafe_allow_html=True)
    user_input = st.chat_input("Ask a follow-up...")
    if user_input:
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        st.rerun()
    if st.session_state.chat_messages and st.session_state.chat_messages[-1]["role"] == "user":
        with st.spinner("Thinking..."):
            try:
                engine = MADEngine(st.session_state.gemini_key)
                resp = engine.chat_response(st.session_state.chat_messages[-1]["content"], st.session_state.chat_messages, st.session_state.current_analysis)
                st.session_state.chat_messages.append({"role": "assistant", "content": resp})
                st.rerun()
            except Exception as e: st.error(f"Error: {e}")
else:
    st.markdown(f'<h1 class="gradient-text">{selected} Agent</h1>', unsafe_allow_html=True)
    
    # Process Context
    file_context = st.session_state.url_context
    if st.session_state.uploaded_files:
        st.markdown("###### 📎 Attached Context:")
        badges = ""
        for f in st.session_state.uploaded_files:
            badges += f'<span class="file-badge">📄 {f.name}</span>'
            if f.type == "application/pdf": file_context += f"\nFILE: {f.name}\n{extract_text_from_pdf(f)}"
            elif "text" in f.type: file_context += f"\nFILE: {f.name}\n{extract_text_from_txt(f)}"
            elif "document" in f.type: file_context += f"\nFILE: {f.name}\n{extract_text_from_docx(f)}"
        st.markdown(badges, unsafe_allow_html=True)
    
    # Image Context with Spinner
    if st.session_state.uploaded_images:
        st.markdown("###### 🖼️ Images:")
        cols = st.columns(5)
        for i, img in enumerate(st.session_state.uploaded_images):
            with cols[i%5]: st.image(img, width=100)
            with st.spinner(f"Analyzing {img.name}..."):
               analysis = analyze_image_with_gemini(img, 'Describe this image for marketing analysis')
               file_context += f"\nIMAGE ANALYSIS for {img.name}:\n{analysis}"
    
    if selected == "Audit":
        st.markdown('<div class="ui-card"><h3>🏆 GA4 & GTM Auditor</h3></div>', unsafe_allow_html=True)
        inp = st.text_area("Input Data", height=150)
        if st.button("🔍 Run Audit", type="primary"):
            if not inp and not file_context: st.warning("Provide data.")
            else:
                with st.spinner("Analyzing..."):
                    eng = MADEngine(st.session_state.gemini_key)
                    display_mad_result(eng.solve_task(f"Audit GA4/GTM data:\n{inp}", context=file_context), "audit.md")

    elif selected == "PPC":
        st.markdown('<div class="ui-card"><h3>💰 PPC Optimizer</h3></div>', unsafe_allow_html=True)
        inp = st.text_area("Campaign Data", height=150)
        if st.button("📊 Analyze", type="primary"):
            if not inp and not file_context: st.warning("Provide data.")
            else:
                with st.spinner("Analyzing..."):
                    eng = MADEngine(st.session_state.gemini_key)
                    display_mad_result(eng.solve_task(f"Analyze PPC data:\n{inp}", context=file_context), "ppc.md")

    elif selected == "SEO":
        st.markdown('<div class="ui-card"><h3>🔍 SEO Planner</h3></div>', unsafe_allow_html=True)
        kw = st.text_area("Keywords", height=100)
        if st.button("🎯 Plan", type="primary"):
            with st.spinner("Planning..."):
                eng = MADEngine(st.session_state.gemini_key)
                display_mad_result(eng.solve_task(f"SEO Strategy for:\n{kw}", context=file_context), "seo.md")

    elif selected == "Social":
        st.markdown('<div class="ui-card"><h3>📱 Social Media Manager</h3></div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1: niche = st.text_input("Niche")
        with c2: plat = st.multiselect("Platforms", ["LinkedIn", "Twitter", "Instagram"])
        if st.button("📅 Generate", type="primary"):
            with st.spinner("Generating..."):
                eng = MADEngine(st.session_state.gemini_key)
                display_mad_result(eng.solve_task(f"Social Calendar for {niche} on {plat}", context=file_context), "calendar.md")

    elif selected == "Research":
        st.markdown('<div class="ui-card"><h3>🌍 Deep Researcher</h3></div>', unsafe_allow_html=True)
        q = st.text_input("Topic")
        use_perp = st.checkbox("Use Perplexity", value=bool(st.session_state.perplexity_key), disabled=not st.session_state.perplexity_key)
        if st.button("🔎 Research", type="primary"):
            with st.spinner("Researching..."):
                try:
                    eng = MADEngine(st.session_state.gemini_key)
                    web_data = ""
                    
                    # Perplexity API Logic
                    if use_perp and st.session_state.perplexity_key:
                        try:
                            url = "https://api.perplexity.ai/chat/completions"
                            headers = {"Authorization": f"Bearer {st.session_state.perplexity_key}", "Content-Type": "application/json"}
                            resp = requests.post(url, json={"model": "sonar-pro", "messages": [{"role": "user", "content": q}]}, headers=headers)
                            web_data = resp.json()['choices'][0]['message']['content']
                        except Exception as e:
                            st.warning(f"Perplexity failed ({e}). Using DuckDuckGo.")
                            use_perp = False
                    
                    if not use_perp and q:
                        results = DDGS().text(q, max_results=5)
                        web_data = str(results)
                    
                    display_mad_result(eng.solve_task(f"Research: {q}\nWeb Data: {web_data}", context=file_context), "research.md")
                except Exception as e: st.error(str(e))

    elif selected == "Copy":
        st.markdown('<div class="ui-card"><h3>✍️ AI Copywriter</h3></div>', unsafe_allow_html=True)
        txt = st.text_area("Text", height=150)
        style = st.selectbox("Style", ["Simplify", "Persuasive", "Professional"])
        if st.button("✨ Rewrite", type="primary"):
            with st.spinner("Writing..."):
                eng = MADEngine(st.session_state.gemini_key)
                # Use clean_markdown to format output
                res = eng.call_creator(f"Rewrite in {style} style:\n{txt if txt else file_context}")
                st.markdown(clean_markdown(res))

    elif selected == "Strategy":
        st.markdown('<div class="ui-card"><h3>🧩 Strategy Architect</h3></div>', unsafe_allow_html=True)
        goal = st.text_input("Goal")
        if st.button("🚀 Build", type="primary"):
            with st.spinner("Building..."):
                eng = MADEngine(st.session_state.gemini_key)
                display_mad_result(eng.solve_task(f"Strategy for: {goal}", context=file_context), "strategy.md")

# --- FOOTER ---
st.markdown("---")
st.markdown("""<div style="text-align: center; color: #a8a29e; font-size: 0.8rem;">MarketingOS v5.0 | Enterprise AI</div>""", unsafe_allow_html=True)
