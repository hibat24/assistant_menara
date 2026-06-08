import streamlit as st
import requests
import json

# Set up page configurations
st.set_page_config(
    page_title="NM 10.1.008 RAG Testing Client",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    .reportview-container {
        background: #f8f9fa;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stChatFloatingInputContainer {
        bottom: 20px;
    }
    .context-box {
        background-color: #f0f2f6;
        border-left: 5px solid #0068c9;
        padding: 10px;
        margin: 5px 0;
        border-radius: 4px;
        font-size: 0.9rem;
    }
    .sidebar-status {
        padding: 10px;
        border-radius: 5px;
        background-color: #262730;
        color: white;
        margin-bottom: 10px;
    }
    .badge-ok {
        background-color: #28a745;
        color: white;
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .badge-error {
        background-color: #dc3545;
        color: white;
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 0.8rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Main Title and Subtitle
st.title("💬 NM 10.1.008 RAG Assistant")
st.caption("Testing client for the Moroccan Concrete Standard (NM 10.1.008) QA API")

# Sidebar Configuration
st.sidebar.image("https://img.icons8.com/color/96/concrete-mixer.png", width=80)
st.sidebar.title("Configuration & Tools")

# API Base URL configuration
api_url = st.sidebar.text_input("Backend API URL", value="http://localhost:8000")

# Fetch Backend Status function
def get_backend_status():
    try:
        response = requests.get(f"{api_url}/status", timeout=3)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

# Check Backend connection
status_data = get_backend_status()

# Display status in the sidebar
st.sidebar.subheader("API Status")
if status_data:
    st.sidebar.markdown(f"🟢 **Online**")
    
    # Details in sidebar
    with st.sidebar.expander("System Specifications", expanded=False):
        st.write(f"**Model:** `{status_data.get('llm_model')}`")
        st.write(f"**API Key Configured:** {'Yes' if status_data.get('api_key_configured') else 'No'}")
        st.write(f"**Collection Name:** `{status_data.get('collection_name')}`")
        st.write(f"**Chunks Indexed:** `{status_data.get('collection_size')}`")
        st.write(f"**DB Path:** `{status_data.get('chroma_db_path')}`")
else:
    st.sidebar.markdown(f"🔴 **Offline** (Could not reach {api_url})")

st.sidebar.divider()

# API Key Settings Block
st.sidebar.subheader("API Key Settings")
groq_key_configured = status_data.get('api_key_configured') if status_data else False
if not groq_key_configured:
    st.sidebar.warning("⚠️ Groq API key is missing on the server. Please enter your key below:")
    groq_api_key = st.sidebar.text_input("Groq API Key", type="password", help="Retrieve your API key from https://console.groq.com")
else:
    st.sidebar.success("🔑 API Key configured on server")
    groq_api_key = st.sidebar.text_input("Override API Key (Optional)", type="password", help="Enter a custom key to override the server configuration.")

st.sidebar.divider()

# RAG Hyperparameters Section
st.sidebar.subheader("RAG Parameters")
index_top_k = st.sidebar.slider(
    "Index Top K (Retrieve)", 
    min_value=1, 
    max_value=20, 
    value=4, 
    help="Number of document chunks retrieved from Chroma DB database initially."
)
reranker_top_n = st.sidebar.slider(
    "Reranker Top N (Context to LLM)", 
    min_value=1, 
    max_value=10, 
    value=2, 
    help="Number of retrieved chunks passed to the LLM after reranking them."
)

st.sidebar.divider()

# Ingestion Section
st.sidebar.subheader("Database Management")
st.sidebar.info("Ensure PDF documents are placed in `rag/corpus` folder in the backend before ingesting.")

if st.sidebar.button("📂 Trigger Corpus Ingestion", use_container_width=True):
    with st.spinner("Ingesting PDF documents from `rag/corpus`..."):
        try:
            response = requests.post(f"{api_url}/ingest", timeout=300)
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    st.sidebar.success(f"Ingested successfully!\n- Files: {', '.join(result.get('ingested_files', []))}\n- Total Chunks: {result.get('total_chunks')}")
                elif result.get("status") == "no_files":
                    st.sidebar.warning(result.get("message"))
                else:
                    st.sidebar.error(f"Status: {result.get('status')}\nMessage: {result.get('message')}")
            else:
                st.sidebar.error(f"Error {response.status_code}: {response.text}")
        except Exception as e:
            st.sidebar.error(f"Request failed: {str(e)}")
            
        # Refresh page state to update status
        st.rerun()

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Clear Chat History button
if st.sidebar.button("🧹 Clear Chat History", use_container_width=True):
    st.session_state.messages = []
    st.rerun()

# Render existing messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # If there are contexts associated with this message, render them in an expander
        if "contexts" in message and message["contexts"]:
            with st.expander(f"📚 Retrieved Contexts ({len(message['contexts'])} chunks)"):
                for idx, ctx in enumerate(message["contexts"]):
                    st.markdown(f"**Chunk #{idx+1}:**")
                    st.markdown(f"<div class='context-box'>{ctx}</div>", unsafe_allow_html=True)

# Chat Input for query
if query := st.chat_input("Ex: Quelle est la résistance caractéristique minimale sur cylindres pour la classe B25?"):
    # 1. Display user query in chat
    with st.chat_message("user"):
        st.markdown(query)
    
    # Add to history
    st.session_state.messages.append({"role": "user", "content": query})
    
    # 2. Query the backend API
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        with st.spinner("Querying Moroccan Concrete RAG Backend..."):
            try:
                payload = {
                    "query": query,
                    "index_top_k": index_top_k,
                    "reranker_top_n": reranker_top_n
                }
                if groq_api_key:
                    payload["groq_api_key"] = groq_api_key
                res = requests.post(f"{api_url}/query", json=payload, timeout=120)
                
                if res.status_code == 200:
                    data = res.json()
                    answer = data.get("answer", "No answer found.")
                    contexts = data.get("contexts", [])
                    
                    # Display the response
                    response_placeholder.markdown(answer)
                    
                    # Display the sources in expander
                    if contexts:
                        with st.expander(f"📚 Retrieved Contexts ({len(contexts)} chunks)"):
                            for idx, ctx in enumerate(contexts):
                                st.markdown(f"**Chunk #{idx+1}:**")
                                st.markdown(f"<div class='context-box'>{ctx}</div>", unsafe_allow_html=True)
                    
                    # Add to session history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "contexts": contexts
                    })
                    
                else:
                    err_msg = f"⚠️ API Error (Status {res.status_code}): {res.text}"
                    response_placeholder.markdown(err_msg)
                    st.session_state.messages.append({"role": "assistant", "content": err_msg})
                    
            except Exception as e:
                err_msg = f"⚠️ Failed to connect to API backend: {str(e)}"
                response_placeholder.markdown(err_msg)
                st.session_state.messages.append({"role": "assistant", "content": err_msg})
