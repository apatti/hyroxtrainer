import streamlit as st
from src.components import (
    render_workout_input,
    render_daily_workout,
    render_workout_tracker,
    render_progress_dashboard,
    render_coaching,
)

# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title="Hyrox Trainer",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed",  # Better for mobile
)

# Mobile-optimized CSS
st.markdown("""
<style>
    /* Mobile-first responsive design */
    .stApp {
        max-width: 100%;
    }

    /* Compact header for mobile */
    .main-header {
        text-align: center;
        padding: 0.5rem 0;
        margin-bottom: 1rem;
    }

    /* Bottom navigation for mobile */
    .nav-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: var(--background-color);
        border-top: 1px solid #ddd;
        padding: 0.5rem;
        z-index: 999;
        display: flex;
        justify-content: space-around;
    }

    /* Make buttons more touch-friendly */
    .stButton > button {
        min-height: 48px;
        font-size: 16px;
    }

    /* Larger touch targets for inputs */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stTextArea > div > div > textarea {
        font-size: 16px !important;
        min-height: 48px;
    }

    /* Reduce padding on mobile */
    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
        padding-bottom: 5rem; /* Space for bottom nav */
    }

    /* Responsive columns */
    @media (max-width: 768px) {
        .row-widget.stHorizontalBlock {
            flex-direction: column;
        }

        .row-widget.stHorizontalBlock > div {
            width: 100% !important;
            flex: 1 1 100% !important;
        }

        /* Smaller metrics on mobile */
        [data-testid="stMetricValue"] {
            font-size: 1.5rem !important;
        }

        /* Stack expanders better */
        .streamlit-expanderHeader {
            font-size: 1rem;
        }
    }

    /* Hide sidebar toggle on mobile for cleaner look */
    @media (max-width: 768px) {
        [data-testid="collapsedControl"] {
            display: none;
        }
    }

    /* Tab styling for mobile */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 10px 16px;
        font-size: 14px;
    }

    /* Form submit button full width */
    .stForm [data-testid="stFormSubmitButton"] > button {
        width: 100%;
    }

    /* Expander content padding */
    .streamlit-expanderContent {
        padding: 0.5rem 0;
    }

    /* Chart responsiveness */
    .js-plotly-plot {
        width: 100% !important;
    }

    /* Cards/containers */
    .element-container {
        margin-bottom: 0.5rem;
    }

    /* Better dividers */
    hr {
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application entry point."""

    # Initialize session state
    if "page" not in st.session_state:
        st.session_state.page = "today"

    # Header
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("Hyrox Trainer")
    st.markdown('</div>', unsafe_allow_html=True)

    # Navigation tabs (mobile-friendly)
    tabs = st.tabs([
        " Today",
        " Add",
        " Progress",
        " Coach",
        " Track"
    ])

    with tabs[0]:
        render_daily_workout()

    with tabs[1]:
        render_workout_input()

    with tabs[2]:
        render_progress_dashboard()

    with tabs[3]:
        render_coaching()

    with tabs[4]:
        if "active_workout" in st.session_state:
            render_workout_tracker()
        else:
            st.info("Start a workout from the Today tab to begin tracking.")
            if st.button("Go to Today's Workout"):
                st.rerun()


if __name__ == "__main__":
    main()
