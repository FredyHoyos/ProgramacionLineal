import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from PyQt5.QtWidgets import QApplication
from gui.ventana_principal import VentanaPrincipal

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec_())
