from copy import deepcopy
from fractions import Fraction
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QTextEdit, QHBoxLayout
from PyQt5.QtGui import QFont
import re


class SimplexPasoAPaso(QDialog):
    def __init__(self, datos):
        super().__init__()
        self.setWindowTitle("Método Simplex Paso a Paso")
        self.setMinimumSize(900, 350)

        self.datos = datos
        self.iteracion_actual = 0
        self.historial = []  # Para guardar estados anteriores

        self.texto = QTextEdit()
        self.texto.setReadOnly(True)
        fuente = QFont("Courier New")
        fuente.setStyleHint(QFont.Monospace)
        fuente.setPointSize(10)
        self.texto.setFont(fuente)

        self.boton_siguiente = QPushButton("Siguiente")
        self.boton_siguiente.clicked.connect(self.mostrar_siguiente)

        self.boton_anterior = QPushButton("Retroceder")
        self.boton_anterior.clicked.connect(self.mostrar_anterior)
        self.boton_anterior.setEnabled(False)

        botones_layout = QHBoxLayout()
        botones_layout.addWidget(self.boton_anterior)
        botones_layout.addWidget(self.boton_siguiente)

        layout = QVBoxLayout()
        layout.addWidget(self.texto)
        layout.addLayout(botones_layout)
        self.setLayout(layout)

        self.preparar_datos()
        self.mostrar_actual()

    def preparar_datos(self):
        lineas = [l.strip() for l in self.datos.splitlines() if l.strip() and '=' in l]
        self.variables = []
        self.tabla = []
        self.basicas = []
        restricciones_temp = []

        for linea in lineas:
            lhs, rhs = linea.split('=')
            coeficientes = self.extraer_coeficientes(lhs.strip())
            for _, var in coeficientes:
                if var not in self.variables:
                    self.variables.append(var)
            restricciones_temp.append((coeficientes, float(rhs.strip())))

        for i, (coeficientes, rhs_val) in enumerate(restricciones_temp):
            coef_dict = {var: float(coef) for coef, var in coeficientes}
            fila = [coef_dict.get(var, 0.0) for var in self.variables]
            fila.append(rhs_val)
            self.tabla.append(fila)

            if i == 0:
                self.basicas.append("Z")
            else:
                encontrada = False
                for var in self.variables:
                    if var.lower().startswith("s"):
                        self.basicas.append(f"s{i+2}")
                        encontrada = True
                        break
                if not encontrada:
                    self.basicas.append(f"VB{i}")

    def extraer_coeficientes(self, expresion):
        resultado = []
        expresion = expresion.replace(' ', '')
        if not expresion.startswith(('+', '-')):
            expresion = '+' + expresion
        terminos = re.findall(r'[+-][^+-]+', expresion)
        for termino in terminos:
            signo = -1.0 if termino[0] == '-' else 1.0
            cuerpo = termino[1:]
            match = re.match(r'(\d*\.?\d*)?([A-Za-z]\w*)', cuerpo)
            if match:
                coef_str, var = match.groups()
                coef = float(coef_str) if coef_str else 1.0
                resultado.append((signo * coef, var))
        return resultado

    def mostrar_tabla(self):
        encabezado = f"Iteración = {self.iteracion_actual}\n"
        columnas = ['Ec #', 'VB'] + self.variables + ['Lado der', 'Razón']
        ancho = 8
        linea_sep = "+" + "+".join("-" * ancho for _ in columnas) + "+"
        fila_encabezado = "|" + "|".join(f"{col:^{ancho}}" for col in columnas) + "|"
        resultado = encabezado + linea_sep + "\n" + fila_encabezado + "\n" + linea_sep + "\n"

        for i, fila in enumerate(self.tabla):
            razon = "-"
            if i != 0:
                pivot_col = self.columna_pivote()
                if pivot_col is not None and fila[pivot_col] > 0:
                    razon = round(fila[-1] / fila[pivot_col], 2)
            celdas = [f"({i})", self.basicas[i]] + \
                     [str(Fraction(v).limit_denominator()) for v in fila] + \
                     [str(razon)]
            fila_str = "|" + "|".join(f"{c:^{ancho}}" for c in celdas) + "|"
            resultado += fila_str + "\n" + linea_sep + "\n"

        return resultado

    def columna_pivote(self):
        z_row = self.tabla[0][1:-1]
        negativos = [(i, val) for i, val in enumerate(z_row) if val < 0]
        if not negativos:
            return None
        return 1 + min(negativos, key=lambda x: x[1])[0]

    def fila_pivote(self, col):
        razones = []
        for i in range(1, len(self.tabla)):
            if self.tabla[i][col] > 0:
                razon = self.tabla[i][-1] / self.tabla[i][col]
                razones.append((i, razon))
        if not razones:
            return None
        return min(razones, key=lambda x: x[1])[0]

    def pivotear(self, fila_pivot, col_pivot):
        pivot_val = self.tabla[fila_pivot][col_pivot]
        self.tabla[fila_pivot] = [x / pivot_val for x in self.tabla[fila_pivot]]
        for i in range(len(self.tabla)):
            if i != fila_pivot:
                factor = self.tabla[i][col_pivot]
                self.tabla[i] = [a - factor * b for a, b in zip(self.tabla[i], self.tabla[fila_pivot])]
        self.basicas[fila_pivot] = self.variables[col_pivot]

    def guardar_estado(self):
        self.historial.append((deepcopy(self.tabla), deepcopy(self.basicas)))

    def mostrar_actual(self):
        self.texto.setPlainText(self.mostrar_tabla())
        self.boton_anterior.setEnabled(self.iteracion_actual > 0)

    def mostrar_siguiente(self):
        col = self.columna_pivote()
        if col is None:
            self.texto.setPlainText(self.mostrar_tabla() + "\n✅ Solución óptima alcanzada.")
            self.boton_siguiente.setEnabled(False)
            return

        fila = self.fila_pivote(col)
        if fila is None:
            self.texto.setPlainText("❌ El problema no tiene solución acotada.")
            self.boton_siguiente.setEnabled(False)
            return

        self.guardar_estado()
        self.pivotear(fila, col)
        self.iteracion_actual += 1
        self.mostrar_actual()

    def mostrar_anterior(self):
        if self.iteracion_actual > 0:
            self.iteracion_actual -= 1
            self.tabla, self.basicas = self.historial.pop()
            self.boton_siguiente.setEnabled(True)
            self.mostrar_actual()
