"""
Custom Chat API Interface
Allows users to connect to external APIs and chat with custom endpoints
"""

import streamlit as st
import httpx
import json
import asyncio
import sys
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class APIClient:
    """Generic HTTP client for external APIs"""
    
    def __init__(self, base_url: str, headers: Optional[Dict[str, str]] = None):
        self.base_url = base_url.rstrip('/')
        self.headers = headers or {}
        
    async def post_request(
        self, 
        endpoint: str, 
        data: Dict[str, Any],
        timeout: int = 30
    ) -> Dict[str, Any]:
        """Make a POST request to the API"""
        async with httpx.AsyncClient(timeout=timeout) as client:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            
            response = await client.post(
                url=url,
                json=data,
                headers=self.headers
            )
            
            response.raise_for_status()
            return response.json()
    
    async def get_request(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """Make a GET request to the API"""
        async with httpx.AsyncClient(timeout=timeout) as client:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            
            response = await client.get(
                url=url,
                params=params,
                headers=self.headers
            )
            
            response.raise_for_status()
            return response.json()


def validate_url(url: str) -> bool:
    """Validate if the URL is properly formatted"""
    try:
        import re
        pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return pattern.match(url) is not None
    except:
        return False


async def test_api_connection(client: APIClient, test_endpoint: str) -> tuple[bool, str]:
    """Test the API connection"""
    try:
        # Try a simple GET request first
        await client.get_request(test_endpoint)
        return True, "✅ Connection successful"
    except httpx.HTTPStatusError as e:
        return False, f"❌ HTTP Error: {e.response.status_code} - {e.response.text}"
    except httpx.ConnectError:
        return False, "❌ Connection failed: Unable to connect to the server"
    except httpx.TimeoutException:
        return False, "❌ Connection timeout: Server is not responding"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"


async def send_chat_message(
    client: APIClient,
    message: str,
    chat_endpoint: str,
    message_format: Dict[str, Any],
    conversation_history: List[Dict[str, str]]
) -> tuple[bool, str]:
    """Send a chat message to the API"""
    try:
        # Prepare the request data based on the message format
        request_data = message_format.copy()
        
        # Replace placeholders in the message format
        def replace_placeholders(obj, message_text, history):
            if isinstance(obj, dict):
                return {k: replace_placeholders(v, message_text, history) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_placeholders(item, message_text, history) for item in obj]
            elif isinstance(obj, str):
                obj = obj.replace("{{message}}", message_text)
                obj = obj.replace("{{conversation_history}}", json.dumps(history))
                return obj
            return obj
        
        request_data = replace_placeholders(request_data, message, conversation_history)
        
        # Send the request
        response = await client.post_request(chat_endpoint, request_data)
        
        # Extract the response text (this might need customization based on API response format)
        response_text = ""
        if isinstance(response, dict):
            # Common response patterns
            possible_keys = ['response', 'message', 'text', 'content', 'answer', 'reply']
            for key in possible_keys:
                if key in response:
                    response_text = str(response[key])
                    break
            
            if not response_text:
                # If no standard key found, try to get the first string value
                for value in response.values():
                    if isinstance(value, str) and len(value) > 0:
                        response_text = value
                        break
                
                # If still no response, return the full JSON
                if not response_text:
                    response_text = json.dumps(response, indent=2)
        else:
            response_text = str(response)
        
        return True, response_text
        
    except Exception as e:
        return False, f"Error sending message: {str(e)}"


def run_async(coro):
    """Run async function in sync context"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, use thread executor
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


# Streamlit Page Configuration
st.set_page_config(
    page_title="NotebookLlama - Custom Chat API",
    page_icon="🔗",
    layout="wide",
    menu_items={
        "Get Help": "https://github.com/run-llama/notebooklm-clone/discussions/categories/general",
        "Report a bug": "https://github.com/run-llama/notebooklm-clone/issues/",
        "About": "Custom Chat API interface for connecting to external AI services",
    },
)

st.sidebar.header("Custom Chat API 🔗")
st.sidebar.info("Connect to external AI APIs and chat with custom endpoints!")

st.markdown("---")
st.markdown("## NotebookLlama - Custom Chat API 🔗")

# Initialize session state
if "api_client" not in st.session_state:
    st.session_state.api_client = None
if "api_connected" not in st.session_state:
    st.session_state.api_connected = False
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# Configuration Section
st.markdown("### 🔧 API Configuration")

with st.expander("API Settings", expanded=not st.session_state.api_connected):
    col1, col2 = st.columns(2)
    
    with col1:
        api_url = st.text_input(
            "API Base URL",
            placeholder="https://api.example.com",
            help="Enter the base URL of your API endpoint"
        )
        
        chat_endpoint = st.text_input(
            "Chat Endpoint",
            value="chat",
            placeholder="chat",
            help="The endpoint path for chat (e.g., 'chat', 'v1/chat/completions')"
        )
        
        test_endpoint = st.text_input(
            "Test Endpoint (optional)",
            value="health",
            placeholder="health",
            help="Endpoint to test connection (e.g., 'health', 'status')"
        )
    
    with col2:
        # API Headers
        st.markdown("**Request Headers**")
        
        use_auth = st.checkbox("Use Authentication", value=False)
        
        headers = {}
        if use_auth:
            auth_type = st.selectbox(
                "Authentication Type",
                ["Bearer Token", "API Key", "Custom Header"]
            )
            
            if auth_type == "Bearer Token":
                token = st.text_input("Bearer Token", type="password")
                if token:
                    headers["Authorization"] = f"Bearer {token}"
            elif auth_type == "API Key":
                api_key = st.text_input("API Key", type="password")
                key_header = st.text_input("API Key Header", value="X-API-Key")
                if api_key and key_header:
                    headers[key_header] = api_key
            elif auth_type == "Custom Header":
                header_name = st.text_input("Header Name")
                header_value = st.text_input("Header Value", type="password")
                if header_name and header_value:
                    headers[header_name] = header_value
        
        # Content type
        content_type = st.selectbox(
            "Content Type",
            ["application/json", "application/x-www-form-urlencoded", "text/plain"]
        )
        headers["Content-Type"] = content_type

# Message Format Configuration
st.markdown("**Message Format**")
st.markdown("Configure how messages are sent to your API. Use `{{message}}` as placeholder for the user input.")

format_preset = st.selectbox(
    "Format Preset",
    [
        "Custom",
        "OpenAI Compatible",
        "Anthropic Compatible", 
        "Simple Message",
        "Conversation History"
    ]
)

# Predefined formats
if format_preset == "OpenAI Compatible":
    message_format = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": "{{message}}"}
        ]
    }
elif format_preset == "Anthropic Compatible":
    message_format = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 1000,
        "messages": [
            {"role": "user", "content": "{{message}}"}
        ]
    }
elif format_preset == "Simple Message":
    message_format = {
        "message": "{{message}}"
    }
elif format_preset == "Conversation History":
    message_format = {
        "message": "{{message}}",
        "history": "{{conversation_history}}"
    }
else:  # Custom
    message_format = {
        "message": "{{message}}"
    }

# JSON editor for message format
message_format_json = st.text_area(
    "Message Format (JSON)",
    value=json.dumps(message_format, indent=2),
    height=150,
    help="JSON format for sending messages. Use {{message}} placeholder for user input."
)

try:
    message_format = json.loads(message_format_json)
except json.JSONDecodeError as e:
    st.error(f"Invalid JSON format: {e}")
    message_format = {"message": "{{message}}"}

# Connection Controls
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔍 Test Connection", type="secondary"):
        if not api_url:
            st.error("Please enter an API URL")
        elif not validate_url(api_url):
            st.error("Please enter a valid URL")
        else:
            with st.spinner("Testing connection..."):
                client = APIClient(api_url, headers)
                success, message = run_async(test_api_connection(client, test_endpoint))
                
                if success:
                    st.success(message)
                else:
                    st.error(message)

with col2:
    if st.button("🔗 Connect", type="primary"):
        if not api_url:
            st.error("Please enter an API URL")
        elif not validate_url(api_url):
            st.error("Please enter a valid URL")
        else:
            st.session_state.api_client = APIClient(api_url, headers)
            st.session_state.api_connected = True
            st.session_state.api_url = api_url
            st.session_state.chat_endpoint = chat_endpoint
            st.session_state.message_format = message_format
            st.success("✅ Connected to API!")
            st.rerun()

with col3:
    if st.button("🔌 Disconnect"):
        st.session_state.api_client = None
        st.session_state.api_connected = False
        st.session_state.conversation_history = []
        st.session_state.chat_messages = []
        st.success("Disconnected from API")
        st.rerun()

# Connection Status
if st.session_state.api_connected:
    st.success(f"🟢 Connected to: {st.session_state.api_url}")
else:
    st.warning("🔴 Not connected to any API")

st.markdown("---")

# Chat Interface
if st.session_state.api_connected:
    st.markdown("### 💬 Chat Interface")
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_messages = []
        st.session_state.conversation_history = []
        st.rerun()
    
    # Display chat messages
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "timestamp" in message:
                st.caption(f"📅 {message['timestamp']}")
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat history
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_message = {
            "role": "user", 
            "content": prompt,
            "timestamp": timestamp
        }
        st.session_state.chat_messages.append(user_message)
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
            st.caption(f"📅 {timestamp}")
        
        # Send message to API
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                success, response = run_async(
                    send_chat_message(
                        st.session_state.api_client,
                        prompt,
                        st.session_state.chat_endpoint,
                        st.session_state.message_format,
                        st.session_state.conversation_history
                    )
                )
                
                if success:
                    st.markdown(response)
                    response_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.caption(f"📅 {response_timestamp}")
                    
                    # Add assistant response to chat history
                    assistant_message = {
                        "role": "assistant",
                        "content": response,
                        "timestamp": response_timestamp
                    }
                    st.session_state.chat_messages.append(assistant_message)
                    
                    # Update conversation history for context
                    st.session_state.conversation_history.append({
                        "user": prompt,
                        "assistant": response
                    })
                    
                    # Limit conversation history to prevent API payload from being too large
                    if len(st.session_state.conversation_history) > 10:
                        st.session_state.conversation_history = st.session_state.conversation_history[-10:]
                    
                else:
                    st.error(response)
                    error_message = {
                        "role": "assistant",
                        "content": f"❌ Error: {response}",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.chat_messages.append(error_message)
        
        st.rerun()

else:
    st.info("👆 Please configure and connect to an API to start chatting!")

# Help Section
st.markdown("---")
with st.expander("ℹ️ Help & Examples"):
    st.markdown("""
    ### How to use Custom Chat API
    
    1. **Configure API Settings**: Enter your API base URL and endpoints
    2. **Set Authentication**: Add necessary headers for authentication
    3. **Configure Message Format**: Customize how messages are sent to your API
    4. **Test Connection**: Verify your API is accessible
    5. **Connect & Chat**: Start chatting with your custom API
    
    ### Common API Formats
    
    **OpenAI Compatible:**
    ```json
    {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": "{{message}}"}
        ]
    }
    ```
    
    **Simple REST API:**
    ```json
    {
        "message": "{{message}}",
        "user_id": "user123"
    }
    ```
    
    **With Conversation History:**
    ```json
    {
        "query": "{{message}}",
        "context": "{{conversation_history}}"
    }
    ```
    
    ### Supported Placeholders
    - `{{message}}`: The user's current message
    - `{{conversation_history}}`: JSON string of previous conversation
    
    ### Examples of Compatible APIs
    - OpenAI API
    - Anthropic Claude API
    - Local LLMs (Ollama, LM Studio)
    - Custom chatbot APIs
    - Azure OpenAI Service
    - Google Bard API
    """)
