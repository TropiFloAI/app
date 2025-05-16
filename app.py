import streamlit as st
import json
import pandas as pd
from pathlib import Path
from st_diff_viewer import diff_viewer

# --- Configuration ---
BASE_DIR = Path("tasks/MPPE_POC_1/PinacoladaV0")
BASELINE_FILE = Path("tasks/MPPE_POC_1/baseline/experiment.py")
LOGO_PATH = Path("logo.jpeg")

# Hardcoded credentials
USERNAME = "admin"
PASSWORD = "password123"

@st.cache_data
def load_results(base_dir: Path):
    results = []
    for subdir in sorted(base_dir.iterdir()):
        if subdir.is_dir():
            results_file = subdir / "results.json"
            if results_file.exists():
                try:
                    data = json.loads(results_file.read_text())
                    auc = data.get("ROC_AUC")
                    if auc is not None:
                        results.append({"idea": subdir.name, "auc": auc, "path": subdir})
                except Exception as e:
                    st.warning(f"Skipped {subdir.name}: {e}")
    return sorted(results, key=lambda x: x["auc"], reverse=True)

def login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if username == USERNAME and password == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid credentials")

def main():
    # Page config: wide layout, custom title
    st.set_page_config(
        layout="wide",
        page_title="Idea by ROC_AUC MPP&E POC#1 SNP500",
        initial_sidebar_state="expanded"
    )

    # Initialize session state for authentication
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    # Show login page if not authenticated
    if not st.session_state.authenticated:
        login_page()
        return

    # HEADER: display logo at very top of the page
    st.image(str(LOGO_PATH), width=600)

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
            width: 300px !important;
        }
        /* Force all sidebar text to black */
        [data-testid="stSidebar"] * {
            color: #000000 !important;
        }
        /* Hide default Streamlit menu, header bar, and footer */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True
    )

    # Sidebar: selection panel
    st.sidebar.title("MPP&E POC#1 SNP500")
    results = load_results(BASE_DIR)
    ideas = [r["idea"] for r in results]
    selected = st.sidebar.radio("Select an idea:", ideas)
    if not selected:
        st.sidebar.info("No ideas found.")
        return
    auc_val = next(item["auc"] for item in results if item["idea"] == selected)
    st.sidebar.markdown(f"**ROC_AUC:** {auc_val:.4f}")

    # Main: diff view
    st.header(f"Diff for idea: {selected}")
    cand_path = BASE_DIR / selected / "final_candidate.py"
    if not cand_path.exists():
        st.error(f"Could not find final_candidate.py in {selected}")
        return
    if not BASELINE_FILE.exists():
        st.error(f"Baseline file not found: {BASELINE_FILE}")
        return

    old_text = BASELINE_FILE.read_text()
    new_text = cand_path.read_text()
    diff_viewer(old_text, new_text, split_view=False,highlight_lines=[],extra_lines_surrounding_diff=[])


if __name__ == "__main__":
    main()
