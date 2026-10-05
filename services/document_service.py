import os
import io

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import docx
except ImportError:
    docx = None

class DocumentService:
    def __init__(self):
        pass

    def extract_text(self, file_path, filename):
        ext = os.path.splitext(filename)[1].lower()
        if ext == '.txt':
            return self._extract_txt(file_path)
        elif ext == '.pdf':
            return self._extract_pdf(file_path)
        elif ext == '.docx':
            return self._extract_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _extract_txt(self, file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read().strip()

    def _extract_pdf(self, file_path):
        if not PyPDF2:
            raise ImportError("PyPDF2 is not installed.")
        text = []
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
        
        extracted = " ".join(text).strip()
        if not extracted:
            raise ValueError("Text could not be extracted from this document (may be a scanned image).")
        return extracted

    def _extract_docx(self, file_path):
        if not docx:
            raise ImportError("python-docx is not installed.")
        doc = docx.Document(file_path)
        text = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n".join(text).strip()
