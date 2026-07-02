import os
from pypdf import PdfReader
from docx import Document

def load_file(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":   return _load_pdf(file_path)
    elif ext == ".docx": return _load_docx(file_path)
    elif ext in (".txt", ".md"):  return _load_txt(file_path)
    else: raise ValueError("지원하지 않는 파일 형식: " + ext)

def _load_pdf(path):
    reader = PdfReader(path)
    return "\n".join([p.extract_text() or "" for p in reader.pages])

def _load_docx(path):
    doc = Document(path)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def _load_txt(path):
    for enc in ["utf-8", "cp949", "euc-kr"]:
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise ValueError("파일 인코딩을 읽을 수 없습니다.")
