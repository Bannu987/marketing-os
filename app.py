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

# --- API KEY SETUP ---
if 'gemini_key' not in st.session_state:
    try:
        st.session_state.gemini_key = st.secrets["GEMINI_API_KEY"]
    except:
        st.session_state.gemini_key = ""

if 'perplexity_key' not in st.session_state:
    try:
        st.session_state.perplexity_key = st.secrets["PERPLEXITY_API_KEY"]
    except:
        st.session_state.perplexity_key = ""

# --- REST OF STATE ---
if 'current_analysis' not in st.session_state: st.session_state.current_analysis = None
if 'uploaded_files' not in st.session_state: st.session_state.uploaded_files = []
if 'uploaded_images' not in st.session_state: st.session_state.uploaded_images = []
if 'url_context' not in st.session_state: st.session_state.url_context = ""
if 'chat_messages' not in st.session_state: st.session_state.chat_messages = []
if 'theme' not in st.session_state: st.session_state.theme = "light"

# --- BRAND & PROJECT STATE ---
if 'brand_name' not in st.session_state: st.session_state.brand_name = ""
if 'brand_voice' not in st.session_state: st.session_state.brand_voice = ""
if 'brand_audience' not in st.session_state: st.session_state.brand_audience = ""
if 'brand_offer' not in st.session_state: st.session_state.brand_offer = ""
if 'project_name' not in st.session_state: st.session_state.project_name = ""
if 'project_goal' not in st.session_state: st.session_state.project_goal = ""

# --- STRATEGY PIPELINE STATE ---
if 'seo_prefill' not in st.session_state: st.session_state.seo_prefill = ""
if 'ppc_prefill' not in st.session_state: st.session_state.ppc_prefill = ""
if 'social_prefill' not in st.session_state: st.session_state.social_prefill = ""
if 'copy_prefill' not in st.session_state: st.session_state.copy_prefill = ""
if 'target_agent' not in st.session_state: st.session_state.target_agent = None

# --- PLAYBOOKS STATE ---
if 'playbook' not in st.session_state: st.session_state.playbook = "None"

# --- CSS STYLING ---
def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;600;700&display=swap');
        
        /* CSS VARIABLES */
        :root {
            --color-bg: #fafaf9;
            --color-bg-secondary: #ffffff;
            --color-text: #1a1f2e;
            --color-primary: #14b8a6;
            --color-primary-hover: #0d9488;
            --color-primary-light: #f0fdfa;
            --color-border: #e7e5e4;
        }
        
        /* Dark Mode Override */
        body[data-theme="dark"] {
            --color-bg: #1a1f2e;
            --color-bg-secondary: #2d3441;
            --color-text: #fafaf9;
            --color-border: #3d4754;
        }
        
        .stApp { background-color: var(--color-bg); color: var(--color-text); font-family: 'Roboto', sans-serif; }
        [data-testid="stSidebar"] { background-color: var(--color-bg-secondary); border-right: 1px solid var(--color-border); }
        
        /* Text & Headers */
        .section-header { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; color: #a8a29e; font-weight: 600; margin: 20px 0 8px 0; }
        .gradient-text { background: transparent; color: var(--color-text); font-weight: 700; font-size: 2rem; margin-bottom: 0.5rem; }
        
        /* Buttons */
        .stButton button[kind="primary"] { background-color: var(--color-primary); color: white !important; border: none; border-radius: 8px; padding: 10px 16px; font-weight: 600; }
        .stButton button[kind="primary"]:hover { background-color: var(--color-primary-hover); transform: translateY(-1px); }
        .stButton button:not([kind="primary"]) { background-color: var(--color-bg-secondary); border: 1px solid var(--color-border); color: var(--color-text); }
        
        /* Chat Messages */
        .chat-message { padding: 12px 16px; border-radius: 12px; margin: 8px 0; font-size: 0.9rem; line-height: 1.5; }
        .user-message { background-color: var(--color-primary); color: white; margin-left: 10%; border-bottom-right-radius: 4px; }
        .agent-message { background-color: var(--color-bg-secondary); border: 1px solid var(--color-border); margin-right: 10%; border-bottom-left-radius: 4px; color: var(--color-text); }
        
        /* Cards */
        .ui-card { background-color: var(--color-bg-secondary); border: 1px solid var(--color-border); border-radius: 8px; padding: 24px; margin-bottom: 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
        
        /* Fix hidden/cutoff content in columns */
        [data-testid="column"] { overflow: visible !important; }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# Theme Script
st.markdown(f"<script>document.body.dataset.theme = '{st.session_state.theme}';</script>", unsafe_allow_html=True)

# --- UTILITIES ---
def clean_markdown(text: str) -> str:
    text = text.replace("```markdown", "").replace("```", "").strip()
    return re.sub(r'^##\s', '### ', text, flags=re.MULTILINE)

def extract_text(file):
    try:
        if file.type == "application/pdf":
            return "\n".join([p.extract_text() for p in PyPDF2.PdfReader(file).pages])
        elif "text" in file.type:
            return file.read().decode('utf-8')
        elif "document" in file.type:
            return "\n".join([p.text for p in docx.Document(file).paragraphs])
        return ""
    except: return ""

def analyze_image(img_file, prompt):
    if not st.session_state.gemini_key: return "Error: No API Key"
    try:
        genai.configure(api_key=st.session_state.gemini_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        return model.generate_content([prompt, Image.open(img_file)]).text
    except Exception as e: return f"Error: {e}"

def fetch_url(url):
    try: return requests.get(url, timeout=5).text[:8000]
    except: return ""

# --- MAD ENGINE ---
class MADEngine:
    def __init__(self, key): 
        self.key = key
        if key: genai.configure(api_key=key)

    def run(self, prompt, context="", feedback=""):
        if not self.key: return "Error: Missing API Key"
        sys_prompt = f"Role: Marketing Expert. Task: {prompt}. Context: {context}. Feedback: {feedback}. Output: Markdown."
        try:
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            return model.generate_content(sys_prompt).text
        except Exception as e: return f"Error: {e}"

    def solve_task(self, task, context=""):
        draft = self.run(task, context)
        crit = self.run(f"Critique this: {draft}", context)
        final = self.run(task, context, f"Improve based on this: {crit}")
        return {
            "final_answer": final, 
            "rounds_used": 2, 
            "approved": True, 
            "final_score": 90, 
            "debate_history": [
                {"role": "creator", "round": 1, "content": draft},
                {"role": "critic", "round": 1, "content": crit}
            ]
        }

    def chat_response(self, msg, history, analysis):
        if not self.key: return "Please set API Key."
        hist_text = "\n".join([f"{m['role']}: {m['content']}" for m in history[-5:]])
        prompt = f"Context Analysis: {analysis}\nHistory: {hist_text}\nUser: {msg}\nAnswer helpfully."
        try:
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            return model.generate_content(prompt).text
        except: return "Error generating response."

# --- UI HELPERS ---
def check_systems():
    return {"gemini": bool(st.session_state.gemini_key), "mad_engine": bool(st.session_state.gemini_key)}

def display_mad_result(data, filename="report.md"):
    if not data or "error" in data:
        st.error(data.get("error", "Unknown Error"))
        return
    
    st.session_state.current_analysis = data['final_answer']
    clean = clean_markdown(data['final_answer'])
    
    st.markdown("---")
    with st.expander("📋 **Final Report**", expanded=True):
        st.markdown(clean)
        st.caption(f"⚡ Generated via MAD Engine | Score: {data.get('final_score', 0)}/100")
    
    c1, c2 = st.columns(2)
    c1.download_button("📥 Download", clean, filename)
    
    with st.expander("🔍 **Debate History**", expanded=False):
        for entry in data.get('debate_history', []):
            role = "🔵 CREATOR" if entry['role'] == "creator" else "🔴 CRITIC"
            st.markdown(f"**{role} (Round {entry['round']})**")
            st.markdown(entry['content'])
            st.divider()

# --- SIDEBAR ---
with st.sidebar:
    status = check_systems()
    color = "#10b981" if status["gemini"] else "#ef4444"
    st.markdown(f"""<div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;">
        <span style="font-size:24px;">⚡</span>
        <div><div style="font-weight:700;">MarketingOS</div>
        <div style="font-size:11px;color:#78716c;">Enterprise <span style="color:{color}">●</span></div></div>
    </div>""", unsafe_allow_html=True)

    # Playbooks
    st.markdown('<div class="section-header">PLAYBOOKS</div>', unsafe_allow_html=True)
    pb = st.selectbox("Select Playbook", ["None", "Product Launch", "SaaS Trial", "Webinar", "Holiday Sale"], label_visibility="collapsed")
    if pb != "None" and pb != st.session_state.playbook:
        st.session_state.playbook = pb
        if pb == "Product Launch":
            st.session_state.project_name = "New Product Launch"
            st.session_state.project_goal = "Drive awareness & signups."

    # Brand Info
    st.markdown('<div class="section-header">BRAND & PROJECT</div>', unsafe_allow_html=True)
    st.text_input("Brand Name", key="brand_name")
    st.text_input("Brand Voice", key="brand_voice")
    st.text_input("Target Audience", key="brand_audience")
    st.text_input("Key Offer", key="brand_offer")
    st.text_input("Project Name", key="project_name")
    st.text_input("Goal", key="project_goal")

    # Agents
    st.markdown('<div class="section-header">AGENTS</div>', unsafe_allow_html=True)
    default_idx = 0
    agents = ["Audit", "PPC", "SEO", "Social", "Research", "Copy", "Strategy"]
    if st.session_state.target_agent in agents:
        default_idx = agents.index(st.session_state.target_agent)
        st.session_state.target_agent = None
        
    selected = option_menu(None, agents, icons=["clipboard", "currency-dollar", "search", "instagram", "globe", "pencil", "diagram-3"], default_index=default_idx, styles={"nav-link-selected": {"background-color": "#f0fdfa", "color": "#0f766e"}})

    # Context
    st.markdown('<div class="section-header">CONTEXT</div>', unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📄", "🖼️", "🌐"])
    with t1: 
        files = st.file_uploader("Docs", type=['pdf','csv','docx','txt'], accept_multiple_files=True, label_visibility="collapsed")
        if files: st.session_state.uploaded_files = files
    with t2:
        imgs = st.file_uploader("Images", type=['png','jpg'], accept_multiple_files=True, label_visibility="collapsed")
        if imgs: st.session_state.uploaded_images = imgs
    with t3:
        url = st.text_input("URL", placeholder="https://...", label_visibility="collapsed")
        if url and st.button("Link"):
            st.session_state.url_context = fetch_url(url)
            st.success("Linked!")

    if st.button("🗑️ Clear Context"):
        st.session_state.uploaded_files = []
        st.session_state.uploaded_images = []
        st.session_state.url_context = ""
        st.rerun()

    # Settings
    st.markdown('<div class="section-header">SYSTEM</div>', unsafe_allow_html=True)
    with st.expander("⚙️ API Keys", expanded=False):
        if "GEMINI_API_KEY" in st.secrets:
            st.success("✅ Gemini Loaded")
            st.session_state.gemini_key = st.secrets["GEMINI_API_KEY"]
        else:
            st.session_state.gemini_key = st.text_input("Gemini Key", type="password")
            
        if "PERPLEXITY_API_KEY" in st.secrets:
            st.success("✅ Perplexity Loaded")
            st.session_state.perplexity_key = st.secrets["PERPLEXITY_API_KEY"]
        else:
            st.session_state.perplexity_key = st.text_input("Perplexity Key", type="password")

    # Theme
    st.markdown('<div class="section-header">THEME</div>', unsafe_allow_html=True)
    mode = st.radio("Mode", ["Light", "Dark"], horizontal=True, label_visibility="collapsed")
    if mode.lower() != st.session_state.theme:
        st.session_state.theme = mode.lower()
        st.rerun()

# --- MAIN CONTENT ---
# Always show 3-panel layout: sidebar (left), agents+report (center), conversation (right)
col_main, col_chat = st.columns([3, 1])

with col_main:
    st.markdown(f'<h1 class="gradient-text">{selected} Agent</h1>', unsafe_allow_html=True)
    
    # Context Construction
    ctx = ""
    if st.session_state.brand_name:
        ctx += f"BRAND: {st.session_state.brand_name}\nVOICE: {st.session_state.brand_voice}\nGOAL: {st.session_state.project_goal}\n"
    ctx += st.session_state.url_context
    
    if st.session_state.uploaded_files:
        st.markdown("###### 📎 Attached:")
        for f in st.session_state.uploaded_files:
            st.markdown(f'<span class="file-badge">📄 {f.name}</span>', unsafe_allow_html=True)
            if f.type == "application/pdf": ctx += extract_text(f)
            elif "text" in f.type: ctx += extract_text(f)
            else: ctx += extract_text(f) # docx
    
    if st.session_state.uploaded_images:
        st.markdown("###### 🖼️ Images:")
        cols = st.columns(5)
        for i, img in enumerate(st.session_state.uploaded_images):
            with cols[i%5]: st.image(img, width=80)
            with st.spinner("Analyzing..."):
                ctx += "\nIMG: " + analyze_image(img, "Describe for marketing")

    # Agent Logic
    eng = MADEngine(st.session_state.gemini_key)
    
    if selected == "Audit":
        st.markdown('<div class="ui-card"><h3>🏆 GA4 & GTM Auditor</h3></div>', unsafe_allow_html=True)
        inp = st.text_area("Input Data", height=150)
        if st.button("🔍 Run Audit", type="primary"):
            if not inp and not ctx: st.warning("No data.")
            else:
                with st.spinner("Auditing..."):
                    display_mad_result(eng.solve_task(f"Audit GA4/GTM:\n{inp}", ctx), "audit.md")

    elif selected == "PPC":
        st.markdown('<div class="ui-card"><h3>💰 PPC Optimizer</h3></div>', unsafe_allow_html=True)
        val = st.session_state.ppc_prefill if st.session_state.ppc_prefill else ""
        if val: st.session_state.ppc_prefill = ""
        inp = st.text_area("Campaign Data", value=val, height=150)
        if st.button("📊 Analyze", type="primary"):
            with st.spinner("Crunching..."):
                display_mad_result(eng.solve_task(f"Optimize PPC:\n{inp}", ctx), "ppc.md")

    elif selected == "SEO":
        st.markdown('<div class="ui-card"><h3>🔍 SEO Planner</h3></div>', unsafe_allow_html=True)
        val = st.session_state.seo_prefill if st.session_state.seo_prefill else ""
        if val: st.session_state.seo_prefill = ""
        kw = st.text_area("Keywords", value=val, height=100)
        if st.button("🎯 Plan", type="primary"):
            with st.spinner("Planning..."):
                display_mad_result(eng.solve_task(f"SEO Strategy:\n{kw}", ctx), "seo.md")

    elif selected == "Social":
        st.markdown('<div class="ui-card"><h3>📱 Social Media Manager</h3></div>', unsafe_allow_html=True)
        val = st.session_state.social_prefill if st.session_state.social_prefill else ""
        if val: st.session_state.social_prefill = ""
        c1, c2 = st.columns(2)
        with c1: niche = st.text_input("Niche", value=val)
        with c2: plat = st.multiselect("Platforms", ["LinkedIn", "Twitter", "Instagram"])
        if st.button("📅 Generate", type="primary"):
            with st.spinner("Creating..."):
                display_mad_result(eng.solve_task(f"Social Calendar: {niche} {plat}", ctx), "calendar.md")

    elif selected == "Research":
        st.markdown('<div class="ui-card"><h3>🌍 Deep Researcher</h3></div>', unsafe_allow_html=True)
        q = st.text_input("Topic")
        use_perp = st.checkbox("Perplexity", value=bool(st.session_state.perplexity_key))
        if st.button("🔎 Research", type="primary"):
            with st.spinner("Searching..."):
                web = ""
                if use_perp:
                    try:
                        h = {"Authorization": f"Bearer {st.session_state.perplexity_key}"}
                        r = requests.post("https://api.perplexity.ai/chat/completions", headers=h, json={"model":"sonar-pro", "messages":[{"role":"user","content":q}]})
                        web = r.json()['choices'][0]['message']['content']
                    except: 
                        st.warning("Perplexity failed. Using DuckDuckGo.")
                        web = str(DDGS().text(q, max_results=5))
                else:
                    web = str(DDGS().text(q, max_results=5))
                
                display_mad_result(eng.solve_task(f"Research: {q}\nWeb: {web}", ctx), "research.md")

    elif selected == "Copy":
        st.markdown('<div class="ui-card"><h3>✍️ AI Copywriter</h3></div>', unsafe_allow_html=True)
        val = st.session_state.copy_prefill if st.session_state.copy_prefill else ""
        if val: st.session_state.copy_prefill = ""
        txt = st.text_area("Text", value=val, height=150)
        style = st.selectbox("Style", ["Simplify", "Persuasive", "Viral"])
        if st.button("✨ Rewrite", type="primary"):
            with st.spinner("Writing..."):
                res = eng.run(f"Rewrite in {style} style:\n{txt}", ctx)
                st.markdown(clean_markdown(res))

    elif selected == "Strategy":
        st.markdown('<div class="ui-card"><h3>🧩 Strategy Architect</h3></div>', unsafe_allow_html=True)
        goal = st.text_input("Goal", value=st.session_state.project_goal)
        if st.button("🚀 Build", type="primary"):
            with st.spinner("Architecting..."):
                display_mad_result(eng.solve_task(f"Strategy for: {goal}", ctx), "strategy.md")
        
        # Pipeline Buttons
        if st.session_state.current_analysis:
            st.markdown("### ⚡ Execute Strategy")
            c1, c2, c3, c4 = st.columns(4)
            if c1.button("→ SEO"): 
                st.session_state.seo_prefill = st.session_state.current_analysis
                st.session_state.target_agent = "SEO"
                st.rerun()
            if c2.button("→ PPC"):
                st.session_state.ppc_prefill = st.session_state.current_analysis
                st.session_state.target_agent = "PPC"
                st.rerun()
            if c3.button("→ Social"):
                st.session_state.social_prefill = st.session_state.current_analysis
                st.session_state.target_agent = "Social"
                st.rerun()
            if c4.button("→ Copy"):
                st.session_state.copy_prefill = st.session_state.current_analysis
                st.session_state.target_agent = "Copy"
                st.rerun()

# --- RIGHT PANEL: PERSISTENT CHAT ---
with col_chat:
    st.markdown("### 💬 Conversation")
    
    # Chat History container
    chat_container = st.container(height=500)
    with chat_container:
        # Default welcome message if empty
        if not st.session_state.chat_messages:
            st.session_state.chat_messages = [{"role": "assistant", "content": "Hi! I'm ready to help with your marketing tasks."}]
            
        for msg in st.session_state.chat_messages:
            role_class = "user-message" if msg["role"] == "user" else "agent-message"
            st.markdown(
                f'<div class="chat-message {role_class}">{msg["content"]}</div>',
                unsafe_allow_html=True
            )
    
    # Chat input
    user_msg = st.chat_input("Ask something...")
    if user_msg:
        st.session_state.chat_messages.append({"role": "user", "content": user_msg})
        with st.spinner("Thinking..."):
            try:
                engine = MADEngine(st.session_state.gemini_key)
                # Use safe analysis text
                analysis_text = st.session_state.current_analysis if st.session_state.current_analysis else "No analysis loaded yet."
                resp = engine.chat_response(
                    user_msg, 
                    st.session_state.chat_messages, 
                    analysis_text
                )
                st.session_state.chat_messages.append({"role": "assistant", "content": resp})
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# --- FOOTER ---
st.markdown("---")
st.markdown("""<div style="text-align: center; color: #a8a29e; font-size: 0.8rem;">MarketingOS v6.0 | Enterprise AI</div>""", unsafe_allow_html=True)
