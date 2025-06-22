import streamlit as st
import os
from datetime import datetime

def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_model" not in st.session_state:
        st.session_state.current_model = "Llama 2"
    if "temperature" not in st.session_state:
        st.session_state.temperature = 0.7
    if "max_tokens" not in st.session_state:
        st.session_state.max_tokens = 1024
    if "system_prompt" not in st.session_state:
        st.session_state.system_prompt = "You are a helpful assistant."
    if "context_docs" not in st.session_state:
        st.session_state.context_docs = {}

def clear_chat():
    """Clear the chat history."""
    st.session_state.messages = []

def save_conversation():
    """Save the current conversation to a file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"conversation_{timestamp}.txt"
    
    with open(filename, "w") as f:
        for message in st.session_state.messages:
            f.write(f"{message['role']}: {message['content']}\n\n")
    
    return filename

def main():
    st.set_page_config(page_title="LLM Chat Assistant", page_icon="💬", layout="wide")
    
    initialize_session_state()
    
    st.title("🤖 LLM Chat Assistant")
    
    # Sidebar for settings
    with st.sidebar:
        st.header("Settings")
        
        st.session_state.current_model = st.selectbox(
            "Select Model", 
            ["Llama 2", "Falcon"]
        )
        
        st.session_state.temperature = st.slider(
            "Temperature", 
            min_value=0.0, 
            max_value=1.0, 
            value=st.session_state.temperature,
            step=0.1
        )
        
        st.session_state.max_tokens = st.slider(
            "Max Tokens", 
            min_value=64, 
            max_value=4096, 
            value=st.session_state.max_tokens,
            step=64
        )
        
        st.session_state.system_prompt = st.text_area(
            "System Prompt", 
            value=st.session_state.system_prompt,
            height=100
        )
        
        # File uploader
        st.header("Document Upload")
        uploaded_file = st.file_uploader("Upload a document for context", 
                                        type=["txt", "pdf", "docx"])
        
        if uploaded_file is not None:
            # Here we'd process the file and add to context
            file_name = uploaded_file.name
            st.success(f"File '{file_name}' uploaded successfully!")
            
            # Placeholder for file processing logic
            # This will be implemented in the document processing component
            st.session_state.context_docs[file_name] = "File content placeholder"
        
        # Display uploaded documents
        if st.session_state.context_docs:
            st.subheader("Uploaded Documents")
            for doc_name in st.session_state.context_docs:
                st.write(f"- {doc_name}")
                if st.button(f"Remove {doc_name}"):
                    del st.session_state.context_docs[doc_name]
                    st.experimental_rerun()
        
        # Conversation management
        st.header("Conversation")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Clear Chat"):
                clear_chat()
                st.experimental_rerun()
        
        with col2:
            if st.button("Save Chat"):
                filename = save_conversation()
                st.success(f"Saved as {filename}")
    
    # Chat interface
    chat_container = st.container()
    
    with chat_container:
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    
        # Chat input
        user_input = st.chat_input("Type your message here...")
        
        if user_input:
            # Add user message to chat
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Display user message
            with st.chat_message("user"):
                st.write(user_input)
            
            # Here's where we'd call the LLM - placeholder for now
            # This will be replaced with actual LLM call in the model integration component
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    # Placeholder response
                    response = f"This is a placeholder response. You selected {st.session_state.current_model} with temperature {st.session_state.temperature} and max tokens {st.session_state.max_tokens}."
                    
                    # In the actual implementation, we'll call the LLM here
                    st.write(response)
            
            # Add assistant message to chat
            st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()