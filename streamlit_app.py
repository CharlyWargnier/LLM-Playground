import streamlit as st
import openai
import requests

st.set_page_config(page_title="Open-LLM Playground - via DeepInfra", page_icon='🦙')

MODEL_IMAGES = {
    "meta-llama/Meta-Llama-3-8B-Instruct": "https://em-content.zobj.net/source/twitter/376/llama_1f999.png",
    "codellama/CodeLlama-34b-Instruct-hf": "https://em-content.zobj.net/source/twitter/376/llama_1f999.png",
    "mistralai/Mistral-7B-Instruct-v0.1": "https://em-content.zobj.net/source/twitter/376/tornado_1f32a-fe0f.png",
    "mistralai/Mixtral-8x7B-Instruct-v0.1": "https://em-content.zobj.net/source/twitter/376/tornado_1f32a-fe0f.png",
}

# Create a mapping from formatted model names to their original identifiers
def format_model_name(model_key):
    parts = model_key.split('/')
    model_name = parts[-1]  # Get the last part after '/'
    name_parts = model_name.split('-')
    
    if "Meta-Llama-3-8B-Instruct" in model_key:
        return "Llama 3 8B-Instruct"
    elif "codellama/CodeLlama-34b-Instruct-hf" in model_key or "mistralai/Mistral-7B-Instruct-v0.1" in model_key:
        return None  # Filter out Codellama 34B and Mistral 7B
    else:
        formatted_name = ' '.join(name_parts[:-2]).title()  # General formatting for other models
        return formatted_name

# Filter out None values and create a final dictionary of models to display
formatted_names_to_identifiers = {format_model_name(key): key for key in MODEL_IMAGES.keys() if format_model_name(key) is not None}

selected_formatted_name = st.sidebar.radio(
    "Select LLM Model",
    list(formatted_names_to_identifiers.keys())
)

selected_model = formatted_names_to_identifiers[selected_formatted_name]

if MODEL_IMAGES[selected_model].startswith("http"):
    st.image(MODEL_IMAGES[selected_model], width=90)
else:
    st.write(f"Model Icon: {MODEL_IMAGES[selected_model]}", unsafe_allow_html=True)





# Display the selected model using the formatted name
model_display_name = selected_formatted_name  # Already formatted
# st.write(f"Model being used: `{model_display_name}`")

st.sidebar.markdown('---')

API_KEY = st.secrets["api_key"]

openai.api_base = "https://api.deepinfra.com/v1/openai"
MODEL_CODELLAMA = selected_model

def get_response(api_key, model, user_input, max_tokens, top_p):
    openai.api_key = api_key
    try:
        response_json = {}
        if "meta-llama/Meta-Llama-3-8B-Instruct" in model:
            # Assume different API setup for Meta-Llama
            response = requests.post(
                "https://api.deepinfra.com/v1/openai/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": user_input}],
                    "max_tokens": max_tokens,
                    "top_p": top_p
                }
            )
            response_json = response.json()
        else:
            # Existing setup for other models
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": user_input}],
                max_tokens=max_tokens,
                top_p=top_p
            )
            response_json = response if isinstance(response, dict) else response.__dict__

        if 'choices' in response_json and response_json['choices']:
            return response_json['choices'][0]['message']['content'], None
        else:
            return None, "No 'choices' key found in the response."
    except Exception as e:
        return None, str(e)

st.header(f"`{model_display_name}` Model")

with st.expander("About this app"):
    st.write("""
    🎈 Welcome to our [Streamlit](https://streamlit.io) Chatbot app where you can interact with Meta's new [Llama 3](https://llama.meta.com/llama3/) `8B-Instruct` and Mixtral `8X7B`:

    - **Select LLM Model**: Pick your model between `Llama 3 8B-Instruct` and `Mixtral 8X7B` (more soon).
    - **Max Tokens**: You can set the max number of tokens for the model's response, anywhere from `100` to a `30,000`.
    - **Top P**: Tweak the probability threshold for random sampling.
    
    For more detailed info, you can consult [DeepInfra's documentation](https://deepinfra.com/docs/advanced/openai_api). 
    """)

if "api_key" not in st.session_state:
    st.session_state.api_key = ""

with st.sidebar:
    #max_tokens = st.slider('Max Tokens', 500, 500, 100000)
    max_tokens = st.slider('Max Tokens', min_value=100, max_value=30000 , value=200, step=100)

    top_p = st.slider('Top P', 0.0, 1.0, 0.5, 0.05)

if max_tokens > 500:
    user_provided_api_key = st.text_input("👇 Your DeepInfra API Key", value=st.session_state.api_key, type='password')
    if user_provided_api_key:
        st.session_state.api_key = user_provided_api_key
    if not st.session_state.api_key:
        st.warning("❄️ If you want to try this app with more than `500` tokens, you must provide your own DeepInfra API key. Get yours here → https://deepinfra.com/dash/api_keys")

if max_tokens <= 512 or st.session_state.api_key:
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
        
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response, error = get_response(st.session_state.api_key, MODEL_CODELLAMA, prompt, max_tokens, top_p)
                if error:
                    st.error(f"Error: {error}") 
                else:
                    placeholder = st.empty()
                    placeholder.markdown(response)
                    message = {"role": "assistant", "content": response}
                    st.session_state.messages.append(message)

# Clear chat history function and button
def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
st.sidebar.button('Clear Chat History', on_click=clear_chat_history)
