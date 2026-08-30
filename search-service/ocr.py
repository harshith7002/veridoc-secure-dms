import io
from abc import ABC, abstractmethod


class OCRBackend(ABC):
    @abstractmethod
    def extract_text(self, image_bytes: bytes) -> str: ...


class TesseractBackend(OCRBackend):
    """Wraps the system `tesseract` binary via pytesseract. NOT exercised in this build - no
    tesseract binary was available in the environment this was written in (pytesseract shells
    out to it; there's nothing to mock the way moto mocks S3). The call itself is the standard,
    documented pytesseract usage - install tesseract-ocr (apt/brew/choco) and Pillow, then run
    it against a real scanned document before treating this as demo-ready."""

    def extract_text(self, image_bytes: bytes) -> str:
        import pytesseract
        from PIL import Image
        image = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(image)


class PlainTextPassthrough(OCRBackend):
    """For documents that are already text (typed FIRs, court filings submitted as .txt/.pdf
    with a text layer) - no OCR needed, just decode. This is the default and the one actually
    tested, since most of a case file in practice isn't a scanned image."""

    def extract_text(self, image_bytes: bytes) -> str:
        return image_bytes.decode("utf-8", errors="replace")


def get_ocr_backend() -> OCRBackend:
    import os
    backend = os.environ.get("OCR_BACKEND", "plaintext")
    if backend == "tesseract":
        return TesseractBackend()
    return PlainTextPassthrough()
