# question_bank_manager.py - PRODUCTION VERSION WITH VISUAL DEBUGGING
import streamlit as st
import pandas as pd
import json
import os
import shutil
from datetime import datetime
import uuid

class QuestionBankManager:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.base_path = "question_banks"
        self.default_banks_path = f"{self.base_path}/default"
        self.user_banks_path = f"{self.base_path}/users"
        self.editable_banks_path = f"{self.base_path}/editable"  # New path for editable banks
        
        # Create directories
        os.makedirs(self.default_banks_path, exist_ok=True)
        os.makedirs(self.user_banks_path, exist_ok=True)
        os.makedirs(self.editable_banks_path, exist_ok=True)  # Create editable banks directory
        if self.user_id:
            os.makedirs(f"{self.user_banks_path}/{self.user_id}", exist_ok=True)
            os.makedirs(f"{self.editable_banks_path}/{self.user_id}", exist_ok=True)  # User-specific editable banks
    
    def load_sessions_from_csv(self, csv_path):
        """Load sessions from a CSV file"""
        try:
            df = pd.read_csv(csv_path)
            sessions = []
            
            for _, row in df.iterrows():
                session_id = int(row['session_id'])
                
                session = next((s for s in sessions if s['id'] == session_id), None)
                if not session:
                    session = {
                        'id': session_id,
                        'title': str(row.get('title', f'Session {session_id}')),
                        'guidance': str(row.get('guidance', '')) if pd.notna(row.get('guidance', '')) else '',
                        'questions': [],
                        'word_target': int(row.get('word_target', 500)) if pd.notna(row.get('word_target', 500)) else 500
                    }
                    sessions.append(session)
                
                if pd.notna(row['question']):
                    session['questions'].append(str(row['question']).strip())
            
            return sorted(sessions, key=lambda x: x['id'])
        except Exception as e:
            st.error(f"Error loading CSV: {e}")
            return []
    
    def get_default_banks(self):
        """Get list of default banks from CSV files"""
        banks = []
        
        if os.path.exists(self.default_banks_path):
            for filename in os.listdir(self.default_banks_path):
                if filename.endswith('.csv'):
                    bank_id = filename.replace('.csv', '')
                    name_parts = bank_id.replace('_', ' ').title()
                    
                    try:
                        df = pd.read_csv(f"{self.default_banks_path}/{filename}")
                        sessions = df['session_id'].nunique()
                        topics = len(df)
                        
                        banks.append({
                            "id": bank_id,
                            "name": f"📖 {name_parts}",
                            "description": f"{sessions} sessions • {topics} topics",
                            "sessions": sessions,
                            "topics": topics,
                            "filename": filename,
                            "type": "default"
                        })
                    except Exception as e:
                        st.error(f"Error reading {filename}: {e}")
        
        return banks
    
    def load_default_bank(self, bank_id):
        """Load a default bank by ID"""
        filename = f"{self.default_banks_path}/{bank_id}.csv"
        
        if os.path.exists(filename):
            return self.load_sessions_from_csv(filename)
        return []
    
    # ============ NEW EDITABLE DEFAULT BANKS ============
    
    def create_editable_bank_from_default(self, bank_id):
        """Create an editable copy of a default bank"""
        if not self.user_id:
            st.error("You must be logged in")
            return None
        
        # Load the default bank
        sessions = self.load_default_bank(bank_id)
        if not sessions:
            st.error("Could not load default bank")
            return None
        
        # Get bank info
        default_banks = self.get_default_banks()
        bank_info = next((b for b in default_banks if b['id'] == bank_id), {})
        
        # Create editable copy
        user_editable_dir = f"{self.editable_banks_path}/{self.user_id}"
        os.makedirs(user_editable_dir, exist_ok=True)
        
        now = datetime.now().isoformat()
        
        # Create chapters-only version (remove all questions)
        chapters_sessions = []
        for session in sessions:
            chapters_sessions.append({
                'id': session['id'],
                'title': session['title'],
                'guidance': session.get('guidance', ''),
                'questions': [],  # Empty questions list for chapters-only
                'word_target': session.get('word_target', 500)
            })
        
        # Save the editable chapters bank
        bank_file = f"{user_editable_dir}/{bank_id}_chapters.json"
        with open(bank_file, 'w') as f:
            json.dump({
                'id': f"{bank_id}_chapters",
                'original_bank': bank_id,
                'name': f"{bank_info.get('name', '')} (Chapters)",
                'description': f"Chapters-only version of {bank_info.get('name', '')}",
                'created_at': now,
                'updated_at': now,
                'bank_type': 'chapters',
                'sessions': chapters_sessions
            }, f, indent=2)
        
        return f"{bank_id}_chapters"
    
    def get_editable_banks(self):
        """Get all editable banks for the current user"""
        if not self.user_id:
            return []
        
        user_editable_dir = f"{self.editable_banks_path}/{self.user_id}"
        banks = []
        
        if os.path.exists(user_editable_dir):
            for filename in os.listdir(user_editable_dir):
                if filename.endswith('.json'):
                    try:
                        with open(f"{user_editable_dir}/{filename}", 'r') as f:
                            data = json.load(f)
                            banks.append({
                                'id': data.get('id'),
                                'name': data.get('name'),
                                'description': data.get('description'),
                                'created_at': data.get('created_at'),
                                'updated_at': data.get('updated_at'),
                                'bank_type': data.get('bank_type', 'chapters'),
                                'session_count': len(data.get('sessions', [])),
                                'filename': filename
                            })
                    except Exception as e:
                        st.error(f"Error reading editable bank: {e}")
        
        return banks
    
    def load_editable_bank(self, bank_id):
        """Load an editable bank"""
        if not self.user_id:
            return []
        
        bank_file = f"{self.editable_banks_path}/{self.user_id}/{bank_id}.json"
        if os.path.exists(bank_file):
            with open(bank_file, 'r') as f:
                data = json.load(f)
                return data.get('sessions', [])
        return []
    
    def save_editable_bank(self, bank_id, sessions):
        """Save changes to an editable bank"""
        if not self.user_id:
            return False
        
        bank_file = f"{self.editable_banks_path}/{self.user_id}/{bank_id}.json"
        
        if os.path.exists(bank_file):
            with open(bank_file, 'r') as f:
                data = json.load(f)
            data['sessions'] = sessions
            data['updated_at'] = datetime.now().isoformat()
            with open(bank_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        return False
    
    def delete_editable_bank(self, bank_id):
        """Delete an editable bank"""
        if not self.user_id:
            return False
        
        bank_file = f"{self.editable_banks_path}/{self.user_id}/{bank_id}.json"
        if os.path.exists(bank_file):
            os.remove(bank_file)
            return True
        return False
    
    # ============ CUSTOM BANK METHODS - FULLY WORKING ============
    
    def get_user_banks(self):
        """Get all custom banks for the current user"""
        if not self.user_id:
            return []
        
        catalog_file = f"{self.user_banks_path}/{self.user_id}/catalog.json"
        if os.path.exists(catalog_file):
            with open(catalog_file, 'r') as f:
                return json.load(f)
        return []
    
    def _save_user_banks(self, banks):
        """Save user banks catalog"""
        if not self.user_id:
            return
        
        catalog_file = f"{self.user_banks_path}/{self.user_id}/catalog.json"
        with open(catalog_file, 'w') as f:
            json.dump(banks, f, indent=2)
    
    def create_custom_bank(self, name, description="", copy_from=None, bank_type="standard"):
        """Create a new custom bank
        bank_type: "standard" (with topics) or "chapters" (chapters only, no topics)
        """
        if not self.user_id:
            st.error("You must be logged in")
            return None
        
        user_dir = f"{self.user_banks_path}/{self.user_id}"
        os.makedirs(user_dir, exist_ok=True)
        
        bank_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()
        
        sessions = []
        if copy_from:
            sessions = self.load_default_bank(copy_from)
        
        # Save bank file
        bank_file = f"{user_dir}/{bank_id}.json"
        
        # For chapters-only banks, ensure all sessions have empty questions lists
        if bank_type == "chapters":
            # If copying from a standard bank, clear all questions
            for session in sessions:
                session['questions'] = []
        
        with open(bank_file, 'w') as f:
            json.dump({
                'id': bank_id,
                'name': name,
                'description': description,
                'created_at': now,
                'updated_at': now,
                'bank_type': bank_type,  # Store the bank type
                'sessions': sessions
            }, f, indent=2)
        
        # Update catalog
        banks = self.get_user_banks()
        banks.append({
            'id': bank_id,
            'name': name,
            'description': description,
            'created_at': now,
            'updated_at': now,
            'session_count': len(sessions),
            'topic_count': sum(len(s.get('questions', [])) for s in sessions),
            'bank_type': bank_type
        })
        self._save_user_banks(banks)
        
        st.success(f"✅ {bank_type.title()} Bank '{name}' created successfully!")
        return bank_id
    
    def load_user_bank(self, bank_id):
        """Load a custom bank"""
        if not self.user_id:
            return []
        
        bank_file = f"{self.user_banks_path}/{self.user_id}/{bank_id}.json"
        if os.path.exists(bank_file):
            with open(bank_file, 'r') as f:
                data = json.load(f)
                return data.get('sessions', [])
        return []
    
    def delete_user_bank(self, bank_id):
        """Delete a custom bank"""
        if not self.user_id:
            return False
        
        bank_file = f"{self.user_banks_path}/{self.user_id}/{bank_id}.json"
        if os.path.exists(bank_file):
            os.remove(bank_file)
        
        banks = self.get_user_banks()
        banks = [b for b in banks if b['id'] != bank_id]
        self._save_user_banks(banks)
        
        return True
    
    def export_user_bank_to_csv(self, bank_id):
        """Export custom bank to CSV for download"""
        sessions = self.load_user_bank(bank_id)
        
        rows = []
        for session in sessions:
            for i, q in enumerate(session.get('questions', [])):
                rows.append({
                    'session_id': session['id'],
                    'title': session['title'],
                    'guidance': session.get('guidance', '') if i == 0 else '',
                    'question': q,
                    'word_target': session.get('word_target', 500)
                })
        
        if rows:
            df = pd.DataFrame(rows)
            return df.to_csv(index=False)
        return None
    
    def save_user_bank(self, bank_id, sessions):
        """Save changes to a custom bank"""
        if not self.user_id:
            return False
        
        bank_file = f"{self.user_banks_path}/{self.user_id}/{bank_id}.json"
        
        if os.path.exists(bank_file):
            with open(bank_file, 'r') as f:
                data = json.load(f)
            data['sessions'] = sessions
            data['updated_at'] = datetime.now().isoformat()
            with open(bank_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Update catalog
            banks = self.get_user_banks()
            for bank in banks:
                if bank['id'] == bank_id:
                    bank['updated_at'] = datetime.now().isoformat()
                    bank['session_count'] = len(sessions)
                    bank['topic_count'] = sum(len(s.get('questions', [])) for s in sessions)
                    break
            self._save_user_banks(banks)
            
            return True
        return False
    
    # ============ UI METHODS ============
    
    def display_bank_selector(self):
        """Main UI for bank selection"""
        st.title("📚 Question Bank Manager")
        
        tab1, tab2, tab3, tab4 = st.tabs(["📖 Default Banks", "📝 My Editable Banks", "✨ My Custom Banks", "➕ Create New"])
        
        with tab1:
            self._display_default_banks()
        
        with tab2:
            if self.user_id:
                self._display_editable_banks()
            else:
                st.info("🔐 Please log in to manage editable banks")
        
        with tab3:
            if self.user_id:
                self._display_my_banks()
            else:
                st.info("🔐 Please log in to manage custom question banks")
        
        with tab4:
            if self.user_id:
                self._display_create_bank_form()
            else:
                st.info("🔐 Please log in to create custom question banks")
    
    def _display_default_banks(self):
        """Display default banks with load and edit options"""
        
        banks = self.get_default_banks()
        
        if not banks:
            st.info("📁 No question banks found. Please add CSV files to the question_banks/default/ folder.")
            return
        
        st.markdown("### Default Banks")
        st.info("💡 You can load these banks as-is, or create an editable chapters-only version to customize.")
        
        # 2-COLUMN GRID
        cols = st.columns(2)
        for i, bank in enumerate(banks):
            with cols[i % 2]:
                with st.container():
                    st.markdown(f"""
                    <div style="border:1px solid #ddd; border-radius:10px; padding:1rem; margin-bottom:1rem;">
                        <h4>{bank['name']}</h4>
                        <p>{bank['description']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        is_loaded = st.session_state.get('current_bank_id') == bank['id']
                        button_label = "✅ Loaded" if is_loaded else "📂 Load"
                        button_type = "secondary" if is_loaded else "primary"
                        
                        if st.button(button_label, key=f"load_default_{bank['id']}", 
                                   use_container_width=True, type=button_type):
                            if not is_loaded:
                                sessions = self.load_default_bank(bank['id'])
                                if sessions:
                                    st.session_state.current_question_bank = sessions
                                    st.session_state.current_bank_name = bank['name']
                                    st.session_state.current_bank_type = "default"
                                    st.session_state.current_bank_id = bank['id']
                                    
                                    st.success(f"✅ Question Bank Loaded: '{bank['name']}'")
                                    
                                    for session in sessions:
                                        session_id = session["id"]
                                        if session_id not in st.session_state.responses:
                                            st.session_state.responses[session_id] = {
                                                "title": session["title"],
                                                "questions": {},
                                                "summary": "",
                                                "completed": False,
                                                "word_target": session.get("word_target", 500)
                                            }
                                    st.rerun()
                    
                    with col2:
                        if self.user_id:
                            # Check if already have editable version
                            editable_banks = self.get_editable_banks()
                            has_editable = any(f"{bank['id']}_chapters" == b['id'] for b in editable_banks)
                            
                            if has_editable:
                                st.button("✅ Has Editable", disabled=True, use_container_width=True, key=f"has_editable_{bank['id']}")
                            else:
                                if st.button("✏️ Create Editable", key=f"create_editable_{bank['id']}", 
                                           use_container_width=True, type="secondary"):
                                    editable_id = self.create_editable_bank_from_default(bank['id'])
                                    if editable_id:
                                        st.success(f"✅ Created editable chapters version of '{bank['name']}'")
                                        st.rerun()
                        else:
                            st.button("🔒 Login to Edit", disabled=True, use_container_width=True, key=f"login_edit_{bank['id']}")
    
    def _display_editable_banks(self):
        """Display user's editable banks"""
        banks = self.get_editable_banks()
        
        if not banks:
            st.info("📝 You haven't created any editable banks yet. Go to the 'Default Banks' tab and click 'Create Editable' on any bank to get started!")
            return
        
        st.markdown("### My Editable Chapters Banks")
        st.info("✏️ These are chapters-only versions of default banks that you can edit and customize.")
        
        # Add a status area at the top
        status_container = st.empty()
        
        for bank in banks:
            with st.expander(f"📖 {bank['name']}", expanded=False):
                st.write(f"**Description:** {bank.get('description', 'No description')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Chapters", bank.get('session_count', 0))
                with col2:
                    st.caption(f"Last updated: {bank.get('updated_at', '')[:10]}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    is_loaded = st.session_state.get('current_bank_id') == bank['id']
                    button_label = "✅ Loaded" if is_loaded else "📂 Load"
                    button_type = "secondary" if is_loaded else "primary"
                    
                    if st.button(button_label, key=f"load_editable_{bank['id']}", 
                               use_container_width=True, type=button_type):
                        if not is_loaded:
                            sessions = self.load_editable_bank(bank['id'])
                            if sessions:
                                st.session_state.current_question_bank = sessions
                                st.session_state.current_bank_name = bank['name']
                                st.session_state.current_bank_type = "editable"
                                st.session_state.current_bank_id = bank['id']
                                
                                status_container.success(f"✅ Bank Loaded: '{bank['name']}'")
                                
                                for session in sessions:
                                    session_id = session["id"]
                                    if session_id not in st.session_state.responses:
                                        st.session_state.responses[session_id] = {
                                            "title": session["title"],
                                            "questions": {},
                                            "summary": "",
                                            "completed": False,
                                            "word_target": session.get("word_target", 500)
                                        }
                                st.rerun()
                
                with col2:
                    if st.button("✏️ Edit Chapters", key=f"edit_editable_{bank['id']}", 
                               use_container_width=True):
                        st.session_state.editing_bank_id = bank['id']
                        st.session_state.editing_bank_name = bank['name']
                        st.session_state.editing_bank_type = "editable"
                        st.session_state.show_bank_editor = True
                        st.rerun()
                
                with col3:
                    if st.button("🗑️ Delete", key=f"delete_editable_{bank['id']}", 
                               use_container_width=True):
                        if self.delete_editable_bank(bank['id']):
                            status_container.success(f"✅ Deleted '{bank['name']}'")
                            st.rerun()
    
    def _display_my_banks(self):
        """Display user's custom banks"""
        banks = self.get_user_banks()
        
        if not banks:
            st.info("✨ You haven't created any custom question banks yet. Go to the 'Create New' tab to get started!")
            return
        
        # Add a status area at the top
        status_container = st.empty()
        
        for bank in banks:
            # Add emoji based on bank type
            bank_type_emoji = "📚" if bank.get('bank_type', 'standard') == 'standard' else "📖"
            bank_type_label = "Standard Bank" if bank.get('bank_type', 'standard') == 'standard' else "Chapters-Only Bank"
            
            with st.expander(f"{bank_type_emoji} {bank['name']} - {bank_type_label}", expanded=False):
                st.write(f"**Description:** {bank.get('description', 'No description')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Chapters/Sessions", bank.get('session_count', 0))
                with col2:
                    if bank.get('bank_type', 'standard') == 'standard':
                        st.metric("Topics", bank.get('topic_count', 0))
                    else:
                        st.metric("Type", "Chapters Only")
                
                st.caption(f"Created: {bank['created_at'][:10]}")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    is_loaded = st.session_state.get('current_bank_id') == bank['id']
                    button_label = "✅ Loaded" if is_loaded else "📂 Load"
                    button_type = "secondary" if is_loaded else "primary"
                    
                    if st.button(button_label, key=f"load_user_{bank['id']}", 
                               use_container_width=True, type=button_type):
                        status_container.info(f"Loading bank {bank['id']}...")
                        if not is_loaded:
                            sessions = self.load_user_bank(bank['id'])
                            if sessions:
                                st.session_state.current_question_bank = sessions
                                st.session_state.current_bank_name = bank['name']
                                st.session_state.current_bank_type = "custom"
                                st.session_state.current_bank_id = bank['id']
                                
                                status_container.success(f"✅ Bank Loaded: '{bank['name']}'")
                                
                                for session in sessions:
                                    session_id = session["id"]
                                    if session_id not in st.session_state.responses:
                                        st.session_state.responses[session_id] = {
                                            "title": session["title"],
                                            "questions": {},
                                            "summary": "",
                                            "completed": False,
                                            "word_target": session.get("word_target", 500)
                                        }
                                st.rerun()
                        else:
                            status_container.warning("Bank already loaded")
                
                with col2:
                    if st.button("✏️ Edit", key=f"edit_user_{bank['id']}", 
                               use_container_width=True):
                        st.session_state.editing_bank_id = bank['id']
                        st.session_state.editing_bank_name = bank['name']
                        st.session_state.editing_bank_type = "custom"
                        st.session_state.show_bank_editor = True
                        st.rerun()
                
                with col3:
                    # EXPORT TO CSV
                    csv_data = self.export_user_bank_to_csv(bank['id'])
                    if csv_data:
                        st.download_button(
                            label="📥 Save as CSV",
                            data=csv_data,
                            file_name=f"{bank['name'].replace(' ', '_')}.csv",
                            mime="text/csv",
                            key=f"download_{bank['id']}",
                            use_container_width=True
                        )
                    else:
                        st.button(
                            "📥 No Data", 
                            disabled=True, 
                            use_container_width=True,
                            key=f"no_data_{bank['id']}"
                        )
                
                with col4:
                    if st.button("🗑️ Delete", key=f"delete_user_{bank['id']}", 
                               use_container_width=True):
                        if self.delete_user_bank(bank['id']):
                            status_container.success(f"✅ Deleted '{bank['name']}'")
                            st.rerun()
    
    def _display_create_bank_form(self):
        """Display form to create new bank"""
        st.markdown("### Create New Custom Question Bank")
        
        # Add bank type selector
        bank_type = st.radio(
            "Select Bank Type:",
            options=["standard", "chapters"],
            format_func=lambda x: "📚 Standard Bank (with topics/questions)" if x == "standard" else "📖 Chapters-Only Bank (just chapter titles, no topics)",
            horizontal=True,
            help="Chapters-Only banks are perfect for organizing your life into chapters without specific questions"
        )
        
        with st.form("create_bank_form"):
            name = st.text_input("Bank Name *", placeholder="e.g., 'My Life Chapters' or 'Family History'")
            description = st.text_area("Description", placeholder="What kind of stories will this bank contain?")
            
            st.markdown("#### Start from template (optional)")
            default_banks = self.get_default_banks()
            options = ["-- Start from scratch --"] + [b['name'] for b in default_banks]
            selected = st.selectbox("Copy questions from:", options)
            
            submitted = st.form_submit_button("✅ Create Bank", type="primary", use_container_width=True)
            
            if submitted:
                if name.strip():
                    copy_from = None
                    if selected != "-- Start from scratch --":
                        for bank in default_banks:
                            if bank['name'] == selected:
                                copy_from = bank['id']
                                break
                    
                    self.create_custom_bank(name, description, copy_from, bank_type)
                    st.rerun()
                else:
                    st.error("❌ Please enter a bank name")
    
    def display_bank_editor(self, bank_id):
        """Display the bank editor interface"""
        # Determine bank type and load sessions
        if st.session_state.get('editing_bank_type') == 'editable':
            sessions = self.load_editable_bank(bank_id)
            bank_type = 'chapters'  # Editable banks are always chapters-only
            bank_name = st.session_state.get('editing_bank_name', '')
        else:
            # Get bank info to determine type
            banks = self.get_user_banks()
            bank_info = next((b for b in banks if b['id'] == bank_id), {})
            bank_type = bank_info.get('bank_type', 'standard')
            bank_name = bank_info.get('name', '')
            sessions = self.load_user_bank(bank_id)
        
        # Add visible banner at the top
        bank_type_label = "📖 CHAPTERS-ONLY BANK" if bank_type == "chapters" else "📚 STANDARD BANK"
        banner_color = "#2196F3" if bank_type == "chapters" else "#4CAF50"
        
        st.markdown(f"""
        <div style="background-color: {banner_color}; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
            <h3 style="color: white; margin: 0;">✏️ EDITOR MODE - {bank_type_label}: {bank_name}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.title(f"Edit Bank")
        
        st.divider()
        
        # Different header based on bank type
        if bank_type == "chapters":
            st.subheader("📖 Chapters")
            st.info("This is a Chapters-Only bank. Each chapter has a title and guidance, but no topic questions.")
        else:
            st.subheader("📋 Sessions")
        
        if st.button("➕ Add New " + ("Chapter" if bank_type == "chapters" else "Session"), 
                    use_container_width=True, type="primary"):
            max_id = max([s['id'] for s in sessions], default=0)
            sessions.append({
                'id': max_id + 1,
                'title': 'New ' + ("Chapter" if bank_type == "chapters" else "Session"),
                'guidance': '',
                'questions': [],
                'word_target': 500
            })
            if st.session_state.get('editing_bank_type') == 'editable':
                self.save_editable_bank(bank_id, sessions)
            else:
                self.save_user_bank(bank_id, sessions)
            st.rerun()
        
        for i, session in enumerate(sessions):
            # Different expander title based on bank type
            expander_title = f"📁 Chapter {session['id']}: {session['title']}" if bank_type == "chapters" else f"📁 Session {session['id']}: {session['title']}"
            
            with st.expander(expander_title, expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    new_title = st.text_input("Title", session['title'], key=f"title_{session['id']}")
                    new_guidance = st.text_area("Guidance", session.get('guidance', ''), 
                                               key=f"guidance_{session['id']}", height=100)
                    new_target = st.number_input("Word Target", 
                                               value=session.get('word_target', 500),
                                               min_value=100, max_value=5000, step=100,
                                               key=f"target_{session['id']}")
                
                with col2:
                    st.write("**Actions**")
                    if i > 0:
                        if st.button("⬆️ Move Up", key=f"up_{session['id']}", use_container_width=True):
                            sessions[i], sessions[i-1] = sessions[i-1], sessions[i]
                            for idx, s in enumerate(sessions):
                                s['id'] = idx + 1
                            if st.session_state.get('editing_bank_type') == 'editable':
                                self.save_editable_bank(bank_id, sessions)
                            else:
                                self.save_user_bank(bank_id, sessions)
                            st.rerun()
                    
                    if i < len(sessions) - 1:
                        if st.button("⬇️ Move Down", key=f"down_{session['id']}", use_container_width=True):
                            sessions[i], sessions[i+1] = sessions[i+1], sessions[i]
                            for idx, s in enumerate(sessions):
                                s['id'] = idx + 1
                            if st.session_state.get('editing_bank_type') == 'editable':
                                self.save_editable_bank(bank_id, sessions)
                            else:
                                self.save_user_bank(bank_id, sessions)
                            st.rerun()
                    
                    if st.button("💾 Save", key=f"save_{session['id']}", use_container_width=True, type="primary"):
                        session['title'] = new_title
                        session['guidance'] = new_guidance
                        session['word_target'] = new_target
                        if st.session_state.get('editing_bank_type') == 'editable':
                            self.save_editable_bank(bank_id, sessions)
                        else:
                            self.save_user_bank(bank_id, sessions)
                        st.success("✅ Saved")
                        st.rerun()
                    
                    if st.button("🗑️ Delete", key=f"delete_{session['id']}", use_container_width=True):
                        sessions.pop(i)
                        for idx, s in enumerate(sessions):
                            s['id'] = idx + 1
                        if st.session_state.get('editing_bank_type') == 'editable':
                            self.save_editable_bank(bank_id, sessions)
                        else:
                            self.save_user_bank(bank_id, sessions)
                        st.rerun()
                
                # Only show topics/questions section for standard banks
                if bank_type == "standard":
                    st.divider()
                    st.write("**Topics/Questions:**")
                    
                    new_topic = st.text_input("Add new topic", key=f"new_topic_{session['id']}")
                    if new_topic:
                        if st.button("➕ Add", key=f"add_topic_{session['id']}", use_container_width=True):
                            session['questions'].append(new_topic)
                            self.save_user_bank(bank_id, sessions)
                            st.rerun()
                    
                    for j, topic in enumerate(session.get('questions', [])):
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            edited = st.text_area(f"Topic {j+1}", topic, 
                                                key=f"topic_{session['id']}_{j}", height=60)
                        
                        with col2:
                            if j > 0:
                                if st.button("⬆️", key=f"topic_up_{session['id']}_{j}"):
                                    session['questions'][j], session['questions'][j-1] = session['questions'][j-1], session['questions'][j]
                                    self.save_user_bank(bank_id, sessions)
                                    st.rerun()
                            if j < len(session['questions']) - 1:
                                if st.button("⬇️", key=f"topic_down_{session['id']}_{j}"):
                                    session['questions'][j], session['questions'][j+1] = session['questions'][j+1], session['questions'][j]
                                    self.save_user_bank(bank_id, sessions)
                                    st.rerun()
                        
                        with col3:
                            if st.button("💾", key=f"topic_save_{session['id']}_{j}"):
                                session['questions'][j] = edited
                                self.save_user_bank(bank_id, sessions)
                                st.rerun()
                            
                            if st.button("🗑️", key=f"topic_del_{session['id']}_{j}"):
                                session['questions'].pop(j)
                                self.save_user_bank(bank_id, sessions)
                                st.rerun()
                        
                        st.divider()
                else:
                    # For chapters-only banks, show a simple message
                    st.caption("✨ This is a chapters-only bank. No topics/questions needed.")
        
        if st.button("🔙 Back to Bank Manager", use_container_width=True):
            st.session_state.show_bank_editor = False
            st.rerun()
