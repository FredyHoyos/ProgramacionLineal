import re
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget,
                             QTableWidgetItem, QHBoxLayout, QApplication)
from PyQt5.QtCore import Qt

class ConversorSimplex:
    @staticmethod
    def estandarizar_problema(funcion_objetivo, restricciones, tipo='max'):
        variables = ['x', 'y']
        obj_coef = [0] * len(variables)

        # Extraer coeficientes de la función objetivo
        for i, var in enumerate(variables):
            match = re.search(rf'([+-]?*){var}', funcion_objetivo.replace(' ', ''))
            if match:
                coef = match.group(1)
                obj_coef[i] = float(coef) if coef not in ['', '+', '-'] else 1.0 if coef != '-' else -1.0

        if tipo == 'max':
            obj_coef = [-c for c in obj_coef]

        A = []
        b = []
        etiquetas = []
        artificiales = []
        slack_vars = 0
        art_vars = 0

        for restr in restricciones:
            restr = restr.replace(' ', '')
            if '<=' in restr:
                lhs, rhs = restr.split('<=')
                signo = '<='
            elif '>=' in restr:
                lhs, rhs = restr.split('>=')
                signo = '>='
            elif '=' in restr:
                lhs, rhs = restr.split('=')
                signo = '='
            else:
                raise ValueError(f"Operador inválido en la restricción: {restr}")

            fila = [0] * len(variables)
            for i, var in enumerate(variables):
                match = re.search(rf'([+-]?*){var}', lhs)
                if match:
                    coef = match.group(1)
                    fila[i] = float(coef) if coef not in ['', '+', '-'] else 1.0 if coef != '-' else -1.0

            rhs_val = float(rhs)
            b.append(rhs_val)

            if signo == '<=':
                fila += [1]
                etiquetas.append(f's{slack_vars+1}')
                slack_vars += 1
            elif signo == '>=':
                fila += [-1]
                etiquetas.append(f'e{slack_vars+1}')
                slack_vars += 1
                fila += [1]
                etiquetas.append(f'A{art_vars+1}')
                artificiales.append(len(fila)-1)
                art_vars += 1
            elif signo == '=':
                fila += [1]
                etiquetas.append(f'A{art_vars+1}')
                artificiales.append(len(fila)-1)
                art_vars += 1

            A.append(fila)

        # Asegura que todas las filas de A tengan la misma longitud
        max_len = max(len(fila) for fila in A)
        for fila in A:
            fila += [0] * (max_len - len(fila))

        # Crear z_row del mismo tamaño
        z_row = obj_coef + [0] * (max_len - len(obj_coef))

        # Penalización por variables artificiales (método de la Gran M)
        for idx in artificiales:
            z_row[idx] = -1e6


        etiquetas_finales = variables + etiquetas
        return {
            'tabla': A,
            'rhs': b,
            'z': z_row,
            'etiquetas': etiquetas_finales
        }


class SimplexTabular:
    def __init__(self, tabla, rhs, z):
        self.A = [fila.copy() for fila in tabla]
        self.b = rhs.copy()
        self.z = z.copy()
        self.historial = []
        self.iteracion = 0
        self.vars_basicas = [f"S{i+1}" for i in range(len(tabla))]
        self.registrar_estado("Inicio")

    def registrar_estado(self, descripcion=""):
        self.historial.append({
            'iteracion': self.iteracion,
            'A': [fila.copy() for fila in self.A],
            'b': self.b.copy(),
            'z': self.z.copy(),
            'vb': self.vars_basicas.copy(),
            'descripcion': descripcion
        })

    def siguiente_paso(self):
        col_pivote = min(range(len(self.z)), key=lambda j: self.z[j])
        if self.z[col_pivote] >= 0:
            self.registrar_estado("Óptimo alcanzado")
            return False

        razones = []
        for i in range(len(self.A)):
            aij = self.A[i][col_pivote]
            if aij > 0:
                razones.append(self.b[i] / aij)
            else:
                razones.append(float('inf'))

        fila_pivote = razones.index(min(razones))
        pivote = self.A[fila_pivote][col_pivote]

        self.A[fila_pivote] = [val / pivote for val in self.A[fila_pivote]]
        self.b[fila_pivote] /= pivote

        for i in range(len(self.A)):
            if i != fila_pivote:
                factor = self.A[i][col_pivote]
                self.A[i] = [self.A[i][j] - factor * self.A[fila_pivote][j] for j in range(len(self.z))]
                self.b[i] -= factor * self.b[fila_pivote]

        factor = self.z[col_pivote]
        self.z = [self.z[j] - factor * self.A[fila_pivote][j] for j in range(len(self.z))]

        self.vars_basicas[fila_pivote] = f"X{col_pivote+1}"
        self.iteracion += 1
        self.registrar_estado(f"Iteración {self.iteracion}")
        return True

    def obtener_historial(self):
        return self.historial


class VentanaSimplexPaso(QWidget):
    def __init__(self, historial):
        super().__init__()
        self.historial = historial
        self.indice = 0

        self.setWindowTitle("Simplex Paso a Paso")
        self.setGeometry(200, 200, 600, 300)

        self.layout = QVBoxLayout()
        self.tabla = QTableWidget()
        self.label_iter = QLabel("Iteración: 0")
        self.btn_siguiente = QPushButton("Siguiente paso")
        self.btn_siguiente.clicked.connect(self.mostrar_siguiente)

        self.layout.addWidget(self.label_iter)
        self.layout.addWidget(self.tabla)
        self.layout.addWidget(self.btn_siguiente)
        self.setLayout(self.layout)
        self.mostrar_iteracion(self.indice)

    def mostrar_iteracion(self, indice):
        datos = self.historial[indice]
        filas = len(datos['A']) + 1
        columnas = len(datos['A'][0]) + 2

        self.tabla.setRowCount(filas)
        self.tabla.setColumnCount(columnas)

        headers = [f"X{i+1}" for i in range(len(datos['A'][0]))] + ["LD", "VB"]
        self.tabla.setHorizontalHeaderLabels(headers)

        for i, fila in enumerate(datos['A']):
            for j, val in enumerate(fila):
                self.tabla.setItem(i, j, QTableWidgetItem(f"{val:.2f}"))
            self.tabla.setItem(i, columnas - 2, QTableWidgetItem(f"{datos['b'][i]:.2f}"))
            self.tabla.setItem(i, columnas - 1, QTableWidgetItem(datos['vb'][i]))

        for j, val in enumerate(datos['z']):
            self.tabla.setItem(filas - 1, j, QTableWidgetItem(f"{val:.2f}"))
        self.tabla.setItem(filas - 1, columnas - 1, QTableWidgetItem("Z"))

        self.label_iter.setText(f"{datos['descripcion']}")

    def mostrar_siguiente(self):
        if self.indice + 1 < len(self.historial):
            self.indice += 1
            self.mostrar_iteracion(self.indice)
