import re
import matplotlib.pyplot as plt
import numpy as np
from core.graficador_lineal import GraficadorLineal
from core.conversorSimplex import ConversorSimplex, SimplexTabular, VentanaSimplexPaso
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QTextEdit,
    QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox, QRadioButton,
    QMessageBox
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
        self.graficar_btn.clicked.connect(self.graficar)
        self.resolver_btn.clicked.connect(self.resolver)

        # Agregar todos los grupos al layout principal
        layout.addLayout(funcion_layout)
        layout.addLayout(restricciones_layout)
        layout.addLayout(tipo_layout)
        layout.addWidget(self.paso_a_paso_checkbox)
        layout.addLayout(botones_layout)

        self.setLayout(layout)

    def mostrar_error(self, mensaje):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Error de entrada")
        msg.setInformativeText(mensaje)
        msg.setWindowTitle("Entrada inválida")
        msg.exec_()

    def graficar(self):
        try:
            funcion_str = self.funcion_input.text()
            restricciones_texto = self.restricciones_input.toPlainText().split('\n')
            es_max = self.max_radio.isChecked()

            if not funcion_str.strip():
                self.mostrar_error("Debe ingresar una función objetivo.")
                return

            if not any(op in r for r in restricciones_texto for op in ['<=', '≥', '>=']):
                self.mostrar_error("Debe ingresar restricciones válidas.")
                return

            graficador = GraficadorLineal(funcion_str, restricciones_texto, es_max)
            graficador.graficar()

        except Exception as e:
            self.mostrar_error(f"Ocurrió un error al graficar: {str(e)}")

    def resolver(self):
        try:
            funcion_str = self.funcion_input.text()
            restricciones_texto = self.restricciones_input.toPlainText().split('\n')
            tipo = 'max' if self.max_radio.isChecked() else 'min'

            resultado = ConversorSimplex.estandarizar_problema(funcion_str, restricciones_texto, tipo)
            simplex = SimplexTabular(resultado['tabla'], resultado['rhs'], resultado['z'])

            while simplex.siguiente_paso():
                pass

            if self.paso_a_paso_checkbox.isChecked():
                self.ventana_pasos = VentanaSimplexPaso(simplex.obtener_historial())
                self.ventana_pasos.show()
            else:
                resumen = simplex.obtener_resumen_final()
                msg = QMessageBox()
                msg.setWindowTitle("Resultado final")
                msg.setText("\n".join(resumen))
                msg.exec_()

        except Exception as e:
            self.mostrar_error(f"Error al resolver: {str(e)}")