import sys
from PySide6.QtWidgets import QApplication
from controller.dashboard_controller import DashboardController

def main():
    app = QApplication(sys.argv)
    
    window = DashboardController()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()