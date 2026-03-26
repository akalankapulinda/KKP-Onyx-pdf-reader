import io
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QSlider, QGraphicsView, QGraphicsScene, 
                             QGraphicsPixmapItem, QLabel, QFileDialog, QLineEdit)
from PyQt6.QtGui import QPixmap, QShortcut, QKeySequence, QBrush, QColor, QIcon 
# Import our backend layers
from engine.pdf_document import PDFEngine
from logic.image_processor import ImageProcessor
from PyQt6.QtCore import Qt, QTimer

class PDFGraphicsView(QGraphicsView):
    def __init__(self, scene, main_window): # <-- Added main_window reference
        super().__init__(scene)
        self.main_window = main_window 
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    def wheelEvent(self, event):
        """Handle mouse wheel zooming and Smart Scrolling."""
        # 1. Handle Zooming (CTRL + Wheel)
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self.scale(1.15, 1.15)
            else:
                self.scale(0.85, 0.85)
                
        # 2. Handle Smart Scrolling (Just the Wheel)
        else:
            scrollbar = self.verticalScrollBar()
            scroll_dir = event.angleDelta().y()

            # If scrolling DOWN and we are at the absolute bottom of the page
            if scroll_dir < 0 and scrollbar.value() == scrollbar.maximum():
                self.main_window.next_page()
                return # Stop normal scrolling

            # If scrolling UP and we are at the absolute top of the page
            elif scroll_dir > 0 and scrollbar.value() == scrollbar.minimum():
                self.main_window.prev_page()
                # Jump to the bottom of the previous page so it feels natural
                scrollbar.setValue(scrollbar.maximum()) 
                return

            # Otherwise, just scroll normally!
            super().wheelEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # --- UPDATED: Identity & Branding ---
        self.setWindowTitle("KKP Onyx PDF Reader")
        self.resize(1200, 800)
        
        # Set the icon for the taskbar and window corner
        # (Assumes logo.png is saved inside the ui/ folder)
        self.setWindowIcon(QIcon("ui/logo.png")) 
        # -------------------------------------
        # 1. Initialize our backend classes
        self.engine = PDFEngine()
        self.processor = ImageProcessor()
        self.current_raw_image = None
        self.is_dark_mode = False
        self.current_rotation = 0
        self.is_double_page = False
        
        # Pagination State
        self.current_page = 0
        self.total_pages = 0

        # 2. Setup the User Interface
        self.setup_ui()

        # --- NEW CODE: Performance Timer ---
        self.render_timer = QTimer()
        self.render_timer.setSingleShot(True)
        self.render_timer.timeout.connect(self.update_display)

        
    def setup_ui(self):
        # Create the central widget and main VERTICAL layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Remove the invisible borders around the edge of the app
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ==========================================
        # --- THE TOP TOOLBAR ---
        # ==========================================
        toolbar = QWidget()
        # Give it a dark background with some padding to look professional
        toolbar.setStyleSheet("""
            QWidget { background-color: #2b2b2b; color: white; font-size: 13px; }
            QPushButton { background-color: #3e3e42; border: 1px solid #555; border-radius: 4px; padding: 5px 10px; }
            QPushButton:hover { background-color: #505050; }
            QLineEdit { background-color: #1e1e1e; border: 1px solid #555; border-radius: 4px; color: white; }
        """)
        
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(15, 10, 15, 10)

        # --- NEW CODE: APP BRANDING (Inserted at the start) ---
        # 1. Add the Logo
        lbl_logo = QLabel()
        logo_pixmap = QPixmap("ui/logo.png")
        # Professionally scale the line art to 30px high to fit the toolbar perfectly
        scaled_logo = logo_pixmap.scaledToHeight(30, Qt.TransformationMode.SmoothTransformation)
        lbl_logo.setPixmap(scaled_logo)
        toolbar_layout.addWidget(lbl_logo)
        
        # 2. Add the Name "KKP Onyx"
        lbl_app_name = QLabel("KKP Onyx")
        lbl_app_name.setStyleSheet("font-weight: bold; font-size: 16px; color: #ffffff; padding-right: 15px;")
        toolbar_layout.addWidget(lbl_app_name)
        
        # A small visual vertical separator
        lbl_sep = QLabel("|")
        lbl_sep.setStyleSheet("color: #555; padding-right: 15px;")
        toolbar_layout.addWidget(lbl_sep)
        # -------------------------------------------------------

        # 1. Open Button
        self.btn_open = QPushButton("🗁 Open")
        self.btn_open.clicked.connect(self.open_file)
        toolbar_layout.addWidget(self.btn_open)

        toolbar_layout.addSpacing(20) # Add a visual gap

        # 2. Pagination Controls
        self.btn_prev = QPushButton("<")
        self.btn_next = QPushButton(">")
        self.btn_prev.clicked.connect(self.prev_page)
        self.btn_next.clicked.connect(self.next_page)

        self.input_page = QLineEdit()
        self.input_page.setFixedWidth(40)
        self.input_page.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_page.returnPressed.connect(self.jump_to_page)
        self.lbl_total_pages = QLabel("of 0")

        toolbar_layout.addWidget(self.btn_prev)
        toolbar_layout.addWidget(self.input_page)
        toolbar_layout.addWidget(self.lbl_total_pages)
        toolbar_layout.addWidget(self.btn_next)

        toolbar_layout.addSpacing(20)

        # 3. Zoom Controls
        self.btn_zoom_out = QPushButton("−")
        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_out.clicked.connect(self.zoom_out)
        self.btn_zoom_in.clicked.connect(self.zoom_in)
        toolbar_layout.addWidget(QLabel("Zoom:"))
        toolbar_layout.addWidget(self.btn_zoom_out)
        toolbar_layout.addWidget(self.btn_zoom_in)

        toolbar_layout.addSpacing(20)

        # 4. View & Rotate Controls
        self.btn_rotate = QPushButton("⟳ Rotate")
        self.btn_view_mode = QPushButton("🕮 Page View")
        self.btn_rotate.clicked.connect(self.rotate_right)
        self.btn_view_mode.clicked.connect(self.toggle_view_mode)
        toolbar_layout.addWidget(self.btn_rotate)
        toolbar_layout.addWidget(self.btn_view_mode)

        # 5. Push all remaining items all the way to the Right side
        toolbar_layout.addStretch()

        # 6. Dark Mode & Brightness (Aligned to the right)
        toolbar_layout.addWidget(QLabel("Brightness:"))
        self.slider_brightness = QSlider(Qt.Orientation.Horizontal)
        self.slider_brightness.setFixedWidth(100) # Keep slider compact
        self.slider_brightness.setMinimum(50)
        self.slider_brightness.setMaximum(150)
        self.slider_brightness.setValue(100)
        self.slider_brightness.valueChanged.connect(self.on_slider_drag)
        toolbar_layout.addWidget(self.slider_brightness)

        toolbar_layout.addSpacing(10)

        self.btn_dark_mode = QPushButton("⎚-⎚ Dark Mode")
        self.btn_dark_mode.clicked.connect(self.toggle_dark_mode)
        toolbar_layout.addWidget(self.btn_dark_mode)

        # Finally, add the finished toolbar to the very top of the app
        main_layout.addWidget(toolbar)

        # ==========================================
        # --- THE PDF VIEWER (Bottom) ---
        # ==========================================
        self.scene = QGraphicsScene()
        self.view = PDFGraphicsView(self.scene, self) # <-- Added 'self'
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)
        
        # Make the background behind the PDF dark gray to match the pro look
        from PyQt6.QtGui import QBrush, QColor
        self.view.setBackgroundBrush(QBrush(QColor("#1e1e1e")))

        # Add viewer to the layout so it fills the rest of the screen
        main_layout.addWidget(self.view)

        # Global Keyboard Shortcuts (Keep your existing shortcuts here)
        self.shortcut_right = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        self.shortcut_right.activated.connect(self.next_page)
        
        self.shortcut_space = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        self.shortcut_space.activated.connect(self.next_page)

        self.shortcut_left = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        self.shortcut_left.activated.connect(self.prev_page)

        self.shortcut_up = QShortcut(QKeySequence(Qt.Key.Key_Up), self)
        self.shortcut_up.activated.connect(self.scroll_up)
        
        self.shortcut_down = QShortcut(QKeySequence(Qt.Key.Key_Down), self)
        self.shortcut_down.activated.connect(self.scroll_down)
    def update_page_label(self):
        """Updates the text box and the 'of Y' label."""
        # Note: We add 1 because humans start counting at Page 1, but Python starts at Page 0!
        self.input_page.setText(str(self.current_page + 1))
        self.lbl_total_pages.setText(f"of {self.total_pages}")

    def jump_to_page(self):
        """Triggered when the user types a number and hits Enter."""
        try:
            # Get the text, convert to integer, and subtract 1 (Python uses 0-based indexing)
            target_page = int(self.input_page.text()) - 1
            
            # Check if the page actually exists!
            if 0 <= target_page < self.total_pages:
                self.current_page = target_page
                self.load_page(self.current_page)
            else:
                # If they typed a fake page (like 9999), reset the text box to the real current page
                self.update_page_label()
        except ValueError:
            # If they typed letters instead of numbers, ignore it and reset
            self.update_page_label()

    def zoom_in(self):
        """Zooms the viewer in by 15%."""
        self.view.scale(1.15, 1.15)

    def zoom_out(self):
        """Zooms the viewer out by 15%."""
        self.view.scale(0.85, 0.85)

    def next_page(self):
        """Goes to the next page (or next two pages)."""
        step = 2 if self.is_double_page else 1
        if self.current_page + step < self.total_pages:
            self.current_page += step
            self.load_page(self.current_page)

    def prev_page(self):
        """Goes to the previous page (or previous two pages)."""
        step = 2 if self.is_double_page else 1
        if self.current_page - step >= 0:
            self.current_page -= step
            self.load_page(self.current_page)
        elif self.current_page > 0: # Catch-all to get back to page 0
            self.current_page = 0
            self.load_page(self.current_page)

    def load_page(self, page_num):
        """Fetches images from the engine and stitches if necessary."""
        img1 = self.engine.get_page_image(page_num)
        
        # If double page mode is on, and there is a next page available
        if self.is_double_page and page_num + 1 < self.total_pages:
            img2 = self.engine.get_page_image(page_num + 1)
            # Ask the logic layer to glue them together!
            self.current_raw_image = self.processor.stitch_images(img1, img2)
            self.input_page.setText(f"{page_num + 1}-{page_num + 2}") # Show "1-2"
        else:
            self.current_raw_image = img1
            self.input_page.setText(str(page_num + 1))
            
        self.lbl_total_pages.setText(f"of {self.total_pages}")
        self.update_display()

        self.view.verticalScrollBar().setValue(0)
        self.view.horizontalScrollBar().setValue(0)

    def toggle_dark_mode(self):
        """Flips the dark mode state and updates the screen."""
        self.is_dark_mode = not self.is_dark_mode
        self.update_display()

    def update_display(self):
        """Applies filters and updates the QGraphicsView."""
        if not self.current_raw_image:
            return

        brightness_val = self.slider_brightness.value() / 100.0

        processed_img = self.processor.apply_filters(
            image=self.current_raw_image, 
            brightness=brightness_val, 
            dark_mode=self.is_dark_mode
        )

        # Safely convert the PIL Image to a QPixmap using a byte buffer
        byte_stream = io.BytesIO()
        processed_img.save(byte_stream, format="PNG") 
        
        pixmap = QPixmap()
        pixmap.loadFromData(byte_stream.getvalue())

        self.pixmap_item.setPixmap(pixmap)
        self.apply_rotation()

    def open_file(self):
        """Opens a native file dialog to select a new PDF."""
        # 1. Open the file explorer (filters to only show .pdf files)
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Open PDF File", 
            "", 
            "PDF Files (*.pdf);;All Files (*)"
        )
        
        # 2. If the user picked a file (and didn't hit cancel)
        if file_path:
            # 3. Tell the engine to load this new file
            if self.engine.load_pdf(file_path):
                # 4. Reset the page count and jump to page 1
                self.total_pages = self.engine.get_page_count()
                self.current_page = 0
                self.load_page(self.current_page)

    def on_slider_drag(self):
        """
        Triggered every time the slider moves. 
        Instead of rendering immediately, we restart a 150ms countdown timer.
        If the user keeps dragging, the timer keeps resetting. 
        It only renders when they stop!
        """
        self.render_timer.start(150) # Wait 150 milliseconds

    def keyPressEvent(self, event):
        """Listens for keyboard presses anywhere in the app."""
        if event.key() == Qt.Key.Key_Right:
            self.next_page()
        elif event.key() == Qt.Key.Key_Left:
            self.prev_page()

    def scroll_up(self):
        """Smoothly scrolls the PDF up by 75 pixels."""
        scrollbar = self.view.verticalScrollBar()
        scrollbar.setValue(scrollbar.value() - 75)

    def scroll_down(self):
        """Smoothly scrolls the PDF down by 75 pixels."""
        scrollbar = self.view.verticalScrollBar()
        scrollbar.setValue(scrollbar.value() + 75)

    def rotate_left(self):
        """Rotates the page 90 degrees counter-clockwise."""
        self.current_rotation = (self.current_rotation - 90) % 360
        self.apply_rotation()

    def rotate_right(self):
        """Rotates the page 90 degrees clockwise."""
        self.current_rotation = (self.current_rotation + 90) % 360
        self.apply_rotation()

    def apply_rotation(self):
        """Applies the current rotation angle to the image."""
        # 1. Set the anchor point for rotation to the exact center of the image
        center = self.pixmap_item.boundingRect().center()
        self.pixmap_item.setTransformOriginPoint(center)
        
        # 2. Spin the image
        self.pixmap_item.setRotation(self.current_rotation)
        
        # 3. Update the scene boundary so the scrollbars adapt to the new shape!
        self.scene.setSceneRect(self.pixmap_item.sceneBoundingRect())

    def toggle_view_mode(self):
        """Switches between Single and Double page views."""
        self.is_double_page = not self.is_double_page
        
        if self.is_double_page:
            self.btn_view_mode.setText("⿻ Double")
            # If we are on the last page, step back one so we can see two pages
            if self.current_page == self.total_pages - 1 and self.total_pages > 1:
                self.current_page -= 1
        else:
            self.btn_view_mode.setText("⬚ Single")
            
        self.load_page(self.current_page)