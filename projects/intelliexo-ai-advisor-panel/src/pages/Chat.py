# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from langchain_nvidia_ai_endpoints import ChatNVIDIA
from dotenv import load_dotenv
import streamlit as st
from elevenlabs import play
from elevenlabs.client import ElevenLabs
from lightrag import LightRAG, QueryParam
from lightrag.llm import nvidia_openai_complete
from src.pages.Profile import get_profile_context
from src.pages.PersonaManager import load_personas
import os
import textract
import time

st.title("💬 IntelliExo: Your Panel of Personal AI Advisors")

### APP / PAGE CONFIGURATIONS ###
load_dotenv()
nvidia_api_key = os.getenv('NVIDIA_API_KEY')

client = ElevenLabs(
    api_key=os.getenv('ELEVENLABS_API_KEY')
)

model = "nvdev/mistralai/mistral-7b-instruct-v0.3"
store = {}

# Generate response
llm = ChatNVIDIA(
    model=model,
    nvidia_api_key=nvidia_api_key,
    base_url="https://integrate.api.nvidia.com/v1",
    temperature=0.2,
    top_p=0.7,
    max_tokens=2048,
)

### FUNCTION DEFINITIONS ###

def get_persona_prompt(persona_name):
    """Returns the prompt for the selected persona."""
    personas = load_personas()
    return personas[persona_name]["prompt"]

def get_summary(user_input):
    """Summarises a QnA transcript."""
    response = llm.invoke(
        "Summarise the following: " + user_input,
    )
    return response.content

def text_to_speech(text, persona_name):
    """Convert text to speech using ElevenLabs with persona-specific voice"""
    with st.spinner(f"Converting text to speech..."):
        personas = load_personas()
        voice_id = personas[persona_name]["voice_id"]
        audio_generator = client.generate(
            text=text,
            voice=voice_id,
            model="eleven_multilingual_v2",
            voice_settings={"stability":0.31, "similarity_boost": 0.98, "style": 0.46}
        )
        # Convert generator to bytes
        audio_bytes = b"".join(audio_generator)
        return audio_bytes

def construct_prompt(user_input, conversation_history, persona_name):
    conversation = f'role: assistant\ncontent: {get_persona_prompt(persona_name)}\n'

    user_context = get_profile_context()

    if st.session_state.personalize:
        conversation += f'user context: {user_context}\n\n\n'

    ## Get conversation history
    for speaker, message in conversation_history:
        conversation += f'role: {speaker}\ncontent: {message}\n'

    conversation += f'role: user\ncontent: {user_input}\nrole: assistant\ncontent: '

    return conversation

def get_response(user_input, conversation_history, persona_name, base_model=False):
    """Generates a response based on the selected persona and conversation history."""

    if base_model:
        st.toast("Getting response from base model...")
        print("Trying to get response from base model...")
        response = llm.invoke(
            str(conversation_history) + user_input
        )
        print("Response from base model: ", response.content)
        return response.content, []

    # Construct the prompt
    prompt = construct_prompt(user_input, conversation_history, persona_name)

    # Log the messages payload
    print("Messages Payload Before Chain Invocation: %s", prompt)
    
    persona_directory = './data/' + persona_name

    ## Initilalise the LightRAG model
    rag = LightRAG(
        working_dir=persona_directory,
        llm_model_func=nvidia_openai_complete,
    )

    with st.spinner(f"Indexing {persona_name}'s knowledge base..."):
        st.info("Running query on a new persona for the first time may take a little longer. Thanks for being patient")
        ## Insert all the persona's transcript into the graphml knowledge base
        try:
            for file in os.listdir(persona_directory):
                if file.endswith('.pdf') or file.endswith('.txt'):
                    file_path = os.path.join(persona_directory, file)
                    text_content = textract.process(file_path)
                    print(text_content.decode('utf-8'))
                    rag.insert(text_content.decode('utf-8'))
        except Exception as e:
            print(f"An error occurred while loading {persona_name}'s knowledge base: {e}")
            st.error(f"An error occurred while loading {persona_name}'s knowledge base: {e}")
            return "An error occurred while loading the knowledge base. Please try again later.", []
    
    st.toast(f"Loaded {persona_name}'s knowledge base!", icon="😺")
        
    with st.spinner(f"Consulting {persona_name}..."):
        ## Query the LightRAG
        try:
            response = rag.query(
                prompt,
                param=QueryParam(mode="hybrid")
            )
        except Exception as e:
            print(f"An error occurred while querying {persona_name}: {e}")
            st.error(f"An error occurred while querying {persona_name}. Is persona's folder empty? \n{e}")
            return "Sorry, I don't have the knowledge to answer that!", []
    
    st.toast(f"{persona_name} gave us their thoughts!", icon="🎉")

    return response, []

# Handle user input and generate responses
def ask_question(question, respondents):
    st.session_state.question_counter += 1  # Increment counter for each new question
    st.session_state.messages.append({"role": "user", "content": question, "respondents": respondents})
    responses = []
    summarise_response_button = False
    with st.spinner(f"Asking and picking their brains..."):
        for persona in st.session_state.chat_variables["selected_personas"]:
            response, sourced_texts = get_response(question, [(msg["role"], msg["content"]) for msg in st.session_state.messages if msg["role"] == "user" or msg["role"] == "assistant"], persona, persona==st.session_state.chat_variables["base_model"])
            responses.append({"role": "assistant", "content": response, "persona": persona, "sourced_texts": sourced_texts})
        st.session_state.messages.extend(responses)

    
# Initialize chat input in session state if not exists
if 'chat_input' not in st.session_state:
    st.session_state.chat_input = ""

def set_chat_input(question):
    st.session_state.chat_input = question

if not ("chat_variables" in st.session_state and "num_personas" in st.session_state.chat_variables and st.session_state.chat_variables["num_personas"] > 0):
    # Display a message to select personas
    st.info("Please select at least one persona to ask questions.")
else:
    # Initialize session state for storing messages and responses
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "knowledge_base" not in st.session_state:
        st.session_state.knowledge_base = {}

    if "question_counter" not in st.session_state:
        st.session_state.question_counter = 0

    summarise_response_button = False

    # Add suggested questions
    st.write("💡 Try asking:")
    col1, col2, col3 = st.columns(3)
    q1, q2, q3, q4, q5, q6 = "How do you think I can improve my leadership abilities?", "How do you approach problem-solving?", "Share a key life experience.", "Two of my best friends are in a fight. How can I help them reconcile?", "What is confucius teachings about?", "What can I do to level up my career while creating a postive impact on the people around me?"
    with col1:
        st.button(q1, 
                on_click=ask_question, 
                args=[q1, st.session_state.chat_variables["selected_personas"]],
                use_container_width=True)
        st.button(q2, 
                on_click=ask_question, 
                args=[q2, st.session_state.chat_variables["selected_personas"]],
                use_container_width=True)

    with col2:
        st.button(q3, 
                on_click=ask_question, 
                args=[q3, st.session_state.chat_variables["selected_personas"]],
                use_container_width=True)
        st.button(q4, 
                on_click=ask_question, 
                args=[q4, st.session_state.chat_variables["selected_personas"]],
                use_container_width=True)

    with col3:
        st.button(q5, 
                on_click=ask_question, 
                args=[q5, st.session_state.chat_variables["selected_personas"]],
                use_container_width=True)
        st.button(q6, 
                on_click=ask_question, 
                args=[q6, st.session_state.chat_variables["selected_personas"]],
                use_container_width=True)

    if question := st.chat_input("Ask any question, be it about something small or about what you should do with your career!", key="chat_input"):
        ask_question(question, st.session_state.chat_variables["selected_personas"])

    # Display the conversation history in columns
    responses = []
    sourced_texts = []
    personas = []
    resp_collect_count = 0
    audio_id = 0
    num_personas = st.session_state.chat_variables["num_personas"]
    num_responses_expected = 0
    for message in st.session_state.messages:
        if message["role"] == "user":
            respondents = message["respondents"]
            num_responses_expected = len(respondents)
            with st.chat_message("user"):
                question = message["content"]
                st.session_state.latest_question = "Question: " + question
                st.markdown(question)

        elif message["role"] == "assistant": # Collect the replies from personas
            responses.append(message["content"])
            sourced_texts.append(message["sourced_texts"])
            personas.append(message["persona"])
            resp_collect_count += 1

        # Check if we've gathered everything for this qn, if so, display it
        if resp_collect_count == num_responses_expected: # Display all the replies from the personas
            st.session_state.latest_responses = []
            persona_columns = st.columns(num_responses_expected)
            for idx, respondent in enumerate(respondents):
                with persona_columns[idx]:
                    st.markdown(f"### {respondent}")
                    st.session_state.latest_responses.append(f'Response from {respondent}: {responses[idx]} \n')
                    st.markdown(responses[idx])
                    
                    # Add play audio button with persona-specific voice
                    if st.button(f"🔊 Play {respondent}'s Perspective", key=f"play_{respondent}_{st.session_state.question_counter}_{audio_id}"):
                        print("Play audio button clicked")
                        audio = text_to_speech(responses[idx], respondent)
                        st.audio(audio, format='audio/mp3')
                        
                    with st.expander("Inspect Retrieved Sources!", expanded=False):
                        for i, doc in enumerate(sourced_texts[idx]):
                            st.markdown(f"### Source Document {i + 1}")
                            st.markdown(f"Source: {doc.metadata['source']}")
                            st.markdown(doc.page_content)
            audio_id += 1
            resp_collect_count = 0
            responses = []
            sourced_texts = []

    if "latest_responses" in st.session_state: #ensures that there has been at least one response
        summarise_response_button = st.button("Summarise Latest Responses", use_container_width=True)

    summary = ""
    if summarise_response_button:
        summary = get_summary(st.session_state.latest_question + " ".join(st.session_state.latest_responses))
        st.success("Summary:  \n\n" + summary)

    # Add play audio button for summary with default voice
    if summary and st.button(f"🔊 Play Summary", key=f"play_summary_{str(time.time())}"):
        audio = text_to_speech(summary, f"Base Model: {model}")
        st.audio(audio, format='audio/mp3')

