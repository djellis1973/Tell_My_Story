# biography_publisher.py - Standalone Book Publisher
import streamlit as st
import json
from datetime import datetime
import os
import re
import base64
import io
import zipfile
import hashlib

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="Tell My Story - Publisher",
    page_icon="📚",
    layout="wide"
)

# ============================================================================
# CSS STYLING
# ============================================================================
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 30px;
    }
    .story-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .question {
        font-weight: bold;
        color: #2c3e50;
        border-left: 4px solid #3498db;
        padding-left: 15px;
        margin-bottom: 10px;
    }
    .stats-box {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        border-left: 4px solid #27ae60;
    }
    .preview-image {
        max-width: 100%;
        border-radius: 5px;
        margin: 10px 0;
    }
    .stButton button {
        width: 100%;
    }
    .success-message {
        padding: 20px;
        background: #d4edda;
        color: #155724;
        border-radius: 10px;
        text-align: center;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DIRECTORY SETUP
# ============================================================================
os.makedirs("uploads/published", exist_ok=True)
os.makedirs("uploads/covers", exist_ok=True)

# ============================================================================
# SAMPLE DATA (for testing without main app)
# ============================================================================
SAMPLE_STORIES = [
    {
        "question": "Where were you born?",
        "answer_text": "I was born in a small town called Springfield. It was a quiet place with tree-lined streets and friendly neighbors. Our house was a modest two-story home with a big backyard where I spent countless hours playing.",
        "session_title": "Early Years",
        "session_id": 1,
        "has_images": False
    },
    {
        "question": "Tell me about your parents",
        "answer_text": "My father was a teacher who loved literature. He would read to me every night, instilling a love for stories that stays with me to this day. My mother was a nurse, compassionate and strong. She taught me the value of helping others.",
        "session_title": "Early Years",
        "session_id": 1,
        "has_images": False
    },
    {
        "question": "What was your first job?",
        "answer_text": "My first job was at a local bookstore when I was sixteen. I loved being surrounded by books and helping customers find their next great read. It taught me responsibility and the joy of earning my own money.",
        "session_title": "Career & Life's Work",
        "session_id": 3,
        "has_images": False
    }
]

# ============================================================================
# IMAGE HANDLER (for standalone mode)
# ============================================================================
class ImageHandler:
    def __init__(self):
        self.upload_dir = "uploads"
    
    def get_image_base64(self, image_id):
        """Get image as base64 string"""
        try:
            # Try multiple possible paths
            possible_paths = [
                f"{self.upload_dir}/{image_id}.jpg",
                f"{self.upload_dir}/user_{image_id[:8]}/{image_id}.jpg",
                f"{self.upload_dir}/thumbnails/{image_id}.jpg"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, 'rb') as f:
                        return base64.b64encode(f.read()).decode()
            
            # Also check metadata to find actual path
            meta_path = f"{self.upload_dir}/metadata/{image_id}.json"
            if os.path.exists(meta_path):
                with open(meta_path, 'r') as f:
                    meta = json.load(f)
                user_hash = hashlib.md5(meta.get('user_id', '').encode()).hexdigest()[:8]
                img_path = f"{self.upload_dir}/user_{user_hash}/{image_id}.jpg"
                if os.path.exists(img_path):
                    with open(img_path, 'rb') as f:
                        return base64.b64encode(f.read()).decode()
        except:
            pass
        return None

# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================
def load_user_data_file(file):
    """Load data from uploaded JSON file"""
    try:
        content = file.read().decode('utf-8')
        data = json.loads(content)
        return data
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

def load_from_main_app():
    """Try to load data from main app session state if available"""
    try:
        # Check if we're running inside main app
        import streamlit as st
        if hasattr(st, 'session_state') and 'responses' in st.session_state:
            stories = []
            image_handler = ImageHandler()
            
            # Get sessions from main app
            sessions = st.session_state.get('current_question_bank', [])
            responses = st.session_state.responses
            
            for session in sessions:
                session_id = session["id"]
                session_data = responses.get(session_id, {})
                
                for question, answer_data in session_data.get("questions", {}).items():
                    # Get images
                    images = []
                    if answer_data.get("images"):
                        for img_ref in answer_data.get("images", []):
                            img_id = img_ref.get("id")
                            b64 = image_handler.get_image_base64(img_id)
                            if b64:
                                images.append({
                                    "id": img_id,
                                    "base64": b64,
                                    "caption": img_ref.get("caption", "")
                                })
                    
                    stories.append({
                        "question": question,
                        "answer_text": re.sub(r'<[^>]+>', '', answer_data.get("answer", "")),
                        "session_title": session["title"],
                        "session_id": session_id,
                        "has_images": answer_data.get("has_images", False),
                        "image_count": answer_data.get("image_count", 0),
                        "images": images
                    })
            
            # Get user info
            user_info = {}
            if st.session_state.get('user_account'):
                profile = st.session_state.user_account.get('profile', {})
                user_info = {
                    "first_name": profile.get('first_name', 'Author'),
                    "last_name": profile.get('last_name', ''),
                    "email": profile.get('email', '')
                }
            
            return {
                "success": True,
                "stories": stories,
                "user_info": user_info,
                "total_stories": len(stories),
                "source": "main_app"
            }
    except:
        pass
    return {"success": False}

# ============================================================================
# GENERATION FUNCTIONS
# ============================================================================
def generate_docx(title, author, stories, format_style="interview", include_toc=True, include_images=True, cover_image=None):
    """Generate a Word document from stories"""
    try:
        from docx import Document
        from docx.shared import Inches, Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        
        doc = Document()
        
        # Set default font
        style = doc.styles['Normal']
        style.font.name = 'Times New Roman'
        style.font.size = Pt(12)
        
        # Cover page
        if cover_image:
            try:
                img_stream = io.BytesIO(cover_image)
                doc.add_picture(img_stream, width=Inches(5))
                last_paragraph = doc.paragraphs[-1]
                last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                doc.add_paragraph()
            except:
                pass
        
        # Title
        title_para = doc.add_paragraph()
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title_para.add_run(title)
        title_run.font.size = Pt(28)
        title_run.font.bold = True
        
        # Author
        author_para = doc.add_paragraph()
        author_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        author_run = author_para.add_run(f"by {author}")
        author_run.font.size = Pt(16)
        author_run.font.italic = True
        
        doc.add_page_break()
        
        # Copyright
        copyright_para = doc.add_paragraph()
        copyright_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        copyright_para.add_run(f"© {datetime.now().year} {author}. All rights reserved.")
        doc.add_page_break()
        
        # Table of Contents
        if include_toc:
            toc_para = doc.add_paragraph()
            toc_run = toc_para.add_run("Table of Contents")
            toc_run.font.size = Pt(18)
            toc_run.font.bold = True
            
            # Group by session
            sessions = {}
            for story in stories:
                session_title = story.get('session_title', 'Untitled Session')
                if session_title not in sessions:
                    sessions[session_title] = []
                sessions[session_title].append(story)
            
            for session_title in sessions.keys():
                doc.add_paragraph(f"  {session_title}", style='List Bullet')
            
            doc.add_page_break()
        
        # Stories
        current_session = None
        for story in stories:
            session_title = story.get('session_title', 'Untitled Session')
            
            if session_title != current_session:
                current_session = session_title
                doc.add_heading(session_title, level=1)
            
            if format_style == "interview":
                q_para = doc.add_paragraph()
                q_run = q_para.add_run(story.get('question', ''))
                q_run.font.bold = True
                q_run.font.italic = True
            
            # Answer
            answer_text = story.get('answer_text', '')
            if answer_text:
                paragraphs = answer_text.split('\n')
                for para in paragraphs:
                    if para.strip():
                        doc.add_paragraph(para.strip())
            
            # Images
            if include_images and story.get('images'):
                for img in story.get('images', []):
                    if img.get('base64'):
                        try:
                            img_data = base64.b64decode(img['base64'])
                            img_stream = io.BytesIO(img_data)
                            doc.add_picture(img_stream, width=Inches(4))
                            last_paragraph = doc.paragraphs[-1]
                            last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            
                            if img.get('caption'):
                                caption = doc.add_paragraph(img['caption'])
                                caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        except:
                            pass
            
            doc.add_paragraph()
        
        # Save to bytes
        docx_bytes = io.BytesIO()
        doc.save(docx_bytes)
        docx_bytes.seek(0)
        return docx_bytes.getvalue()
        
    except ImportError:
        st.error("Please install python-docx: pip install python-docx")
        return None
    except Exception as e:
        st.error(f"Error generating DOCX: {str(e)}")
        return None

def generate_html(title, author, stories, format_style="interview", include_toc=True, include_images=True, cover_image=None):
    """Generate an HTML document from stories"""
    
    # Cover image HTML if provided
    cover_html = ""
    if cover_image:
        try:
            img_base64 = base64.b64encode(cover_image).decode()
            cover_html = f'<img src="data:image/jpeg;base64,{img_base64}" style="max-width:100%; max-height:70vh; margin:20px auto; display:block; border-radius:10px; box-shadow:0 10px 30px rgba(0,0,0,0.2);">'
        except:
            pass
    
    # Start building HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Georgia', serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #fff;
        }}
        h1 {{
            font-size: 42px;
            text-align: center;
            margin-bottom: 10px;
            color: #000;
        }}
        h2 {{
            font-size: 28px;
            margin-top: 40px;
            margin-bottom: 20px;
            color: #444;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }}
        .author {{
            text-align: center;
            font-size: 18px;
            color: #666;
            margin-bottom: 40px;
            font-style: italic;
        }}
        .question {{
            font-weight: bold;
            font-size: 18px;
            margin-top: 30px;
            margin-bottom: 10px;
            color: #2c3e50;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }}
        .story-image {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 20px auto;
            border-radius: 5px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .image-caption {{
            text-align: center;
            font-size: 14px;
            color: #666;
            margin-top: -10px;
            margin-bottom: 20px;
            font-style: italic;
        }}
        .cover-page {{
            text-align: center;
            margin-bottom: 50px;
            page-break-after: always;
        }}
        .copyright {{
            text-align: center;
            font-size: 12px;
            color: #999;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }}
        .toc {{
            background: #f9f9f9;
            padding: 20px;
            border-radius: 5px;
            margin: 30px 0;
        }}
        .toc ul {{
            list-style-type: none;
            padding-left: 0;
        }}
        .toc li {{
            margin-bottom: 10px;
        }}
        .toc a {{
            color: #3498db;
            text-decoration: none;
        }}
        .toc a:hover {{
            text-decoration: underline;
        }}
        @media print {{
            body {{
                padding: 0.5in;
            }}
            .cover-page {{
                page-break-after: always;
            }}
        }}
    </style>
</head>
<body>
    <div class="cover-page">
        {cover_html}
        <h1>{title}</h1>
        <p class="author">by {author}</p>
    </div>
    
    <p class="copyright">© {datetime.now().year} {author}. All rights reserved.</p>
"""
    
    if include_toc:
        html += """
    <div class="toc">
        <h3>Table of Contents</h3>
        <ul>
"""
        # Group by session for TOC
        sessions = {}
        for story in stories:
            session_title = story.get('session_title', 'Untitled Session')
            if session_title not in sessions:
                sessions[session_title] = []
            sessions[session_title].append(story)
        
        for session_title in sessions.keys():
            anchor = session_title.lower().replace(' ', '-').replace('?', '').replace('!', '').replace(',', '')
            html += f'            <li><a href="#{anchor}">{session_title}</a></li>\n'
        
        html += """
        </ul>
    </div>
"""
    
    # Add stories
    current_session = None
    for story in stories:
        session_title = story.get('session_title', 'Untitled Session')
        anchor = session_title.lower().replace(' ', '-').replace('?', '').replace('!', '').replace(',', '')
        
        if session_title != current_session:
            current_session = session_title
            html += f'    <h2 id="{anchor}">{session_title}</h2>\n'
        
        if format_style == "interview":
            html += f'    <div class="question">{story.get("question", "")}</div>\n'
        
        # Answer text
        answer_text = story.get('answer_text', '')
        if answer_text:
            paragraphs = answer_text.split('\n')
            for para in paragraphs:
                if para.strip():
                    escaped_para = para.strip().replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    html += f'    <p>{escaped_para}</p>\n'
        
        # Images
        if include_images and story.get('images'):
            for img in story.get('images', []):
                if img.get('base64'):
                    html += f'    <img src="data:image/jpeg;base64,{img["base64"]}" class="story-image">\n'
                    if img.get('caption'):
                        caption = img['caption'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        html += f'    <p class="image-caption">{caption}</p>\n'
        
        html += '    <hr style="margin: 30px 0; border: none; border-top: 1px dashed #ccc;">\n'
    
    html += """
</body>
</html>"""
    
    return html

def generate_zip(title, author, stories, format_style="interview", include_toc=True, include_images=True, cover_image=None):
    """Generate a ZIP package with HTML and images"""
    
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Generate HTML
        html_content = generate_html(
            title, author, stories, format_style, include_toc, include_images, cover_image
        )
        
        # Save HTML
        html_filename = f"{title.replace(' ', '_')}.html"
        zip_file.writestr(html_filename, html_content)
        
        # Add images to images folder
        if include_images:
            for i, story in enumerate(stories):
                for j, img in enumerate(story.get('images', [])):
                    if img.get('base64'):
                        try:
                            img_data = base64.b64decode(img['base64'])
                            img_filename = f"images/image_{i}_{j}.jpg"
                            zip_file.writestr(img_filename, img_data)
                        except:
                            pass
    
    return zip_buffer.getvalue()

# ============================================================================
# MAIN PUBLISHER INTERFACE
# ============================================================================
def main():
    st.markdown('<div class="main-header"><h1>📚 Tell My Story - Book Publisher</h1><p>Transform your stories into a beautiful book</p></div>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'stories' not in st.session_state:
        st.session_state.stories = []
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'user_info' not in st.session_state:
        st.session_state.user_info = {}
    
    # Try to load from main app automatically
    if not st.session_state.data_loaded:
        main_app_data = load_from_main_app()
        if main_app_data.get('success'):
            st.session_state.stories = main_app_data['stories']
            st.session_state.user_info = main_app_data.get('user_info', {})
            st.session_state.data_loaded = True
            st.session_state.data_source = "main_app"
    
    # Data source selection
    st.markdown("## 📥 Load Your Stories")
    
    tab1, tab2, tab3 = st.tabs(["📤 Upload JSON", "📝 Use Sample Data", "📊 Current Stats"])
    
    with tab1:
        st.markdown("Upload a JSON backup file from Tell My Story")
        uploaded_file = st.file_uploader("Choose JSON file", type=['json'])
        
        if uploaded_file:
            data = load_user_data_file(uploaded_file)
            if data and 'stories' in data:
                st.session_state.stories = data['stories']
                st.session_state.user_info = data.get('user_info', {})
                st.session_state.data_loaded = True
                st.session_state.data_source = "upload"
                st.success(f"Loaded {len(data['stories'])} stories!")
                st.rerun()
    
    with tab2:
        if st.button("📝 Load Sample Stories", type="primary"):
            st.session_state.stories = SAMPLE_STORIES
            st.session_state.user_info = {
                "first_name": "John",
                "last_name": "Doe"
            }
            st.session_state.data_loaded = True
            st.session_state.data_source = "sample"
            st.success("Sample stories loaded!")
            st.rerun()
    
    with tab3:
        if st.session_state.data_loaded:
            st.markdown(f"""
            <div class="stats-box">
                <h3>📊 Current Data</h3>
                <p>Source: {st.session_state.get('data_source', 'unknown')}</p>
                <p>Total Stories: {len(st.session_state.stories)}</p>
                <p>Sessions: {len(set(s['session_title'] for s in st.session_state.stories))}</p>
                <p>Total Words: {sum(len(s['answer_text'].split()) for s in st.session_state.stories):,}</p>
                <p>Images: {sum(s.get('image_count', 0) for s in st.session_state.stories)}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No data loaded yet. Upload a file or load sample data.")
    
    # Publishing section (only show if data is loaded)
    if st.session_state.data_loaded and st.session_state.stories:
        st.markdown("---")
        st.markdown("## 🎨 Design Your Book")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Get default name from user_info
            first_name = st.session_state.user_info.get('first_name', 'My')
            last_name = st.session_state.user_info.get('last_name', '')
            
            book_title = st.text_input(
                "Book Title",
                value=f"{first_name}'s Life Story",
                key="pub_book_title"
            )
            
            author_name = st.text_input(
                "Author Name",
                value=f"{first_name} {last_name}".strip() or "Author Name",
                key="pub_author_name"
            )
            
            format_style = st.selectbox(
                "Format Style",
                ["interview", "biography", "memoir"],
                format_func=lambda x: {
                    "interview": "📝 Interview Q&A (Questions shown)",
                    "biography": "📖 Continuous Biography (No questions)",
                    "memoir": "📚 Chapter-based Memoir"
                }[x],
                key="pub_format"
            )
        
        with col2:
            st.markdown("### Cover Options")
            cover_choice = st.radio(
                "Cover Type",
                ["simple", "uploaded"],
                format_func=lambda x: "🎨 Simple Cover" if x == "simple" else "📸 Upload Cover Image",
                key="pub_cover_type"
            )
            
            cover_image = None
            if cover_choice == "uploaded":
                uploaded_cover = st.file_uploader(
                    "Upload Cover Image",
                    type=['jpg', 'jpeg', 'png'],
                    key="pub_cover_upload"
                )
                if uploaded_cover:
                    cover_image = uploaded_cover.getvalue()
                    st.image(cover_image, caption="Cover Preview", width=200)
            
            include_toc = st.checkbox("Include Table of Contents", value=True, key="pub_toc")
            include_images = st.checkbox("Include Images", value=True, key="pub_images")
        
        # Preview section
        st.markdown("---")
        st.markdown("## 📖 Preview")
        
        with st.expander("Show Story Preview", expanded=False):
            for i, story in enumerate(st.session_state.stories[:3]):  # Show first 3
                st.markdown(f"""
                <div class="story-card">
                    <div class="question">{story['question']}</div>
                    <p>{story['answer_text'][:200]}...</p>
                    <small>Session: {story['session_title']}</small>
                </div>
                """, unsafe_allow_html=True)
            
            if len(st.session_state.stories) > 3:
                st.info(f"... and {len(st.session_state.stories) - 3} more stories")
        
        # Generate buttons
        st.markdown("---")
        st.markdown("## 📥 Generate Your Book")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Generate DOCX", type="primary", use_container_width=True):
                with st.spinner("Creating Word document..."):
                    docx_bytes = generate_docx(
                        book_title, author_name, st.session_state.stories,
                        format_style, include_toc, include_images, cover_image
                    )
                    
                    if docx_bytes:
                        filename = f"{book_title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.docx"
                        
                        st.download_button(
                            label="📥 Download DOCX",
                            data=docx_bytes,
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True,
                            key="docx_download"
                        )
                        
                        st.markdown('<div class="success-message">✅ DOCX generated successfully!</div>', unsafe_allow_html=True)
                        st.balloons()
        
        with col2:
            if st.button("🌐 Generate HTML", type="primary", use_container_width=True):
                with st.spinner("Creating HTML page..."):
                    html_content = generate_html(
                        book_title, author_name, st.session_state.stories,
                        format_style, include_toc, include_images, cover_image
                    )
                    
                    filename = f"{book_title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.html"
                    
                    st.download_button(
                        label="📥 Download HTML",
                        data=html_content,
                        file_name=filename,
                        mime="text/html",
                        use_container_width=True,
                        key="html_download"
                    )
                    
                    st.markdown('<div class="success-message">✅ HTML generated successfully!</div>', unsafe_allow_html=True)
                    st.balloons()
        
        with col3:
            if st.button("📦 Generate ZIP", type="primary", use_container_width=True):
                with st.spinner("Creating ZIP package..."):
                    zip_data = generate_zip(
                        book_title, author_name, st.session_state.stories,
                        format_style, include_toc, include_images, cover_image
                    )
                    
                    filename = f"{book_title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.zip"
                    
                    st.download_button(
                        label="📥 Download ZIP",
                        data=zip_data,
                        file_name=filename,
                        mime="application/zip",
                        use_container_width=True,
                        key="zip_download"
                    )
                    
                    st.markdown('<div class="success-message">✅ ZIP package generated successfully!</div>', unsafe_allow_html=True)
                    st.balloons()
        
        # Statistics
        st.markdown("---")
        st.markdown("## 📊 Book Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Stories", len(st.session_state.stories))
        
        with col2:
            total_words = sum(len(story['answer_text'].split()) for story in st.session_state.stories)
            st.metric("Total Words", f"{total_words:,}")
        
        with col3:
            sessions_count = len(set(story['session_title'] for story in st.session_state.stories))
            st.metric("Sessions", sessions_count)
        
        with col4:
            images_count = sum(story.get('image_count', 0) for story in st.session_state.stories)
            st.metric("Images", images_count)
    
    else:
        # Show welcome message when no data
        st.markdown("""
        <div style="text-align:center; padding:50px; background:#f8f9fa; border-radius:10px;">
            <h2>✨ Welcome to the Book Publisher</h2>
            <p>Upload your Tell My Story JSON backup or load sample data to get started.</p>
            <p>Your stories will be transformed into a beautiful, professionally formatted book.</p>
        </div>
        """, unsafe_allow_html=True)

# ============================================================================
# RUN THE APP
# ============================================================================
if __name__ == "__main__":
    main()

