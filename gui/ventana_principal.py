import matplotlib.pyplot as plt
import numpy as np
from PyQt5.QtWidgets import QMessageBox


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
        self.graficar_btn.clicked.connect(self.graficar)


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
        import re
        import numpy as np
        import matplotlib.pyplot as plt
        from scipy.optimize import linprog
        try:
            # Leer función objetivo
            funcion_str = self.funcion_input.text().replace(' ', '')
            if not funcion_str:
                self.mostrar_error("Debe ingresar una función objetivo.")
                return

            if not re.fullmatch(r'[+-]?\d*x([+-]\d*y)?', funcion_str):
                self.mostrar_error("La función debe estar en formato como: 3x+5y o -2x+y")
                return

            # Validar restricciones
            restricciones_texto = self.restricciones_input.toPlainText().split('\n')
            if not restricciones_texto or all(r.strip() == '' for r in restricciones_texto):
                self.mostrar_error("Debe ingresar al menos una restricción.")
                return

            operadores_validos = ['<=', '≥', '>=']
            for restr in restricciones_texto:
                if restr.strip() == '':
                    continue
                if not any(op in restr for op in operadores_validos):
                    self.mostrar_error(f"La restricción \"{restr}\" no contiene un operador válido (<=, >=).")
                    return
                if not re.search(r'[xy]', restr):
                    self.mostrar_error(f"La restricción \"{restr}\" no contiene variables x o y.")
                    return

            # 1. Procesar función objetivo
            coef_obj = [0, 0]  # Suponiendo 2 variables x e y
            coef_obj[0] = float(re.search(r'([+-]?\d*)x', funcion_str).group(1) or 1)
            coef_y_match = re.search(r'([+-]?\d*)y', funcion_str)
            if coef_y_match:
                val = coef_y_match.group(1)
                coef_obj[1] = float(val) if val not in ['', '+', '-'] else 1.0 if val != '-' else -1.0

            if self.max_radio.isChecked():
                c = [-coef for coef in coef_obj]  # Maximizar = minimizar negativo
            else:
                c = coef_obj  # Minimizar

            # 2. Procesar restricciones
            A = []
            b = []
            bounds = [(0, None), (0, None)]  # x, y ≥ 0 por defecto

            x = np.linspace(0, 10, 400)
            plt.close('all')  # <- Limpia ventanas previas
            plt.figure(figsize=(8, 6))

            for restriccion in restricciones_texto:
                restriccion = restriccion.replace(' ', '')
                if restriccion == '':
                    continue

                if restriccion in ['x>=0', 'x≥0']:
                    bounds[0] = (0, None)
                    continue
                if restriccion in ['y>=0', 'y≥0']:
                    bounds[1] = (0, None)
                    continue

                if '<=' in restriccion:
                    izquierda, derecha = restriccion.split('<=')
                    c_rhs = float(derecha)

                    coef_x = re.search(r'([+-]?\d*)x', izquierda)
                    coef_y = re.search(r'([+-]?\d*)y', izquierda)

                    a = float(coef_x.group(1)) if coef_x and coef_x.group(1) not in ['', '+', '-'] else 1.0 if coef_x else 0
                    if coef_x and coef_x.group(1) == '-':
                        a = -1.0

                    b_val = float(coef_y.group(1)) if coef_y and coef_y.group(1) not in ['', '+', '-'] else 1.0 if coef_y else 0
                    if coef_y and coef_y.group(1) == '-':
                        b_val = -1.0

                    A.append([a, b_val])
                    b.append(c_rhs)

                    if b_val != 0:
                        y_vals = (c_rhs - a * x) / b_val
                        plt.plot(x, y_vals, label=restriccion)
                    else:
                        plt.axvline(x=c_rhs / a, linestyle='--', label=restriccion)

                elif restriccion.startswith('x<='):
                    val = float(restriccion.split('<=')[1])
                    A.append([1, 0])
                    b.append(val)
                    plt.axvline(x=val, linestyle='--', label=restriccion)

                elif restriccion.startswith('y<='):
                    val = float(restriccion.split('<=')[1])
                    A.append([0, 1])
                    b.append(val)
                    plt.axhline(y=val, linestyle='--', label=restriccion)

            # 3. Resolver con linprog
            res = linprog(c=c, A_ub=A, b_ub=b, bounds=bounds, method='highs')

            if res.success:
                x_opt, y_opt = res.x
                plt.plot(x_opt, y_opt, 'ro', label=f'Óptimo ({x_opt:.2f}, {y_opt:.2f})')
            else:
                print("No se pudo encontrar solución óptima.")

            

            # 4. Mostrar gráfica
            plt.xlim(0, 10)
            plt.ylim(0, 10)
            plt.xlabel("x")
            plt.ylabel("y")
            plt.title("Región factible y punto óptimo")
            plt.legend()
            plt.grid(True)
            plt.show()
        except Exception as e:
            self.mostrar_error(f"Ocurrió un error verifique los datos: {str(e)}")
        