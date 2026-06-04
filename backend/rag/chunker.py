from config import settings
from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_text(text: str, chunk_size: int = None, chunk_overlap: int = None) -> list:
    if chunk_size is None:
        chunk_size = settings.chunk_size
    if chunk_overlap is None:
        chunk_overlap = settings.chunk_overlap

    splitter = RecursiveCharacterTextSplitter(
        chunk_size    = chunk_size,
        chunk_overlap = chunk_overlap,
        separators    = ["\n\n", "\n", ".", " ", ""]
    )
    chunks = splitter.split_text(text)
    return [c.strip() for c in chunks if c.strip()]