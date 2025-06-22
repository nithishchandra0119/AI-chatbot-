import os
from langchain_groq import ChatGroq
from langchain.memory import ChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import json

class LLMHandler:
    def __init__(self):
        self.available_models = {
            # Groq models (free)
            "Llama2-70b": "llama2-70b-4096",
            "Mixtral 8x7B": "mixtral-8x7b-32768",
            "Llama3-8b": "llama3-8b-8192",
        }
        
        # Define model providers to know which API to use
        self.model_providers = {
            "Llama2-70b": "groq",
            "Mixtral 8x7B": "groq",
            "Llama3-8b": "groq",
        }
        
        self.current_model = None
        self.message_history = ChatMessageHistory()
        self.llm = None
        self.provider = "groq"  # Always groq
        
        # Get API key from environment
        self.groq_api_key = os.environ.get("GROQ_API_KEY")
        
    def initialize_model(self, model_name, api_token=None):
        """Initialize the selected LLM model."""
        # Get the model ID from our available models
        model_id = self.available_models.get(model_name)
        if not model_id:
            raise ValueError(f"Model {model_name} not found in available models")
        
        # Use provided token or fall back to environment variable
        if not api_token:
            api_token = self.groq_api_key
            
        if not api_token:
            raise ValueError("Please provide a Groq API key in .env file or through the UI")
        
        try:
            # Initialize the LLM with ChatGroq
            self.llm = ChatGroq(
                model_name=model_id,
                groq_api_key=api_token,
                temperature=float(os.environ.get("DEFAULT_TEMPERATURE", 0.7)),
                max_tokens=int(os.environ.get("DEFAULT_MAX_TOKENS", 1024))
            )
            
            self.current_model = model_name
            return True
            
        except Exception as e:
            print(f"Error initializing Groq model: {str(e)}")
            return False
            
    def generate_response(self, user_input, system_message="You are a helpful assistant.", 
                         temperature=0.7, max_tokens=1024, context_docs=None):
        if not self.llm:
            raise ValueError("Model not initialized. Call initialize_model first.")
        
        # Update model parameters
        self.llm.temperature = temperature
        self.llm.max_tokens = max_tokens
        
        # Optional context
        context = ""
        if context_docs:
            context = "\nContext information:\n"
            for doc_name, doc_content in context_docs.items():
                context += f"From {doc_name}:\n{doc_content}\n\n"
        
        # Add the system message if it's not already in the history
        messages = self.message_history.messages
        if not messages or not isinstance(messages[0], SystemMessage):
            self.message_history.add_message(SystemMessage(content=system_message))
        
        # Add the user message to history
        full_input = context + user_input if context else user_input
        self.message_history.add_message(HumanMessage(content=full_input))
        
        try:
            # Generate response using the message history directly
            response = self.llm.invoke(self.message_history.messages)
            
            # Extract the content from the response
            if hasattr(response, 'content'):
                content = response.content
            else:
                # Fallback for unexpected response format
                content = str(response)
            
            # Add the AI response to history
            self.message_history.add_message(AIMessage(content=content))
            
            return content
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            print(error_msg)
            return error_msg
    
    def reset_memory(self):
        self.message_history = ChatMessageHistory()