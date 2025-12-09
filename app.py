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

# --- SESSION STATE INITIALIZATION (Secure Load) ---
if 'history' not in st.session_state: st.session_state.history = []

# --- API KEY SETUP: LOADS SECRETS IMMEDIATELY ---
if 'gemini_key' not in st.session_state:
    try:
        # Tries to load from Streamlit Secrets or local secrets.toml
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
if 'chat_mode' not in st.session_state: st.session_state.chat_mode = False
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

# --- HYBRID AESTHETIC CSS ---
def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;600;700&display=swap');
        
        /* CSS VARIABLES - Light Mode (Default) */
        :root {
            --color-bg: #fafaf9;
            --color-bg-secondary: #ffffff;
            --color-text: #1a1f2e;
            --color-text-secondary: #57534e;
            --color-text-muted: #a8a29e;
            --color-primary: #14b8a6;
            --color-primary-hover: #0d9488;
            --color-primary-light: #f0fdfa;
            --color-primary-dark: #0f766e;
            --color-accent: #10b981;
            --color-error: #ef4444;
            --color-border: #e7e5e4;
            --color-border-hover: #d6d3d1;
            --color-card-bg: #ffffff;
            --color-card-border: #e7e5e4;
            --color-shadow: rgba(0, 0, 0, 0.05);
            --color-shadow-hover: rgba(0, 0, 0, 0.08);
            --color-primary-shadow: rgba(20, 184, 166, 0.2);
            --color-primary-shadow-hover: rgba(20, 184, 166, 0.3);
        }
        
        /* CSS VARIABLES - Dark Mode */
        body[data-theme="dark"] {
            --color-bg: #1a1f2e;
            --color-bg-secondary: #2d3441;
            --color-text: #fafaf9;
            --color-text-secondary: #d6d3d1;
            --color-text-muted: #a8a29e;
            --color-primary: #14b8a6;
            --color-primary-hover: #0d9488;
            --color-primary-light: #1a3d37;
            --color-primary-dark: #0f766e;
            --color-accent: #10b981;
            --color-error: #ef4444;
            --color-border: #3d4754;
            --color-border-hover: #4a5568;
            --color-card-bg: #2d3441;
            --color-card-border: #3d4754;
            --color-shadow: rgba(0, 0, 0, 0.3);
            --color-shadow-hover: rgba(0, 0, 0, 0.5);
            --color-primary-shadow: rgba(20, 184, 166, 0.3);
            --color-primary-shadow-hover: rgba(20, 184, 166, 0.4);
        }
        
        /* BASE */
        .stApp { background-color: var(--color-bg); color: var(--color-text); font-family: 'Roboto', sans-serif; }
        
        /* SIDEBAR */
        [data-testid="stSidebar"] { background-color: var(--color-bg-secondary); border-right: 1px solid var(--color-border); font-family: 'Roboto', sans-serif; }
        
        /* HEADERS & TEXT */
        .section-header { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; color: var(--color-text-muted); font-weight: 600; margin: 20px 0 8px 0; font-family: 'Roboto', sans-serif; }
        .gradient-text { background: transparent; -webkit-text-fill-color: var(--color-text); color: var(--color-text); font-weight: 700; font-size: 2rem; margin-bottom: 0.5rem; letter-spacing: -0.02em; font-family: 'Roboto', sans-serif; }
        
        /* BUTTONS */
        .stButton button[kind="primary"] { background-color: var(--color-primary); color: white !important; border: none; width: 100%; border-radius: 8px; padding: 10px 16px; font-weight: 600; font-size: 0.95rem; box-shadow: 0 2px 4px var(--color-primary-shadow); transition: all 0.2s ease; }
        .stButton button[kind="primary"]:hover { background-color: var(--color-primary-hover); box-shadow: 0 4px 12px var(--color-primary-shadow-hover); transform: translateY(-1px); }
        .stButton button:not([kind="primary"]) { background-color: var(--color-bg-secondary); color: var(--color-text); border: 1px solid var(--color-border); border-radius: 6px; font-weight: 500; padding: 10px 20px; transition: all 0.2s ease; }
        .stButton button:not([kind="primary"]):hover { border-color: var(--color-primary); color: var(--color-primary); }
        
        /* COMPONENTS */
        iframe[title="streamlit_option_menu.option_menu"] { margin-top: -10px; }
        .streamlit-expanderHeader { font-size: 0.9rem; color: var(--color-text-secondary); background-color: transparent; border: none; }
        [data-testid="stFileUploader"] { border: 1px dashed var(--color-border); padding: 10px; border-radius: 8px; background-color: var(--color-bg-secondary); }
        
        /* CARDS */
        .ui-card { background-color: var(--color-card-bg); border: 1px solid var(--color-card-border); border-radius: 8px; padding: 24px; margin-bottom: 16px; box-shadow: 0 1px 2px var(--color-shadow); transition: all 0.2s ease; }
        .ui-card:hover { box-shadow: 0 4px 12px var(--color-shadow-hover); border-color: var(--color-border-hover); transform: translateY(-1px); }
        
        /* STATUS & DEBATE */
        .status-badge { display: inline-flex; align-items: center; padding: 4px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: 500; background-color: var(--color-bg); border: 1px solid var(--color-border); color: var(--color-text-secondary); margin-right: 8px; font-family: 'Roboto', sans-serif; }
        .dot-online { width: 6px; height: 6px; background-color: var(--color-accent); border-radius: 50%; margin-right: 6px; }
        .dot-offline { width: 6px; height: 6px; background-color: var(--color-error); border-radius: 50%; margin-right: 6px; }
        .debate-creator { background-color: var(--color-primary-light); border-left: 3px solid var(--color-primary); padding: 12px 16px; margin: 8px 0; border-radius: 4px; font-size: 0.9em; }
        .debate-critic { background-color: rgba(239, 68, 68, 0.1); border-left: 3px solid var(--color-error); padding: 12px 16px; margin: 8px 0; border-radius: 4px; font-size: 0.9em; }
        
        /* INPUTS */
        .stTextArea textarea, .stTextInput input { border-radius: 6px; border: 1px solid var(--color-border); transition: border-color 0.2s ease; font-family: 'Roboto', sans-serif; background-color: var(--color-bg-secondary); color: var(--color-text); }
        .stTextArea textarea:focus, .stTextInput input:focus { border-color: var(--color-primary); box-shadow: 0 0 0 1px var(--color-primary); outline: none; }
        
        /* METRICS & TAGS */
        [data-testid="stMetricValue"] { color: var(--color-text); font-weight: 600; font-family: 'Roboto', sans-serif; }
        [data-baseweb="tag"] { background-color: var(--color-primary-light) !important; border: 1px solid var(--color-primary) !important; color: var(--color-primary-dark) !important; font-weight: 500; padding: 4px 12px; border-radius: 6px; font-family: 'Roboto', sans-serif; }
        [data-baseweb="tag"] svg { fill: var(--color-primary-hover) !important; }
        [data-baseweb="tag"]:hover { background-color: rgba(20, 184, 166, 0.2) !important; border-color: var(--color-primary-hover) !important; }
        
        /* CHAT MESSAGES */
        .chat-message { padding: 12px 16px; border-radius: 12px; margin: 8px 0; font-size: 0.95rem; line-height: 1.5; }
        .user-message { background-color: var(--color-primary); color: white; margin-left: 20%; border-bottom-right-radius: 4px; }
        .agent-message { background-color: var(--color-bg-secondary); border: 1px solid var(--color-border); margin-right: 20%; border-bottom-left-radius: 4px; color: var(--color-text); }
        .file-badge { display: inline-flex; align-items: center; gap: 6px; padding: 4px 8px; background-color: var(--color-primary-light); border: 1px solid var(--color-primary); border-radius: 4px; font-size: 0.8rem; color: var(--color-primary-dark); margin-right: 6px; margin-bottom: 6px; }
        
        /* MOBILE RESPONSIVENESS */
        @media (max-width: 768px) {
            /* Reduce font sizes and spacing for mobile */
            .gradient-text { 
                font-size: 1.5rem !important; 
                margin-bottom: 0.25rem !important; 
            }
            
            .section-header { 
                font-size: 0.65rem !important; 
                margin: 12px 0 6px 0 !important; 
            }
            
            .chat-message { 
                font-size: 0.85rem !important; 
                padding: 10px 12px !important; 
                margin: 6px 0 !important; 
            }
            
            p, .stMarkdown p { 
                font-size: 0.9rem !important; 
                line-height: 1.4 !important; 
            }
            
            /* Reduce padding on cards and sidebar */
            .ui-card { 
                padding: 16px !important; 
                margin-bottom: 12px !important; 
            }
            
            [data-testid="stSidebar"] { 
                padding: 1rem 0.75rem !important; 
            }
            
            /* Make image grid responsive - stack to 2 columns */
            /* Target columns container and make each column 50% width for mobile */
            [data-testid="column"] {
                flex: 0 0 50% !important;
                max-width: 50% !important;
                min-width: 50% !important;
            }
            
            /* Ensure images within columns are responsive */
            [data-testid="column"] img {
                max-width: 100% !important;
                height: auto !important;
            }
            
            /* Improve tap targets in sidebar */
            [data-testid="stSidebar"] [class*="nav-link"] {
                padding: 12px 12px !important;
                margin: 4px 0 !important;
                min-height: 44px !important;
            }
            
            /* Increase tap targets for tabs */
            [data-testid="stTabs"] button {
                padding: 10px 12px !important;
                min-height: 44px !important;
            }
            
            /* Adjust chat message margins for mobile */
            .user-message { 
                margin-left: 10% !important; 
            }
            
            .agent-message { 
                margin-right: 10% !important; 
            }
        }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# --- THEME SCRIPT INJECTION ---
theme = st.session_state.theme
st.markdown(f"""
<script>
document.body.dataset.theme = '{theme}';
</script>
""", unsafe_allow_html=True)

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
            
            IMPORTANT: You must follow the structure requested in the task text above. Use markdown headings (##, ###) for all required sections and include any requested markdown tables where specified. Be specific, actionable, and data-driven. Ensure all requested sections are clearly labeled and present in your response."""
            
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
            
            CRITICAL: Check if all requested sections and any requested tables mentioned in the Original Task are present and clearly labeled in the Creator's Output. If required sections or structure are missing or unclear, mark approved: false and lower the score significantly (below 70).
            
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
    
    # Optional full-screen chat button still available if needed
    if st.button("💬 Full Screen Chat", type="primary"):
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
    # Check system status for status dot
    status = check_systems()
    status_color = "#10b981" if (status["gemini"] and status["mad_engine"]) else "#ef4444"
    st.markdown(f"""<div style="padding:10px 0 20px 0; display:flex; align-items:center; gap:10px;"><div style="font-size:24px;">⚡</div><div style="flex:1;"><div style="display:flex; align-items:center; gap:8px;"><div style="font-weight:700; font-size:16px; color:#1a1f2e;">MarketingOS</div><div style="width:8px; height:8px; background-color:{status_color}; border-radius:50%;"></div></div><div style="font-size:11px; color:#78716c;">Enterprise Edition</div></div></div>""", unsafe_allow_html=True)
    
    # --- PLAYBOOKS SECTION ---
    st.markdown('<div class="section-header">PLAYBOOKS</div>', unsafe_allow_html=True)
    playbook_selection = st.selectbox("Playbook", ["None", "Product Launch", "SaaS Free Trial", "Webinar Promotion", "Seasonal Sale"], label_visibility="collapsed", key="playbook_select")
    st.session_state.playbook = playbook_selection
    
    # Apply playbook preset values BEFORE creating widgets (only if fields are empty)
    if st.session_state.playbook != "None":
        if st.session_state.playbook == "Product Launch":
            if not st.session_state.project_name:
                st.session_state.project_name = "New Product Launch"
            if not st.session_state.project_goal:
                st.session_state.project_goal = "Drive awareness and signups for a new product launch in the next 4–8 weeks."
        elif st.session_state.playbook == "SaaS Free Trial":
            if not st.session_state.project_name:
                st.session_state.project_name = "SaaS Free Trial Campaign"
            if not st.session_state.project_goal:
                st.session_state.project_goal = "Increase free trial signups and activations for the SaaS product."
        elif st.session_state.playbook == "Webinar Promotion":
            if not st.session_state.project_name:
                st.session_state.project_name = "Webinar Promotion"
            if not st.session_state.project_goal:
                st.session_state.project_goal = "Drive registrations and attendance for an upcoming webinar."
        elif st.session_state.playbook == "Seasonal Sale":
            if not st.session_state.project_name:
                st.session_state.project_name = "Seasonal Sale Campaign"
            if not st.session_state.project_goal:
                st.session_state.project_goal = "Boost revenue with a time-limited seasonal discount campaign."
    
    st.markdown('<div class="section-header">BRAND & PROJECT</div>', unsafe_allow_html=True)
    st.text_input("Brand Name", key="brand_name")
    st.text_input("Brand Voice / Tone", key="brand_voice")
    st.text_input("Ideal Customer / Audience", key="brand_audience")
    st.text_input("Key Offer / Product", key="brand_offer")
    st.text_input("Project / Campaign Name", key="project_name")
    st.text_input("Main Goal", key="project_goal")
    
    st.markdown('<div class="section-header">AI AGENTS</div>', unsafe_allow_html=True)
    # Determine default index based on target_agent (for Strategy pipeline navigation)
    agent_list = ["Audit", "PPC", "SEO", "Social", "Research", "Copy", "Strategy"]
    default_idx = 0
    if st.session_state.target_agent and st.session_state.target_agent in agent_list:
        default_idx = agent_list.index(st.session_state.target_agent)
        st.session_state.target_agent = None  # Clear after use
    selected = option_menu(None, agent_list, icons=["clipboard-data", "currency-dollar", "search", "instagram", "globe", "pencil-square", "diagram-3"], menu_icon="robot", default_index=default_idx, styles={"container": {"padding": "0!important", "background-color": "transparent"}, "icon": {"color": "#14b8a6", "font-size": "16px"}, "nav-link": {"font-size": "14px", "text-align": "left", "margin": "2px 0", "padding": "8px 12px", "color": "#57534e", "font-weight": "400"}, "nav-link-selected": {"background-color": "#f0fdfa", "color": "#0f766e", "font-weight": "600"}})
    
    st.markdown('<div class="section-header">CONTEXT</div>', unsafe_allow_html=True)
    st.caption("Shared context (docs, images, URLs) used by all agents.")
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
    
    # --- THEME TOGGLE ---
    st.markdown('<div class="section-header">THEME</div>', unsafe_allow_html=True)
    theme_option = st.radio("Theme", ["Light", "Dark"], index=0 if st.session_state.theme == "light" else 1, label_visibility="collapsed", horizontal=True)
    if theme_option == "Light" and st.session_state.theme != "light":
        st.session_state.theme = "light"
        st.rerun()
    elif theme_option == "Dark" and st.session_state.theme != "dark":
        st.session_state.theme = "dark"
        st.rerun()

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
    # Set up the main layout - two columns if chat panel is enabled and there's an analysis, otherwise single column
    if st.session_state.get('show_chat_panel', True) and st.session_state.current_analysis is not None:
        col_main, col_chat = st.columns([3, 1])
    else:
        col_main, = st.columns([1])  # Single column layout (Corrected Fix)
        col_chat = None  # No chat panel

    with col_main:
        st.markdown(f'<h1 class="gradient-text">{selected} Agent</h1>', unsafe_allow_html=True)
        
        # Process Context
        file_context = ""
        
        # Prepend Brand & Project Context if any fields are non-empty
        brand_fields = {
            "Brand Name": st.session_state.brand_name,
            "Brand Voice": st.session_state.brand_voice,
            "Ideal Customer": st.session_state.brand_audience,
            "Key Offer": st.session_state.brand_offer,
            "Project Name": st.session_state.project_name,
            "Main Goal": st.session_state.project_goal
        }
        
        if any(brand_fields.values()):
            brand_context = "BRAND & PROJECT CONTEXT\n"
            for key, value in brand_fields.items():
                if value:
                    brand_context += f"{key}: {value}\n"
            file_context = brand_context + "\n"
        
        file_context += st.session_state.url_context
        if st.session_state.uploaded_files:
            st.markdown("###### 📎 Attached Context:")
            badges = "".join([f'<span class="file-badge">📄 {f.name}</span>' for f in st.session_state.uploaded_files])
            st.markdown(badges, unsafe_allow_html=True)
            for f in st.session_state.uploaded_files:
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

        # --- AGENT INTERFACES ---
        if selected == "Audit":
            st.markdown('<div class="ui-card"><h3>🏆 GA4 & GTM Auditor</h3><p style="color: #78716c; font-size: 0.9rem; margin-top: -10px;">Comprehensive analysis of Google Analytics 4 and Google Tag Manager configurations, data quality, and tracking accuracy.</p></div>', unsafe_allow_html=True)
            st.caption("Provide your GA4, GTM, and key event tracking details. This agent returns a clear audit of tracking accuracy, gaps, and optimization opportunities.")
            inp = st.text_area("Input Data", height=150)
            if st.button("🔍 Run Audit", type="primary"):
                if not inp and not file_context: st.warning("Provide data.")
                else:
                    with st.spinner("Analyzing..."):
                        eng = MADEngine(st.session_state.gemini_key)
                        task = f"""Audit GA4/GTM data and provide a comprehensive analysis.

Input Data:
{inp}

Required Structure:
- ## Overview
- ## Tracking Issues
- ## Data Quality Risks
- ## Recommended Fixes
- ## Quick Wins & Next Steps

Use markdown headings for each section and provide specific, actionable findings."""
                        display_mad_result(eng.solve_task(task, context=file_context), "audit.md")

        elif selected == "PPC":
            st.markdown('<div class="ui-card"><h3>💰 PPC Optimizer</h3><p style="color: #78716c; font-size: 0.9rem; margin-top: -10px;">Analyze and optimize pay-per-click campaigns across Google Ads, Microsoft Ads, and other platforms for better ROI.</p></div>', unsafe_allow_html=True)
            st.caption("Provide your campaign structure, targeting, budgets, and performance data. This agent returns a prioritized plan to improve ROAS and cut wasted spend.")
            # Use prefill value if available, then clear it
            prefill_value = st.session_state.ppc_prefill if st.session_state.ppc_prefill else ""
            if st.session_state.ppc_prefill:
                st.session_state.ppc_prefill = ""  # Clear after displaying once
            inp = st.text_area("Campaign Data", height=150, value=prefill_value)
            if st.button("📊 Analyze", type="primary"):
                if not inp and not file_context: st.warning("Provide data.")
                else:
                    with st.spinner("Analyzing..."):
                        eng = MADEngine(st.session_state.gemini_key)
                        task = f"""Analyze PPC campaign data and provide optimization recommendations.

Campaign Data:
{inp}

Required Structure:
- ## Account Overview
- ## Waste & Inefficiencies
- ## Winning Segments
- ## Recommended Changes
- ## KPIs to Monitor

Include a markdown table for key campaigns or ad groups with columns: Campaign, Issue/Opportunity, Action, Expected Impact."""
                        display_mad_result(eng.solve_task(task, context=file_context), "ppc.md")

        elif selected == "SEO":
            st.markdown('<div class="ui-card"><h3>🔍 SEO Planner</h3><p style="color: #78716c; font-size: 0.9rem; margin-top: -10px;">Develop comprehensive SEO strategies with keyword research, content planning, and technical optimization recommendations.</p></div>', unsafe_allow_html=True)
            st.caption("Provide your target keywords, pages, and SEO objectives. This agent returns a structured strategy with topic clusters, on‑page improvements, and content priorities.")
            # Use prefill value if available, then clear it
            prefill_value = st.session_state.seo_prefill if st.session_state.seo_prefill else ""
            if st.session_state.seo_prefill:
                st.session_state.seo_prefill = ""  # Clear after displaying once
            kw = st.text_area("Keywords", height=100, value=prefill_value)
            if st.button("🎯 Plan", type="primary"):
                with st.spinner("Planning..."):
                    eng = MADEngine(st.session_state.gemini_key)
                    task = f"""Create an SEO strategy plan based on the following keywords and objectives.

Keywords/Input:
{kw}

Required Structure:
- ## SEO Overview
- ## Keyword/Topic Clusters
- ## On‑Page Improvements
- ## Content Opportunities
- ## Technical Notes
- ## Next 30‑Day Plan

Include at least one markdown table listing: Keyword/Cluster, Intent, Priority, Suggested Page/Content."""
                    display_mad_result(eng.solve_task(task, context=file_context), "seo.md")

        elif selected == "Social":
            st.markdown('<div class="ui-card"><h3>📱 Social Media Manager</h3><p style="color: #78716c; font-size: 0.9rem; margin-top: -10px;">Generate content calendars, post ideas, and engagement strategies tailored to your niche and target platforms.</p></div>', unsafe_allow_html=True)
            st.caption("Describe your brand, audience, and chosen social platforms. This agent returns a channel‑specific content calendar with post ideas and messaging angles.")
            # Use prefill value if available, then clear it
            prefill_value = st.session_state.social_prefill if st.session_state.social_prefill else ""
            if st.session_state.social_prefill:
                st.session_state.social_prefill = ""  # Clear after displaying once
            c1, c2 = st.columns(2)
            with c1: niche = st.text_input("Niche", value=prefill_value)
            with c2: plat = st.multiselect("Platforms", ["LinkedIn", "Twitter", "Instagram"])
            if st.button("📅 Generate", type="primary"):
                with st.spinner("Generating..."):
                    eng = MADEngine(st.session_state.gemini_key)
                    task = f"""Create a social media content calendar and strategy.

Brand/Niche: {niche}
Platforms: {', '.join(plat) if plat else 'Not specified'}

Required Structure:
- ## Audience & Positioning
- ## Content Themes
- ## Posting Cadence
- ## Sample Posts by Platform
- ## CTAs & KPIs

Include a simple markdown table or bullet calendar with columns: Day, Platform, Theme, Hook."""
                    display_mad_result(eng.solve_task(task, context=file_context), "calendar.md")

        elif selected == "Research":
            st.markdown('<div class="ui-card"><h3>🌍 Deep Researcher</h3><p style="color: #78716c; font-size: 0.9rem; margin-top: -10px;">Conduct in-depth research on any topic using web search, Perplexity AI, or DuckDuckGo to gather comprehensive insights.</p></div>', unsafe_allow_html=True)
            st.caption("Provide the market, audience, or topic you want to understand. This agent returns synthesized insights from web data, including trends, competitors, and opportunities.")
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
                        
                        task = f"""Conduct deep research on the following topic and synthesize insights.

Research Topic: {q}

Web Data:
{web_data}

Required Structure:
- ## Executive Summary
- ## Market Overview
- ## Audience Insights
- ## Competitor Highlights
- ## Risks & Opportunities
- ## Recommended Actions

Provide comprehensive, well-organized insights based on the research data."""
                        display_mad_result(eng.solve_task(task, context=file_context), "research.md")
                    except Exception as e: 
                        st.error(str(e))

        elif selected == "Copy":
            st.markdown('<div class="ui-card"><h3>✍️ AI Copywriter</h3><p style="color: #78716c; font-size: 0.9rem; margin-top: -10px;">Rewrite and enhance your marketing copy in different styles to improve clarity, persuasiveness, or professionalism.</p></div>', unsafe_allow_html=True)
            st.caption("Provide the message, offer, or content you want refined, plus your preferred tone. This agent returns on‑brand copy variations tailored to your objectives.")
            # Use prefill value if available, then clear it
            prefill_value = st.session_state.copy_prefill if st.session_state.copy_prefill else ""
            if st.session_state.copy_prefill:
                st.session_state.copy_prefill = ""  # Clear after displaying once
            txt = st.text_area("Text", height=150, value=prefill_value)
            style = st.selectbox("Style", ["Simplify", "Persuasive", "Professional"])
            if st.button("✨ Rewrite", type="primary"):
                with st.spinner("Writing..."):
                    eng = MADEngine(st.session_state.gemini_key)
                    # Use clean_markdown to format output
                    task = f"""Rewrite the following content in {style} style.

Original Content:
{txt if txt else file_context}

Required Structure:
- ## Brief Understanding
- ## Core Message
- ## Variations (provide multiple versions of the copy)
- ## Notes on Tone & Angle

Provide multiple copy variations and explain the tone and messaging approach."""
                    res = eng.call_creator(task)
                    st.markdown(clean_markdown(res))

        elif selected == "Strategy":
            st.markdown('<div class="ui-card"><h3>🧩 Strategy Architect</h3><p style="color: #78716c; font-size: 0.9rem; margin-top: -10px;">Build comprehensive marketing strategies with actionable plans, tactics, and roadmaps to achieve your business objectives.</p></div>', unsafe_allow_html=True)
            st.caption("Provide your primary business or campaign goal and any constraints. This agent returns a cross‑channel marketing strategy with key plays and success metrics.")
            # Prefill goal with project_goal if goal is empty and project_goal exists
            if 'strategy_goal' not in st.session_state:
                st.session_state.strategy_goal = ""
            # If strategy_goal is empty and project_goal exists, use project_goal as default
            if not st.session_state.strategy_goal and st.session_state.project_goal:
                st.session_state.strategy_goal = st.session_state.project_goal
            goal = st.text_input("Goal", key="strategy_goal")
            if st.button("🚀 Build", type="primary"):
                with st.spinner("Building..."):
                    eng = MADEngine(st.session_state.gemini_key)
                    task = f"""Build a comprehensive marketing strategy.

Goal: {goal}

Required Structure:
- ## Context & Goal
- ## Channel Strategy (SEO, PPC, Social, Email, Other)
- ## Key Plays
- ## Timeline / Phasing
- ## KPIs & Targets
- ## Risks & Assumptions

Provide a detailed, actionable cross-channel marketing strategy with clear phases and success metrics."""
                    display_mad_result(eng.solve_task(task, context=file_context), "strategy.md")
            
            # --- STRATEGY PIPELINE: Send to execution agents ---
            if st.session_state.current_analysis is not None and selected == "Strategy":
                st.markdown("---")
                st.markdown("### Use this strategy in other agents")
                st.caption("Send your strategy to execution agents to create detailed plans.")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Send to SEO agent", use_container_width=True):
                        st.session_state.seo_prefill = st.session_state.current_analysis
                        st.session_state.target_agent = "SEO"
                        st.rerun()
                    if st.button("Send to PPC agent", use_container_width=True):
                        st.session_state.ppc_prefill = st.session_state.current_analysis
                        st.session_state.target_agent = "PPC"
                        st.rerun()
                with col2:
                    if st.button("Send to Social agent", use_container_width=True):
                        st.session_state.social_prefill = st.session_state.current_analysis
                        st.session_state.target_agent = "Social"
                        st.rerun()
                    if st.button("Send to Copy agent", use_container_width=True):
                        st.session_state.copy_prefill = st.session_state.current_analysis
                        st.session_state.target_agent = "Copy"
                        st.rerun()

    # Right-side chat panel
    if col_chat and st.session_state.current_analysis is not None:
        with col_chat:
            st.markdown("### 💬 Conversation")
            
            # Display chat messages
            for msg in st.session_state.chat_messages[-5:]:  # Show last 5 messages
                role_class = "user-message" if msg["role"] == "user" else "agent-message"
                st.markdown(
                    f'<div class="chat-message {role_class}">{msg["content"]}</div>',
                    unsafe_allow_html=True
                )
            
            # Chat input
            user_msg = st.chat_input("Ask something about this analysis...")
            if user_msg:
                st.session_state.chat_messages.append({"role": "user", "content": user_msg})
                with st.spinner("Thinking..."):
                    try:
                        engine = MADEngine(st.session_state.gemini_key)
                        resp = engine.chat_response(
                            user_msg, 
                            st.session_state.chat_messages, 
                            st.session_state.current_analysis
                        )
                        st.session_state.chat_messages.append({"role": "assistant", "content": resp})
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

# --- FOOTER ---
st.markdown("---")
st.markdown("""<div style="text-align: center; color: #a8a29e; font-size: 0.8rem;">MarketingOS v5.0 | Enterprise AI</div>""", unsafe_allow_html=True)
