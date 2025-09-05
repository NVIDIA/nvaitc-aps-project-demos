# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import streamlit as st
import os
import json
import shutil

def load_personas():
    try:
        with open(os.path.join('data', 'persona_profiles.json'), 'r') as f:
            data = json.load(f)
            return data['personas']
    except Exception as e:
        st.error(f"Error loading persona profiles: {e}")
        return {}

def save_personas(personas):
    try:
        with open(os.path.join('data', 'persona_profiles.json'), 'w') as f:
            json.dump({'personas': personas}, f, indent=4)
        return True
    except Exception as e:
        st.error(f"Error saving persona profiles: {e}")
        return False

def list_persona_files(persona_name):
    """Returns a list of document files for a given persona."""
    persona_dir = os.path.join('data', persona_name)
    if not os.path.exists(persona_dir):
        return []
    return [f for f in os.listdir(persona_dir) 
            if os.path.isfile(os.path.join(persona_dir, f)) 
            and f.lower().endswith(('.pdf', '.txt', '.doc', '.docx'))]

def generate_prompt_suggestions(persona_name):
    from src.pages.Chat import llm

    """Generate prompt suggestions for a new persona."""
    prompt = f"""Generate 3 different AI assistant prompts for a persona named '{persona_name}'. Each prompt should establish the persona's identity and role,
                define their area of expertise or unique perspective, and the tone and style of reply of that persona.

            Format the response as a JSON object with numbered prompts.
            Example format: {{"prompt1": "first prompt text", "prompt2": "second prompt text", "prompt3": "third prompt text"}}"""
    
    try:
        response = llm.invoke(prompt)
        print("LLM Response:", response.content)
        suggestions = json.loads(response.content)
        # Extract just the prompt values from the JSON object
        prompts = [suggestions.get(f"prompt{i+1}", "") for i in range(3)]
        return [p for p in prompts if p]  # Filter out any empty prompts
    except Exception as e:
        st.error(f"Error generating prompt suggestions: {e}")
        return []

st.title("👥 Persona Manager")
st.write("View, edit, and create new personas for your AI panel.")

# Load existing personas
personas = load_personas()

# Display existing personas
st.header("Existing Personas")
for persona_name, persona_data in personas.items():
    with st.expander(f"📝 {persona_name}"):
        # Create columns for the form
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Edit prompt
            new_prompt = st.text_area(
                "Prompt", 
                value=persona_data['prompt'],
                key=f"prompt_{persona_name}"
            )
            
            # Edit voice ID
            new_voice_id = st.text_input(
                "Voice ID",
                value=persona_data['voice_id'],
                key=f"voice_{persona_name}",
                help="Name of the voice in your ElevenLabs account"
            )
            
            # Save changes button
            if st.button("Save Changes", key=f"save_{persona_name}"):
                personas[persona_name]['prompt'] = new_prompt
                personas[persona_name]['voice_id'] = new_voice_id
                if save_personas(personas):
                    st.success("Changes saved successfully!")
                    
            # Delete persona button
            if st.button("Delete Persona", key=f"delete_{persona_name}"):
                if st.session_state.get(f"confirm_delete_{persona_name}", False):
                    try:
                        # First remove from personas dictionary and save to JSON
                        del personas[persona_name]
                        if not save_personas(personas):
                            raise Exception("Failed to update persona_profiles.json")
                        
                        # Then try to delete the directory
                        persona_dir = os.path.join('data', persona_name)
                        if os.path.exists(persona_dir):
                            shutil.rmtree(persona_dir)
                        
                        st.success(f"Persona '{persona_name}' deleted successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting persona: {e}")
                else:
                    st.session_state[f"confirm_delete_{persona_name}"] = True
                    st.warning("Click again to confirm deletion.")
        
        with col2:
            # Show existing files
            st.write("Uploaded Files:")
            files = list_persona_files(persona_name)
            if files:
                for file in files:
                    st.text(f"📄 {file}")
            else:
                st.text("No files uploaded")
            
            # File uploader
            uploaded_files = st.file_uploader(
                "Upload new files",
                type=['pdf', 'txt', 'doc', 'docx'],
                accept_multiple_files=True,
                key=f"upload_{persona_name}"
            )
            
            if uploaded_files:
                persona_dir = os.path.join('data', persona_name)
                os.makedirs(persona_dir, exist_ok=True)
                
                for uploaded_file in uploaded_files:
                    file_path = os.path.join(persona_dir, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                st.success("Files uploaded successfully!")
                st.rerun()

# Create new persona
st.header("Create New Persona", divider="rainbow")

# Move form inputs outside the form for real-time updates
new_name = st.text_input("Persona Name")

# Generate and show prompt suggestions if name is provided
if new_name:
    if "prompt_suggestions" not in st.session_state or st.session_state.get("last_name") != new_name:
        with st.spinner("Generating prompt suggestions..."):
            st.session_state.prompt_suggestions = generate_prompt_suggestions(new_name)
            st.session_state.last_name = new_name

    if st.session_state.prompt_suggestions:
        st.write("📝 Suggested prompts (click to use):")
        for i, suggestion in enumerate(st.session_state.prompt_suggestions):
            st.text(suggestion)
            if st.button(f"Use Suggestion {i+1}", key=f"use_suggestion_{i}"):
                st.session_state.selected_prompt = suggestion

# # Wrap the rest in a form
# with st.form("new_persona_form", clear_on_submit=False):
new_prompt = st.text_area(
    "Persona Prompt",
    value=st.session_state.get("selected_prompt", ""),
    help="You can use a suggestion above or write your own prompt",
)
new_voice_id = st.text_input("Voice ID",
                            help="Name of the voice in your ElevenLabs account"
                            )
new_files = st.file_uploader(
    "Upload Files",
    type=['pdf', 'txt', 'doc', 'docx'],
    accept_multiple_files=True
)

submitted = st.button("Create Persona")
if submitted and new_name and new_prompt and new_voice_id:
    if new_name in personas:
        st.error("A persona with this name already exists!")
    else:
        # Add new persona to JSON
        personas[new_name] = {
            "prompt": new_prompt,
            "voice_id": new_voice_id
        }
        
        # Save updated personas
        if save_personas(personas):
            # Create directory and save files if any were uploaded
            if new_files:
                persona_dir = os.path.join('data', new_name)
                os.makedirs(persona_dir, exist_ok=True)
                
                for uploaded_file in new_files:
                    file_path = os.path.join(persona_dir, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
            
            # Clear the session state for prompt suggestions
            if "prompt_suggestions" in st.session_state:
                del st.session_state.prompt_suggestions
            if "selected_prompt" in st.session_state:
                del st.session_state.selected_prompt
            if "last_name" in st.session_state:
                del st.session_state.last_name
            
            st.success("New persona created successfully!")
            st.rerun()