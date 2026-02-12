# vignettes.py - COMPLETE WORKING VERSION
import streamlit as st
import json
from datetime import datetime
import os
import uuid

class VignetteManager:
    def __init__(self, user_id):
        self.user_id = user_id
        self.file = f"user_vignettes/{user_id}_vignettes.json"
        os.makedirs("user_vignettes", exist_ok=True)
        self._load()
    
    def _load(self):
        try:
            if os.path.exists(self.file):
                with open(self.file, 'r') as f:
                    self.vignettes = json.load(f)
            else:
                self.vignettes = []
        except:
            self.vignettes = []
    
    def _save(self):
        with open(self.file, 'w') as f:
            json.dump(self.vignettes, f)
    
    def create_vignette(self, title, content, theme, is_draft=False):
        vignette = {
            "id": str(uuid.uuid4())[:8],
            "title": title,
            "content": content,
            "theme": theme,
            "word_count": len(content.split()),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "is_draft": is_draft,
            "is_published": not is_draft
        }
        self.vignettes.append(vignette)
        self._save()
        return vignette
    
    def update_vignette(self, id, title, content, theme):
        for v in self.vignettes:
            if v["id"] == id:
                v["title"] = title
                v["content"] = content
                v["theme"] = theme
                v["word_count"] = len(content.split())
                v["updated_at"] = datetime.now().isoformat()
                self._save()
                return True
        return False
    
    def delete_vignette(self, id):
        self.vignettes = [v for v in self.vignettes if v["id"] != id]
        self._save()
        return True
    
    def publish_vignette(self, id):
        for v in self.vignettes:
            if v["id"] == id:
                v["is_draft"] = False
                v["is_published"] = True
                v["published_at"] = datetime.now().isoformat()
                self._save()
                return True
        return False
    
    def get_vignette_by_id(self, id):
        for v in self.vignettes:
            if v["id"] == id:
                return v
        return None
    
    def display_vignette_creator(self, on_publish=None, edit_vignette=None):
        if edit_vignette:
            st.subheader("✏️ Edit Vignette")
            title = st.text_input("Title", value=edit_vignette.get("title", ""))
            theme = st.text_input("Theme", value=edit_vignette.get("theme", ""))
            content = st.text_area("Story", value=edit_vignette.get("content", ""), height=300)
            
            if st.button("💾 Save Changes"):
                if title and content:
                    self.update_vignette(edit_vignette["id"], title, content, theme)
                    st.success("Saved!")
                    st.rerun()
                    return True
        else:
            st.subheader("✍️ Create Vignette")
            title = st.text_input("Title")
            theme = st.text_input("Theme")
            content = st.text_area("Story", height=300)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚀 Publish"):
                    if title and content:
                        v = self.create_vignette(title, content, theme, is_draft=False)
                        if on_publish:
                            on_publish(v)
                        st.success("Published!")
                        st.rerun()
                        return True
            with col2:
                if st.button("💾 Draft"):
                    if content:
                        title = title if title else "Draft"
                        self.create_vignette(title, content, theme, is_draft=True)
                        st.success("Draft saved!")
                        st.rerun()
                        return True
        return False
    
    def display_vignette_gallery(self, filter_by="all", on_select=None, on_edit=None, on_delete=None):
        if filter_by == "published":
            vignettes = [v for v in self.vignettes if v.get("is_published")]
        elif filter_by == "drafts":
            vignettes = [v for v in self.vignettes if v.get("is_draft")]
        else:
            vignettes = self.vignettes
        
        if not vignettes:
            st.info("No vignettes yet.")
            return
        
        for v in vignettes:
            st.markdown(f"### {v['title']}")
            st.markdown(f"*Theme: {v['theme']}*")
            st.markdown(v['content'][:200] + "..." if len(v['content']) > 200 else v['content'])
            st.markdown(f"📝 {v['word_count']} words")
            st.markdown(f"**{'Published' if v.get('is_published') else 'Draft'}**")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Read", key=f"read_{v['id']}"):
                    if on_select:
                        on_select(v['id'])
            with col2:
                if st.button("Edit", key=f"edit_{v['id']}"):
                    if on_edit:
                        on_edit(v['id'])
            with col3:
                if st.button("Delete", key=f"delete_{v['id']}"):
                    if on_delete:
                        on_delete(v['id'])
            st.divider()
    
    def display_full_vignette(self, vignette_id, on_back=None, on_edit=None):
        v = self.get_vignette_by_id(vignette_id)
        if not v:
            st.error("Vignette not found")
            return
        
        if st.button("← Back"):
            if on_back:
                on_back()
        
        st.title(v['title'])
        st.markdown(f"**Theme:** {v['theme']}")
        st.markdown(f"**Words:** {v['word_count']}")
        if v.get('is_published'):
            st.markdown(f"**Published:** {v.get('published_at', '')[:10]}")
        else:
            st.markdown(f"**Created:** {v.get('created_at', '')[:10]}")
        
        st.markdown("---")
        st.write(v['content'])
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✏️ Edit"):
                if on_edit:
                    on_edit(v['id'])
        with col2:
            if st.button("← Back to Gallery"):
                if on_back:
                    on_back()
        
        if v.get('is_draft'):
            if st.button("🚀 Publish"):
                self.publish_vignette(v['id'])
                st.success("Published!")
                st.rerun()
