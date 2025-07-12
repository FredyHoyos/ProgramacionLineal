from pulp import LpMaximize, LpMinimize, LpProblem, LpVariable, value

class AnalisisSensibilidad:
    def __init__(self, variables, coef_obj, restricciones, tipo_restricciones, rhs, es_maximizacion):
        self.variables = variables
        self.coef_obj = coef_obj
        self.restricciones = restricciones
        self.tipo_restricciones = tipo_restricciones
        self.rhs = rhs
        self.es_maximizacion = es_maximizacion

    def construir_y_resolver(self):
        # Crear problema
        sentido = LpMaximize if self.es_maximizacion else LpMinimize
        self.problema = LpProblem("PL", sentido)

        # Crear variables
        self.vars = [LpVariable(var, lowBound=0) for var in self.variables]

        # Función objetivo
        self.problema += sum(c * v for c, v in zip(self.coef_obj, self.vars)), "FO"

        # Restricciones
        self.restr_objs = []
        for i, (fila, tipo, b) in enumerate(zip(self.restricciones, self.tipo_restricciones, self.rhs)):
            expr = sum(coef * var for coef, var in zip(fila, self.vars))
            if tipo == "<=" or tipo == "≤":
                restr = expr <= b
            elif tipo == ">=" or tipo == "≥":
                restr = expr >= b
            else:
                restr = expr == b
            nombre = f"restr_{i}"
            self.problema += restr, nombre
            self.restr_objs.append(self.problema.constraints[nombre])

        self.problema.solve()

    def obtener_resultados(self):
        resultado = f"<b>Estado:</b> {self.problema.status}<br><b>Solución óptima:</b><br>"
        for var in self.vars:
            resultado += f"{var.name} = {var.varValue}<br>"
        resultado += f"Z = {value(self.problema.objective)}<br><br>"

        resultado += "<b>Análisis de sensibilidad - VARIABLES:</b><br>"
        resultado += ("<table border='1' cellspacing='0' cellpadding='4'>"
                      "<tr><th>Variable</th><th>Valor Final</th><th>Coef. Objetivo</th><th>Costo Reducido</th><th>Perm. Aumentar</th><th>Perm. Reducir</th></tr>")
        for idx, (var, coef) in enumerate(zip(self.vars, self.coef_obj)):
            reducido = var.dj
            aumento, reduccion = self._rango_coeficiente_objetivo(idx, coef)
            resultado += f"<tr><td>{var.name}</td><td>{var.varValue:.4f}</td><td>{coef}</td><td>{reducido:.4f}</td><td>{aumento}</td><td>{reduccion}</td></tr>"
        resultado += "</table><br><br>"

        resultado += "<b>Análisis de sensibilidad - RESTRICCIONES:</b><br>"
        resultado += ("<table border='1' cellspacing='0' cellpadding='4'>"
              "<tr><th>Restricción</th><th>Valor Final </th><th>Lado Derecho</th><th>Precio Sombra</th><th>Perm. Aumentar</th><th>Perm. Reducir</th></tr>")


        for i, restr in enumerate(self.restr_objs):
            shadow_price = restr.pi
            valor_izquierdo = sum(coef * var.varValue for coef, var in zip(self.restricciones[i], self.vars))
            rhs_val = self.rhs[i]
            aumento, reduccion = self._rango_rhs(i)
            resultado += f"<tr><td>restr_{i}</td><td>{valor_izquierdo:.4f}</td><td>{rhs_val:.4f}</td><td>{shadow_price:.4f}</td><td>{aumento}</td><td>{reduccion}</td></tr>"


        resultado += "</table>"

        return resultado

    def _rango_rhs(self, restr_index):
        original_rhs = self.rhs[restr_index]
        paso = 0.5
        max_cambio = 100

        # Permisible aumentar
        aumento = 0
        for i in range(1, int(max_cambio / paso)):
            nuevo_rhs = original_rhs + i * paso
            if not self._sigue_optima_rhs(restr_index, nuevo_rhs):
                break
            aumento = i * paso

        # Permisible reducir
        reduccion = 0
        for i in range(1, int(max_cambio / paso)):
            nuevo_rhs = original_rhs - i * paso
            if nuevo_rhs < 0:
                break
            if not self._sigue_optima_rhs(restr_index, nuevo_rhs):
                break
            reduccion = i * paso

        return round(aumento, 4), round(reduccion, 4)

    def _sigue_optima_rhs(self, restr_index, nuevo_rhs):
        sentido = LpMaximize if self.es_maximizacion else LpMinimize
        temp_problem = LpProblem("temp", sentido)
        vars_temp = [LpVariable(var.name, lowBound=0) for var in self.vars]
        temp_problem += sum(c * v for c, v in zip(self.coef_obj, vars_temp)), "FO"
        for i, (fila, tipo, b) in enumerate(zip(self.restricciones, self.tipo_restricciones, self.rhs)):
            b_mod = nuevo_rhs if i == restr_index else b
            expr = sum(coef * var for coef, var in zip(fila, vars_temp))
            if tipo == "<=" or tipo == "≤":
                temp_problem += expr <= b_mod
            elif tipo == ">=" or tipo == "≥":
                temp_problem += expr >= b_mod
            else:
                temp_problem += expr == b_mod
        temp_problem.solve()
        vars_opt = [v.varValue for v in vars_temp]
        base_actual = [round(v.varValue, 4) for v in self.vars]
        return all(abs(a - b) < 1e-3 for a, b in zip(vars_opt, base_actual))

    def _rango_coeficiente_objetivo(self, var_index, original_coef):
        paso = 0.5
        max_cambio = 100
        # Aumentar
        aumento = 0
        for i in range(1, int(max_cambio / paso)):
            nuevo_coef = original_coef + i * paso
            if not self._sigue_optima_coef(var_index, nuevo_coef):
                break
            aumento = i * paso
        # Reducir
        reduccion = 0
        for i in range(1, int(max_cambio / paso)):
            nuevo_coef = original_coef - i * paso
            if not self._sigue_optima_coef(var_index, nuevo_coef):
                break
            reduccion = i * paso
        return round(aumento, 4), round(reduccion, 4)

    def _sigue_optima_coef(self, var_index, nuevo_coef):
        sentido = LpMaximize if self.es_maximizacion else LpMinimize
        temp_problem = LpProblem("temp", sentido)
        vars_temp = [LpVariable(var.name, lowBound=0) for var in self.vars]
        nueva_funcion = [nuevo_coef if i == var_index else c for i, c in enumerate(self.coef_obj)]
        temp_problem += sum(c * v for c, v in zip(nueva_funcion, vars_temp)), "FO"
        for i, (fila, tipo, b) in enumerate(zip(self.restricciones, self.tipo_restricciones, self.rhs)):
            expr = sum(coef * var for coef, var in zip(fila, vars_temp))
            if tipo == "<=" or tipo == "≤":
                temp_problem += expr <= b
            elif tipo == ">=" or tipo == "≥":
                temp_problem += expr >= b
            else:
                temp_problem += expr == b
        temp_problem.solve()
        vars_opt = [v.varValue for v in vars_temp]
        base_actual = [round(v.varValue, 4) for v in self.vars]
        return all(abs(a - b) < 1e-3 for a, b in zip(vars_opt, base_actual))
    
