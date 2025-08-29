# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import streamlit as st
import random
from lightrag import LightRAG, QueryParam
from lightrag.llm import nvidia_openai_complete
from src.pages.PersonaManager import load_personas

st.set_page_config(
    page_title="IntelliExo AI Assistant",
    page_icon="🤖",
    layout="wide"
)

# Load personas dynamically
PERSONAS = load_personas()

# Add personalization toggle
if 'personalize' not in st.session_state:
    st.session_state.personalize = True

if 'chat_variables' not in st.session_state:
    st.session_state.chat_variables = {}
    st.session_state.chat_variables['base_model'] = list(PERSONAS.keys())[0]

if 'show_persona_selection' not in st.session_state:
    st.session_state.show_persona_selection = False

with st.sidebar:
    st.session_state.personalize = st.checkbox(
        "Personalize responses based on my profile",
        help="Include your profile information when generating responses",
        value=True
    )

    # List chosen personas
    st.subheader("Personas Chosen:")
    chosen_personas = st.session_state.chat_variables.get('selected_personas', ['None'])
    #list the chosen personas
    emoji_list = ["💁‍♂️","🙆‍♂️","👤","💆‍♂️","🙆"]
    if chosen_personas:
        for idx, persona in enumerate(chosen_personas): 
            st.write(f"- {persona}")
    else:
        st.write("No personas selected.")

    # Add a button to change the selected personas
    if st.button("Add/Change Selected Personas"):
        st.session_state.show_persona_selection = True

    # Show persona selection UI when the state is True
    if st.session_state.show_persona_selection:
        st.warning("Warning! Changing currently selected personas will reset the chat history.")
        select_personas = st.multiselect(
            "Select up to 3 personas",
            options=list(PERSONAS.keys()),
            default=st.session_state.chat_variables.get('selected_personas', []),
            max_selections=3
        )

        if st.button("Confirm Selection"):
            st.session_state.chat_variables['selected_personas'] = select_personas
            st.session_state.chat_variables['num_personas'] = len(select_personas)
            st.session_state.show_persona_selection = False
            st.success("Personas updated successfully!")

        if st.button("Cancel"):
            st.session_state.show_persona_selection = False

# Navigation setup
pg = st.navigation({
    "Main Features": [
        st.Page("src/pages/Profile.py", title="My Profile", icon="👤"),
        st.Page("src/pages/Chat.py", title="Chat", icon="💬", default=True),
        st.Page("src/pages/KnowledgeGraph.py", title="Knowledge Graph", icon="🕸️"),
        st.Page("src/pages/PersonaEvaluator.py", title="Persona Evaluator", icon="✅")
    ],
    "Settings": [
        st.Page("src/pages/PersonaManager.py", title="Manage Personas", icon="👥")
    ]
})

pg.run()