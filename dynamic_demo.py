import streamlit as st
import json
import pandas as pd
from pathlib import Path
import random
import time
import threading
from st_diff_viewer import diff_viewer

# --- Configuration ---
CONFIG_FILE = Path("config/users.json")
LOGO_PATH = Path("images/Co-DataScientist.png")
SELECTED_USER = "algo_trading"  # Hardcoded to algo_trading dataset

def load_user_config(username: str) -> dict:
    """Load user configuration from JSON file."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            if username in config:
                user_config = config[username]
                return {
                    'password': user_config['password'],
                    'base_dir': Path(user_config['base_dir']),
                    'baseline_file': Path(user_config['baseline_file']),
                    'page_title': user_config['page_title'],
                    'ideas_file': Path(user_config['ideas_file']),
                    'baseline_score': user_config.get('baseline_score', 0.51),
                    'metric': user_config.get('metric', 'ROC_AUC'),
                    'random': user_config.get('random', 'false').lower() == 'true'
                }
    except Exception as e:
        st.error(f"Error loading configuration: {e}")
    return None

def load_ideas_data(ideas_file: Path) -> list:
    """Load ideas data from JSON file."""
    try:
        with open(ideas_file, 'r') as f:
            ideas_data = json.load(f)
            # Ensure it's a list of ideas
            if isinstance(ideas_data, list):
                return ideas_data
            else:
                return []
    except Exception as e:
        st.warning(f"Could not load ideas data: {e}")
        return []

def load_real_results(base_dir: Path, metric: str, use_random: bool = False):
    """Load real results from the data directory structure."""
    results = []
    for subdir in sorted(base_dir.iterdir()):
        if subdir.is_dir():
            if use_random:
                # Use idea name as seed for consistent random values
                random.seed(hash(subdir.name) % (2**32))
                # Generate random metric value between 0.3 and 0.9
                metric_value = round(random.uniform(0.3, 0.9), 4)
                results.append({"idea": subdir.name, "metric_value": metric_value, "path": subdir})
            else:
                results_file = subdir / "results.json"
                if results_file.exists():
                    try:
                        data = json.loads(results_file.read_text())
                        metric_value = data.get(metric)
                        if metric_value is not None:
                            results.append({"idea": subdir.name, "metric_value": metric_value, "path": subdir})
                    except Exception as e:
                        st.warning(f"Skipped {subdir.name}: {e}")
    return sorted(results, key=lambda x: x["metric_value"], reverse=True)

def create_header():
    """Create a simple header with logo and text only."""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=250)
        else:
            st.markdown("# Co-DataScientist - Dynamic Demo")
    
    with col2:
        pass

def main():
    # Page config
    st.set_page_config(
        layout="wide",
        page_title="Co-DataScientist - Algo Trading Demo",
        initial_sidebar_state="collapsed"
    )

    # Initialize session state
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'processed_ideas' not in st.session_state:
        st.session_state.processed_ideas = []
    if 'selected_idea' not in st.session_state:
        st.session_state.selected_idea = None
    if 'user_config' not in st.session_state:
        st.session_state.user_config = None
    if 'ideas_data' not in st.session_state:
        st.session_state.ideas_data = []
    if 'all_results' not in st.session_state:
        st.session_state.all_results = []
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
    if 'user_goal' not in st.session_state:
        st.session_state.user_goal = ""
    if 'selected_deployment_idea' not in st.session_state:
        st.session_state.selected_deployment_idea = None

    # Load algo_trading configuration automatically
    if not st.session_state.user_config:
        user_config = load_user_config(SELECTED_USER)
        if user_config:
            st.session_state.user_config = user_config
            # Load ideas data
            st.session_state.ideas_data = load_ideas_data(user_config['ideas_file'])
            # Load all results
            st.session_state.all_results = load_real_results(
                user_config['base_dir'], 
                user_config['metric'], 
                user_config['random']
            )
        else:
            st.error(f"Could not load configuration for {SELECTED_USER}")
            return

    # Header
    create_header()

    # CSS styling
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            background-color: #FFFFFF !important;
            color: #000000 !important;
        }
        [data-testid="stSidebar"] {
            display: none !important;
        }
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* All buttons light mode */
        div[data-testid="stButton"] > button {
            background-color: white !important;
            color: black !important;
            border: 1px solid #ccc !important;
        }
        
        /* Download button styling */
        div[data-testid="stDownloadButton"] > button {
            background-color: white !important;
            color: black !important;
            border: 1px solid #ccc !important;
        }
        
        /* File uploader styling */
        div[data-testid="stFileUploader"] {
            background-color: white !important;
        }
        div[data-testid="stFileUploader"] > div {
            background-color: white !important;
            border: 1px solid #ccc !important;
        }
        
        /* Drag and drop area styling */
        div[data-testid="stFileUploader"] section {
            background-color: white !important;
            color: black !important;
            border: 2px dashed #ccc !important;
        }
        
        /* File uploader text and labels */
        div[data-testid="stFileUploader"] label,
        div[data-testid="stFileUploader"] span,
        div[data-testid="stFileUploader"] p,
        div[data-testid="stFileUploader"] small {
            color: black !important;
        }
        
        /* Upload button within file uploader */
        div[data-testid="stFileUploader"] button {
            background-color: white !important;
            color: black !important;
            border: 1px solid #ccc !important;
        }
        
        /* Ensure all text is black */
        .stMarkdown, .stText, .stInfo, .stSuccess, .stWarning, .stError {
            color: black !important;
        }
        
        /* Progress bar styling */
        .stProgress > div > div {
            background-color: #0066cc !important;
        }
        
        /* Info/success/warning boxes light styling */
        div[data-testid="stAlert"] {
            background-color: #f8f9fa !important;
            color: black !important;
            border: 1px solid #dee2e6 !important;
        }
        
        /* More specific selectors for info boxes */
        .stAlert {
            background-color: #e7f3ff !important;
            color: #000000 !important;
            border: 1px solid #b3d9ff !important;
            border-radius: 5px !important;
        }
        
        /* Info box text styling */
        .stAlert p, .stAlert div, .stAlert span {
            color: #000000 !important;
        }
        
        /* Success boxes */
        div[data-testid="stAlert"][data-baseweb="notification"][kind="success"] {
            background-color: #e8f5e8 !important;
            color: #000000 !important;
            border: 1px solid #c3e6c3 !important;
        }
        
        /* Warning boxes */
        div[data-testid="stAlert"][data-baseweb="notification"][kind="warning"] {
            background-color: #fff3cd !important;
            color: #000000 !important;
            border: 1px solid #ffeaa7 !important;
        }
        
        /* Info boxes specifically */
        div[data-testid="stAlert"][data-baseweb="notification"][kind="info"] {
            background-color: #e7f3ff !important;
            color: #000000 !important;
            border: 1px solid #b3d9ff !important;
        }
        
        /* Additional fallback for any alert text */
        [data-testid="stAlert"] * {
            color: #000000 !important;
        }
        
        /* Markdown styling for light mode */
        .stMarkdown {
            background-color: transparent !important;
            color: #000000 !important;
        }
        
        /* Code blocks in markdown */
        .stMarkdown code {
            background-color: #f8f9fa !important;
            color: #000000 !important;
            border: 1px solid #e9ecef !important;
            padding: 2px 4px !important;
            border-radius: 3px !important;
        }
        
        /* Inline code styling */
        code {
            background-color: #f8f9fa !important;
            color: #000000 !important;
            border: 1px solid #e9ecef !important;
            padding: 2px 4px !important;
            border-radius: 3px !important;
        }
        
        /* Strong/bold text */
        .stMarkdown strong, .stMarkdown b {
            color: #000000 !important;
        }
        
        /* All markdown elements */
        .stMarkdown p, .stMarkdown div, .stMarkdown span, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
            color: #000000 !important;
        }
        
        /* Slider styling */
        .stSlider label {
            color: #000000 !important;
            font-weight: 500 !important;
        }
        
        /* Slider text and help text */
        .stSlider .stMarkdown {
            color: #000000 !important;
        }
        
        /* Slider help text */
        .stSlider div[data-baseweb="tooltip"] {
            color: #000000 !important;
        }
        
        /* All form labels */
        label {
            color: #000000 !important;
        }
        
        /* Text area styling */
        .stTextArea textarea {
            background-color: white !important;
            color: #000000 !important;
            border: 1px solid #ccc !important;
        }
        
        /* Text area label */
        .stTextArea label {
            color: #000000 !important;
        }
        
        /* Center text on landing page */
        .centered-text {
            text-align: center;
        }
        
        .centered-text h1, .centered-text h2, .centered-text h3 {
            text-align: center;
        }
        
        /* Make the main button more enticing */
        .stButton > button[kind="primary"] {
            background: linear-gradient(45deg, #1e3a8a, #0891b2, #059669, #0d9488) !important;
            background-size: 400% 400% !important;
            animation: gradientShift 3s ease infinite !important;
            border: none !important;
            color: white !important;
            font-weight: bold !important;
            font-size: 18px !important;
            padding: 15px 30px !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 15px rgba(8, 145, 178, 0.4) !important;
            transform: translateY(0) !important;
            transition: all 0.3s ease !important;
        }
        
        .stButton > button[kind="primary"]:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 8px 25px rgba(8, 145, 178, 0.6) !important;
        }
        
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        /* Text area label */
        .stTextArea label {
            color: #000000 !important;
        }
        
        /* Form elements styling for deployment page */
        .stTextInput input {
            background-color: white !important;
            color: #000000 !important;
            border: 1px solid #ccc !important;
        }
        
        .stTextInput label {
            color: #000000 !important;
        }
        
        .stSelectbox div[data-baseweb="select"] {
            background-color: white !important;
            color: #000000 !important;
            border: 1px solid #ccc !important;
        }
        
        .stSelectbox label {
            color: #000000 !important;
        }
        
        .stNumberInput input {
            background-color: white !important;
            color: #000000 !important;
            border: 1px solid #ccc !important;
        }
        
        .stNumberInput label {
            color: #000000 !important;
        }
        
        .stCheckbox label {
            color: #000000 !important;
        }
        
        .stCheckbox span {
            color: #000000 !important;
        }
        
        /* Help text styling */
        .help {
            color: #666666 !important;
        }
        
        /* Additional selectbox styling */
        .stSelectbox > div > div {
            background-color: white !important;
            color: #000000 !important;
        }
        
        /* Dropdown menu styling */
        .stSelectbox [data-baseweb="popover"] {
            background-color: white !important;
        }
        
        .stSelectbox [data-baseweb="popover"] div {
            background-color: white !important;
            color: #000000 !important;
        }
        
        /* Vertical divider between columns */
        .column-divider {
            border-right: 2px solid #000000;
            padding-right: 15px;
            margin-right: 15px;
        }
        
        /* Floating panel styling */
        .floating-panel {
            background-color: #ffffff;
            border-radius: 12px;
            padding: 25px;
            margin: 15px 8px;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
            border: 1px solid #e0e0e0;
            height: fit-content;
            min-height: 200px;
        }
        
        /* Panel titles - bigger and bolder */
        .panel-title {
            font-size: 30px !important;
            font-weight: bold !important;
            color: #333333 !important;
            margin-bottom: 15px !important;
            text-align: center !important;
            border-bottom: 2px solid #0891b2 !important;
            padding-bottom: 8px !important;
        }
        
        /* Light background for better panel contrast */
        .main .block-container {
            background-color: #f8f9fa !important;
            padding: 20px !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Page navigation
    if st.session_state.current_page == 1:
        show_setup_page()
    elif st.session_state.current_page == 2:
        show_processing_page()
    elif st.session_state.current_page == 3:
        show_deployment_page()

def show_setup_page():
    """Page 1: Landing page with progressive workflow"""
    
    # Center the content using columns
    col_left, col_center, col_right = st.columns([1, 2, 1])
    
    with col_center:
        # Add centered text wrapper
        st.markdown('<div class="centered-text">', unsafe_allow_html=True)
        
        # Catchy landing page title
        st.markdown("# 🚀 The One Stop Shop for AI Models!")
        st.markdown("### Discover, generate, and test AI models with just a few clicks")
        
        st.markdown("---")
        
        # Step 1: Upload Data
        st.markdown("## 1️⃣ Upload Your Data")
        st.markdown('</div>', unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose your dataset", 
            type=['csv', 'xlsx', 'json'],
            help="Upload your dataset to get started with AI model generation"
        )
        
        if uploaded_file is not None:
            st.session_state.uploaded_file = uploaded_file
            st.success(f"✅ Dataset uploaded: {uploaded_file.name}")
            
            st.markdown("---")
            
            # Step 2: Goal Description (only shows after upload)
            st.markdown('<div class="centered-text">', unsafe_allow_html=True)
            st.markdown("## 2️⃣ Tell Us What You're Trying to Predict")
            st.markdown('</div>', unsafe_allow_html=True)
            
            user_goal = st.text_area(
                "Describe your prediction goal:",
                value=st.session_state.user_goal,
                height=100,
                placeholder="e.g., I want to predict customer churn based on usage patterns, or forecast sales based on historical data and market trends..."
            )
            st.session_state.user_goal = user_goal
            
            # Step 3: Ideas & Launch (only shows after goal is entered)
            if user_goal.strip():  # Only show if user has entered a goal
                st.markdown("---")
                
                st.markdown('<div class="centered-text">', unsafe_allow_html=True)
                st.markdown("## 3️⃣ Choose Your AI Power Level")
                st.markdown('</div>', unsafe_allow_html=True)
                
                total_available = len(st.session_state.all_results)
                max_ideas = min(25, total_available)
                
                if 'selected_idea_count' not in st.session_state:
                    st.session_state.selected_idea_count = min(5, max_ideas)
                
                selected_count = st.slider(
                    "How many AI models should we generate?",
                    min_value=1,
                    max_value=max_ideas,
                    value=st.session_state.selected_idea_count,
                    help=f"More models = better results (max {max_ideas} available)"
                )
                st.session_state.selected_idea_count = selected_count
                
                st.markdown("---")
                
                # Magic Button!
                st.markdown('<div class="centered-text">', unsafe_allow_html=True)
                st.markdown("### 🌟 Ready to Transform Your Data Into Gold?")
                st.markdown('</div>', unsafe_allow_html=True)
                
                if st.button("�� Unleash AI Magic & Discover Hidden Insights! ✨", use_container_width=True, type="primary"):
                    st.session_state.processing = True
                    st.session_state.processed_ideas = []
                    st.session_state.selected_idea = None
                    st.session_state.current_stage = 0
                    st.session_state.stage_start_time = time.time()
                    st.session_state.current_page = 2
                    st.rerun()
            else:
                # Encourage user to fill in the goal
                st.info("👆 Please describe what you're trying to predict to continue")
        else:
            st.info("👆 Upload your data to get started")

def show_processing_page():
    """Page 2: Processing and results"""
    # Navigation back
    if st.button("← Back to Setup", key="back_button"):
        st.session_state.current_page = 1
        st.rerun()
    
    st.markdown("---")
    
    # Three column layout: Processing | Ideas | Results  
    col1, col2, col3 = st.columns([1.0, 0.8, 2.5])
    
    # LEFT PANEL: Processing Status
    with col1:
        # Create container for floating panel
        with st.container():
            # st.markdown('<div class="floating-panel">', unsafe_allow_html=True)
            
            # Bigger, bolder title
            st.markdown('<h2 class="panel-title">🔄 Processing</h2>', unsafe_allow_html=True)
            
            total_ideas = st.session_state.selected_idea_count
            processed_count = len(st.session_state.processed_ideas)
            
            # Overall progress at top
            overall_progress = processed_count / total_ideas if total_ideas > 0 else 0
            st.markdown(f"**Processing Idea {processed_count + 1} of {total_ideas}**")
            st.progress(overall_progress)
            
            if st.session_state.processing:
                # Initialize stage tracking if not exists
                if 'current_stage' not in st.session_state:
                    st.session_state.current_stage = 0
                if 'stage_start_time' not in st.session_state:
                    st.session_state.stage_start_time = time.time()
                
                current_stage = st.session_state.current_stage
                stage_start_time = st.session_state.stage_start_time
                
                # Current idea being processed
                st.markdown("---")
                if processed_count < total_ideas:
                    current_idea_index = processed_count
                    current_idea_name = st.session_state.all_results[current_idea_index]["idea"] if current_idea_index < len(st.session_state.all_results) else "Completed"
                    
                    # Only show idea name after Reading Literature stage is complete
                    if current_stage > 0:  # After first stage (Reading Literature)
                        st.markdown(f"🔬 **Current Idea:** `{current_idea_name.replace('_', ' ').title()}`")
                    else:  # During Reading Literature stage
                        st.markdown("🔍 **Discovering idea from literature...**")
                else:
                    st.markdown("🎉 **All Ideas Completed!**")
                
                # Define the stages
                stages = [
                    {"name": "📚 Reading Literature", "icon": "📚", "duration": 3},
                    {"name": "💡 Implementing Idea", "icon": "💡", "duration": 4},
                    {"name": "🧠 Training Model", "icon": "🧠", "duration": 5},
                    {"name": "📊 Evaluating Results", "icon": "📊", "duration": 3},
                    {"name": "✅ Finalizing Code", "icon": "✅", "duration": 2}
                ]
                
                # Only show stages if we're still processing an idea
                if processed_count < total_ideas:
                    # Display stages with animations
                    for i, stage in enumerate(stages):
                        if i < current_stage:
                            # Completed stage
                            st.markdown(f"✅ ~~{stage['name']}~~")
                        elif i == current_stage:
                            # Current stage with animation
                            elapsed = time.time() - stage_start_time
                            stage_progress = min(elapsed / stage['duration'], 1.0)
                            
                            # Animated dots
                            dots_count = int((elapsed * 2) % 4)
                            dots = "." * dots_count
                            
                            col_stage, col_progress = st.columns([3, 1])
                            with col_stage:
                                st.markdown(f"🔄 **{stage['name']}{dots}**")
                            with col_progress:
                                st.markdown(f"`{stage_progress*100:.0f}%`")
                            
                            # Stage progress bar
                            st.progress(stage_progress)
                            
                        else:
                            # Pending stage
                            st.markdown(f"⏳ {stage['name']}")
                
            else:
                st.success(f"✅ Processing complete! ({processed_count} ideas)")
                if st.button("🔄 Run Again", use_container_width=True):
                    st.session_state.processing = True
                    st.session_state.processed_ideas = []
                    st.session_state.selected_idea = None
                    st.session_state.current_stage = 0
                    st.session_state.stage_start_time = time.time()
                    st.rerun()
            
            # Close floating panel
            # st.markdown('</div>', unsafe_allow_html=True)

    # MIDDLE PANEL: Processed Ideas
    with col2:
        # Create container for floating panel
        with st.container():
            # st.markdown('<div class="floating-panel">', unsafe_allow_html=True)
            
            # Bigger, bolder title
            st.markdown('<h2 class="panel-title">💡 Processed Ideas</h2>', unsafe_allow_html=True)
            
            if st.session_state.processed_ideas:
                # Sort by metric value
                sorted_ideas = sorted(st.session_state.processed_ideas, 
                                    key=lambda x: x['metric_value'], reverse=True)
                
                threshold = st.session_state.user_config.get('baseline_score', 0.51)
                best_metric = max(idea['metric_value'] for idea in sorted_ideas) if sorted_ideas else 0
                
                for idea in sorted_ideas:
                    # Generate emoji based on performance
                    if idea['metric_value'] == best_metric:
                        emoji = "⭐"
                    elif idea['metric_value'] >= threshold:
                        emoji = "🟢"
                    else:
                        emoji = "🔴"
                    
                    # Truncate long names for display
                    display_name = idea['display_name']
                    if len(display_name) > 25:
                        display_name = display_name[:25] + "..."
                    
                    # Check if this is the selected idea
                    is_selected = (st.session_state.selected_idea and 
                                  st.session_state.selected_idea['name'] == idea['name'])
                    
                    button_text = f"{emoji} {display_name}\n({idea['metric_value']:.4f})"
                    if is_selected:
                        st.info(f"🔍 **Selected:** {button_text}")
                    else:
                        if st.button(button_text, key=f"select_{idea['name']}", use_container_width=True):
                            st.session_state.selected_idea = idea
                            st.rerun()
            elif st.session_state.processing:
                st.info("🔄 Processing ideas...")
            else:
                st.info("⚡ Start processing to see ideas appear here")
            
            # Close floating panel
            # st.markdown('</div>', unsafe_allow_html=True)

    # RIGHT PANEL: Idea Details + Code Diff
    with col3:
        # Create container for floating panel
        with st.container():
            # st.markdown('<div class="floating-panel">', unsafe_allow_html=True)
            
            # Bigger, bolder title
            st.markdown('<h2 class="panel-title">📊 Results</h2>', unsafe_allow_html=True)
            
            # Idea Details Section
            if st.session_state.selected_idea:
                idea = st.session_state.selected_idea
                st.markdown(f"### **Title:** {idea['title']}")
                st.markdown(f"##### **Description:** {idea['description']}")
                st.markdown(f"**Score:** {idea['metric_value']:.4f}")
                
                # Download button for the candidate file
                cand_path = Path(idea['path']) / "final_candidate.py"
                if cand_path.exists():
                    with open(cand_path, 'r') as f:
                        python_code = f.read()
                    
                    # Two buttons side by side
                    col_download, col_deploy = st.columns(2)
                    
                    with col_download:
                        st.download_button(
                            label=f"📥 Download {idea['name']}.py",
                            data=python_code,
                            file_name=f"{idea['name']}.py",
                            mime="text/x-python"
                        )
                    
                    with col_deploy:
                        if st.button(f"🚀 Deploy!", key=f"deploy_{idea['name']}", use_container_width=True, type="primary"):
                            st.session_state.selected_deployment_idea = idea
                            st.session_state.current_page = 3
                            st.rerun()
                else:
                    st.warning("Could not find final_candidate.py")
            elif st.session_state.processed_ideas:
                st.info("👈 Select an idea from the left panel to view details")
            
            st.markdown("---")
            
            # Code Diff Section
            if st.session_state.selected_idea and st.session_state.user_config:
                idea = st.session_state.selected_idea
                baseline_file = st.session_state.user_config['baseline_file']
                cand_path = Path(idea['path']) / "final_candidate.py"
                
                if baseline_file.exists() and cand_path.exists():
                    old_text = baseline_file.read_text()
                    new_text = cand_path.read_text()
                    
                    # Custom styling for diff view
                    custom_styles = {
                        "line": {"padding": "5px 0px"},
                        "wordDiff": {"display": "inline", "padding": "0px"},
                        "diff": {
                            "add": {"background": "#e6ffe6", "color": "#000000"},
                            "del": {"background": "#ffe6e6", "color": "#000000"}
                        }
                    }
                    
                    diff_viewer(
                        old_text, 
                        new_text, 
                        split_view=False,
                        highlight_lines=[],
                        extra_lines_surrounding_diff=[],
                        styles=custom_styles
                    )
                else:
                    st.error("Could not find baseline or candidate files")
            elif st.session_state.processed_ideas:
                st.info("👈 Select an idea to view the code diff")
            
            # Close floating panel
            # st.markdown('</div>', unsafe_allow_html=True)

    # Handle dynamic processing
    if st.session_state.processing and st.session_state.all_results:
        process_ideas_dynamically()

def process_ideas_dynamically():
    """Simulate processing ideas one by one with detailed stage progression"""
    
    processed_count = len(st.session_state.processed_ideas)
    total_count = st.session_state.selected_idea_count  # Use selected count instead of all results
    
    if processed_count < total_count and processed_count < len(st.session_state.all_results):
        # Define the stages with their durations (in seconds)
        stages = [
            {"name": "📚 Reading Literature", "duration": 3},
            {"name": "💡 Implementing Idea", "duration": 4},
            {"name": "🧠 Training Model", "duration": 5},
            {"name": "📊 Evaluating Results", "duration": 3},
            {"name": "✅ Finalizing Code", "duration": 2}
        ]
        
        # Initialize stage tracking if not exists
        if 'current_stage' not in st.session_state:
            st.session_state.current_stage = 0
        if 'stage_start_time' not in st.session_state:
            st.session_state.stage_start_time = time.time()
        
        current_stage = st.session_state.current_stage
        stage_start_time = st.session_state.stage_start_time
        elapsed = time.time() - stage_start_time
        
        # Check if current stage is complete
        if elapsed >= stages[current_stage]['duration']:
            # Move to next stage
            st.session_state.current_stage += 1
            st.session_state.stage_start_time = time.time()
            
            # If all stages complete, process the idea
            if st.session_state.current_stage >= len(stages):
                # Get the next idea to process
                next_result = st.session_state.all_results[processed_count]
                
                # Find corresponding idea data
                idea_data = None
                for idea in st.session_state.ideas_data:
                    if idea.get("Name") == next_result["idea"]:
                        idea_data = idea
                        break
                
                # Create processed idea entry
                processed_idea = {
                    'name': next_result["idea"],
                    'display_name': next_result["idea"].replace("_", " ").title(),
                    'title': idea_data.get('Title', next_result["idea"].replace("_", " ").title()) if idea_data else next_result["idea"].replace("_", " ").title(),
                    'description': idea_data.get('Idea', 'No description available.') if idea_data else 'No description available.',
                    'metric_value': next_result["metric_value"],
                    'path': next_result["path"]
                }
                
                # Add to processed ideas
                st.session_state.processed_ideas.append(processed_idea)
                
                # Automatically select the newest idea to show diff immediately
                st.session_state.selected_idea = processed_idea
                
                # Reset for next idea or mark as complete
                if len(st.session_state.processed_ideas) >= total_count:
                    st.session_state.processing = False
                else:
                    st.session_state.current_stage = 0
                    st.session_state.stage_start_time = time.time()
        
        # Small delay to control refresh rate
        time.sleep(0.5)
        
        # Refresh to show the updated stage
        st.rerun()

def show_deployment_page():
    """Page 3: Deployment configuration"""
    # Navigation back
    if st.button("← Back to Results", key="back_to_results"):
        st.session_state.current_page = 2
        st.rerun()
    
    # Center the content using columns
    col_left, col_center, col_right = st.columns([1, 2, 1])
    
    with col_center:
        idea = st.session_state.selected_deployment_idea
        
        # Add centered text wrapper
        st.markdown('<div class="centered-text">', unsafe_allow_html=True)
        st.markdown("# 🚀 Deploy Your AI Model")
        st.markdown(f"### Ready to launch: **{idea['title']}**")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Deployment Configuration Form
        st.markdown('<div class="centered-text">', unsafe_allow_html=True)
        st.markdown("## ⚙️ Deployment Configuration")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Model Name
        model_name = st.text_input(
            "Model Name:",
            value=f"{idea['name']}_v1",
            help="Choose a unique name for your deployed model"
        )
        
        # Environment Selection
        environment = st.selectbox(
            "Deployment Environment:",
            ["Production", "Staging", "Development"],
            index=1,
            help="Select where you want to deploy your model"
        )
        
        # API Configuration
        st.markdown("### 🔌 API Settings")
        api_rate_limit = st.number_input(
            "API Rate Limit (requests/minute):",
            min_value=10,
            max_value=10000,
            value=1000,
            help="Maximum number of API calls per minute"
        )
        
        enable_auth = st.checkbox(
            "Enable API Authentication",
            value=True,
            help="Require authentication for API access"
        )
        
        # Scaling Configuration
        st.markdown("### 📈 Scaling Settings")
        instance_type = st.selectbox(
            "Instance Type:",
            ["Small (1 CPU, 2GB RAM)", "Medium (2 CPU, 4GB RAM)", "Large (4 CPU, 8GB RAM)", "XLarge (8 CPU, 16GB RAM)"],
            index=1,
            help="Select the computing power for your deployment"
        )
        
        auto_scaling = st.checkbox(
            "Enable Auto-scaling",
            value=True,
            help="Automatically scale based on demand"
        )
        
        if auto_scaling:
            col_min, col_max = st.columns(2)
            with col_min:
                min_instances = st.number_input("Min Instances:", min_value=1, max_value=10, value=1)
            with col_max:
                max_instances = st.number_input("Max Instances:", min_value=1, max_value=50, value=5)
        
        # Monitoring
        st.markdown("### 📊 Monitoring & Alerts")
        enable_monitoring = st.checkbox(
            "Enable Performance Monitoring",
            value=True,
            help="Track model performance and usage metrics"
        )
        
        alert_email = st.text_input(
            "Alert Email:",
            placeholder="your-email@company.com",
            help="Email for deployment alerts and notifications"
        )
        
        # Data Input Configuration
        st.markdown("### 📥 Data Input Settings")
        input_format = st.selectbox(
            "Expected Input Format:",
            ["JSON", "CSV", "Parquet", "Real-time Stream"],
            help="Format of data your model will receive"
        )
        
        batch_processing = st.checkbox(
            "Enable Batch Processing",
            value=False,
            help="Process multiple predictions in batches"
        )
        
        st.markdown("---")
        
        # Final Deploy Button
        st.markdown('<div class="centered-text">', unsafe_allow_html=True)
        st.markdown("### 🌟 Ready to Go Live?")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("🚀 Deploy Model to Production! ✨", use_container_width=True, type="primary"):
            # Show deployment success
            st.balloons()
            st.success("🎉 Model Successfully Deployed!")
            st.markdown(f"""
            **Deployment Details:**
            - **Model:** {model_name}
            - **Environment:** {environment}
            - **Instance:** {instance_type}
            - **API Endpoint:** `https://api.co-datascientist.com/models/{model_name}`
            - **Status:** Live and Ready! 🟢
            """)
            
            if st.button("🏠 Return to Home", use_container_width=True):
                st.session_state.current_page = 1
                st.rerun()

if __name__ == "__main__":
    main()
