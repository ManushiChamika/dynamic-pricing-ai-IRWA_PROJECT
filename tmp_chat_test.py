from streamlit.testing.v1 import AppTest
import os

os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")

app = AppTest.from_file("app/streamlit_app.py")
# Enable session for chat test
app.session_state["session"] = {"user_id": 1, "full_name": "Test User", "email": "test@example.com"}
app.session_state["current_section"] = "AI CHAT"
app.session_state["is_dark_mode"] = False
app.query_params["page"] = "dashboard"
app.query_params["section"] = "chat"

app.run(timeout=15)

initial_history = app.session_state["chat_history"] if "chat_history" in app.session_state else None
print("initial history", initial_history)

chat = app.chat_input
print("chat widget", chat)
chat[0].set_value("Hello pricing")
app.run(timeout=15)

after_history = app.session_state["chat_history"] if "chat_history" in app.session_state else None
print("after input history", after_history)

chat[0].set_value("Hello")
app.run(timeout=15)
print("after second input", app.session_state["chat_history"] if "chat_history" in app.session_state else None)
print("awaiting", app.session_state["awaiting"] if "awaiting" in app.session_state else None)
