import sys
import multiprocessing
from PyQt6.QtWidgets import QApplication
from ui.main_window import TelegramApp

if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    app = QApplication(sys.argv)
    win = TelegramApp()
    win.show()
    sys.exit(app.exec())