# ============================================================================
# BUTTONS ROW - WITH SPELLCHECK AND AI REWRITE
# ============================================================================
col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 2])

# Spellcheck state management
spellcheck_base = f"spell_{editor_base_key}"
spell_result_key = f"{spellcheck_base}_result"
current_content = st.session_state.get(content_key, "")
has_content = current_content and current_content != "<p><br></p>" and current_content != "<p>Start writing your story here...</p>"
showing_results = spell_result_key in st.session_state and st.session_state[spell_result_key].get("show", False)

with col1:
    if st.button("💾 Save", key=f"save_btn_{editor_base_key}", type="primary", use_container_width=True):
        current_content = st.session_state[content_key]
        if current_content and current_content.strip() and current_content != "<p><br></p>" and current_content != "<p>Start writing your story here...</p>":
            with st.spinner("Saving your story..."):
                if save_response(current_session_id, current_question_text, current_content):
                    st.success("✅ Saved!")
                    time.sleep(0.5)
                    st.rerun()
                else: 
                    st.error("Failed to save")
        else: 
            st.warning("Please write something!")

with col2:
    if existing_answer and existing_answer != "<p>Start writing your story here...</p>":
        if st.button("🗑️ Delete", key=f"del_btn_{editor_base_key}", use_container_width=True):
            if delete_response(current_session_id, current_question_text):
                st.session_state[content_key] = "<p>Start writing your story here...</p>"
                st.success("✅ Deleted!")
                st.rerun()
    else: 
        st.button("🗑️ Delete", key=f"del_disabled_{editor_base_key}", disabled=True, use_container_width=True)

with col3:
    # Spellcheck Button
    if has_content and not showing_results:
        if st.button("🔍 Spell Check", key=f"spell_{editor_base_key}", use_container_width=True):
            with st.spinner("Checking spelling and grammar..."):
                text_only = re.sub(r'<[^>]+>', '', current_content)
                if len(text_only.split()) >= 3:
                    corrected = auto_correct_text(text_only)
                    if corrected and corrected != text_only:
                        st.session_state[spell_result_key] = {
                            "original": text_only,
                            "corrected": corrected,
                            "show": True
                        }
                    else:
                        st.session_state[spell_result_key] = {
                            "message": "✅ No spelling or grammar issues found!",
                            "show": True
                        }
                    st.rerun()
                else:
                    st.warning("Text too short for spell check (minimum 3 words)")
    else:
        st.button("🔍 Spell Check", key=f"spell_disabled_{editor_base_key}", disabled=True, use_container_width=True)

with col4:
    # AI Rewrite Button
    if has_content:
        if st.button("✨ AI Rewrite", key=f"rewrite_btn_{editor_base_key}", use_container_width=True):
            st.session_state.show_ai_rewrite_menu = True
            st.rerun()
    else:
        st.button("✨ AI Rewrite", key=f"rewrite_disabled_{editor_base_key}", disabled=True, use_container_width=True)

with col5:
    # Person selector dropdown (appears when AI Rewrite is clicked)
    if st.session_state.get('show_ai_rewrite_menu', False):
        person_option = st.selectbox(
            "Voice:",
            options=["1st", "2nd", "3rd"],
            format_func=lambda x: {"1st": "👤 First Person", "2nd": "💬 Second Person", "3rd": "📖 Third Person"}[x],
            key=f"person_select_{editor_base_key}",
            label_visibility="collapsed"
        )
        
        if st.button("Go", key=f"go_rewrite_{editor_base_key}", type="primary", use_container_width=True):
            with st.spinner(f"Rewriting in {person_option} person..."):
                current_content = st.session_state[content_key]
                result = ai_rewrite_answer(
                    current_content, 
                    person_option, 
                    current_question_text, 
                    current_session['title']
                )
                
                if result.get('success'):
                    st.session_state.current_rewrite_data = result
                    st.session_state.show_ai_rewrite = True
                    st.session_state.show_ai_rewrite_menu = False
                    st.rerun()
                else:
                    st.error(result.get('error', 'Failed to rewrite'))
    else:
        # Placeholder to maintain column layout
        st.markdown("")

with col6:
    nav1, nav2 = st.columns(2)
    with nav1: 
        prev_disabled = st.session_state.current_question == 0
        if st.button("← Previous", disabled=prev_disabled, key=f"prev_{editor_base_key}", use_container_width=True):
            if not prev_disabled:
                st.session_state.current_question -= 1
                st.session_state.current_question_override = None
                st.session_state.show_ai_rewrite_menu = False
                st.rerun()
    with nav2:
        next_disabled = st.session_state.current_question >= len(current_session["questions"]) - 1
        if st.button("Next →", disabled=next_disabled, key=f"next_{editor_base_key}", use_container_width=True):
            if not next_disabled:
                st.session_state.current_question += 1
                st.session_state.current_question_override = None
                st.session_state.show_ai_rewrite_menu = False
                st.rerun()

# Display spellcheck results if they exist (below the button row)
if showing_results:
    result = st.session_state[spell_result_key]
    if "corrected" in result:
        st.markdown("---")
        st.markdown("### ✅ Suggested Corrections:")
        st.markdown(f'<div style="background-color: #f0f9ff; padding: 15px; border-radius: 8px; border-left: 4px solid #4CAF50;">{result["corrected"]}</div>', unsafe_allow_html=True)
        
        col_apply1, col_apply2, col_apply3 = st.columns([1, 1, 1])
        with col_apply2:
            if st.button("📋 Apply Corrections", key=f"{spellcheck_base}_apply", type="primary", use_container_width=True):
                corrected = result["corrected"]
                if not corrected.startswith('<p>'):
                    corrected = f'<p>{corrected}</p>'
                
                st.session_state[content_key] = corrected
                save_response(current_session_id, current_question_text, corrected)
                st.session_state[version_key] += 1
                st.session_state[spell_result_key] = {"show": False}
                st.success("✅ Corrections applied!")
                st.rerun()
            
            if st.button("❌ Dismiss", key=f"{spellcheck_base}_dismiss", use_container_width=True):
                st.session_state[spell_result_key] = {"show": False}
                st.rerun()
    
    elif "message" in result:
        st.success(result["message"])
        if st.button("Dismiss", key=f"{spellcheck_base}_dismiss_msg"):
            st.session_state[spell_result_key] = {"show": False}
            st.rerun()

st.markdown("---")





