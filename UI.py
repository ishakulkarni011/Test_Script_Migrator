# UI.py
import os
import traceback
import streamlit as st
import httpx
from dotenv import load_dotenv

load_dotenv()

# Defaults from .env
BACKEND_URL = os.getenv("BACKEND_URL")
OUTPUT_DIR = os.getenv("OUTPUT_DIR")

st.set_page_config(page_title="Test Script Migration", layout="wide")

# Centered header
st.markdown(
    """
    <div style="text-align: center;">
        <h1>Test Script Migration</h1>
        <p style="font-size: 1.1rem;">
            Upload a Protractor test file, choose a Python test framework, and generate Selenium code
            using a free local open-source LLM (Ollama) via the FastAPI backend.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def call_backend_convert_sync(filename: str, framework: str, source: str) -> str:
    timeout = httpx.Timeout(600.0, connect=30.0)
    with httpx.Client(timeout=timeout) as client:
        r = client.post(
            f"{BACKEND_URL.rstrip('/')}/convert",
            json={"filename": filename, "framework": framework, "source": source},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Backend error {r.status_code}: {r.text}")
        return r.json()["python_code"]

st.divider()

st.write("Step 1")
uploaded = st.file_uploader("Upload Protractor file (.js / .ts)", type=["js", "ts"])

st.write("Step 2")
framework_label = st.selectbox("Target framework", ["Pytest", "Unittest", "BDD"], index=0)

FRAMEWORK_MAP = {
    "Pytest": "pytest",
    "Unittest": "unittest",
    "BDD": "bdd",
}
framework = FRAMEWORK_MAP[framework_label]

source_text = None
if uploaded is not None:
    file_bytes = uploaded.getvalue()
    source_text = file_bytes.decode("utf-8", errors="replace")
    size_kb = len(file_bytes) / 1024

    st.success("File uploaded successfully.")
    st.write(f"**File:** {uploaded.name}")
    st.write(f"**Size:** {size_kb:.1f} KB")
else:
    st.info("Upload a Protractor test file to begin.")

st.markdown("<br>", unsafe_allow_html=True)

# Center the Generate button
left, center, right = st.columns([1, 1, 1])
with center:
    generate = st.button("Generate Scripts", type="primary", disabled=uploaded is None)

if generate and uploaded is not None and source_text is not None:
    try:
        with st.spinner("Generating Python Selenium code..."):
            python_code = call_backend_convert_sync(uploaded.name, framework, source_text)

        st.subheader("Generated Python Selenium Script")
        st.code(python_code, language="python")

        ensure_output_dir()
        base = os.path.splitext(uploaded.name)[0]
        out_filename = f"{base}_{framework_label.lower()}.py"
        out_path = os.path.join(OUTPUT_DIR, out_filename)

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(python_code)

        st.download_button(
            label="Download generated Python file",
            data=python_code,
            file_name=out_filename,
            mime="text/x-python",
        )

    except Exception as e:
        st.error(str(e) if str(e) else e.__class__.__name__)
        st.code(traceback.format_exc())

st.divider()
st.caption(
    "Notes: Ensure Ollama is running (ollama serve), the model exists (ollama list), "
    "and the backend is running at BACKEND_URL."
)
