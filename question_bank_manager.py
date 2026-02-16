# question_bank_manager.py - Enhanced with Descriptions and Preview

import streamlit as st
import json
import os
import csv
import shutil
from datetime import datetime
import hashlib

class QuestionBankManager:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.base_path = "question_banks"
        self.default_path = f"{self.base_path}/default"
        self.user_banks_path = f"{self.base_path}/users"
        
        # Ensure directories exist
        for path in [self.base_path, self.default_path, self.user_banks_path]:
            os.makedirs(path, exist_ok=True)
        
        # Default banks with descriptions
        self.default_banks = {
            "life_story_short": {
                "name": "📖 Life Story - Short",
                "description": "A concise journey through your life's key moments. Perfect for capturing essential memories in 9 focused sessions.",
                "file": "life_story_short.csv",
                "sessions": 9,
                "topics": 46,
                "estimated_time": "2-3 hours",
                "difficulty": "Beginner"
            },
            "life_story_comprehensive": {
                "name": "📖 Life Story - Comprehensive",
                "description": "An in-depth exploration of your entire life story. 13 detailed sessions covering childhood, career, relationships, and legacy.",
                "file": "life_story_comprehensive.csv",
                "sessions": 13,
                "topics": 71,
                "estimated_time": "5-8 hours",
                "difficulty": "Intermediate"
            },
            "business_legacy": {
                "name": "💼 Business Legacy",
                "description": "Document your professional journey, leadership lessons, and entrepreneurial wisdom for future generations.",
                "file": "business_legacy.csv",
                "sessions": 8,
                "topics": 42,
                "estimated_time": "3-4 hours",
                "difficulty": "Intermediate"
            },
            "family_history": {
                "name": "👪 Family History",
                "description": "Preserve your family's stories, traditions, and genealogy. Capture the moments that define your family's unique legacy.",
                "file": "family_history.csv",
                "sessions": 10,
                "topics": 38,
                "estimated_time": "4-6 hours",
                "difficulty": "Beginner"
            },
            "memoir_focus": {
                "name": "📝 Memoir - Themed",
                "description": "Focus on specific themes like resilience, love, or adventure. Perfect for a themed memoir rather than a complete life story.",
                "file": "memoir_focus.csv",
                "sessions": 6,
                "topics": 28,
                "estimated_time": "2-3 hours",
                "difficulty": "Beginner"
            }
        }
    
    def load_default_bank(self, bank_key):
        """Load a default question bank"""
        bank_info = self.default_banks.get(bank_key)
        if not bank_info:
            return None
        
        filepath = f"{self.default_path}/{bank_info['file']}"
        if not os.path.exists(filepath):
            # Create a sample bank if it doesn't exist
            self._create_sample_bank(bank_key, filepath)
        
        return self._load_bank_from_file(filepath)
    
    def _create_sample_bank(self, bank_key, filepath):
        """Create a sample question bank file"""
        samples = {
            "life_story_short": [
                {"id": 1, "title": "Childhood Memories", "questions": [
                    "What is your earliest memory?",
                    "Describe your childhood home.",
                    "Who was your favorite family member growing up?",
                    "What games did you play as a child?",
                    "Tell me about a favorite teacher."
                ]},
                {"id": 2, "title": "School Years", "questions": [
                    "What subjects did you love?",
                    "Who were your best friends?",
                    "Describe a memorable school event.",
                    "What were your dreams as a teenager?"
                ]}
            ],
            "life_story_comprehensive": [
                {"id": 1, "title": "Childhood", "questions": [
                    "What is your earliest memory?",
                    "Describe your childhood home and neighborhood.",
                    "Tell me about your parents - their personalities and stories.",
                    "Did you have siblings? What was your relationship?",
                    "What family traditions shaped your early years?",
                    "Describe a typical day when you were 10 years old."
                ]}
            ]
        }
        
        bank_data = samples.get(bank_key, samples["life_story_short"])
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["session_id", "session_title", "question_text", "guidance", "word_target"])
            
            for session in bank_data:
                for i, q in enumerate(session["questions"]):
                    writer.writerow([
                        session["id"],
                        session["title"],
                        q,
                        f"Take your time with this {session['title'].lower()} question...",
                        500
                    ])
    
    def _load_bank_from_file(self, filepath):
        """Load a question bank from CSV file"""
        sessions = []
        current_session = None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    session_id = int(row.get('session_id', 1))
                    session_title = row.get('session_title', f'Session {session_id}')
                    question = row.get('question_text', '')
                    guidance = row.get('guidance', '')
                    word_target = int(row.get('word_target', 500))
                    
                    if not current_session or current_session['id'] != session_id:
                        if current_session:
                            sessions.append(current_session)
                        current_session = {
                            'id': session_id,
                            'title': session_title,
                            'questions': [],
                            'guidance': guidance,
                            'word_target': word_target
                        }
                    
                    if question and current_session:
                        current_session['questions'].append(question)
                
                if current_session:
                    sessions.append(current_session)
            
            return sessions
        except Exception as e:
            st.error(f"Error loading bank: {e}")
            return None
    
    def display_bank_selector(self):
        """Display the enhanced bank selector with descriptions and preview"""
        st.title("📚 Question Bank Manager")
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["📖 Default Banks", "✨ My Custom Banks", "➕ Create New"])
        
        with tab1:
            self._display_default_banks()
        
        with tab2:
            self._display_custom_banks()
        
        with tab3:
            self._display_bank_creator()
    
    def _display_default_banks(self):
        """Display default banks with descriptions and preview buttons"""
        cols = st.columns(2)
        
        for i, (bank_key, bank_info) in enumerate(self.default_banks.items()):
            with cols[i % 2]:
                with st.container():
                    st.markdown(f"""
                    <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:15px;">
                        <h3 style="margin-top:0;">{bank_info['name']}</h3>
                        <p style="color:#666;">{bank_info['description']}</p>
                        <p>📊 <strong>{bank_info['sessions']} sessions</strong> • <strong>{bank_info['topics']} topics</strong></p>
                        <p>⏱️ Estimated time: {bank_info['estimated_time']} • Difficulty: {bank_info['difficulty']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"🔍 Preview", key=f"preview_{bank_key}", use_container_width=True):
                            self._preview_bank(bank_key)
                    
                    with col2:
                        if st.button(f"📥 Load Bank", key=f"load_{bank_key}", type="primary", use_container_width=True):
                            sessions = self.load_default_bank(bank_key)
                            if sessions:
                                # Store in session state for the main app to load
                                st.session_state.pending_bank_load = {
                                    "sessions": sessions,
                                    "name": bank_info['name'],
                                    "type": "default",
                                    "id": bank_key
                                }
                                st.success(f"✅ {bank_info['name']} ready to load!")
                                st.rerun()
        
        # Check if we have a pending bank load
        if st.session_state.get('pending_bank_load'):
            bank = st.session_state.pending_bank_load
            st.info(f"Ready to load: {bank['name']}")
            if st.button("✅ Confirm Load Bank", type="primary", use_container_width=True):
                # Import the load function from main app
                from biographer import load_question_bank
                load_question_bank(
                    bank['sessions'],
                    bank['name'],
                    bank['type'],
                    bank['id']
                )
                del st.session_state.pending_bank_load
                st.success(f"✅ {bank['name']} loaded successfully!")
                st.rerun()
    
    def _preview_bank(self, bank_key):
        """Show a preview of the bank's sessions and topics"""
        bank_info = self.default_banks.get(bank_key)
        if not bank_info:
            return
        
        sessions = self.load_default_bank(bank_key)
        if not sessions:
            st.error("Could not load preview")
            return
        
        # Create a modal-like preview
        st.markdown("---")
        st.markdown(f"### 🔍 Preview: {bank_info['name']}")
        st.markdown(f"*{bank_info['description']}*")
        
        # Show summary stats
        total_topics = sum(len(s['questions']) for s in sessions)
        st.markdown(f"**{len(sessions)} sessions** • **{total_topics} topics**")
        
        # Create expandable sections for each session
        for session in sessions:
            with st.expander(f"📖 Session {session['id']}: {session['title']} ({len(session['questions'])} topics)"):
                for i, question in enumerate(session['questions'], 1):
                    st.markdown(f"{i}. {question}")
        
        if st.button("← Close Preview", key=f"close_preview_{bank_key}"):
            st.rerun()
    
    def _display_custom_banks(self):
        """Display user's custom banks"""
        st.info("✨ Create your own custom question banks in the 'Create New' tab.")
        
        # List existing custom banks
        if os.path.exists(self.user_banks_path):
            custom_banks = [f for f in os.listdir(self.user_banks_path) if f.endswith('.csv')]
            
            if custom_banks:
                for bank_file in custom_banks:
                    bank_name = bank_file.replace('.csv', '').replace('_', ' ').title()
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.markdown(f"**{bank_name}**")
                    with col2:
                        if st.button("🔍 Preview", key=f"preview_custom_{bank_file}"):
                            filepath = f"{self.user_banks_path}/{bank_file}"
                            sessions = self._load_bank_from_file(filepath)
                            if sessions:
                                self._display_custom_preview(bank_name, sessions)
                    with col3:
                        if st.button("🗑️ Delete", key=f"delete_{bank_file}"):
                            os.remove(f"{self.user_banks_path}/{bank_file}")
                            st.rerun()
            else:
                st.info("No custom banks yet. Create one in the 'Create New' tab!")
    
    def _display_custom_preview(self, bank_name, sessions):
        """Display preview of custom bank"""
        st.markdown("---")
        st.markdown(f"### 🔍 Preview: {bank_name}")
        
        for session in sessions:
            with st.expander(f"📖 Session {session['id']}: {session['title']} ({len(session['questions'])} topics)"):
                for i, question in enumerate(session['questions'], 1):
                    st.markdown(f"{i}. {question}")
        
        if st.button("← Close Preview", key="close_custom_preview"):
            st.rerun()
    
    def _display_bank_creator(self):
        """Interface for creating custom banks"""
        st.markdown("### Create Custom Question Bank")
        
        with st.form("create_bank_form"):
            bank_name = st.text_input("Bank Name", placeholder="e.g., My Family History")
            bank_description = st.text_area("Description", placeholder="Describe what this bank covers...")
            
            st.markdown("#### Sessions")
            st.markdown("Add your sessions and questions below:")
            
            # Session input area
            if 'custom_sessions' not in st.session_state:
                st.session_state.custom_sessions = [{"title": "", "questions": [""]}]
            
            # Display existing sessions
            sessions_to_remove = []
            for i, session in enumerate(st.session_state.custom_sessions):
                with st.expander(f"Session {i+1}", expanded=i==len(st.session_state.custom_sessions)-1):
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        session['title'] = st.text_input(f"Session Title", value=session['title'], key=f"sess_title_{i}")
                    with col2:
                        if st.button("🗑️", key=f"remove_sess_{i}"):
                            sessions_to_remove.append(i)
                    
                    # Questions for this session
                    questions_to_remove = []
                    for j, question in enumerate(session['questions']):
                        col1, col2 = st.columns([5, 1])
                        with col1:
                            session['questions'][j] = st.text_area(
                                f"Question {j+1}", 
                                value=question, 
                                key=f"q_{i}_{j}",
                                height=68
                            )
                        with col2:
                            if st.button("🗑️", key=f"remove_q_{i}_{j}"):
                                questions_to_remove.append(j)
                    
                    # Remove checked questions
                    for j in reversed(questions_to_remove):
                        session['questions'].pop(j)
                    
                    # Add question button
                    if st.button(f"➕ Add Question to Session {i+1}", key=f"add_q_{i}"):
                        session['questions'].append("")
                        st.rerun()
            
            # Remove checked sessions
            for i in reversed(sessions_to_to_remove):
                st.session_state.custom_sessions.pop(i)
            
            # Add session button
            if st.button("➕ Add New Session", type="secondary"):
                st.session_state.custom_sessions.append({"title": "", "questions": [""]})
                st.rerun()
            
            st.markdown("---")
            
            # Submit button
            if st.form_submit_button("💾 Create Bank", type="primary", use_container_width=True):
                if not bank_name:
                    st.error("Please enter a bank name")
                else:
                    self._save_custom_bank(bank_name, bank_description, st.session_state.custom_sessions)
    
    def _save_custom_bank(self, bank_name, description, sessions):
        """Save custom bank to file"""
        try:
            filename = bank_name.lower().replace(' ', '_') + '.csv'
            filepath = f"{self.user_banks_path}/{filename}"
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["session_id", "session_title", "question_text", "guidance", "word_target"])
                
                for session_id, session in enumerate(sessions, 1):
                    if session['title'] and any(session['questions']):
                        for question in session['questions']:
                            if question.strip():
                                writer.writerow([
                                    session_id,
                                    session['title'],
                                    question,
                                    f"Write about {session['title'].lower()}...",
                                    500
                                ])
            
            # Save metadata with description
            meta_path = f"{self.user_banks_path}/{bank_name.lower().replace(' ', '_')}_meta.json"
            with open(meta_path, 'w') as f:
                json.dump({
                    "name": bank_name,
                    "description": description,
                    "created": datetime.now().isoformat(),
                    "sessions": len([s for s in sessions if s['title']]),
                    "topics": sum(len([q for q in s['questions'] if q.strip()]) for s in sessions)
                }, f, indent=2)
            
            st.success(f"✅ Bank '{bank_name}' created successfully!")
            st.session_state.custom_sessions = [{"title": "", "questions": [""]}]
            st.rerun()
            
        except Exception as e:
            st.error(f"Error saving bank: {e}")
    
    def display_bank_editor(self, bank_id):
        """Display editor for modifying existing banks"""
        st.title("✏️ Edit Question Bank")
        st.info("Bank editor coming soon!")
        if st.button("← Back"):
            st.session_state.show_bank_editor = False
            st.rerun()
