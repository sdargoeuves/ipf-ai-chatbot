import streamlit as st
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage # Correct import for message objects

# New Imports for Memory and LCEL Runnable with History
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_sessions import ChatSession # Type hinting for memory function
from langchain.memory import ConversationBufferMemory
# Updated Prompt Imports for message history
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate


# ---- Streamlit Setup ---- #
st.set_page_config(layout="wide")
st.title("Ollama Chatbot with Memory") # Updated title

# ---- Sidebar Inputs ---- #
st.sidebar.header("Settings")

# Dropdown for model selection
model_options = ["llama3.2:latest", "qwen3:4b"] # Ensure these model names are correct for your Ollama setup
MODEL = st.sidebar.selectbox("Choose a Model", model_options, index=0)

# Removed MAX_HISTORY and CONTEXT_SIZE for now to simplify this step.
# We can add these back later if this version works.

# ---- Function to Clear Memory When Settings Change (Model Change) ---- #
# We'll clear memory only if the model changes for now.
def clear_memory():
    """Clears both display chat history and LangChain memory."""
    st.session_state.chat_history = []
    # Re-initialize the LangChain memory instance
    # This line still might show a deprecation warning depending on your LangChain version,
    # but should not prevent execution based on previous tests.
    st.session_state.memory = ConversationBufferMemory(return_messages=True)
    st.rerun() # Rerun to clear chat display immediately

# Clear memory if model changes
if "prev_model" not in st.session_state or st.session_state.prev_model != MODEL:
    clear_memory()
    st.session_state.prev_model = MODEL


# ---- Initialize Chat History for Display and LangChain Memory ---- #
# st.session_state.messages was used in the simple version.
# Let's switch to st.session_state.chat_history for consistency with the earlier attempt.
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Use return_messages=True as it's standard for chat models and LCEL
if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(return_messages=True)


# ---- LangChain LLM Setup ---- #
try:
    llm = ChatOllama(model=MODEL, streaming=True) # Re-enabling streaming
    # st.sidebar.success(f"Connected to Ollama model: {MODEL}") # Optional success message
except Exception as e:
    st.error(f"Failed to connect to Ollama model {MODEL}: {e}")
    st.stop() # Stop the app execution if connection fails


# ---- Prompt Template (Using ChatPromptTemplate for message history) ---- #
# This template defines how the list of messages from memory and the current human input
# are formatted before being sent to the chat model.
prompt_template = ChatPromptTemplate.from_messages([
    MessagesPlaceholder(variable_name="history"), # Placeholder for message history from memory
    HumanMessagePromptTemplate.from_template("{human_input}") # Template for the current user input
])

# ---- LCEL Chain Setup with Memory ---- #

# 1. Define the core chain: Combine the prompt template and the LLM.
core_chain = prompt_template | llm

# 2. Define a function to get the session history (the memory object).
def get_session_history(session_id: str) -> ChatSession:
    # We ignore session_id here as Streamlit session state is global per user.
    return st.session_state.memory

# 3. Wrap the core chain with RunnableWithMessageHistory
# This handles loading history before invoking the core chain
# and saving the current interaction to memory afterwards.
chain = RunnableWithMessageHistory(
    core_chain,
    get_session_history,
    input_messages_key="human_input", # Matches the variable name in HumanMessagePromptTemplate
    history_messages_key="history"     # Matches the variable name in MessagesPlaceholder
)

# ---- Display Chat History ---- #
# Now displaying from st.session_state.chat_history
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---- Handle User Input ---- #
if prompt := st.chat_input("Say something"):
    # 1. Add user message to display history and display it immediately
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Get AI Response (Streaming with Memory)
    with st.chat_message("assistant"):
        response_container = st.empty()
        full_response = ""

        try:
            # Invoke the RunnableWithMessageHistory chain.
            # Pass the current human input under the key specified by input_messages_key ("human_input").
            # RunnableWithMessageHistory automatically loads history using get_session_history,
            # passes it to the core_chain, runs the core_chain, and saves the turn to memory.
            for chunk in chain.stream(
                {"human_input": prompt}, # Pass only the current input string
                config={"configurable": {"session_id": "unused"}} # Required config for RunnableWithMessageHistory
            ):
                 # Chunks from chain.stream are typically message chunks
                if hasattr(chunk, 'content'):
                    full_response += chunk.content
                    response_container.markdown(full_response + "▌") # Add a blinking cursor effect
                # Handle other possible chunk types if necessary, though content is common

        except Exception as e:
            full_response = f"An error occurred during LLM invocation: {e}"
            st.error(full_response)
            # Decide if you want to add the error message to chat history
            # st.session_state.chat_history.append({"role": "assistant", "content": full_response})


        # Remove blinking cursor after streaming and display final response
        response_container.markdown(full_response)

    # 3. Add the final AI response to the display history
    st.session_state.chat_history.append({"role": "assistant", "content": full_response})

    # 4. Re-run the app to update the chat display and clear the input box
    st.rerun()

# Add an initial instructional message if no messages yet
if not st.session_state.chat_history:
    st.info("Type a message above to start the conversation!")


