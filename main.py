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

"""


Ejemplo con gran M

Función objetivo:
0.4x + 0.5y 

Restricciones:
0.3x + 0.1y <= 2.7
0.5x + 0.5y = 6
0.6x + 0.4y >= 6
x, y >= 0


"""