
import re
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import linprog


class GraficadorLineal:
    def __init__(self, funcion_str, restricciones_texto, es_maximizacion):
        self.funcion_str = funcion_str.replace(' ', '')
        self.restricciones_texto = restricciones_texto
        self.es_maximizacion = es_maximizacion

    def graficar(self):
        # 1. Función objetivo
        coef_obj = [0, 0]
        coef_obj[0] = float(re.search(r'([+-]?\d*)x', self.funcion_str).group(1) or 1)
        coef_y_match = re.search(r'([+-]?\d*)y', self.funcion_str)
        if coef_y_match:
            val = coef_y_match.group(1)
            coef_obj[1] = float(val) if val not in ['', '+', '-'] else 1.0 if val != '-' else -1.0

        c = [-coef for coef in coef_obj] if self.es_maximizacion else coef_obj

        # 2. Restricciones
        A = []
        b = []
        bounds = [(0, None), (0, None)]
        x = np.linspace(0, 10, 400)
        plt.close('all')
        plt.figure(figsize=(8, 6))

        for restriccion in self.restricciones_texto:
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

        # 3. Resolver
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
