import pymupdf

def read_pdf(path):
    pages = []
    with pymupdf.open(path) as document:
        for page_number, page in enumerate(document, start=1):
            pages.append({
                "page": page_number,
                "text": page.get_text(),
            })
    return pages

def read_pdf_bytes(pdf_bytes):
    pages = []

    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as document:
        for page_number, page in enumerate(document, start=1):
            pages.append({
                "page": page_number,
                "text": page.get_text(),
            })

    return pages

def split_into_chunks(pages, chunk_size=1000, overlap=150):
    chunks = []
    for page in pages:
        text = page["text"]
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({
                    "page": page["page"],
                    "text": chunk_text,
                })
            start += chunk_size - overlap
    return chunks