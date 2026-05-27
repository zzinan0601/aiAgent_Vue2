from config import settings
from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_text(text: str) -> list:

    splitter = RecursiveCharacterTextSplitter(
        chunk_size    = settings.chunk_size,
        chunk_overlap = settings.chunk_overlap,
        separators    = ["\n\n", "\n", ".", " ", ""]
    )
    chunks = splitter.split_text(text)
    return [c.strip() for c in chunks if c.strip()]