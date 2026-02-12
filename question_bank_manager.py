# question_bank_manager.py - COMPLETE CONTROL VERSION WITH DEBUGGING
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
        
        # ONLY create directories - NEVER create files
        os.makedirs(self.default_banks_path, exist_ok=True)
        os.makedirs(self.user_banks_path, exist_ok=True)
        if self.user_id:
            os.makedirs(f"{self.user_banks_path}/{self.user_id}", exist_ok=True)
        
        # NO FILE CREATION - DELETED _init_default_banks completely
    
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
        """Get list of default banks - READ ONLY from CSV files"""
        banks = []
        
        # Read existing CSV files - NEVER create them
        if os.path.exists(self.default_banks_path):
            for filename in os.listdir(self.default_banks_path):
                if filename.endswith('.csv'):
                    bank_id = filename.replace('.csv', '')
                    
                    # Create display name from filename
                    name_parts = bank_id.replace('_', ' ').title()
                    
                    try:
                        # Count sessions and topics
                        df = pd.read_csv(f"{self.default_banks_path}/{filename}")
                        sessions = df['session_id'].nunique()
                        topics = len(df)
                        
                        banks.append({
                            "id": bank_id,
                            "name": f"📖 {name_parts}",
                            "description": f"Loaded from {filename}",
                            "sessions": sessions,
                            "topics": topics,
                            "filename": filename
                        })
                    except Exception as e:
                        st.error(f"Error reading {filename}: {e}")
        
        return banks
    
    def load_default_bank(self, bank_id):
        """Load a default bank by ID - READ ONLY from CSV"""
        filename = f"{self.default_banks_path}/{bank_id}.csv"
        
        if os.path.exists(filename):
            return self.load_sessions_from_csv(filename)
        return []
    
    def delete_default_bank(self, bank_id, filename):
        """DELETE a default bank CSV file from the cloud"""
        try:
            filepath = f"{self.default_banks_path}/{filename}"
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
        except Exception as e:
            st.error(f"Error deleting file: {e}")
        return False
    
    # ============ CUSTOM BANK METHODS ============
    
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
    
    def create_custom_bank(self, name, description="", copy_from=None):
        """Create a new custom bank"""
        if not self.user_id:
            st.error("You must be logged in")
            return None
        
        user_dir = f"{self.user_banks_path}/{self.user_id}"
        os.makedirs(user_dir, exist_ok=True)
        
        bank_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()
        
        # Get sessions to copy
        sessions = []
        if copy_from:
            sessions = self.load_default_bank(copy_from)
        
        # Save bank file
        bank_file = f"{user_dir}/{bank_id}.json"
        with open(bank_file, 'w') as f:
            json.dump({
                'id': bank_id,
                'name': name,
                'description': description,
                'created_at': now,
                'updated_at': now,
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
            'topic_count': sum(len(s.get('questions', [])) for s in sessions)
        })
        self._save_user_banks(banks)
        
        st.success(f"✅ Bank '{name}' created successfully!")
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
    
    # ============ UI METHODS ============
    
    def display_bank_selector(self):
        """Main UI for bank selection"""
        st.title("📚 Question Bank Manager")
        
        tab1, tab2, tab3 = st.tabs(["📖 Default Banks", "✨ My Custom Banks", "➕ Create New"])
        
        with tab1:
            self._display_default_banks()
        
        with tab2:
            if self.user_id:
                self._display_my_banks()
            else:
                st.info("🔐 Please log in to manage custom question banks")
        
        with tab3:
            if self.user_id:
                self._display_create_bank_form()
            else:
                st.info("🔐 Please log in to create custom question banks")
    
    def _display_default_banks(self):
        """Display default banks with load buttons - READ ONLY + DOWNLOAD + DELETE"""
        
        # ============ MEGA DEBUG - SHOW EVERYTHING ============
        st.error("🔍🔍🔍 DEBUG MODE - SHOWING EVERY PATH 🔍🔍🔍")
        
        import os
        import sys
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**🐍 PYTHON PATHS**")
            st.write(f"Current working dir: `{os.getcwd()}`")
            st.write(f"Script dir: `{os.path.dirname(os.path.abspath(__file__))}`")
            st.write(f"Default banks path: `{os.path.abspath(self.default_banks_path)}`")
            
        with col2:
            st.write("**📁 DIRECTORY CONTENTS**")
            
            # Check root
            st.write("**Root directory:**")
            root_files = os.listdir(".")
            csv_in_root = [f for f in root_files if f.endswith('.csv')]
            st.write(f"CSV files in root: {csv_in_root}")
            
            # Check question_banks
            if os.path.exists("question_banks"):
                qb_files = os.listdir("question_banks")
                st.write(f"question_banks/: {qb_files}")
            else:
                st.write("question_banks/: ❌ NOT FOUND")
            
            # Check question_banks/default
            if os.path.exists(self.default_banks_path):
                default_files = os.listdir(self.default_banks_path)
                st.write(f"{self.default_banks_path}/: {default_files}")
                
                # Show full paths
                st.write("**Full paths:**")
                for f in default_files:
                    full_path = os.path.abspath(f"{self.default_banks_path}/{f}")
                    st.write(f"- `{full_path}`")
            else:
                st.write(f"{self.default_banks_path}/: ❌ NOT FOUND")
        
        st.error("🔍🔍🔍 END DEBUG 🔍🔍🔍")
        st.divider()
        # ============ END DEBUG ============
        
        # Show what files exist in the cloud
        st.subheader("📁 Files in Cloud Storage")
        
        if os.path.exists(self.default_banks_path):
            files = os.listdir(self.default_banks_path)
            csv_files = [f for f in files if f.endswith('.csv')]
            
            if csv_files:
                st.warning("⚠️ These files exist ONLY in Streamlit Cloud, NOT in your GitHub repo!")
                
                for file in csv_files:
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                    with col1:
                        st.code(f"📄 {file}")
                    with col2:
                        # Download button
                        try:
                            df = pd.read_csv(f"{self.default_banks_path}/{file}")
                            csv = df.to_csv(index=False)
                            st.download_button(
                                label="📥 Download",
                                data=csv,
                                file_name=file,
                                mime="text/csv",
                                key=f"download_{file}",
                                use_container_width=True
                            )
                        except:
                            st.button("📥 Error", disabled=True, use_container_width=True)
                    with col3:
                        # Delete button
                        if st.button("🗑️ Delete", key=f"delete_{file}", use_container_width=True):
                            filepath = f"{self.default_banks_path}/{file}"
                            os.remove(filepath)
                            st.success(f"Deleted {file}")
                            st.rerun()
                    with col4:
                        # Info
                        st.caption("☁️ Cloud only")
                st.divider()
            else:
                st.info("✅ No CSV files in cloud storage. All banks are from GitHub.")
        else:
            st.info("📁 No default banks directory found.")
        
        # Now show available banks to load
        st.subheader("📚 Available Question Banks")
        banks = self.get_default_banks()
        
        if not banks:
            st.error("❌ NO CSV FILES FOUND!")
            st.markdown(f"""
            **Debug Information:**
            - Path checked: `{os.path.abspath(self.default_banks_path)}`
            - Directory exists: {os.path.exists(self.default_banks_path)}
            
            **To fix:**
            1. Make sure your CSV file is in the correct GitHub folder: `question_banks/default/life_story_comprehensive.csv`
            2. Go to Streamlit Cloud dashboard and click **Reboot**
            3. Wait 2 minutes and refresh
            4. If still not working, check file permissions in GitHub
            """)
            return
        
        # 2-COLUMN GRID for loading banks
        cols = st.columns(2)
        for i, bank in enumerate(banks):
            with cols[i % 2]:
                with st.container():
                    st.markdown(f"""
                    <div style="border:1px solid #ddd; border-radius:10px; padding:1rem; margin-bottom:1rem;">
                        <h4>{bank['name']}</h4>
                        <p>{bank['description']}</p>
                        <p style="color:#666;">📋 {bank['sessions']} sessions • 💬 {bank['topics']} topics</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show loaded status if this bank is currently loaded
                    is_loaded = st.session_state.get('current_bank_id') == bank['id']
                    button_label = "✅ Loaded" if is_loaded else "📂 Load Question Bank"
                    button_type = "secondary" if is_loaded else "primary"
                    
                    if st.button(button_label, key=f"load_default_{bank['id']}", 
                               use_container_width=True, type=button_type):
                        if not is_loaded:  # Only load if not already loaded
                            sessions = self.load_default_bank(bank['id'])
                            if sessions:
                                st.session_state.current_question_bank = sessions
                                st.session_state.current_bank_name = bank['name']
                                st.session_state.current_bank_type = "default"
                                st.session_state.current_bank_id = bank['id']
                                
                                st.success(f"✅ Question Bank Loaded: '{bank['name']}'")
                                
                                # Initialize responses
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
    
    def _display_my_banks(self):
        """Display user's custom banks"""
        banks = self.get_user_banks()
        
        if not banks:
            st.info("✨ You haven't created any custom question banks yet. Go to the 'Create New' tab to get started!")
            return
        
        for bank in banks:
            with st.expander(f"📚 {bank['name']}", expanded=False):
                st.write(f"**Description:** {bank.get('description', 'No description')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Sessions", bank.get('session_count', 0))
                with col2:
                    st.metric("Topics", bank.get('topic_count', 0))
                
                st.caption(f"Created: {bank['created_at'][:10]}")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    is_loaded = st.session_state.get('current_bank_id') == bank['id']
                    button_label = "✅ Loaded" if is_loaded else "📂 Load Question Bank"
                    button_type = "secondary" if is_loaded else "primary"
                    
                    if st.button(button_label, key=f"load_user_{bank['id']}", 
                               use_container_width=True, type=button_type):
                        if not is_loaded:
                            sessions = self.load_user_bank(bank['id'])
                            if sessions:
                                st.session_state.current_question_bank = sessions
                                st.session_state.current_bank_name = bank['name']
                                st.session_state.current_bank_type = "custom"
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
                    if st.button("✏️ Edit", key=f"edit_user_{bank['id']}", 
                               use_container_width=True):
                        st.session_state.editing_bank_id = bank['id']
                        st.session_state.editing_bank_name = bank['name']
                        st.session_state.show_bank_editor = True
                        st.rerun()
                
                with col3:
                    if st.button("📋 Export", key=f"export_user_{bank['id']}", 
                               use_container_width=True):
                        self._export_bank(bank['id'])
                
                with col4:
                    if st.button("🗑️ Delete", key=f"delete_user_{bank['id']}", 
                               use_container_width=True):
                        if self.delete_user_bank(bank['id']):
                            st.success(f"✅ Deleted '{bank['name']}'")
                            st.rerun()
    
    def _display_create_bank_form(self):
        """Display form to create new bank"""
        st.markdown("### Create New Question Bank")
        
        with st.form("create_bank_form"):
            name = st.text_input("Bank Name *", placeholder="e.g., 'My Family Stories'")
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
                    
                    self.create_custom_bank(name, description, copy_from)
                    st.rerun()
                else:
                    st.error("❌ Please enter a bank name")
    
    def _export_bank(self, bank_id):
        """Export bank to CSV"""
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
            csv = df.to_csv(index=False)
            
            banks = self.get_user_banks()
            bank_name = next((b['name'] for b in banks if b['id'] == bank_id), 'bank')
            
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"{bank_name.replace(' ', '_')}.csv",
                mime="text/csv",
                key=f"download_{bank_id}"
            )
    
    def display_bank_editor(self, bank_id):
        """Display the bank editor interface"""
        st.title(f"✏️ Edit Bank")
        
        sessions = self.load_user_bank(bank_id)
        
        banks = self.get_user_banks()
        bank_info = next((b for b in banks if b['id'] == bank_id), {})
        
        with st.expander("Bank Settings", expanded=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                new_name = st.text_input("Bank Name", value=bank_info.get('name', ''))
                new_desc = st.text_area("Description", value=bank_info.get('description', ''))
            with col2:
                if st.button("💾 Save Settings", use_container_width=True, type="primary"):
                    for bank in banks:
                        if bank['id'] == bank_id:
                            bank['name'] = new_name
                            bank['description'] = new_desc
                            bank['updated_at'] = datetime.now().isoformat()
                    self._save_user_banks(banks)
                    st.success("✅ Settings saved")
                    st.rerun()
        
        st.divider()
        
        st.subheader("📋 Sessions")
        
        if st.button("➕ Add New Session", use_container_width=True, type="primary"):
            max_id = max([s['id'] for s in sessions], default=0)
            sessions.append({
                'id': max_id + 1,
                'title': 'New Session',
                'guidance': '',
                'questions': [],
                'word_target': 500
            })
            self.save_user_bank(bank_id, sessions)
            st.rerun()
        
        for i, session in enumerate(sessions):
            with st.expander(f"📁 Session {session['id']}: {session['title']}", expanded=False):
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
                            self.save_user_bank(bank_id, sessions)
                            st.rerun()
                    
                    if i < len(sessions) - 1:
                        if st.button("⬇️ Move Down", key=f"down_{session['id']}", use_container_width=True):
                            sessions[i], sessions[i+1] = sessions[i+1], sessions[i]
                            for idx, s in enumerate(sessions):
                                s['id'] = idx + 1
                            self.save_user_bank(bank_id, sessions)
                            st.rerun()
                    
                    if st.button("💾 Save", key=f"save_{session['id']}", use_container_width=True, type="primary"):
                        session['title'] = new_title
                        session['guidance'] = new_guidance
                        session['word_target'] = new_target
                        self.save_user_bank(bank_id, sessions)
                        st.success("✅ Saved")
                        st.rerun()
                    
                    if st.button("🗑️ Delete", key=f"delete_{session['id']}", use_container_width=True):
                        sessions.pop(i)
                        for idx, s in enumerate(sessions):
                            s['id'] = idx + 1
                        self.save_user_bank(bank_id, sessions)
                        st.rerun()
                
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
        
        if st.button("🔙 Back to Bank Manager", use_container_width=True):
            st.session_state.show_bank_editor = False
            st.rerun()
    
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
