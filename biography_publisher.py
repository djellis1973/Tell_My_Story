import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Test Publisher", page_icon="📚")

st.title("TEST PUBLISHER")

book_title = st.text_input("Book Title", "My Story")
author_name = st.text_input("Author", "Me")

if st.button("Generate TEST HTML"):
    # Simple test HTML
    html = f"""<!DOCTYPE html>
<html>
<head><title>{book_title}</title></head>
<body>
    <h1 style="color:blue; text-align:center;">{book_title}</h1>
    <h2 style="text-align:center;">by {author_name}</h2>
    <p style="text-align:center;">This is a test page</p>
    <hr>
    <p>Generated at: {datetime.now()}</p>
</body>
</html>"""
    
    st.download_button(
        "Download HTML",
        data=html,
        file_name="test.html",
        mime="text/html"
    )
    
    st.success("HTML generated!")
