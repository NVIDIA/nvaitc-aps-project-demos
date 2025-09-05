# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import streamlit as st
import json
import os

PROFILE_PATH = "data/user_profile.json"

def load_profile():
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, 'r') as f:
            return json.load(f)
    return {}

def save_profile(profile_data):
    os.makedirs(os.path.dirname(PROFILE_PATH), exist_ok=True)
    with open(PROFILE_PATH, 'w') as f:
        json.dump(profile_data, f)

def profile_page():
    st.title("👤 My Profile")
    
    profile = load_profile()
    
    with st.form("profile_form"):
        # Basic Information
        st.subheader("Basic Information")
        name = st.text_input("Name", profile.get("name", ""))
        age = st.number_input("Age", 0, 120, profile.get("age", 25))
        life_stage = st.selectbox(
            "Current Life Stage",
            ["Student", "Early Career", "Mid Career", "Senior Professional", "Retired"],
            index=["Student", "Early Career", "Mid Career", "Senior Professional", "Retired"].index(profile.get("life_stage", "Student"))
        )
        
        # Education
        st.subheader("Education")
        education_level = st.selectbox(
            "Highest Education Level",
            ["High School", "Bachelor's", "Master's", "PhD", "Other"],
            index=["High School", "Bachelor's", "Master's", "PhD", "Other"].index(profile.get("education_level", "Bachelor's"))
        )
        field_of_study = st.text_input("Field of Study", profile.get("field_of_study", ""))
        
        # Personality
        st.subheader("Personality")
        mbti = st.selectbox(
            "MBTI Type",
            ["INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP",
             "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP"],
            index=["INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP",
                   "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP"].index(profile.get("mbti", "INTJ"))
        )
        
        # Interests and Goals
        st.subheader("Interests and Goals")
        interests = st.text_area("What are your interests and hobbies?", profile.get("interests", ""))
        career_goals = st.text_area("What are your career goals?", profile.get("career_goals", ""))
        life_goals = st.text_area("What are your life goals?", profile.get("life_goals", ""))
        
        # Key Life Experiences
        st.subheader("Key Life Experiences")
        achievements = st.text_area("Major Achievements", profile.get("achievements", ""))
        challenges = st.text_area("Significant Challenges Overcome", profile.get("challenges", ""))
        
        if st.form_submit_button("Save Profile"):
            profile_data = {
                "name": name,
                "age": age,
                "life_stage": life_stage,
                "education_level": education_level,
                "field_of_study": field_of_study,
                "mbti": mbti,
                "interests": interests,
                "career_goals": career_goals,
                "life_goals": life_goals,
                "achievements": achievements,
                "challenges": challenges
            }
            save_profile(profile_data)
            st.success("Profile saved successfully!")

def get_profile_context():
    """Return formatted profile context for RAG"""
    profile = load_profile()
    return f"""
    User Profile:
    Name: {profile.get('name', '')}
    Age: {profile.get('age', '')}
    Location: {profile.get('location', '')}
    Education: {profile.get('education_level', '')} in {profile.get('field_of_study', '')}
    MBTI: {profile.get('mbti', '')}
    
    Interests: {profile.get('interests', '')}
    Career Goals: {profile.get('career_goals', '')}
    Life Goals: {profile.get('life_stories', '')}
    Core Values: {profile.get('values', '')}
    """

profile_page()