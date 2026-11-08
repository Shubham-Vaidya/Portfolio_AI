
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader
from docx import Document


def extract_text(file_bytes, filename):

    extension = Path(filename).suffix.lower()

    # Extract PDF
    if extension == ".pdf":

        reader = PdfReader(BytesIO(file_bytes))

        text = "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

    # Extract DOCX
    elif extension == ".docx":

        document = Document(BytesIO(file_bytes))

        paragraphs = [
            paragraph.text
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]

        # Also extract table content
        for table in document.tables:
            for row in table.rows:
                paragraphs.append(
                    " | ".join(cell.text for cell in row.cells)
                )

        text = "\n".join(paragraphs)

    # Extract TXT
    elif extension == ".txt":

        try:
            text = file_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = file_bytes.decode("latin-1")

    else:
        raise ValueError(
            "Unsupported file format. Upload PDF, DOCX, or TXT."
        )

    text = text.strip()

    if not text:
        raise ValueError(
            "No readable text found in the uploaded document."
        )

    return text


def chunk_text(text, chunk_size=1000, overlap=150):

    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("Invalid chunk size or overlap.")

    chunks = []

    start = 0

    while start < len(text):

        end = min(start + chunk_size, len(text))

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start = end - overlap

    return chunks
