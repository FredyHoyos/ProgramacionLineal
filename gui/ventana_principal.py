from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QTextEdit,
    QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox, QRadioButton
)

class VentanaPrincipal(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Programación lineal")
        self.setGeometry(100, 100, 500, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Grupo: Funcion objetivo
        funcion_layout = QHBoxLayout()
        funcion_label = QLabel("Función:")
        self.funcion_input = QLineEdit()
        self.funcion_input.setText("3x + 5y") 
        funcion_layout.addWidget(funcion_label)
        funcion_layout.addWidget(self.funcion_input)

        # Grupo: Restricciones
        restricciones_layout = QHBoxLayout()
        restricciones_label = QLabel("Recursos:")
        self.restricciones_input = QTextEdit()
        self.restricciones_input.setPlainText("x <= 4\n2y <= 12\n3x + 2y <= 18\nx, y >= 0")
        restricciones_layout.addWidget(restricciones_label)
        restricciones_layout.addWidget(self.restricciones_input)

        # Grupo: Maximizar o Minimizar
        tipo_layout = QHBoxLayout()
        self.max_radio = QRadioButton("Maximizar")
        self.min_radio = QRadioButton("Minimizar")
        self.max_radio.setChecked(True)
        tipo_layout.addWidget(self.max_radio)
        tipo_layout.addWidget(self.min_radio)

        # Checkbox paso a paso
        self.paso_a_paso_checkbox = QCheckBox("Mostrar paso a paso")

        # Grupo: Botones
        botones_layout = QHBoxLayout()
        self.resolver_btn = QPushButton("Resolver")
        self.resolver_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.graficar_btn = QPushButton("Gráfica")
        self.graficar_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        botones_layout.addWidget(self.resolver_btn)
        botones_layout.addWidget(self.graficar_btn)

        # Agregar todos los grupos al layout principal
        layout.addLayout(funcion_layout)
        layout.addLayout(restricciones_layout)
        layout.addLayout(tipo_layout)
        layout.addWidget(self.paso_a_paso_checkbox)
        layout.addLayout(botones_layout)

        self.setLayout(layout)
