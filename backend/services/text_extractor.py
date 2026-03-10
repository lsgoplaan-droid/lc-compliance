import fitz  # PyMuPDF


class TextExtractor:
    def extract(self, file_path: str) -> str:
        doc = fitz.open(file_path)
        pages_text = []
        for page in doc:
            text = page.get_text("text")
            pages_text.append(text)
        doc.close()
        return "\n\n".join(pages_text)

    def extract_per_page(self, file_path: str) -> list[str]:
        doc = fitz.open(file_path)
        pages = [page.get_text("text") for page in doc]
        doc.close()
        return pages


text_extractor = TextExtractor()
