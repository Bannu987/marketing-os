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
    page_title="MarketingOS | Enterprise",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SESSION STATE INITIALIZATION ---
if 'history' not in st.session_state: st.session_state.history = []
if 'gemini_key' not in st.session_state:
    try: st.session_state.gemini_key = st.secrets["GEMINI_API_KEY"]
    except: st.session_state.gemini_key = ""
if 'perplexity_key' not in st.session_state:
    try: st.session_state.perplexity_key = st.secrets["PERPLEXITY_API_KEY"]
    except: st.session_state.perplexity_key = ""

# Core State
if 'current_analysis' not in st.session_state: st.session_state.current_analysis = None
if 'uploaded_files' not in st.session_state: st.session_state.uploaded_files = []
if 'uploaded_images' not in st.session_state: st.session_state.uploaded_images = []
if 'url_context' not in st.session_state: st.session_state.url_context = ""
if 'chat_messages' not in st.session_state: st.session_state.chat_messages = []
if 'theme' not in st.session_state: st.session_state.theme = "light"

# Brand & Project State
if 'brand_name' not in st.session_state: st.session_state.brand_name = ""
if 'brand_voice' not in st.session_state: st.session_state.brand_voice = ""
if 'brand_audience' not in st.session_state: st.session_state.brand_audience = ""
if 'brand_offer' not in st.session_state: st.session_state.brand_offer = ""
if 'project_name' not in st.session_state: st.session_state.project_name = ""
if 'project_goal' not in st.session_state: st.session_state.project_goal = ""

# Strategy Pipeline State
if 'seo_prefill' not in st.session_state: st.session_state.seo_prefill = ""
if 'ppc_prefill' not in st.session_state: st.session_state.ppc_prefill = ""
if 'social_prefill' not in st.session_state: st.session_state.social_prefill = ""
if 'copy_prefill' not in st.session_state: st.session_state.copy_prefill = ""
if 'target_agent' not in st.session_state: st.session_state.target_agent = None

# Playbooks State
if 'playbook' not in st.session_state: st.session_state.playbook = "None"

# --- MODERN UI CSS INJECTION (LOVABLE STYLE) ---
def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        /* VARIABLES */
        :root {
            --primary: #14b8a6;
            --primary-hover: #0d9488;
            --primary-light: #f0fdfa;
            --text-dark: #1a1f2e;
            --text-gray: #57534e;
            --text-light: #a8a29e;
            --bg-page: #fafaf9;
            --bg-card: #ffffff;
            --border-color: #e7e5e4;
        }
        
        /* GLOBAL RESET */
        .stApp {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-page);
            color: var(--text-dark);
        }
        
        /* SIDEBAR STYLING */
        [data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid var(--border-color);
        }
        
        /* HEADERS */
        h1, h2, h3 { font-family: 'Inter', sans-serif; font-weight: 700; letter-spacing: -0.02em; }
        .agent-title { font-size: 1.5rem; color: var(--text-dark); display: flex; align-items: center; gap: 10px; margin-bottom: 0.5rem; }
        
        /* UI CARDS */
        .ui-card {
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            margin-bottom: 20px;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .ui-card:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            border-color: #d6d3d1;
        }
        .card-header { font-size: 1.1rem; font-weight: 600; color: var(--text-dark); margin-bottom: 4px; }
        .card-desc { font-size: 0.9rem; color: var(--text-gray); margin-bottom: 16px; }
        
        /* BUTTONS */
        .stButton button {
            border-radius: 8px;
            font-weight: 500;
            padding: 0.5rem 1rem;
            transition: all 0.2s;
            border: 1px solid var(--border-color);
        }
        /* Primary Action Buttons */
        div[data-testid="stVerticalBlock"] > .stButton > button[kind="primary"] {
            background-color: var(--primary);
            color: white;
            border: none;
            box-shadow: 0 2px 4px rgba(20, 184, 166, 0.2);
        }
        div[data-testid="stVerticalBlock"] > .stButton > button[kind="primary"]:hover {
            background-color: var(--primary-hover);
            box-shadow: 0 4px 6px rgba(20, 184, 166, 0.3);
            transform: translateY(-1px);
        }
        
        /* TEXT INPUTS */
        .stTextInput input, .stTextArea textarea {
            border-radius: 8px;
            border: 1px solid var(--border-color);
            background-color: white;
            color: var(--text-dark);
        }
        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 2px var(--primary-light);
        }
        
        /* CHAT BUBBLES */
        .chat-container { display: flex; flex-direction: column; gap: 12px; padding: 10px; }
        .chat-bubble { max-width: 85%; padding: 12px 16px; font-size: 0.9rem; line-height: 1.5; position: relative; }
        
        .user-bubble {
            background-color: var(--primary);
            color: white;
            border-radius: 12px 12px 0 12px;
            align-self: flex-end;
            margin-left: auto;
            box-shadow: 0 2px 4px rgba(20, 184, 166, 0.2);
        }
        
        .agent-bubble {
            background-color: #f4f4f5;
            color: var(--text-dark);
            border: 1px solid var(--border-color);
            border-radius: 12px 12px 12px 0;
            align-self: flex-start;
            margin-right: auto;
        }
        
        /* TAGS & BADGES */
        .status-badge {
            display: inline-flex; align-items: center; gap: 6px;
            padding: 4px 10px; background: white; border: 1px solid var(--border-color);
            border-radius: 20px; font-size: 0.75rem; color: var(--text-gray);
        }
        .dot-online { width: 8px; height: 8px; background: var(--primary); border-radius: 50%; }
        .dot-offline { width: 8px; height: 8px; background: #ef4444; border-radius: 50%; }

        /* MARKDOWN TABLES */
        table { width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 0.9rem; }
        th { text-align: left; background: #f9fafb; padding: 10px; border-bottom: 2px solid var(--border-color); font-weight: 600; }
        td { padding: 10px; border-bottom: 1px solid var(--border-color); }

        /* SECTION HEADERS (Sidebar) */
        .sidebar-section {
            font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;
            color: var(--text-light); font-weight: 600; margin: 20px 0 10px 0;
        }

        /* TABS */
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] {
            height: 40px; white-space: nowrap; background-color: white;
            border-radius: 6px; border: 1px solid var(--border-color);
            padding: 0 16px; gap: 8px; color: var(--text-gray);
        }
        .stTabs [aria-selected="true"] {
            background-color: var(--primary-light); border-color: var(--primary);
            color: var(--primary);
        }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# --- FILE PROCESSING UTILITIES ---
def clean_markdown(text: str) -> str:
    text = text.replace("markdown", "").replace("```", "").strip()
    text = re.sub(r'^##\s', '### ', text, flags=re.MULTILINE)
    return text

def extract_text_from_pdf(file) -> str:
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages: text += page.extract_text() + "\n"
        return text
    except: return "Error reading PDF"

def extract_text_from_docx(file) -> str:
    try:
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    except: return "Error reading DOCX"

def extract_text_from_txt(file) -> str:
    try: return file.read().decode('utf-8')
    except: return "Error reading TXT"

def analyze_image_with_gemini(image_file, prompt: str) -> str:
    try:
        if not st.session_state.gemini_key: return "Error: Gemini API key not configured"
        genai.configure(api_key=st.session_state.gemini_key)
        img = Image.open(image_file)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content([prompt, img])
        return response.text
    except Exception as e: return f"Error analyzing image: {str(e)}"

def fetch_url_content(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        return response.text[:10000]
    except Exception as e: return f"Error fetching URL: {str(e)}"

# --- MAD ENGINE LOGIC ---
class MADEngine:
    def __init__(self, gemini_key: str):
        self.gemini_key = gemini_key
        if gemini_key: genai.configure(api_key=gemini_key)
    
    def call_creator(self, prompt: str, previous_feedback: str = "", context: str = "") -> str:
        try:
            if not self.gemini_key: return "Error: Gemini API key not configured"
            context_str = f"Additional Context from Files/URLs:\n{context}\n" if context else ""
            feedback_str = f"Previous Critic Feedback: {previous_feedback}" if previous_feedback else ""
            full_prompt = f"""You are the CREATOR agent in a Multi-Agent Debate system.
            Role: Generate high-quality marketing content/analysis.
            Task: {prompt}
            {context_str}
            {feedback_str}
            IMPORTANT: Use markdown structure (##, ###). Be specific and data-driven."""
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = model.generate_content(full_prompt)
            return response.text
        except Exception as e: return f"Creator Error: {str(e)}"
    
    def call_critic(self, creator_output: str, original_prompt: str) -> Dict[str, any]:
        try:
            if not self.gemini_key: return {"approved": False, "feedback": "Error: Key missing"}
            critic_prompt = f"""You are the CRITIC agent.
            Original Task: {original_prompt}
            Creator's Output: {creator_output}
            Evaluate for completeness, accuracy, and formatting.
            Respond in JSON: {{ "approved": true/false, "score": 0-100, "feedback": "...", "strengths": [], "weaknesses": [] }}"""
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = model.generate_content(critic_prompt)
            return json.loads(response.text.strip().replace('json', '').replace('```', ''))
        except: return {"approved": True, "score": 75, "feedback": "Auto-approved due to parsing error."}
    
    def solve_task(self, task: str, max_rounds: int = 3, context: str = "") -> Dict:
        debate_history = []
        creator_output = ""
        for round_num in range(1, max_rounds + 1):
            feedback = debate_history[-1]['feedback'] if debate_history else ""
            creator_output = self.call_creator(task, feedback, context)
            debate_history.append({"round": round_num, "role": "creator", "content": creator_output})
            critic_result = self.call_critic(creator_output, task)
            debate_history.append({"round": round_num, "role": "critic", "content": f"Score: {critic_result.get('score', 0)}\n{critic_result.get('feedback', '')}", "feedback": critic_result.get('feedback', ''), "approved": critic_result.get('approved', False), "score": critic_result.get('score', 0)})
            if critic_result.get('approved', False) and critic_result.get('score', 0) >= 80:
                return {"final_answer": creator_output, "rounds_used": round_num, "approved": True, "debate_history": debate_history, "final_score": critic_result.get('score', 0)}
        return {"final_answer": creator_output, "rounds_used": max_rounds, "approved": False, "debate_history": debate_history, "final_score": critic_result.get('score', 0)}

    def chat_response(self, user_message: str, conversation_history: List[Dict], analysis_context: str = "") -> str:
        try:
            chat_context = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in conversation_history[-5:]])
            prompt = f"Context: {analysis_context}\nHistory: {chat_context}\nUser: {user_message}\nProvide a helpful, short response."
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            return model.generate_content(prompt).text
        except: return "I'm having trouble connecting right now."

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    # Header
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; padding-bottom: 20px; border-bottom: 1px solid #e7e5e4;">
        <div style="width: 36px; height: 36px; background: #e0f2fe; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #14b8a6; font-size: 20px;">⚡</div>
        <div>
            <div style="font-weight: 700; font-size: 16px; color: #1a1f2e;">MarketingOS</div>
            <div style="font-size: 11px; color: #57534e;">Enterprise Edition</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Status
    status_color = "#10b981" if st.session_state.gemini_key else "#ef4444"
    st.markdown(f"""
    <div style="margin-top: 15px; display: flex; align-items: center; gap: 8px; font-size: 12px; color: #57534e;">
        <div style="width: 8px; height: 8px; background-color: {status_color}; border-radius: 50%;"></div>
        System Status: {'Online' if st.session_state.gemini_key else 'Key Missing'}
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">PLAYBOOKS</div>', unsafe_allow_html=True)
    playbook_selection = st.selectbox("Playbook", ["None", "Product Launch", "SaaS Free Trial", "Webinar Promotion", "Seasonal Sale"], label_visibility="collapsed")
    
    # Playbook Logic
    if playbook_selection != st.session_state.playbook:
        st.session_state.playbook = playbook_selection
        if playbook_selection == "Product Launch":
            st.session_state.project_name = "New Product Launch"
            st.session_state.project_goal = "Drive awareness and signups (4-8 weeks)."
        elif playbook_selection == "SaaS Free Trial":
            st.session_state.project_name = "SaaS Trial Campaign"
            st.session_state.project_goal = "Increase free trial signups and activation."
        st.rerun()

    st.markdown('<div class="sidebar-section">BRAND & PROJECT</div>', unsafe_allow_html=True)
    st.session_state.brand_name = st.text_input("Brand Name", st.session_state.brand_name, placeholder="e.g. Acme Corp")
    st.session_state.brand_voice = st.text_input("Brand Voice", st.session_state.brand_voice, placeholder="e.g. Professional, Witty")
    st.session_state.project_name = st.text_input("Project Name", st.session_state.project_name, placeholder="Campaign Title")
    st.session_state.project_goal = st.text_input("Main Goal", st.session_state.project_goal, placeholder="What's success look like?")

    st.markdown('<div class="sidebar-section">AI AGENTS</div>', unsafe_allow_html=True)
    
    # Handle Agent Selection from Strategy Pipeline or Manual
    agent_list = ["Audit", "PPC", "SEO", "Social", "Research", "Copy", "Strategy"]
    default_idx = 0
    if st.session_state.target_agent and st.session_state.target_agent in agent_list:
        default_idx = agent_list.index(st.session_state.target_agent)
        st.session_state.target_agent = None 
        
    selected_agent = option_menu(
        None, agent_list,
        icons=["clipboard-data", "currency-dollar", "search", "instagram", "globe", "pencil-square", "diagram-3"],
        menu_icon="cast", default_index=default_idx,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#14b8a6", "font-size": "14px"}, 
            "nav-link": {"font-size": "14px", "text-align": "left", "margin": "2px 0", "padding": "8px 12px", "color": "#57534e"},
            "nav-link-selected": {"background-color": "#f0fdfa", "color": "#0f766e", "font-weight": "600", "border-left": "3px solid #14b8a6"}
        }
    )

    st.markdown('<div class="sidebar-section">CONTEXT</div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["📄 Docs", "🖼 Images", "🌐 URL"])
    with tab1:
        uf = st.file_uploader("Docs", type=['pdf','docx','txt'], accept_multiple_files=True, label_visibility="collapsed")
        if uf: st.session_state.uploaded_files = uf
    with tab2:
        ui = st.file_uploader("Images", type=['png','jpg'], accept_multiple_files=True, label_visibility="collapsed")
        if ui: st.session_state.uploaded_images = ui
    with tab3:
        url_in = st.text_input("URL", placeholder="https://...", label_visibility="collapsed")
        if url_in and st.button("Link"):
            st.session_state.url_context = fetch_url_content(url_in)
            st.success("Linked!")

    st.markdown("---")
    with st.expander("System Keys"):
        st.session_state.gemini_key = st.text_input("Gemini API Key", st.session_state.gemini_key, type="password")
        st.session_state.perplexity_key = st.text_input("Perplexity API Key", st.session_state.perplexity_key, type="password")

# --- MAIN LAYOUT ---
# 3 Columns: Main Content (3) | Chat (1.2)
c_main, c_chat = st.columns([3, 1.2])

with c_main:
    # 1. Header
    st.markdown(f'<div class="agent-title">{selected_agent} Agent</div>', unsafe_allow_html=True)
    
    # 2. Context Summary
    file_context = ""
    # Brand Context
    if st.session_state.brand_name:
        file_context += f"BRAND CONTEXT:\nName: {st.session_state.brand_name}\nVoice: {st.session_state.brand_voice}\nGoal: {st.session_state.project_goal}\n"
    
    # Attached Files
    if st.session_state.uploaded_files or st.session_state.uploaded_images or st.session_state.url_context:
        badge_html = '<div style="display:flex; gap:6px; margin-bottom:16px;">'
        if st.session_state.uploaded_files:
            badge_html += f'<span class="status-badge">📄 {len(st.session_state.uploaded_files)} File(s)</span>'
            for f in st.session_state.uploaded_files:
                if "pdf" in f.type: file_context += extract_text_from_pdf(f)
                elif "document" in f.type: file_context += extract_text_from_docx(f)
                else: file_context += extract_text_from_txt(f)
        if st.session_state.uploaded_images:
            badge_html += f'<span class="status-badge">🖼 {len(st.session_state.uploaded_images)} Image(s)</span>'
            for img in st.session_state.uploaded_images:
                analysis = analyze_image_with_gemini(img, "Describe this image for marketing purposes.")
                file_context += f"\nIMAGE ANALYSIS: {analysis}\n"
        if st.session_state.url_context:
            badge_html += '<span class="status-badge">🌐 URL Linked</span>'
            file_context += f"\nURL CONTENT: {st.session_state.url_context}\n"
        badge_html += '</div>'
        st.markdown(badge_html, unsafe_allow_html=True)

    # 3. Agent Interfaces
    final_output = None
    engine = MADEngine(st.session_state.gemini_key)

    if selected_agent == "Audit":
        st.markdown("""<div class="ui-card"><div class="card-header">🏆 GA4 & GTM Auditor</div>
        <div class="card-desc">Comprehensive analysis of Google Analytics 4 and Google Tag Manager configurations.</div>""", unsafe_allow_html=True)
        inp = st.text_area("GA4/GTM Configuration Details", height=150, placeholder="Paste your tracking setup or data layer details here...")
        st.markdown("</div>", unsafe_allow_html=True) # Close card manually if needed or just stacking
        if st.button("🔍 Run Audit", type="primary"):
            with st.spinner("Auditing..."):
                task = f"Audit this GA4/GTM setup:\n{inp}\nContext:\n{file_context}"
                final_output = engine.solve_task(task)

    elif selected_agent == "PPC":
        st.markdown("""<div class="ui-card"><div class="card-header">💰 PPC Optimizer</div>
        <div class="card-desc">Analyze and optimize pay-per-click campaigns for better ROI.</div>""", unsafe_allow_html=True)
        val = st.session_state.ppc_prefill if st.session_state.ppc_prefill else ""
        if val: st.session_state.ppc_prefill = "" 
        inp = st.text_area("Campaign Data", value=val, height=150, placeholder="Paste campaign metrics, structure, or keywords...")
        st.markdown("</div>", unsafe_allow_html=True)
        if st.button("📊 Analyze PPC", type="primary"):
            with st.spinner("Optimizing..."):
                task = f"Analyze PPC data:\n{inp}\nContext:\n{file_context}"
                final_output = engine.solve_task(task)

    elif selected_agent == "SEO":
        st.markdown("""<div class="ui-card"><div class="card-header">🔍 SEO Planner</div>
        <div class="card-desc">Develop comprehensive SEO strategies and keyword plans.</div>""", unsafe_allow_html=True)
        val = st.session_state.seo_prefill if st.session_state.seo_prefill else ""
        if val: st.session_state.seo_prefill = ""
        inp = st.text_area("Keywords / Topic", value=val, height=150, placeholder="Target keywords or content topics...")
        st.markdown("</div>", unsafe_allow_html=True)
        if st.button("🎯 Plan SEO", type="primary"):
            with st.spinner("Planning..."):
                task = f"Create SEO strategy for:\n{inp}\nContext:\n{file_context}"
                final_output = engine.solve_task(task)

    elif selected_agent == "Social":
        st.markdown("""<div class="ui-card"><div class="card-header">📱 Social Media Manager</div>
        <div class="card-desc">Generate content calendars and engagement strategies.</div>""", unsafe_allow_html=True)
        val = st.session_state.social_prefill if st.session_state.social_prefill else ""
        if val: st.session_state.social_prefill = ""
        c1, c2 = st.columns(2)
        with c1: niche = st.text_input("Niche", value=val, placeholder="e.g. B2B SaaS")
        with c2: platforms = st.multiselect("Platforms", ["LinkedIn", "Twitter", "Instagram", "TikTok"])
        st.markdown("</div>", unsafe_allow_html=True)
        if st.button("📅 Generate Calendar", type="primary"):
            with st.spinner("Generating..."):
                task = f"Create social media calendar for {niche} on {', '.join(platforms)}.\nContext:\n{file_context}"
                final_output = engine.solve_task(task)

    elif selected_agent == "Research":
        st.markdown("""<div class="ui-card"><div class="card-header">🌍 Deep Researcher</div>
        <div class="card-desc">Deep dive into market trends using web search.</div>""", unsafe_allow_html=True)
        topic = st.text_input("Research Topic", placeholder="Enter a market or topic...")
        use_perp = st.checkbox("Use Perplexity (if key available)", value=True)
        st.markdown("</div>", unsafe_allow_html=True)
        if st.button("🔎 Research", type="primary"):
            with st.spinner("Researching..."):
                web_data = ""
                if use_perp and st.session_state.perplexity_key and topic:
                    try:
                        url = "https://api.perplexity.ai/chat/completions"
                        headers = {"Authorization": f"Bearer {st.session_state.perplexity_key}", "Content-Type": "application/json"}
                        r = requests.post(url, json={"model": "sonar-pro", "messages": [{"role":"user","content":topic}]}, headers=headers)
                        web_data = r.json()['choices'][0]['message']['content']
                    except: web_data = "Perplexity Error"
                elif topic:
                    web_data = str(DDGS().text(topic, max_results=5))
                
                task = f"Research report on: {topic}\nWeb Data: {web_data}\nContext: {file_context}"
                final_output = engine.solve_task(task)

    elif selected_agent == "Copy":
        st.markdown("""<div class="ui-card"><div class="card-header">✍ AI Copywriter</div>
        <div class="card-desc">Rewrite content for specific tones and goals.</div>""", unsafe_allow_html=True)
        val = st.session_state.copy_prefill if st.session_state.copy_prefill else ""
        if val: st.session_state.copy_prefill = ""
        txt = st.text_area("Draft Text", value=val, height=150)
        style = st.selectbox("Style", ["Persuasive", "Professional", "Casual", "Urgent"])
        st.markdown("</div>", unsafe_allow_html=True)
        if st.button("✨ Rewrite", type="primary"):
            with st.spinner("Writing..."):
                task = f"Rewrite in {style} style:\n{txt}\nContext:\n{file_context}"
                res = engine.call_creator(task)
                final_output = {"final_answer": res, "rounds_used": 1, "approved": True, "final_score": 90}

    elif selected_agent == "Strategy":
        st.markdown("""<div class="ui-card"><div class="card-header">🧩 Strategy Architect</div>
        <div class="card-desc">Build comprehensive GTM and marketing strategies.</div>""", unsafe_allow_html=True)
        
        # Determine goal (Priority: Input Field > Session Strategy Goal > Session Project Goal)
        default_goal = st.session_state.get('strategy_goal', st.session_state.project_goal)
        goal = st.text_input("Primary Goal", value=default_goal, placeholder="e.g. Launch new feature to 10k users")
        st.session_state.strategy_goal = goal # Sync back
        
        st.markdown("</div>", unsafe_allow_html=True)
        if st.button("🚀 Build Strategy", type="primary"):
            with st.spinner("Architecting..."):
                task = f"Build comprehensive strategy for: {goal}\nContext:\n{file_context}"
                final_output = engine.solve_task(task)

    # 4. Result Display Logic
    if final_output:
        st.session_state.current_analysis = final_output
    
    if st.session_state.current_analysis:
        data = st.session_state.current_analysis
        st.markdown("---")
        
        # Strategy Pipeline Buttons (if Strategy Agent)
        if selected_agent == "Strategy":
            st.markdown("### Use this strategy in other agents:")
            col_p1, col_p2, col_p3, col_p4 = st.columns(4)
            if col_p1.button("→ SEO"):
                st.session_state.seo_prefill = data['final_answer']
                st.session_state.target_agent = "SEO"
                st.rerun()
            if col_p2.button("→ PPC"):
                st.session_state.ppc_prefill = data['final_answer']
                st.session_state.target_agent = "PPC"
                st.rerun()
            if col_p3.button("→ Social"):
                st.session_state.social_prefill = data['final_answer']
                st.session_state.target_agent = "Social"
                st.rerun()
            if col_p4.button("→ Copy"):
                st.session_state.copy_prefill = data['final_answer']
                st.session_state.target_agent = "Copy"
                st.rerun()
            st.markdown("---")

        # Report Card
        st.markdown(f"""
        <div class="ui-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                <div class="card-header" style="margin:0;">📋 Final Analysis</div>
                <div class="status-badge">Score: {data.get('final_score', 'N/A')}/100</div>
            </div>
            <div style="font-size: 0.95rem; line-height: 1.6;">
                {clean_markdown(data['final_answer']).replace(chr(10), '<br>')}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Download
        st.download_button("📥 Download Report", data['final_answer'], "report.md")

        # Debate History Toggle
        with st.expander("🔍 View Debate History"):
            for entry in data.get('debate_history', []):
                role_icon = "🔵" if entry['role'] == "creator" else "🔴"
                st.markdown(f"**{role_icon} {entry['role'].upper()}**")
                st.info(entry['content'])

# --- CHAT PANEL (Right Column) ---
with c_chat:
    if st.session_state.current_analysis:
        st.markdown("""<div style="padding:10px; border-bottom:1px solid #e7e5e4; font-weight:600; color:#1a1f2e;">💬 Conversation</div>""", unsafe_allow_html=True)
        
        # Chat container (Scrollable area simulation)
        chat_container = st.container()
        
        # Input at bottom (Streamlit standard behavior is fixed bottom, we use chat_input)
        user_input = st.chat_input("Ask about the analysis...")
        
        with chat_container:
            # Display messages
            if not st.session_state.chat_messages:
                 st.markdown("<div style='text-align:center; color:#a8a29e; font-size:0.9rem; margin-top:20px;'>Start a conversation contextually linked to the analysis.</div>", unsafe_allow_html=True)
            
            for msg in st.session_state.chat_messages:
                cls = "user-bubble" if msg['role'] == "user" else "agent-bubble"
                st.markdown(f'<div class="chat-container"><div class="chat-bubble {cls}">{msg["content"]}</div></div>', unsafe_allow_html=True)

        # Logic
        if user_input:
            st.session_state.chat_messages.append({"role": "user", "content": user_input})
            st.rerun()

        # Generate Response (Check if last message was user)
        if st.session_state.chat_messages and st.session_state.chat_messages[-1]["role"] == "user":
            with st.spinner("Thinking..."):
                try:
                    eng = MADEngine(st.session_state.gemini_key)
                    resp = eng.chat_response(
                        st.session_state.chat_messages[-1]["content"], 
                        st.session_state.chat_messages, 
                        st.session_state.current_analysis['final_answer']
                    )
                    st.session_state.chat_messages.append({"role": "assistant", "content": resp})
                    st.rerun()
                except Exception as e: st.error(f"Chat Error: {e}")
    else:
        # Empty State for Chat
        st.markdown("""
        <div style="height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #a8a29e; text-align: center; padding: 20px;">
            <div style="font-size: 40px; margin-bottom: 10px;">💬</div>
            <div style="font-size: 14px;">Run an analysis to start the conversation assistant.</div>
        </div>
        """, unsafe_allow_html=True)
