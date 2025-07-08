from copy import deepcopy
from fractions import Fraction
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QTextEdit, QHBoxLayout
from PyQt5.QtGui import QFont
import re


class SimplexPasoAPaso(QDialog):
    def __init__(self, datos):
        super().__init__()
        self.setWindowTitle("Método Simplex Paso a Paso")
        self.setMinimumSize(600, 350)

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
                        self.basicas.append(f"s{i}")
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
        html = f"<h3>Iteración = {self.iteracion_actual}</h3>"
        html += "<table border='1' cellspacing='0' cellpadding='5' style='border-collapse: collapse; font-family: monospace;'>"

        columnas = ['Ec #', 'VB'] + self.variables + ['Lado der', 'Razón']
        html += "<tr style='background-color: #f0f0f0;'>" + "".join(f"<th>{col}</th>" for col in columnas) + "</tr>"

        col_pivot = self.columna_pivote()
        fila_pivot = self.fila_pivote(col_pivot) if col_pivot is not None else None

        for i, fila in enumerate(self.tabla):
            razon = "-"
            if i != 0 and col_pivot is not None and fila[col_pivot] > 0:
                razon = round(fila[-1] / fila[col_pivot], 2)

            celdas = [f"({i})", self.basicas[i]] + \
                    [str(Fraction(v).limit_denominator()) for v in fila] + \
                    [str(razon)]

            html += "<tr>"
            for j, valor in enumerate(celdas):
                estilo = ""

                # columna pivote (variable candidata)
                if col_pivot is not None and j == col_pivot + 2 and i != 0:
                    estilo = "background-color: yellow;"

                # fila pivote (restricción con menor razón)
                if fila_pivot is not None and i == fila_pivot:
                    estilo = "background-color: #cceeff;"  # azul claro

                # celda pivote
                if fila_pivot is not None and col_pivot is not None and i == fila_pivot and j == col_pivot + 2:
                    estilo = "background-color: orange; font-weight: bold;"

                html += f"<td style='{estilo}'>{valor}</td>"
            html += "</tr>"

        html += "</table>"
        return html

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
        self.texto.setHtml(self.mostrar_tabla())
        self.boton_anterior.setEnabled(self.iteracion_actual > 0)

    def mostrar_siguiente(self):
        # Determinar la columna pivote
        col = self.columna_pivote()

        # Si no hay columna pivote, la solución óptima ha sido alcanzada
        if col is None:
            solucion_html = (
                self.mostrar_tabla() +
                "<p style='color: green; font-weight: bold;'>✅ Solución óptima alcanzada.</p>"+
                self.obtener_resultado_final()
            )
            self.texto.setHtml(solucion_html)
            self.boton_siguiente.setEnabled(False)
            return

        # Determinar la fila pivote
        fila = self.fila_pivote(col)

        # Si no hay fila pivote válida, la solución no está acotada
        if fila is None:
            self.texto.setHtml(
                "<p style='color: red; font-weight: bold;'>❌ El problema no tiene solución acotada.</p>"
            )
            self.boton_siguiente.setEnabled(False)
            return

        # Guardar el estado actual antes de pivotear
        self.guardar_estado()

        # Realizar el pivoteo y actualizar la tabla
        self.pivotear(fila, col)
        self.iteracion_actual += 1

        # Mostrar la tabla actualizada
        self.mostrar_actual()

    def mostrar_anterior(self):
        if self.iteracion_actual > 0:
            self.iteracion_actual -= 1
            self.tabla, self.basicas = self.historial.pop()
            self.boton_siguiente.setEnabled(True)
            self.mostrar_actual()

    def resolver_simplex(self):
        self.iteracion_actual = 0
        self.historial.clear()

        while True:
            col = self.columna_pivote()

            if col is None:
                # Solución óptima alcanzada
                html = self.mostrar_tabla()
                html += "<p style='color: green; font-weight: bold;'>✅ Solución óptima alcanzada.</p>"
                html += self.obtener_resultado_final()
                return html

            fila = self.fila_pivote(col)

            if fila is None:
                # Problema no acotado
                return "<p style='color: red; font-weight: bold;'>❌ El problema no tiene solución acotada.</p>"

            self.guardar_estado()
            self.pivotear(fila, col)
            self.iteracion_actual += 1

    def obtener_resultado_final(self):
        html = "<h4>Valores óptimos:</h4><ul>"

        # Inicializar todas las variables en 0
        valores = {var: 0 for var in self.variables}
        for i in range(1, len(self.tabla)):
            var = self.basicas[i]
            if var in valores:
                valores[var] = round(self.tabla[i][-1], 4)

        for var in sorted(valores):
            html += f"<li><b>{var}</b> = {valores[var]}</li>"

        z_opt = round(self.tabla[0][-1], 4)
        html += f"</ul><p><b>Z óptimo = {z_opt}</b></p>"

        return html
