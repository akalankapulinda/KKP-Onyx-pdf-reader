def __init__(self):
        super().__init__()
        self.setWindowTitle("Pro PDF Reader")
        self.resize(1200, 800)

        # 1. Initialize our backend classes
        self.engine = PDFEngine()
        self.processor = ImageProcessor()
        self.current_raw_image = None
        self.is_dark_mode = False
        
        # --- NEW CODE: Pagination State ---
        self.current_page = 0
        self.total_pages = 0
        # ----------------------------------

        # 2. Setup the User Interface
        self.setup_ui()

        # 3. Load our test PDF automatically for now
        if self.engine.load_pdf("sample.pdf"):
            self.total_pages = self.engine.get_page_count() # Get total pages
            self.load_page(self.current_page)