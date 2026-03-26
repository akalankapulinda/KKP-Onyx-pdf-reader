import fitz  # PyMuPDF
from PIL import Image

class PDFEngine:
    def __init__(self):
        self.doc = None

    def load_pdf(self, file_path: str) -> bool:
        """Loads a PDF document from the given file path."""
        try:
            self.doc = fitz.open(file_path)
            print(f"Successfully loaded: {file_path}")
            return True
        except Exception as e:
            print(f"Error loading PDF: {e}")
            self.doc = None
            return False

    def get_page_count(self) -> int:
        """Returns the total number of pages in the document."""
        return len(self.doc) if self.doc else 0

    def get_page_image(self, page_num: int, zoom: float = 2.0) -> Image.Image:
        """
        Renders a specific PDF page and returns it as a Pillow Image.
        The zoom factor increases the resolution (crucial for readability).
        """
        if not self.doc or page_num < 0 or page_num >= len(self.doc):
            return None

        # Load the specific page
        page = self.doc.load_page(page_num)
        
        # Apply a zoom matrix. Without this, the PDF will look blurry.
        # 2.0 means 200% resolution.
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        # Convert the PyMuPDF Pixmap into a standard Pillow Image
        mode = "RGBA" if pix.alpha else "RGB"
        img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
        
        return img
        