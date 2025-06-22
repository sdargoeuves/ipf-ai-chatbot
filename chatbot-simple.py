import streamlit as st
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage # Correct import for message objects

# ---- Streamlit Setup ---- #
st.set_page_config(layout="wide")
st.title("Simple Ollama Chatbot")

# ---- Sidebar Inputs (Minimal) ---- #
st.sidebar.header("Settings")

# Dropdown for model selection
model_options = ["llama3.2:latest", "qwen3:4b"] # Ensure these model names are correct for your Ollama setup
MODEL = st.sidebar.selectbox("Choose a Model", model_options, index=0)

# ---- Initialize Chat History for Display ---- #
# We will store messages here ONLY for display purposes.
# We are NOT feeding this history back to the LLM in this simple version.
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---- LangChain LLM Setup ---- #
# Instantiate the LLM. This might be where a problem could occur if Ollama isn't running
# or the model isn't available.
try:
    llm = ChatOllama(model=MODEL)
    # Optional: Add a success message in sidebar if LLM connection seems okay
    # st.sidebar.success(f"Connected to Ollama model: {MODEL}")
except Exception as e:
    st.error(f"Failed to connect to Ollama model {MODEL}: {e}")
    st.stop() # Stop the app execution if connection fails

# ---- Display Chat History ---- #
# This loop should run every time the page loads and display messages
# that are already in st.session_state.messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ---- Handle User Input ---- #
# This block only runs when the user types something in the chat input
if prompt := st.chat_input("Say something"):

    # 1. Add user message to history and display it immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Get AI Response (Simple non-streaming invoke for first test)
    with st.chat_message("assistant"):
        # We are only sending the CURRENT message to the LLM.
        # No past history is included in this simple version.
        try:
            # Using invoke with a list of messages is standard for chat models
            response = llm.invoke([HumanMessage(content=prompt)])
            ai_content = response.content # Get the string content from the AIMessage object

            # 3. Add AI message to history and display it
            st.session_state.messages.append({"role": "assistant", "content": ai_content})
            st.markdown(ai_content)

        except Exception as e:
            error_message = f"An error occurred during LLM invocation: {e}"
            st.error(error_message)
            st.session_state.messages.append({"role": "assistant", "content": error_message}) # Log the error in history

    # 4. Re-run the app to update the chat display and clear the input box
    st.rerun()

# You can add a simple instructional message if no messages yet
if not st.session_state.messages:
    st.info("Type a message above to start the conversation!")

