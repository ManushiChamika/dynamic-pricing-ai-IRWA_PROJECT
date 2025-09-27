# FluxPricer AI – React Frontend

This is a minimal React (Vite) frontend that provides a Landing page with Login and Register buttons, without changing any backend files.

## Features
- Landing page with hero and CTA buttons
- Routes: `/` (Landing), `/login`, `/register`
- Simple CSS and structure – ready to connect to your Python backend later

## Run (Windows PowerShell)

```powershell
# From repo root
cd .\frontend
npm install
npm run dev
```

Then open the URL shown (default http://localhost:5173).

## Next steps
- Set the Streamlit app URL so the Login/Register pages redirect correctly:

```powershell
$env:VITE_STREAMLIT_URL = "http://localhost:8501" # default
npm run dev
```

- Wire `/login` and `/register` to real API endpoints (e.g., FastAPI), or keep redirect-to-Streamlit for now
- Add protected routes and JWT handling
- Build a dedicated Pricing page and Decisions/Activity views
