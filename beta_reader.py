# beta_reader.py
import streamlit as st
import json
import os
import re
import time
from datetime import datetime
from openai import OpenAI

class BetaReader:
    def __init__(self, openai_client):
        self.client = openai_client
    
    def get_session_full_text(self, session_id, responses_state):
        """Get all responses from a session as continuous text for beta reading"""
        if session_id not in responses_state:
            return ""
        
        session_text = ""
        session_data = responses_state[session_id]
        
        if "questions" in session_data:
            for question, answer_data in session_data["questions"].items():
                session_text += f"Q: {question}\nA: {answer_data['answer']}\n\n"
        
        return session_text
    
    def generate_feedback(self, session_title, session_text, feedback_type="comprehensive"):
        """Generate beta reader/editor feedback for a completed session"""
        if not session_text.strip():
            return {"error": "Session has no content to analyze"}
        
        critique_templates = {
            "comprehensive": """You are a professional editor and beta reader. Analyze this life story excerpt and provide:
            1. **Overall Impression** (2-3 sentences)
            2. **Strengths** (3-5 bullet points)
            3. **Areas for Improvement** (3-5 bullet points with specific suggestions)
            4. **Continuity Check** (Note any timeline inconsistencies)
            5. **Emotional Resonance** (How engaging/emotional is it?)
            6. **Specific Edits** (3-5 suggested rewrites with explanations)
            
            Format your response clearly with headings and bullet points.""",
            
            "concise": """You are an experienced beta reader. Provide brief, actionable feedback on:
            - Main strengths
            - 2-3 specific areas to improve
            - 1-2 specific editing suggestions
            
            Keep it under 300 words.""",
            
            "developmental": """You are a developmental editor. Focus on:
            - Narrative structure and flow
            - Character/personality development
            - Pacing and detail balance
            - Theme consistency
            - Suggested structural changes"""
        }
        
        prompt = critique_templates.get(feedback_type, critique_templates["comprehensive"])
        
        full_prompt = f"""{prompt}

        SESSION TITLE: {session_title}
        
        SESSION CONTENT:
        {session_text}
        
        Please provide your analysis:"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a thoughtful, constructive editor who balances praise with helpful critique."},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            feedback = response.choices[0].message.content
            
            return {
                "session_title": session_title,
                "feedback": feedback,
                "generated_at": datetime.now().isoformat(),
                "feedback_type": feedback_type
            }
            
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
    
    def save_feedback(self, user_id, session_id, feedback_data, get_user_filename_func, load_user_data_func):
        """Save beta feedback to user's data file"""
        try:
            filename = get_user_filename_func(user_id)
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    user_data = json.load(f)
            else:
                user_data = {"responses": {}, "vignettes": [], "beta_feedback": {}}
            
            if "beta_feedback" not in user_data:
                user_data["beta_feedback"] = {}
            
            user_data["beta_feedback"][str(session_id)] = feedback_data
            
            with open(filename, 'w') as f:
                json.dump(user_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving beta feedback: {e}")
            return False
    
    def get_previous_feedback(self, user_id, session_id, get_user_filename_func, load_user_data_func):
        """Retrieve previous beta feedback for a session"""
        try:
            filename = get_user_filename_func(user_id)
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    user_data = json.load(f)
                
                if "beta_feedback" in user_data and str(session_id) in user_data["beta_feedback"]:
                    return user_data["beta_feedback"][str(session_id)]
        except:
            pass
        return None
    
    def show_modal(self, feedback, current_session, user_id, save_feedback_func, on_close_callback=None):
        """Display the beta reader feedback modal"""
        st.markdown('<div class="modal-overlay">', unsafe_allow_html=True)
        
        if st.button("← Back to Writing", key="beta_reader_back"):
            if on_close_callback:
                on_close_callback()
            st.rerun()
        
        st.title(f"🦋 Beta Reader: {feedback.get('session_title', 'Session')}")
        
        try:
            generated_date = datetime.fromisoformat(feedback['generated_at']).strftime('%B %d, %Y at %I:%M %p')
            st.caption(f"Generated: {generated_date}")
        except:
            st.caption("Generated: Recently")
        
        st.divider()
        
        st.subheader("📝 Editor's Analysis")
        st.markdown(feedback["feedback"])
        
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Regenerate Feedback", use_container_width=True):
                if on_close_callback:
                    on_close_callback()
                st.rerun()
        
        with col2:
            if st.button("💾 Save to Profile", use_container_width=True, type="primary"):
                if save_feedback_func(user_id, current_session["id"], feedback):
                    st.success("Feedback saved!")
                    time.sleep(1)
                    if on_close_callback:
                        on_close_callback()
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
