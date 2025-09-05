# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import streamlit as st
import os
import json
from dotenv import load_dotenv
from src.pages.Chat import (
    llm,  # or however you define your ChatNVIDIA in the main code
    model,
    get_response,
    get_persona_prompt
)
import textwrap
from src.pages.PersonaManager import load_personas

### APP / PAGE CONFIGURATIONS ###
load_dotenv()
nvidia_api_key = os.getenv('NVIDIA_API_KEY')
model = "nvdev/mistralai/mistral-7b-instruct-v0.3" # Other models tried: "nvdev/meta/llama3-70b-instruct", "deepseek-ai/deepseek-r1-distill-qwen-7b", "qwen/qwen2.5-7b-instruct", "google/gemma-2-9b-it", "nvdev/google/gemma-2-9b-it"

def evaluate_responses_ranking(responses, persona_name, persona_prompt):
    """
    Rank multiple responses based on coherence with persona characteristics
    Returns rankings and analysis for each dimension
    """
    evaluation_prompt = f"""
    You are an expert in narrative analysis and character development. Given multiple responses from an AI attempting to mimic {persona_name}, 
    rank them based on three dimensions:

    [Character Background]
    {persona_prompt}

    [Responses to Evaluate]
    {responses[0]["label"]}: {responses[0]["text"]}
    {responses[1]["label"]}: {responses[1]["text"]}

    [Evaluation Dimensions]
    1. Coherence with Relations (Coh.Rel): How well does the response maintain consistency with {persona_name}'s 
       relationships, social position, and interpersonal dynamics?
       
    2. Coherence with Attributes (Coh.Att): How well does the response reflect {persona_name}'s personality traits, 
       values, speaking style, and behavioral patterns?
       
    3. Coherence with Context (Coh.Con): How well does the response fit the situational context?

    [Instructions]
    1. For each dimension, rank the responses from best (1) to worst (2)
    2. Succinctly explain your reasoning for each ranking
    3. Format your response as follows:

    Coherence with Relations Ranking:
    1. [Response Label] - [Explanation]
    2. [Response Label] - [Explanation]

    Coherence with Attributes Ranking:
    1. [Response Label] - [Explanation]
    2. [Response Label] - [Explanation]

    Coherence with Context Ranking:
    1. [Response Label] - [Explanation]
    2. [Response Label] - [Explanation]

    [End with just the rankings in this format]
    Coh.Rel: [Label1]>[Label2]
    Coh.Att: [Label1]>[Label2]
    Coh.Con: [Label1]>[Label2]
    """

    # Get evaluation from base model
    eval_response = llm.invoke(evaluation_prompt)
    eval_text = eval_response.content.strip()
    
    try:
        # Extract rankings from last three lines
        lines = eval_text.split('\n')
        rankings = []
        for line in reversed(lines):
            if len(rankings) == 3:
                break
            if line.startswith(('Coh.Rel:', 'Coh.Att:', 'Coh.Con:')):
                ranking = line.split(':')[1].strip()
                rankings.insert(0, ranking)
        
        if len(rankings) != 3:
            raise ValueError("Could not find exactly 3 rankings")
            
        return {
            "coherence_relations": rankings[0],
            "coherence_attributes": rankings[1],
            "coherence_context": rankings[2],
            "analysis": eval_text
        }
        
    except Exception as e:
        st.error(f"Error parsing rankings evaluation: {str(e)}")
        return {
            "coherence_relations": "Error",
            "coherence_attributes": "Error",
            "coherence_context": "Error",
            "analysis": "Error in evaluation", 
            "eval_text": eval_text 
        }

def calculate_preference_stats(eval_responses):
    """Calculate percentage of times persona response was preferred for each dimension"""
    total = len(eval_responses)
    rel_wins = 0
    att_wins = 0
    con_wins = 0
    
    for i, response in enumerate(eval_responses):
        try:
            rankings = response["rankings"] # Check if persona (B) comes before base model (A) in rankings
            rel_wins += 1 if "B>A" in rankings["coherence_relations"] else 0
            att_wins += 1 if "B>A" in rankings["coherence_attributes"] else 0
            con_wins += 1 if "B>A" in rankings["coherence_context"] else 0
        except:
            st.error(f"Error calculating preference stats for response {i}: {response}")
            continue
    
    return {
        "relations": (rel_wins / total) * 100,
        "attributes": (att_wins / total) * 100,
        "context": (con_wins / total) * 100
    }
    
def evaluate_character_utterance(response, persona_name, persona_prompt):
    """Evaluate how well the response matches the character's speaking style"""
    evaluation_prompt = f"""

        You will be given responses written by an Al assistant mimicking the character {persona_name}. Your task is to rate the reponse using the
        specific criterion by following the evaluation steps. Below is the data:

        [Evaluation Criterion]
        Utterance (1-7): Does the response reflect the speaking style of {persona_name}?

        Character Profile:
        {persona_prompt}

        [Evaluation Steps]
        1. Read through the profile and write the speaking style of the real character such as their pet phrases and distinctive linguistic quirks.
        2. Read through the interactions and identify the speaking style of the AI assistant.
        3. After having a clear understanding of the interactions, compare the responses to the profile. Look for any consistencies or inconsistencies.
        4. Use the scale from 1-7 to rate how well the response reflects the speaking style.
        1 = not at all reflective
        7 = perfectly reflective

        First provide your step-by-step reasoning, then give the final score (1-7).
        Give the reasoning and final score in a json format, with keys "reasoning" and "score".
        We only want the JSON, no additional commentary.

        Response to Evaluate:
        {response}

        """
    # Get evaluation from base model
    eval_response = llm.invoke(evaluation_prompt)
    
    # Extract the final score from the JSON response
    try:
        content = eval_response.content
        # Extract substring from the first '{' to the last '}'
        start = content.find("{")
        end = content.rfind("}") + 1
        json_str = content[start:end]
        data = json.loads(json_str)
        score = data["score"]
    except Exception as e:
        score = -1  # Default to -1 if parsing fails
        print("Error parsing utterance score: ", eval_response.content, e)
        st.error(f"Error parsing utterance score: {eval_response.content}")

    return score, eval_response.content

# If your existing code has references to these:
q1 = "How do you think I can improve my leadership abilities?"
q2 = "How do you approach problem-solving?"
q3 = "Share a key life experience."
q4 = "Two of my best friends are in a fight. How can I help them reconcile?"
q5 = "What is confucius teachings about?"
q6 = "What can I do to level up my career while creating a postive impact on the people around me?"
q7 = "How can I make better decisions in uncertain situations?"
q8 = "What are the key principles to achieving financial stability and wealth?"
q9 = "How do I develop self-discipline and stay motivated?"
q10 = "What is the best way to handle failure and setbacks?"
q11 = "How can I improve my emotional intelligence and communication skills?"
q12 = "What habits lead to long-term success and happiness?"
q13 = "How can I manage stress and avoid burnout?"
q14 = "What are the biggest mistakes people make in relationships, and how can they be avoided?"
q15 = "How do I find my true passion and purpose in life?"
q16 = "What is the best way to build a strong personal and professional network?"
q17 = "How can I develop resilience in the face of adversity?"
q18 = "What are the qualities of a great leader, and how can I cultivate them?"
q19 = "What should I focus on in my 20s, 30s, and beyond to live a fulfilling life?"
q20 = "What is the most important lesson you've learned in life?"
QUESTIONS = [q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, q11, q12, q13, q14, q15, q16, q17, q18, q19, q20]

def persona_evaluation_page():
    """
    A Streamlit page that tests how closely a persona's responses match
    its persona style by letting the model guess which response belongs
    to the persona vs. a generic bot.
    """

    st.title("Persona Evaluation Page")

    PERSONAS = load_personas()  # Load personas from your existing code

    # Let user select exactly ONE persona to test
    persona_name = st.selectbox("Select the Persona to Evaluate", 
                                [p for p in PERSONAS.keys() if not p.startswith("Base Model:") 
                                 and p not in ["Friendly Assistant", "Tech Support Specialist"]])

    if not persona_name:
        st.warning("Please select a persona to proceed.")
        return
    
    # Identify the "generic bot" or "base model" you want to compare against
    # e.g., by default let's pick the first "Base Model:" from your PERSONAS
    base_model_name = model
    if not base_model_name:
        st.error("No Base Model found in PERSONAS. Please define one as 'Base Model: your_model_name'.")
        return
    else:
        st.write(f"Comparing against base model: **{base_model_name}**")

    if "eval_responses" not in st.session_state:
        st.session_state.eval_responses = []
    
    # If user wants to run or re-run the evaluation
    if st.button("Generate Persona & Generic Bot Responses for All 20 Questions"):
        st.session_state.eval_responses = []  # clear old data

        q_count = 1
        gen_prog_bar = st.progress(0)
        gen_prog_text = st.empty()
        for q in QUESTIONS:
            gen_prog_bar.progress(q_count / len(QUESTIONS))
            gen_prog_text.text(f"Generating responses for question: {q_count} of {len(QUESTIONS)}")

            # 1. Persona response with error handling
            try:
                persona_resp, _ = get_response(
                    user_input=q,
                    conversation_history=[],  # no real chat history for the test
                    persona_name=persona_name
                )
                st.toast(f"Generated persona response for question: {q_count}")
                print(f"Generated persona response for question: {q_count}")
            except Exception as e:
                st.error(f"Error generating persona response for question {q_count}: {e}")
                persona_resp = "Timed out"

            # 2. Base (generic) response with error handling
            try:
                base_resp, _ = get_response(
                    user_input=q,
                    conversation_history=[],
                    persona_name=base_model_name,
                    base_model=True
                )
                st.toast(f"Generated base response for question: {q_count}")
                print(f"Generated base response for question: {q_count}")
            except Exception as e:
                st.error(f"Error generating base response for question {q_count}: {e}")
                base_resp = "Timed out"

            # We'll store them in st.session_state for later
            st.session_state.eval_responses.append({
                "question": q,
                "persona_resp": persona_resp,
                "base_resp": base_resp,
                "model_guess": None,  # to be filled by the next step
                "correct": None
            })
            q_count += 1
        gen_prog_text.empty()
        st.success("Successfully generated responses from persona and base model.")

    # Now let user ask the base model to guess
    if st.session_state.eval_responses and st.button("Run evaluation on Character Utterance, Coherence of Relations, Attributes, and Context and Preference Scores"):
        # We'll use a single call per question to the base model:
        # We'll show it something like:
        #   "We have 2 responses to the same question..."
        persona_prompt = get_persona_prompt(persona_name)

        eval_prog_bar = st.progress(0)
        eval_prog_text = st.empty()

        for idx, item in enumerate(st.session_state.eval_responses):
            eval_prog_bar.progress((idx+1) / len(st.session_state.eval_responses))
            eval_prog_text.text(f"Evaluating Question {idx+1} of {len(st.session_state.eval_responses)}")

            try: 
                question = item["question"]
                persona_resp = item["persona_resp"]
                base_resp = item["base_resp"]

                utterance_score, utterance_analysis = evaluate_character_utterance(
                    persona_resp, 
                    persona_name, 
                    persona_prompt
                )

                st.session_state.eval_responses[idx]["utterance_score"] = utterance_score
                st.session_state.eval_responses[idx]["utterance_analysis"] = utterance_analysis

                utterance_score, utterance_analysis = evaluate_character_utterance(
                    base_resp, 
                    persona_name, 
                    persona_prompt
                )

                st.session_state.eval_responses[idx]["utterance_score_base"] = utterance_score
                st.session_state.eval_responses[idx]["utterance_analysis_base"] = utterance_analysis

                responses = [
                    {"label": "A", "text": item["base_resp"]},
                    {"label": "B", "text": item["persona_resp"]}
                ]
                
                rankings = evaluate_responses_ranking(
                    responses,
                    persona_name,
                    persona_prompt
                )

                st.session_state.eval_responses[idx]["rankings"] = rankings

                guess_prompt = textwrap.dedent(f"""\
                    We have two responses to the same question: \"{question}\"\n\nResponse A:\n\"\"\"\
                    {base_resp}\n\"\"\"\n\nResponse B:\n\"\"\"\
                    {persona_resp}\n\"\"\"\n\nWe know one response is from the persona named \"{persona_name}\" with the prompt of {persona_prompt},\
                    and the other is from a generic/base bot.\
                    Please guess which is from the persona and which is from the generic bot.\n\nOutput your guess in a JSON format, e.g.:\
                    {{\"persona_guess\": \"A or B\", \"generic_guess\": \"A or B\", \"why\": \"Your short reason for thinking so\"}}\
                    (We only want the JSON, no additional commentary.)\
                    """)

                guess_resp = llm.invoke(guess_prompt)
                guess_text = guess_resp.content.strip()

                import json
                try:
                    guess_data = json.loads(guess_text)
                    persona_guess = guess_data.get("persona_guess", "").strip()
                    generic_guess = guess_data.get("generic_guess", "").strip()
                except:
                    persona_guess = "A"
                    generic_guess = "B"
                    guess_data = {"persona_guess": persona_guess, "generic_guess": generic_guess}

                actual_persona = "A"  
                actual_generic = "B"

                correct = (persona_guess == "B" and generic_guess == "A")
                
                st.session_state.eval_responses[idx]["model_guess"] = guess_data
                st.session_state.eval_responses[idx]["correct"] = correct

            except Exception as e:
                st.error(f"Error processing question {idx+1}: {e}")

        eval_prog_text.empty()
        st.success("The model has guessed for each question.")
        st.session_state.eval_completed = True  # Mark that evaluation has been run

    # Finally, display all results + compute precision
    if 'eval_responses' in st.session_state and any(item['correct'] is not None for item in st.session_state.eval_responses):
        stats = calculate_preference_stats(st.session_state.eval_responses)
        
        eval_results_container = st.container()
        with eval_results_container:
            st.markdown("## Overall Preference Analysis")
            st.markdown("Percentage of times persona response was preferred over base model:")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Relations Coherence", 
                    f"{stats['relations']:.1f}%",
                    help="How often the persona response better matched character relationships"
                )
                
            with col2:
                st.metric(
                    "Attributes Coherence", 
                    f"{stats['attributes']:.1f}%",
                    help="How often the persona response better reflected character traits"
                )
                
            with col3:
                st.metric(
                    "Context Coherence", 
                    f"{stats['context']:.1f}%",
                    help="How often the persona response better fit the context"
                )
            
            # Visual representation
            preference_data = {
                "Dimension": ["Relations", "Attributes", "Context"],
                "Preference %": [
                    stats["relations"],
                    stats["attributes"],
                    stats["context"]
                ]
            }
            
            st.bar_chart(preference_data, x="Dimension", y="Preference %")

            # Calculate average utterance score
            utterance_scores = [float(r["utterance_score"]) for r in st.session_state.eval_responses]
            avg_utterance = sum(utterance_scores) / len(utterance_scores) if utterance_scores else 0

            # Calculate average base utterance score
            utterance_scores_base = [float(r["utterance_score_base"]) for r in st.session_state.eval_responses]
            avg_utterance_base = sum(utterance_scores_base) / len(utterance_scores_base) if utterance_scores_base else 0
            

            correct_count = sum(1 for r in st.session_state.eval_responses if r["correct"])
            total = len(st.session_state.eval_responses)
            if total > 0:
                precision = round(correct_count / total, 3)
            else:
                precision = 0.0

            st.markdown(f"""
            ## Evaluation Results:
            - **Persona Detection Accuracy**: {correct_count}/{total} = {precision*100}%
            - **Average Character Utterance Score**: {avg_utterance:.2f}/7.0
            - **Average Base Model Utterance Score**: {avg_utterance_base:.2f}/7.0
            """)

        # Show detailed results
        for idx, item in enumerate(st.session_state.eval_responses):
            st.markdown("---")
            st.markdown(f"**Q{idx+1}:** {item['question']}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### Generic (A)")
                st.markdown(item['base_resp'])
                st.markdown(f"**Base Character Utterance Score**: {item['utterance_score_base']}/7")
                with st.expander("See utterance analysis"):
                    st.markdown(item['utterance_analysis_base'])
            
            with col2:
                st.markdown("### Persona (B)")
                st.markdown(item['persona_resp'])
                st.markdown(f"**Character Utterance Score**: {item['utterance_score']}/7")
                
                with st.expander("See utterance analysis"):
                    st.markdown(item['utterance_analysis'])
            
            guess_data = item["model_guess"]
            correct = item["correct"]
            if guess_data is not None:
                st.markdown(f"**Model's guess:** `{guess_data}`")
                st.markdown(f"**Correct?** {correct}")
                st.markdown(f"**Reasoning:** {guess_data.get('why', 'No reason provided.')}")
         
def app():
    load_dotenv()
    persona_evaluation_page()

app()
