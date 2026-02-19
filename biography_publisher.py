# Generate buttons
st.markdown("---")
st.markdown("### 🖨️ Generate Your Book")

# Create tabs for different export formats
tab1, tab2, tab3, tab4 = st.tabs(["📊 DOCX", "🌐 HTML", "📱 EPUB", "📄 PDF/RTF"])

with tab1:
    st.markdown("**Microsoft Word Document**")
    if st.button("Generate DOCX", type="primary", use_container_width=True):
        with st.spinner("Creating Word document..."):
            cover_image = st.session_state.cover_image_data if cover_choice == "uploaded" else None
            
            docx_bytes = generate_docx(
                book_title,
                book_author,
                stories,
                format_style,
                include_toc,
                True,
                cover_image,
                cover_choice
            )
            filename = f"{book_title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.docx"
            st.download_button(
                "📥 Download DOCX", 
                data=docx_bytes, 
                file_name=filename, 
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
                use_container_width=True,
                key="docx_download"
            )
            show_celebration()

with tab2:
    st.markdown("**Web Page (HTML)**")
    if st.button("Generate HTML", type="primary", use_container_width=True):
        with st.spinner("Creating HTML page..."):
            cover_image = st.session_state.cover_image_data if cover_choice == "uploaded" else None
            
            html_content = generate_html(
                book_title,
                book_author,
                stories,
                format_style,
                include_toc,
                True,
                cover_image,
                cover_choice
            )
            filename = f"{book_title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.html"
            st.download_button(
                "📥 Download HTML", 
                data=html_content, 
                file_name=filename, 
                mime="text/html", 
                use_container_width=True,
                key="html_download"
            )
            show_celebration()

with tab3:
    st.markdown("**eBook (EPUB)**")
    st.info("⚠️ EPUB generation requires **Pandoc** to be installed on your system.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Generate EPUB", type="primary", use_container_width=True):
            with st.spinner("Creating EPUB file... (may take a moment)"):
                cover_image = st.session_state.cover_image_data if cover_choice == "uploaded" else None
                
                epub_bytes, error = generate_epub(
                    book_title,
                    book_author,
                    stories,
                    format_style,
                    include_toc,
                    True,
                    cover_image,
                    cover_choice
                )
                
                if epub_bytes:
                    filename = f"{book_title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.epub"
                    st.download_button(
                        "📥 Download EPUB", 
                        data=epub_bytes, 
                        file_name=filename, 
                        mime="application/epub+zip", 
                        use_container_width=True,
                        key="epub_download"
                    )
                    show_celebration()
                else:
                    st.error(f"Failed to generate EPUB: {error}")
    
    with col2:
        st.markdown("**Install Pandoc:**")
        st.markdown("""
        - **Windows:** Download from [pandoc.org](https://pandoc.org/installing.html)
        - **Mac:** `brew install pandoc`
        - **Linux:** `sudo apt-get install pandoc`
        """)

with tab4:
    st.markdown("**PDF Document**")
    st.info("⚠️ PDF generation requires **WeasyPrint** (`pip install weasyprint`) or **Pandoc**")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Generate PDF", type="primary", use_container_width=True):
            with st.spinner("Creating PDF file... (may take a moment)"):
                cover_image = st.session_state.cover_image_data if cover_choice == "uploaded" else None
                
                pdf_bytes, error = generate_pdf(
                    book_title,
                    book_author,
                    stories,
                    format_style,
                    include_toc,
                    True,
                    cover_image,
                    cover_choice
                )
                
                if pdf_bytes:
                    filename = f"{book_title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
                    st.download_button(
                        "📥 Download PDF", 
                        data=pdf_bytes, 
                        file_name=filename, 
                        mime="application/pdf", 
                        use_container_width=True,
                        key="pdf_download"
                    )
                    show_celebration()
                else:
                    st.error(f"Failed to generate PDF: {error}")
    
    with col2:
        st.markdown("**Rich Text Format (RTF)**")
        if st.button("Generate RTF", use_container_width=True):
            with st.spinner("Creating RTF file..."):
                cover_image = st.session_state.cover_image_data if cover_choice == "uploaded" else None
                
                rtf_bytes = generate_rtf(
                    book_title,
                    book_author,
                    stories,
                    format_style,
                    include_toc,
                    True,
                    cover_image,
                    cover_choice
                )
                
                filename = f"{book_title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.rtf"
                st.download_button(
                    "📥 Download RTF", 
                    data=rtf_bytes, 
                    file_name=filename, 
                    mime="application/rtf", 
                    use_container_width=True,
                    key="rtf_download"
                )
                show_celebration()
