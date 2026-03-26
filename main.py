import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    # 1. Create the application instance
    app = QApplication(sys.argv)
    
    # 2. Create and show our main window
    window = MainWindow()
    window.show()
    
    # 3. Start the application event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()