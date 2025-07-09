from copy import deepcopy
from fractions import Fraction
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QTextEdit, QHBoxLayout
from PyQt5.QtGui import QFont
import sympy as sp
import re

class SimplexPasoAPasoGranM(QDialog):
    def __init__(self, datos):
        super().__init__()
        self.setWindowTitle("Método Simplex Paso a Paso")
        self.setMinimumSize(600, 350)

        self.datos = datos
        self.iteracion_actual = 0
        self.historial = []
        self.mensajes = []

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

    def insertar_signo_multiplicacion(self, expresion):
        expresion = expresion.replace('m', 'M')  # corregir minúscula
        return re.sub(r'(?<=[0-9])(?=[A-Za-z])', '*', expresion)

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
            restricciones_temp.append((coeficientes, rhs.strip()))

        for i, (coeficientes, rhs) in enumerate(restricciones_temp):
            fila = []
            if i == 0:
                coef_dict = {var: coef.strip() for coef, var in coeficientes}
                for var in self.variables:
                    valor = coef_dict.get(var, '0')
                    valor_corregido = self.insertar_signo_multiplicacion(valor)
                    fila.append(sp.sympify(valor_corregido))
                rhs_corregido = self.insertar_signo_multiplicacion(rhs.strip())
                fila.append(sp.sympify(rhs_corregido))
            else:
                coef_dict = {var: float(coef) for coef, var in coeficientes}
                for var in self.variables:
                    fila.append(coef_dict.get(var, 0.0))
                fila.append(float(rhs))
            self.tabla.append(fila)
            self.basicas.append("Z" if i == 0 else f"X{i+2}")

    def extraer_coeficientes(self, expresion):
        resultado = []
        expresion = expresion.replace(' ', '')
        if not expresion.startswith(('+', '-')):
            expresion = '+' + expresion

        terminos = re.findall(r'([+-])((?:\([^()]+\)|[^()+-]+)?)([A-Za-z]\w*)', expresion)
        for signo, coef_str, var in terminos:
            if not coef_str:
                coef = signo + '1'
            elif coef_str.startswith('(') and coef_str.endswith(')'):
                expr = coef_str[1:-1]
                partes = re.findall(r'[+-]?[^+-]+', expr)
                coef_partes = []
                for parte in partes:
                    parte = parte.strip()
                    if not parte:
                        continue
                    if signo == '-':
                        if parte.startswith('-'):
                            coef_partes.append('+' + parte[1:])
                        elif parte.startswith('+'):
                            coef_partes.append('-' + parte[1:])
                        else:
                            coef_partes.append('-' + parte)
                    else:
                        coef_partes.append(parte)
                coef = '+'.join(coef_partes).replace('+-', '-').replace('--', '+')
            else:
                coef = signo + coef_str if not coef_str.startswith(('+', '-')) else coef_str
            resultado.append((coef, var))
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
            if i != 0 and col_pivot is not None and isinstance(fila[col_pivot], (int, float)) and fila[col_pivot] > 0:
                razon = round(fila[-1] / fila[col_pivot], 2)

            celdas = [f"({i})", self.basicas[i]] + \
                     [str(Fraction(v).limit_denominator()) if isinstance(v, (int, float)) else str(v) for v in fila] + \
                     [str(razon)]

            html += "<tr>"
            for j, valor in enumerate(celdas):
                estilo = ""
                if col_pivot is not None and j == col_pivot + 2 and i != 0:
                    estilo = "background-color: yellow;"
                if fila_pivot is not None and i == fila_pivot:
                    estilo = "background-color: #cceeff;"
                if fila_pivot is not None and col_pivot is not None and i == fila_pivot and j == col_pivot + 2:
                    estilo = "background-color: orange; font-weight: bold;"
                html += f"<td style='{estilo}'>{valor}</td>"
            html += "</tr>"

        html += "</table>"

        # Agregar mensaje explicativo
        if self.iteracion_actual < len(self.mensajes):
            html += f"<div style='margin-top: 10px;'>{self.mensajes[self.iteracion_actual]}</div>"

        return html

    def columna_pivote(self):
        z_row = self.tabla[0][1:-1]  # Omitimos Z (índice 0) y el RHS (último)
        negativos = []

        for i, val in enumerate(z_row, start=1):  # índice real desde 1 para alinear con self.variables
            if isinstance(val, (int, float)):
                if val < 0:
                    negativos.append((i, val))
            elif isinstance(val, sp.Basic):
                M = sp.Symbol('M')
                expr_expand = val.expand()
                coef_M = expr_expand.coeff(M)
                constante = expr_expand.subs(M, 0)
                if coef_M < 0 or (coef_M == 0 and constante < 0):
                    negativos.append((i, val))

        if not negativos:
            return None

        return min(negativos, key=lambda x: x[1].subs(sp.Symbol('M'), 1000))[0]

    def fila_pivote(self, col):
        razones = []
        for i in range(1, len(self.tabla)):
            if isinstance(self.tabla[i][col], (int, float)) and self.tabla[i][col] > 0:
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
        col = self.columna_pivote()

        if col is None:
            self.generar_mensaje_iteracion(col, None)
            solucion_html = (
                self.mostrar_tabla() +
                "<p style='color: green; font-weight: bold;'>✅ Solución óptima alcanzada.</p>" +
                self.obtener_resultado_final()
            )
            self.texto.setHtml(solucion_html)
            self.boton_siguiente.setEnabled(False)
            return

        fila = self.fila_pivote(col)

        if fila is None:
            self.generar_mensaje_iteracion(col, None)
            self.texto.setHtml(
                self.mostrar_tabla() +
                "<p style='color: red; font-weight: bold;'>❌ El problema no tiene solución acotada.</p>"
            )
            self.boton_siguiente.setEnabled(False)
            return

        self.guardar_estado()
        self.generar_mensaje_iteracion(col, fila)
        self.pivotear(fila, col)
        self.iteracion_actual += 1
        self.mostrar_actual()

    def mostrar_anterior(self):
        if self.iteracion_actual > 0:
            self.iteracion_actual -= 1
            self.tabla, self.basicas = self.historial.pop()
            self.boton_siguiente.setEnabled(True)
            self.mostrar_actual()

    def generar_mensaje_iteracion(self, col_pivot, fila_pivot):
        mensaje = ""
        if col_pivot is None:
            mensaje += "<p style='color:green; font-weight:bold;'>No hay coeficientes negativos en Z → ¡SOLUCIÓN ÓPTIMA!</p>"
        else:
            mensaje += f"<p><b>Coeficiente más negativo:</b> {self.variables[col_pivot]} (columna {col_pivot + 1})</p>"
            if fila_pivot is not None:
                mensaje += f"<p><b>Variable que entra:</b> {self.variables[col_pivot]}<br>"
                mensaje += f"<b>Variable que sale:</b> {self.basicas[fila_pivot]}</p>"
            else:
                mensaje += "<p style='color:red;'>No hay fila pivote → el problema no tiene solución acotada.</p>"

        identidad = True
        for j in range(len(self.variables)):
            columna = [self.tabla[i][j] for i in range(1, len(self.tabla))]
            if columna.count(1) != 1 or columna.count(0) != len(columna) - 1:
                identidad = False
                break
        if identidad:
            mensaje += "<p>✅ Las variables básicas forman una <b>matriz identidad</b>.</p>"

        self.mensajes.append(mensaje)

    def obtener_resultado_final(self):
        html = "<h4>Valores óptimos:</h4><ul>"
        valores = {var: 0 for var in self.variables}
        for i in range(1, len(self.tabla)):
            var = self.basicas[i]
            if var in valores:
                valores[var] = round(self.tabla[i][-1], 4)
        for var in sorted(valores):
            html += f"<li><b>{var}</b> = {valores[var]}</li>"
        z_opt = self.tabla[0][-1]
        html += f"</ul><p><b>Z óptimo = {z_opt}</b></p>"
        return html


    def resolver_directo(self):
        while True:
            col = self.columna_pivote()
            if col is None:
                return self.obtener_resultado_final()
            fila = self.fila_pivote(col)
            if fila is None:
                return "<p style='color: red; font-weight: bold;'>❌ El problema no tiene solución acotada.</p>"
            self.pivotear(fila, col)
