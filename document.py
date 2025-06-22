import os
import tempfile
import fitz  # PyMuPDF
import docx
from langchain.text_splitter import RecursiveCharacterTextSplitter

class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    
    def process_file(self, uploaded_file):
        """Process uploaded file and extract text content."""
        file_name = uploaded_file.name
        file_extension = os.path.splitext(file_name)[1].lower()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        try:
            if file_extension == '.pdf':
                text = self._extract_pdf_text(tmp_path)
            elif file_extension == '.docx':
                text = self._extract_docx_text(tmp_path)
            elif file_extension == '.txt':
                text = self._extract_txt_text(tmp_path)
            else:
                text = "Unsupported file format"
        finally:
            os.unlink(tmp_path)  # Clean up the temp file
        
        return text
    
    def _extract_pdf_text(self, file_path):
        """Extract text from PDF file."""
        text = ""
        try:
            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text()
            doc.close()
        except Exception as e:
            text = f"Error extracting PDF text: {str(e)}"
        
        return text
    
    def _extract_docx_text(self, file_path):
        """Extract text from DOCX file."""
        text = ""
        try:
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            text = f"Error extracting DOCX text: {str(e)}"
        
        return text
    
    def _extract_txt_text(self, file_path):
        """Extract text from TXT file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
        except Exception as e:
            text = f"Error extracting TXT text: {str(e)}"
        
        return text
    
    def chunk_text(self, text):
        """Split text into manageable chunks."""
        chunks = self.text_splitter.split_text(text)
        return chunks
    
    def summarize_text(self, text, max_length=1000):
        """Create a summary of text if it's too long."""
        if len(text) <= max_length:
            return text
        
        # Simple summarization - return first part of text
        # In a real implementation, you could use an LLM to summarize
        return text[:max_length] + "... [text truncated]"