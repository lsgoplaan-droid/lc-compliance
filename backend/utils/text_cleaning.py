import re


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def remove_ocr_artifacts(text: str) -> str:
    # Remove isolated single characters that are likely OCR noise
    text = re.sub(r"(?<!\w)[|}{~`](?!\w)", "", text)
    # Remove lines that are just dashes or underscores
    text = re.sub(r"^[-_=]{3,}$", "", text, flags=re.MULTILINE)
    return text


def clean_extracted_text(text: str) -> str:
    text = normalize_whitespace(text)
    text = remove_ocr_artifacts(text)
    return text
