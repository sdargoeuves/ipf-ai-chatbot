import streamlit as st
#from langchain.chat_models import ChatOllama # Older import style
#from langchain_community.chat_models import ChatOllama # Older import style
from langchain_ollama import ChatOllama # Correct modern import

# New Imports for LCEL and ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_sessions import ChatSession # Type hinting for memory function
from langchain.memory import ConversationBufferMemory
# Updated Prompt Imports
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate

# ---- Streamlit Setup ---- #
st.set_page_config(layout="wide")
st.title("My Local Chatbot")

# ---- Sidebar Inputs ---- #
st.sidebar.header("Settings")

# Dropdown for model selection
model_options = ["llama3.2", "deepseek-r1:1.5b"] # Ensure these model names are correct for your Ollama setup
MODEL = st.sidebar.selectbox("Choose a Model", model_options, index=0)

# Inputs for max history and context size
# Note: MAX_HISTORY below is used only for the *display* history trimming.
# ConversationBufferMemory itself does not have a message or token limit by default.
# To limit the memory fed to the LLM, you would need a different memory type
# like ConversationTokenBufferMemory and potentially configure history in RunnableWithMessageHistory.
# For now, we maintain the original behavior of trimming only the display.
MAX_HISTORY = st.sidebar.number_input("Max Display History (Turns)", min_value=1, max_value=10, value=2, step=1)
CONTEXT_SIZE = st.sidebar.number_input("Context Size (LLM Config - often ignored by ChatOllama unless specified)", min_value=1024, max_value=16384, value=8192, step=1024) # Note: Context size is often passed directly to the LLM client, not a chain setting. ChatOllama might require specific config.

# ---- Function to Clear Memory When Settings Change ---- #
def clear_memory():
    """Clears both display chat history and LangChain memory."""
    st.session_state.chat_history = []
    # Re-initialize the LangChain memory instance
    # This is the line causing the specific ConversationBufferMemory warning,
    # but it's currently the standard way to instantiate it for this purpose.
    st.session_state.memory = ConversationBufferMemory(return_messages=True)
    st.rerun() # Rerun to clear chat display immediately

# Clear memory if settings are changed or model changes
# Added model check as changing model should also clear context
if ("prev_context_size" not in st.session_state or st.session_state.prev_context_size != CONTEXT_SIZE) or \
   ("prev_model" not in st.session_state or st.session_state.prev_model != MODEL):
    clear_memory()
    st.session_state.prev_context_size = CONTEXT_SIZE
    st.session_state.prev_model = MODEL


# ---- Initialize Chat Memory ---- #
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Use return_messages=True as it's standard for chat models and LCEL
# This is the line causing the specific ConversationBufferMemory warning.
if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(return_messages=True)

# ---- LangChain LLM Setup ---- #
# Passing context_size here might depend on ChatOllama implementation details.
# Often model parameters are passed directly to the client or during initialization.
llm = ChatOllama(model=MODEL, streaming=True)

# ---- Prompt Template (Using ChatPromptTemplate for message history) ---- #
# This template defines how the list of messages from memory and the current human input
# are formatted before being sent to the chat model.
prompt_template = ChatPromptTemplate.from_messages([
    MessagesPlaceholder(variable_name="history"), # Placeholder for message history from memory
    HumanMessagePromptTemplate.from_template("{human_input}") # Template for the current user input
])

# ---- LCEL Chain Setup ---- #

# 1. Define the core chain: Combine the prompt template and the LLM.
# This chain expects a dictionary with keys "history" (list of messages)
# and "human_input" (string).
core_chain = prompt_template | llm

# 2. Define a function to get the session history (the memory object).
# RunnableWithMessageHistory requires a function that takes a session ID
# and returns a BaseChatMemory or similar object.
# In Streamlit, we'll use a fixed session ID and return the state memory.
def get_session_history(session_id: str) -> ChatSession:
    # Although session_id is required by the signature, we ignore it
    # as Streamlit manages session state globally for the user.
    # For multi-user Streamlit apps, you might use session_id more dynamically.
    return st.session_state.memory

# 3. Wrap the core chain with RunnableWithMessageHistory
# This handles loading history before invoking the core chain
# and saving the current interaction to memory afterwards.
# - input_messages_key: The key in the input dictionary that contains the *current* human message string.
# - history_messages_key: The key in the prompt template where the loaded history (list of messages) should be placed.
chain = RunnableWithMessageHistory(
    core_chain,
    get_session_history,
    input_messages_key="human_input", # Matches the variable name in HumanMessagePromptTemplate
    history_messages_key="history"     # Matches the variable name in MessagesPlaceholder
)

# ---- Display Chat History ---- #
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---- Trim Function (Removes Oldest Messages from DISPLAY History) ---- #
# This function ONLY affects the messages stored in st.session_state.chat_history
# for display purposes. It does NOT affect the LangChain memory object.
def trim_memory():
    # While the number of messages in display history exceeds twice the MAX_HISTORY (user + AI per turn)
    # and there's more than the very latest turn (2 messages)
    while len(st.session_state.chat_history) > MAX_HISTORY * 2 and len(st.session_state.chat_history) > 2:
        st.session_state.chat_history.pop(0)  # Remove oldest User message
        if st.session_state.chat_history: # Check again in case popping user made it empty
            st.session_state.chat_history.pop(0)  # Remove oldest AI response

# ---- Handle User Input ---- #
if prompt := st.chat_input("Say something"):
    # Show User Input Immediately
    with st.chat_message("user"):
        st.markdown(prompt)

    # Store user input in the display history
    st.session_state.chat_history.append({"role": "user", "content": prompt})

    # Trim display chat history BEFORE generating response
    trim_memory()

    # ---- Get AI Response (Streaming) ---- #
    with st.chat_message("assistant"):
        response_container = st.empty()
        full_response = ""

        # Invoke the RunnableWithMessageHistory chain.
        # Pass the current human input under the key specified by input_messages_key ("human_input").
        # RunnableWithMessageHistory automatically loads history using get_session_history
        # and passes it to the core_chain under the key specified by history_messages_key ("history").
        # It also saves the current turn (input and output) to the memory afterwards.
        # The config is needed by RunnableWithMessageHistory to identify the session.
        try:
            for chunk in chain.stream(
                {"human_input": prompt}, # Pass only the current input string
                config={"configurable": {"session_id": "unused"}} # Required config for RunnableWithMessageHistory
            ):
                 # Chunks from chain.stream with ChatOllama | prompt_template are typically AIMessageChunk objects
                if hasattr(chunk, 'content'): # Check if the chunk has a content attribute
                    full_response += chunk.content
                    response_container.markdown(full_response + "▌") # Add a blinking cursor effect
        except Exception as e:
            full_response = f"An error occurred: {e}"
            st.error(full_response)

        # Remove blinking cursor after streaming
        response_container.markdown(full_response)


    # Store the final AI response in the display history
    st.session_state.chat_history.append({"role": "assistant", "content": full_response})

    # Trim display history AFTER storing the response
    # (RunnableWithMessageHistory handles saving to LangChain memory automatically)
    trim_memory()

    # Re-run the app to update the chat display and inputs immediately
    st.rerun()

