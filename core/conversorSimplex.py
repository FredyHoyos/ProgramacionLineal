import re
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget,
                             QTableWidgetItem, QApplication)
from PyQt5.QtCore import Qt

class ConversorSimplex:
    @staticmethod
    def estandarizar_problema(funcion_objetivo, restricciones, tipo='max'):
        variables = ['x', 'y']
        obj_coef = [0] * len(variables)

        for i, var in enumerate(variables):
            match = re.search(rf'([+-]?\d*\.?\d*){var}', funcion_objetivo.replace(' ', ''))
            if match:
                coef = match.group(1)
                obj_coef[i] = float(coef) if coef not in ['', '+', '-'] else 1.0 if coef != '-' else -1.0

        if tipo == 'max':
            obj_coef = [-c for c in obj_coef]

        A, b, etiquetas, artificiales = [], [], [], []
        slack_vars, art_vars = 0, 0

        for restr in restricciones:
            restr = restr.replace(' ', '')
            if '<=' in restr:
                lhs, rhs, signo = restr.split('<=')[0], restr.split('<=')[1], '<='
            elif '>=' in restr:
                lhs, rhs, signo = restr.split('>=')[0], restr.split('>=')[1], '>='
            elif '=' in restr:
                lhs, rhs, signo = restr.split('=')[0], restr.split('=')[1], '='
            else:
                raise ValueError(f"Operador inválido en la restricción: {restr}")

            fila = [0] * len(variables)
            for i, var in enumerate(variables):
                match = re.search(rf'([+-]?\d*\.?\d*){var}', lhs)
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

        max_len = max(len(fila) for fila in A)
        for fila in A:
            fila += [0] * (max_len - len(fila))

        z_row = obj_coef + [0] * (max_len - len(obj_coef))
        for idx in artificiales:
            z_row[idx] = -1e6

        etiquetas_finales = variables + etiquetas
        return {'tabla': A, 'rhs': b, 'z': z_row, 'etiquetas': etiquetas_finales}


class SimplexTabular:
    def __init__(self, tabla, rhs, z, etiquetas):
        self.A = [fila.copy() for fila in tabla]
        self.b = rhs.copy()
        self.z = z.copy()
        self.etiquetas = etiquetas
        self.historial = []
        self.vars_basicas = [f"X{i+1}" for i in range(len(tabla))]
        self.iteracion = 0
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
    def calcular_valor_z(self):
        return sum(self.z[j] * 0 for j in range(len(self.z))) + sum(self.b[i] * self.z[self.etiquetas.index(self.vars_basicas[i])] if self.vars_basicas[i] in self.etiquetas else 0 for i in range(len(self.b)))

    def obtener_historial(self):
        return self.historial

    def obtener_solucion(self):
        """Obtiene la solución óptima del problema de programación lineal."""
        solucion = {}
        for i, var in enumerate(self.vars_basicas):
            if var.startswith('X') or var.startswith('Y'):
                solucion[var.lower()] = self.b[i]
        return solucion

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

        self.vars_basicas[fila_pivote] = self.etiquetas[col_pivote]
        self.iteracion += 1
        self.registrar_estado(f"Iteración {self.iteracion}")
        return True

    def obtener_historial(self):
        return self.historial

    def obtener_solucion(self):
        """Obtiene la solución óptima del problema de programación lineal."""
        solucion = {}
        for i, var in enumerate(self.vars_basicas):
            if var.startswith('X') or var.startswith('Y'):
                solucion[var.lower()] = self.b[i]
        return solucion


class VentanaSimplexPaso(QWidget):
    def __init__(self, simplex: SimplexTabular, etiquetas):
        super().__init__()
        self.simplex = simplex
        self.historial = simplex.obtener_historial()
        self.etiquetas = etiquetas
        self.indice = 0

        self.setWindowTitle("Simplex Paso a Paso")
        self.setGeometry(200, 200, 800, 400)

        self.layout = QVBoxLayout()
        self.label_iter = QLabel("Iteración: 0")
        self.tabla = QTableWidget()
        self.btn_siguiente = QPushButton("Siguiente paso")
        self.btn_siguiente.clicked.connect(self.mostrar_siguiente)

        self.layout.addWidget(self.label_iter)
        self.layout.addWidget(self.tabla)
        self.layout.addWidget(self.btn_siguiente)
        self.setLayout(self.layout)

        self.mostrar_iteracion(self.indice)

    def mostrar_iteracion(self, indice):
        if 0 <= indice < len(self.historial):
            datos = self.historial[indice]
            self.tabla.setRowCount(len(datos['A']) + 1)
            self.tabla.setColumnCount(len(datos['A'][0]) + 1)

            for i in range(len(self.etiquetas)):
                self.tabla.setHorizontalHeaderItem(i, QTableWidgetItem(self.etiquetas[i]))
            self.tabla.setHorizontalHeaderItem(len(self.etiquetas), QTableWidgetItem('b'))

            for j in range(len(datos['z'])):
                self.tabla.setItem(0, j, QTableWidgetItem(f"{datos['z'][j]:.2f}"))

            for i in range(len(datos['A'])):
                for j in range(len(datos['A'][0])):
                    self.tabla.setItem(i+1, j, QTableWidgetItem(f"{datos['A'][i][j]:.2f}"))
                self.tabla.setItem(i+1, len(datos['A'][0]), QTableWidgetItem(f"{datos['b'][i]:.2f}"))

            self.label_iter.setText(f"Iteración: {datos['iteracion']}\nDescripción: {datos['descripcion']}")

    def mostrar_siguiente(self):
        if self.simplex.siguiente_paso():
            self.indice += 1
            self.historial = self.simplex.obtener_historial()
            self.mostrar_iteracion(self.indice)
        else:
            self.label_iter.setText("Solución óptima alcanzada.")
            self.btn_siguiente.setEnabled(False)


# Para ejecutar este código se necesita una llamada como esta:
# app = QApplication([])
# datos = ConversorSimplex.estandarizar_problema("3x + 5y", ["x <= 4", "2y <= 12", "3x + 2y <= 18"])
# simplex = SimplexTabular(**datos)
# while simplex.siguiente_paso(): pass
# ventana = VentanaSimplexPaso(simplex.obtener_historial(), datos['etiquetas'])
# ventana.show()
# app.exec_()
