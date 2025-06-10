import streamlit as st
import json
import pandas as pd
from pathlib import Path
from st_diff_viewer import diff_viewer
import random

# --- Configuration ---
CONFIG_FILE = Path("config/users.json")
IDEAS_FILE = Path("config/ideas.json")  # Path to ideas.json in config directory
LOGO_PATH = Path("images/Co-DataScientist.png")

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
                    'baseline_score': user_config.get('baseline_score', 0.51),  # Default to 0.51 if not specified
                    'metric': user_config.get('metric', 'ROC_AUC'),  # Default to ROC_AUC if not specified
                    'random': user_config.get('random', 'false').lower() == 'true'  # Convert string to boolean
                }
    except Exception as e:
        st.error(f"Error loading configuration: {e}")
    return None

@st.cache_data
def load_results(base_dir: Path, metric: str, use_random: bool = False):
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

def load_ideas_data(ideas_file: Path) -> dict:
    """Load ideas data from JSON file."""
    try:
        with open(ideas_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.warning(f"Could not load ideas data: {e}")
        return {}

def create_header():
    """Create a header that spans the full width visually."""
    # CSS for header styling
    st.markdown(
        """
        <style>
        /* Style the header area */
        .header-section {
            background-color: #f8f9fa;
            padding: 1rem 0;
            margin: -1rem -1rem 2rem -1rem;
            border-bottom: 2px solid #e9ecef;
        }
        
        /* Ensure full width appearance */
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
            max-width: none;
        }
        
        /* Style header text */
        .header-text {
            color: #333;
            font-weight: 500;
            margin: 0;
            line-height: 1.4;
        }
        
        /* Style logout button to prevent wrapping */
        .stButton > button {
            white-space: nowrap !important;
            min-width: 80px !important;
            width: 100% !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Create header container
    st.markdown('<div class="header-section">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=250)
        else:
            st.markdown("# Co-DataScientist")
    
    with col2:
        if st.session_state.authenticated:
            # Create sub-columns for user info and logout button - give more space to logout
            user_col, logout_col = st.columns([3, 2])
            with user_col:
                st.markdown(f'<p class="header-text">Logged in as: <strong>{st.session_state.username}</strong></p>', unsafe_allow_html=True)
            with logout_col:
                if st.button("Logout", key="header_logout"):
                    st.session_state.authenticated = False
                    st.session_state.username = None
                    st.session_state.user_config = None
                    st.session_state.ideas_data = {}
                    st.rerun()
        else:
            st.markdown('<p class="header-text">Please log in</p>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def login_page():
    # Simple, clean login page
    st.markdown("""
        <style>
        .stApp {
            background-color: white;
        }
        /* Center everything */
        .login-page {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding-top: 2rem;
        }
        /* Style the login heading */
        .login-heading {
            color: black !important;
            text-align: center;
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }
        /* Ensure white background and black text for inputs */
        .stTextInput > div > div > input {
            background-color: white !important;
            color: black !important;
            border: 1px solid #ccc !important;
        }
        /* Style login button */
        .stButton > button {
            background-color: white !important;
            color: black !important;
            border: 1px solid #ccc !important;
            width: 100% !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Center the logo
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=400)
        else:
            st.markdown("# Co-DataScientist")
        
        # Add some space
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Simple login form with styled heading
        st.markdown('<h3 class="login-heading">Login</h3>', unsafe_allow_html=True)
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            user_config = load_user_config(username)
            if user_config and password == user_config['password']:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.user_config = user_config
                st.rerun()
            else:
                st.error("Invalid credentials")

def main():
    # Initialize session state for authentication
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'user_config' not in st.session_state:
        st.session_state.user_config = None
    if 'ideas_data' not in st.session_state:
        st.session_state.ideas_data = {}

    # Show login page if not authenticated
    if not st.session_state.authenticated:
        login_page()
        return

    # Load ideas data if we have user config
    if st.session_state.user_config and not st.session_state.ideas_data:
        st.session_state.ideas_data = load_ideas_data(st.session_state.user_config['ideas_file'])
    
    # Page config: wide layout, custom title
    st.set_page_config(
        layout="wide",
        page_title=st.session_state.user_config['page_title'],
        initial_sidebar_state="expanded"
    )

    # HEADER: display logo and user info
    create_header()
    
    # CSS override: full light mode, hide menu/footer, and adjust sidebar width
    st.markdown(
        """
        <style>
        /* Main app container */
        [data-testid="stAppViewContainer"] {
            background-color: #FFFFFF !important;
            color: #000000 !important;
        }
        /* Sidebar background and width */
        [data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            width: 400px !important;
        }
        /* Force all sidebar text to black */
        [data-testid="stSidebar"] * {
            color: #000000 !important;
        }
        /* Hide default Streamlit menu, header bar, and footer */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        /* Style for logout button */
        div[data-testid="stButton"] > button {
            background-color: white !important;
            color: black !important;
            border: 1px solid #ccc !important;
        }
        /* Style for download button */
        div[data-testid="stDownloadButton"] > button {
            background-color: white !important;
            color: black !important;
            border: 1px solid #ccc !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Sidebar: selection panel
    st.sidebar.title(st.session_state.user_config['page_title'])
    results = load_results(
        st.session_state.user_config['base_dir'], 
        st.session_state.user_config['metric'], 
        st.session_state.user_config['random']
    )
    
    # Get the baseline threshold for color coding
    threshold = st.session_state.user_config['baseline_score']

    # Find the best metric value for star emoji
    best_metric_value = max(result["metric_value"] for result in results) if results else 0

    # Create idea options with metric scores and color coding
    idea_options = []
    idea_mapping = {}  # To map display text back to original idea name

    for result in results:
        idea_name = result["idea"].replace("_", " ")
        metric_value = result["metric_value"]
        
        # Determine emoji based on performance
        if metric_value == best_metric_value:
            emoji = "⭐"  # Star for best model
        elif metric_value >= threshold:
            emoji = "🟢"  # Green for above threshold
        else:
            emoji = "🔴"  # Red for below threshold
        
        # Create display text with metric score
        display_text = f"{idea_name} {emoji} ({metric_value:.4f})"
        idea_options.append(display_text)
        idea_mapping[display_text] = result["idea"]  # Store original name

    selected_display = st.sidebar.radio("Select an idea:", idea_options)
    if not selected_display:
        st.sidebar.info("No ideas found.")
        return

    # Get the original idea name and metric value
    selected_original = idea_mapping[selected_display]
    metric_value = next(item["metric_value"] for item in results if item["idea"] == selected_original)

    # Main: idea description and diff view
    # st.header(f"Diff for idea: {selected}")
    
    # Display idea description if available
    # if 'ideas_data' in st.session_state and selected in st.session_state.ideas_data:
    # Search for the idea in the ideas_data by matching the "name" key with selected_original
    idea_data = next(
        (idea for idea in st.session_state.ideas_data if idea["Name"] == selected_original),
        {}
    )
    
    # st.markdown("### Idea Description")
    st.markdown(f"### **Title:** {idea_data.get('Title', 'N/A')}", unsafe_allow_html=True)
    st.markdown(f"##### **Description:** {idea_data.get('Idea', 'No description available.')}", unsafe_allow_html=True)
    
    # Add download button for the Python file
    cand_path = st.session_state.user_config['base_dir'] / selected_original / "final_candidate.py"
    if cand_path.exists():
        with open(cand_path, 'r') as f:
            python_code = f.read()
        st.download_button(
            label=f"Download {selected_original}.py",
            data=python_code,
            file_name=f"{selected_original}.py",
            mime="text/x-python"
        )
    else:
        st.error(f"Could not find final_candidate.py in {selected_original}")
        return

    if not st.session_state.user_config['baseline_file'].exists():
        st.error(f"Baseline file not found: {st.session_state.user_config['baseline_file']}")
        return

    old_text = st.session_state.user_config['baseline_file'].read_text()
    new_text = cand_path.read_text()
    
    # Custom styling for cleaner diff view
    custom_styles = {
        "line": {
            "padding": "5px 0px",
        },
        "wordDiff": {
            "display": "inline",
            "padding": "0px",
        },
        "diff": {
            "add": {
                "background": "#e6ffe6",  # Light green
                "color": "#000000"
            },
            "del": {
                "background": "#ffe6e6",  # Light red
                "color": "#000000"
            }
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

if __name__ == "__main__":
    main()


