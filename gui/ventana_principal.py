import re

import matplotlib.pyplot as plt
import numpy as np

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QTextEdit,
    QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox, QRadioButton,
    QMessageBox, QDialog
)

from core.graficador_lineal import GraficadorLineal
from core.simplex import SimplexPasoAPaso
from core.simplexGranM import SimplexPasoAPasoGranM
from core.granM import MetodoGranM
from core.estandarizar import Estandarizador



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
        self.sensibilidad_btn = QPushButton("Análisis de sensibilidad")
        self.sensibilidad_btn.setStyleSheet("background-color: #FFC107; color: black; font-weight: bold;")
        botones_layout.addWidget(self.resolver_btn)
        botones_layout.addWidget(self.graficar_btn)
        botones_layout.addWidget(self.sensibilidad_btn)
        self.graficar_btn.clicked.connect(self.graficar)
        self.resolver_btn.clicked.connect(self.resolver)
        self.sensibilidad_btn.clicked.connect(self.analisis_sensibilidad)

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
        print(mensaje)
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

    def resolver(self, *args):
        try:
            funcion_str = self.funcion_input.text().strip()
            restricciones_texto = self.restricciones_input.toPlainText().strip().split('\n')
            es_maximizacion = self.max_radio.isChecked()

            if not funcion_str:
                self.mostrar_error("Debe ingresar una función objetivo.")
                return

            if not restricciones_texto:
                self.mostrar_error("Debe ingresar al menos una restricción.")
                return

            # --- Parsear función objetivo ---
            variables = sorted(set(re.findall(r'[a-zA-Z]\w*', funcion_str)))
            coef_obj = [0] * len(variables)

            for term in re.finditer(r'([+-]?\s*\d*\.?\d*)\s*([a-zA-Z]\w*)', funcion_str.replace(' ', '')):
                coef_str, var = term.groups()
                coef = float(coef_str) if coef_str.strip() not in ['', '+', '-'] else float(coef_str + '1')
                coef_obj[variables.index(var)] = coef

            # --- Parsear restricciones ---
            restricciones = []
            tipo_restricciones = []
            rhs = []

            for linea in restricciones_texto:
                if not linea.strip() or linea.strip().lower() in ['x >= 0', 'x, y >= 0']:
                    continue

                match = re.search(r'(<=|>=|=)', linea)
                if not match:
                    continue

                tipo = match.group(1)
                lhs, rhs_val = linea.split(tipo)
                rhs.append(float(rhs_val.strip()))
                tipo_restricciones.append(tipo)

                coef_fila = [0] * len(variables)
                for term in re.finditer(r'([+-]?\s*\d*\.?\d*)\s*([a-zA-Z]\w*)', lhs.replace(' ', '')):
                    coef_str, var = term.groups()
                    coef = float(coef_str) if coef_str.strip() not in ['', '+', '-'] else float(coef_str + '1')
                    coef_fila[variables.index(var)] = coef

                restricciones.append(coef_fila)

            # --- Llamar estandarizador ---
            est = Estandarizador(coef_obj, restricciones, tipo_restricciones, rhs, es_maximizacion)
            texto, resultado = est.convertir_a_estandar_texto()


            self.mostrar_resultado(texto)  # ✅ mostrar en ventana


            resultado = MetodoGranM(resultado).procesar()
            if self.paso_a_paso_checkbox.isChecked():
                if 'M' in resultado:
                    self.simplex_ventana_granM = SimplexPasoAPasoGranM(resultado.lower())  # `resultado` debe incluir los datos de la tabla
                    self.simplex_ventana_granM.exec_()
                else:
                    self.simplex_ventana = SimplexPasoAPaso(resultado.lower())  # `resultado` debe incluir los datos de la tabla
                    self.simplex_ventana.exec_()
            else:
                if 'M' in resultado:
                    ventana = SimplexPasoAPasoGranM(resultado.lower())
                    resultado_html = ventana.resolver_directo()
                else:
                    solucion_directa = SimplexPasoAPaso(resultado.lower())
                    resultado_html = solucion_directa.resolver_simplex()

                # Mostrar en ventana (para ambos casos)
                    dialogo = QDialog(self)
                    dialogo.setWindowTitle("Resultado óptimo")
                    dialogo.setMinimumSize(600, 400)

                    layout = QVBoxLayout()
                    texto_html = QTextEdit()
                    texto_html.setReadOnly(True)
                    texto_html.setHtml(resultado_html)

                    layout.addWidget(texto_html)
                    dialogo.setLayout(layout)
                    dialogo.exec_()

    
        except Exception as e:
            self.mostrar_error(f"Ocurrió un error al resolver: {str(e)}")

    def mostrar_resultado(self, texto):
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Problema estandarizado")
        dialogo.setMinimumSize(500, 400)

        layout = QVBoxLayout()
        area_texto = QTextEdit()
        area_texto.setReadOnly(True)

        explicacion = (
            "\n\n📘 Explicación de variables introducidas:\n"
            "• S = Variables de holgura (se suman cuando la restricción es ≤)\n"
            "• E = Variables de exceso (se restan cuando la restricción es ≥)\n"
            "• A = Variables artificiales (se agregan cuando la restricción es ≥ o =, y se penalizan con M en la función objetivo)\n"
        )

        area_texto.setPlainText(texto + explicacion)

        layout.addWidget(area_texto)
        dialogo.setLayout(layout)
        dialogo.exec_()

    def analisis_sensibilidad(self):
        from core.analisisSensibilidad import AnalisisSensibilidad
        try:
            funcion_str = self.funcion_input.text().strip()
            restricciones_texto = self.restricciones_input.toPlainText().strip().split('\n')
            es_maximizacion = self.max_radio.isChecked()

            if not funcion_str:
                self.mostrar_error("Debe ingresar una función objetivo.")
                return

            if not restricciones_texto:
                self.mostrar_error("Debe ingresar al menos una restricción.")
                return

        # --- Parsear función objetivo ---
            variables = sorted(set(re.findall(r'[a-zA-Z]\w*', funcion_str)))
            coef_obj = [0] * len(variables)

            for term in re.finditer(r'([+-]?\s*\d*\.?\d*)\s*([a-zA-Z]\w*)', funcion_str.replace(' ', '')):
                coef_str, var = term.groups()
                coef = float(coef_str) if coef_str.strip() not in ['', '+', '-'] else float(coef_str + '1')
                coef_obj[variables.index(var)] = coef

        # --- Parsear restricciones ---
            restricciones = []
            tipo_restricciones = []
            rhs = []

            for linea in restricciones_texto:
                if not linea.strip() or linea.strip().lower() in ['x >= 0', 'x, y >= 0']:
                    continue

                match = re.search(r'(<=|>=|=)', linea)
                if not match:
                    continue

                tipo = match.group(1)
                lhs, rhs_val = linea.split(tipo)
                rhs.append(float(rhs_val.strip()))
                tipo_restricciones.append(tipo)

                coef_fila = [0] * len(variables)
                for term in re.finditer(r'([+-]?\s*\d*\.?\d*)\s*([a-zA-Z]\w*)', lhs.replace(' ', '')):
                    coef_str, var = term.groups()
                    coef = float(coef_str) if coef_str.strip() not in ['', '+', '-'] else float(coef_str + '1')
                    coef_fila[variables.index(var)] = coef

                restricciones.append(coef_fila)

        # --- Llamar análisis de sensibilidad ---
            analisis = AnalisisSensibilidad(variables, coef_obj, restricciones, tipo_restricciones, rhs, es_maximizacion)
            analisis.construir_y_resolver()
            html_sensibilidad = analisis.obtener_resultados()

        # --- Mostrar en ventana ---
            dialogo = QDialog(self)
            dialogo.setWindowTitle("Análisis de sensibilidad")
            dialogo.setMinimumSize(600, 400)

            layout = QVBoxLayout()
            texto_html = QTextEdit()
            texto_html.setReadOnly(True)
            texto_html.setHtml(html_sensibilidad)

            layout.addWidget(texto_html)
            dialogo.setLayout(layout)
            dialogo.exec_()

        except Exception as e:
            self.mostrar_error(f"Ocurrió un error en el análisis de sensibilidad: {str(e)}")


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