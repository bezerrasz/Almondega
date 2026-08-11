import sys
from PySide6.QtWidgets import QApplication

# Aqui nós importamos o Controller que você acabou de criar no Passo 2
from controller.dashboard_controller import DashboardController

def main():
    app = QApplication(sys.argv)
    
    window = DashboardController()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()