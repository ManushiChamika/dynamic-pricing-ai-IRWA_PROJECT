// Central place to configure where the Streamlit app runs
// You can override this via Vite env: VITE_STREAMLIT_URL
export const STREAMLIT_URL = import.meta.env.VITE_STREAMLIT_URL || 'http://localhost:8501'
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
