import streamlit as st
import os
from dotenv import load_dotenv
from model import LLMHandler
from document import DocumentProcessor
import traceback
import base64
from datetime import datetime
import json
import uuid
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Load environment variables from .env file
load_dotenv()

# Apply custom CSS to make the UI more ChatGPT-like
def apply_custom_css():
    # Define custom CSS
    st.markdown("""
    <style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 64rem;
        margin: 0 auto;
    }
    
    /* Message styling */
    .chat-message {
        padding: 1rem;
        border-radius: 0.75rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    
    /* User message styling */
    .stChatMessage[data-testid="chat-message-user"] {
        background-color: #f7f7f8;
        border: 1px solid #e5e5e6;
    }
    
    /* Assistant message styling */
    .stChatMessage[data-testid="chat-message-assistant"] {
        background-color: #f0f4fe;
        border: 1px solid #d9e1fd;
    }
    
    /* Code block styling */
    pre {
        background-color: #282a36;
        color: #f8f8f2;
        padding: 1rem;
        border-radius: 0.5rem;
        overflow-x: auto;
    }
    
    /* Input box styling */
    .stChatInputContainer {
        padding: 0.5rem;
        background-color: white;
        border-radius: 0.75rem;
        border: 1px solid #e5e5e6;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 0.25rem;
        border: 1px solid #e5e5e6;
        background-color: white;
        color: #374151;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background-color: #f3f4f6;
        border-color: #d1d5db;
    }
    
    /* Hide password */
    div[data-baseweb="input"] input[type="password"] {
        -webkit-text-security: disc;
        -mox-text-security: disc;
        text-security: disc;
    }
    
    /* Model info footer */
    .model-info-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #f9f9fa;
        padding: 0.5rem;
        text-align: center;
        font-size: 0.75rem;
        color: #6b7280;
        border-top: 1px solid #e5e5e6;
        z-index: 1000;
    }
    </style>
    """, unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_model" not in st.session_state:
        st.session_state.current_model = os.getenv("DEFAULT_MODEL", "Llama3-8b")
    if "temperature" not in st.session_state:
        st.session_state.temperature = float(os.getenv("DEFAULT_TEMPERATURE", 0.7))
    if "max_tokens" not in st.session_state:
        st.session_state.max_tokens = int(os.getenv("DEFAULT_MAX_TOKENS", 1024))
    if "system_prompt" not in st.session_state:
        st.session_state.system_prompt = "You are a helpful assistant."
    if "context_docs" not in st.session_state:
        st.session_state.context_docs = {}
    if "llm_handler" not in st.session_state:
        st.session_state.llm_handler = LLMHandler()
    if "doc_processor" not in st.session_state:
        st.session_state.doc_processor = DocumentProcessor()
    if "model_initialized" not in st.session_state:
        st.session_state.model_initialized = False
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = {}
    if "current_conversation_id" not in st.session_state:
        st.session_state.current_conversation_id = str(uuid.uuid4())

def clear_chat():
    """Clear the chat history and start a new conversation."""
    st.session_state.messages = []
    st.session_state.llm_handler.reset_memory()
    st.session_state.current_conversation_id = str(uuid.uuid4())

def save_conversation():
    """Save the current conversation to conversation history."""
    if not st.session_state.messages:
        return "No messages to save."
    
    conversation_id = st.session_state.current_conversation_id
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Format the conversation title based on the first message
    title = f"Conversation {timestamp}"
    if len(st.session_state.messages) > 0:
        first_user_msg = next((msg for msg in st.session_state.messages if msg["role"] == "user"), None)
        if first_user_msg:
            # Use the first part of the first user message as title
            title = first_user_msg["content"][:40] + ("..." if len(first_user_msg["content"]) > 40 else "")
    
    # Save to conversation history
    st.session_state.conversation_history[conversation_id] = {
        "id": conversation_id,
        "title": title,
        "timestamp": timestamp,
        "messages": st.session_state.messages.copy(),
        "model": st.session_state.current_model,
        "temperature": st.session_state.temperature,
        "max_tokens": st.session_state.max_tokens,
        "system_prompt": st.session_state.system_prompt
    }
    
    # Create a download link for backup
    content = json.dumps({
        "id": conversation_id,
        "title": title,
        "timestamp": timestamp,
        "messages": st.session_state.messages,
        "model": st.session_state.current_model,
        "temperature": st.session_state.temperature,
        "max_tokens": st.session_state.max_tokens,
        "system_prompt": st.session_state.system_prompt
    }, indent=2)
    
    filename = f"conversation_{timestamp.replace(':', '-').replace(' ', '_')}.json"
    b64 = base64.b64encode(content.encode()).decode()
    download_link = f'<a href="data:file/json;base64,{b64}" download="{filename}">Download conversation backup</a>'
    
    return download_link

def load_conversation(conversation_id):
    """Load a conversation from history."""
    if conversation_id in st.session_state.conversation_history:
        conversation = st.session_state.conversation_history[conversation_id]
        st.session_state.messages = conversation["messages"].copy()
        st.session_state.current_model = conversation["model"]
        st.session_state.temperature = conversation["temperature"]
        st.session_state.max_tokens = conversation["max_tokens"]
        st.session_state.system_prompt = conversation["system_prompt"]
        st.session_state.current_conversation_id = conversation_id
        st.session_state.llm_handler.reset_memory()
        
        # Rebuild the LLM handler's memory from the messages
        for msg in st.session_state.messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "system":
                st.session_state.llm_handler.message_history.add_message(SystemMessage(content=content))
            elif role == "user":
                st.session_state.llm_handler.message_history.add_message(HumanMessage(content=content))
            elif role == "assistant":
                st.session_state.llm_handler.message_history.add_message(AIMessage(content=content))

def check_env_setup():
    """Check if the environment is properly configured."""
    issues = []
    
    # Check for Groq API token
    if not os.environ.get("GROQ_API_KEY"):
        issues.append("Groq API token not found in environment variables.")
    
    return issues

def format_markdown_content(content):
    """Format message content with better markdown support."""
    # This function could be extended to enhance markdown rendering
    return content

def main():
    st.set_page_config(
        page_title="AI Chat Assistant", 
        page_icon="🤖", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply custom CSS
    apply_custom_css()
    
    initialize_session_state()
    
    # Check environment setup
    env_issues = check_env_setup()
    
    # Create sidebar navigation
    with st.sidebar:
        # App title
        st.title("AI Chat Assistant 🤖")
        
        # Tabbed interface
        model_tab, settings_tab, docs_tab, history_tab = st.tabs(["Model", "Settings", "Documents", "History"])
        
        # Model tab
        with model_tab:
            if env_issues:
                st.warning("Environment Setup Issues:")
                for issue in env_issues:
                    st.write(f"- {issue}")
            
            # Securely handle API key
            api_key_container = st.container()
            
            with api_key_container:
                # Create a collapsible section for API key
                with st.expander("API Key Settings (Click to expand)", expanded=False):
                    groq_api_key = os.environ.get("GROQ_API_KEY", "")
                    new_api_key = st.text_input(
                        "Groq API Key", 
                        type="password",
                        value=groq_api_key if groq_api_key else "",
                        placeholder="Enter your Groq API key",
                        help="Your API key is stored securely in environment variables"
                    )
                    
                    # Save API key to environment if provided
                    if new_api_key and new_api_key != groq_api_key:
                        os.environ["GROQ_API_KEY"] = new_api_key
                        st.success("API key updated and secured!")
            
            # Model selection
            st.subheader("Model Selection")
            available_models = list(st.session_state.llm_handler.available_models.keys())
            model_name = st.selectbox(
                "Choose a model", 
                available_models,
                index=available_models.index(st.session_state.current_model) if st.session_state.current_model in available_models else 0
            )
            
            # Display model information with improved styling
            selected_model_id = st.session_state.llm_handler.available_models.get(model_name, "")
            st.markdown(f"**Model ID:** `{selected_model_id}`")
            
            if model_name != st.session_state.current_model or not st.session_state.model_initialized:
                if st.button("Initialize Model", use_container_width=True):
                    if not os.environ.get("GROQ_API_KEY"):
                        st.error("API key required. Please add it in the API Key Settings.")
                    else:
                        with st.spinner(f"Initializing {model_name}..."):
                            try:
                                success = st.session_state.llm_handler.initialize_model(
                                    model_name=model_name, 
                                    api_token=os.environ.get("GROQ_API_KEY")
                                )
                                if success:
                                    st.session_state.current_model = model_name
                                    st.session_state.model_initialized = True
                                    st.success(f"{model_name} initialized successfully!")
                                else:
                                    st.error(f"Failed to initialize {model_name}")
                            except Exception as e:
                                st.error(f"Error initializing model: {str(e)}")
                                with st.expander("Error Details"):
                                    st.code(traceback.format_exc())
        
        # Settings tab
        with settings_tab:
            # Model parameters
            st.header("Response Settings")
            
            st.session_state.temperature = st.slider(
                "Temperature", 
                min_value=0.0, 
                max_value=1.0, 
                value=st.session_state.temperature,
                step=0.1,
                help="Higher values make output more random, lower values more deterministic"
            )
            
            st.session_state.max_tokens = st.slider(
                "Max Tokens", 
                min_value=64, 
                max_value=4096, 
                value=st.session_state.max_tokens,
                step=64,
                help="Maximum number of tokens to generate"
            )
            
            st.header("System Instructions")
            st.session_state.system_prompt = st.text_area(
                "System Prompt", 
                value=st.session_state.system_prompt,
                height=150,
                help="Instructions that define the AI assistant's behavior",
                placeholder="You are a helpful assistant..."
            )
        
        # Documents tab
        with docs_tab:
            st.header("Document Context")
            
            uploaded_file = st.file_uploader(
                "Upload a document for context", 
                type=["txt", "pdf", "docx"],
                help="The AI will use the content of this document to inform its responses"
            )
            
            if uploaded_file is not None:
                with st.spinner("Processing document..."):
                    try:
                        # Process the uploaded file
                        doc_text = st.session_state.doc_processor.process_file(uploaded_file)
                        
                        # Summarize if text is too long
                        doc_text = st.session_state.doc_processor.summarize_text(doc_text, 5000)
                        
                        # Store in session state
                        file_name = uploaded_file.name
                        st.session_state.context_docs[file_name] = doc_text
                        
                        st.success(f"File '{file_name}' processed successfully!")
                    except Exception as e:
                        st.error(f"Error processing file: {str(e)}")
                        with st.expander("Error Details"):
                            st.code(traceback.format_exc())
            
            # Display uploaded documents with improved styling
            if st.session_state.context_docs:
                st.subheader("Active Documents")
                for doc_name in list(st.session_state.context_docs.keys()):
                    with st.container():
                        col1, col2 = st.columns([5, 1])
                        with col1:
                            st.markdown(f"📄 **{doc_name}**")
                            with st.expander("Preview"):
                                st.markdown(st.session_state.context_docs[doc_name][:500] + "...")
                        with col2:
                            if st.button("🗑️", key=f"remove_{doc_name}"):
                                del st.session_state.context_docs[doc_name]
                                st.rerun()
        
        # History tab
        with history_tab:
            st.header("Conversation History")
            
            if not st.session_state.conversation_history:
                st.info("No saved conversations yet. Chat and save conversations to see them here.")
            else:
                for conv_id, conv in sorted(st.session_state.conversation_history.items(), 
                                           key=lambda x: x[1]["timestamp"], 
                                           reverse=True):
                    # Create a container for each conversation
                    with st.container():
                        col1, col2 = st.columns([5, 1])
                        with col1:
                            # Format timestamp to be more readable
                            timestamp = conv["timestamp"]
                            title = conv["title"]
                            
                            # Display conversation info
                            st.markdown(f"**{title}**")
                            st.caption(f"{timestamp} | Model: {conv['model']}")
                        
                        with col2:
                            # Load button
                            if st.button("Load", key=f"load_{conv_id}"):
                                load_conversation(conv_id)
                                st.rerun()
        
        # Conversation management
        st.markdown("---")
        st.header("Conversation")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ New Chat", use_container_width=True):
                clear_chat()
                st.rerun()
        
        with col2:
            if st.button("💾 Save Chat", use_container_width=True):
                download_link = save_conversation()
                st.markdown(download_link, unsafe_allow_html=True)
                st.success("Conversation saved! You can access it in the History tab.")
    
    # Main chat interface
    chat_container = st.container()
    
    # Add a subtle header to the chat area
    st.markdown("<h2 style='text-align: center; color: #4b5563;'>AI Chat Assistant</h2>", unsafe_allow_html=True)
    
    # Display a warning if model is not initialized
    if not st.session_state.model_initialized:
        st.warning("Please initialize a model first using the sidebar.")
    
    # Add some space before chat messages
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Display chat messages with improved styling
    with chat_container:
        if not st.session_state.messages:
            # Show welcome message when no messages exist
            st.markdown("""
            <div style="text-align: center; padding: 3rem; color: #6b7280;">
                <h3>Welcome to AI Chat Assistant</h3>
                <p>Start a conversation by typing a message below.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    if message["role"] == "assistant":
                        st.markdown(format_markdown_content(message["content"]))
                    else:
                        st.write(message["content"])
    
    # Chat input 
    user_input = st.chat_input(
        "Type your message here...", 
        disabled=not st.session_state.model_initialized
    )
    
    if user_input:
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Display user message
        with st.chat_message("user"):
            st.write(user_input)
        
        # Generate response from LLM
        if st.session_state.model_initialized:
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        response = st.session_state.llm_handler.generate_response(
                            user_input=user_input,
                            system_message=st.session_state.system_prompt,
                            temperature=st.session_state.temperature,
                            max_tokens=st.session_state.max_tokens,
                            context_docs=st.session_state.context_docs
                        )
                        st.markdown(format_markdown_content(response))
                        
                        # Add assistant message to chat
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    except Exception as e:
                        error_msg = f"Error generating response: {str(e)}"
                        st.error(error_msg)
                        
                        # Add error message to chat
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # Display a footer with model info when a model is initialized
    if st.session_state.model_initialized:
        st.markdown(f"""
        <div class="model-info-footer">
            <span><strong>Model:</strong> {st.session_state.current_model}</span> | 
            <span><strong>Temperature:</strong> {st.session_state.temperature}</span> | 
            <span><strong>Max tokens:</strong> {st.session_state.max_tokens}</span>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()