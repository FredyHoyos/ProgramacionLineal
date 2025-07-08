class Estandarizador:
    def __init__(self, funcion_objetivo, restricciones, tipo_restricciones, rhs, es_maximizacion=True):
        self.funcion_objetivo = funcion_objetivo
        self.restricciones = restricciones
        self.tipo_restricciones = tipo_restricciones
        self.rhs = rhs
        self.es_maximizacion = es_maximizacion

    def convertir_a_estandar_texto(self):
        num_vars = len(self.funcion_objetivo)
        texto = ""
        tipo_obj = "Max" if self.es_maximizacion else "Min"

        texto += f"{tipo_obj}\n Z = " + " + ".join(
            f"{coef}X{i+1}" for i, coef in enumerate(self.funcion_objetivo)) + "\nRestricciones:\n\n"

        for i, (rest, tipo, b_i) in enumerate(zip(self.restricciones, self.tipo_restricciones, self.rhs)):
            restr_txt = " + ".join(f"{coef}X{j+1}" for j, coef in enumerate(rest))
            texto += f"{restr_txt} {tipo} {b_i}\n"
        texto += "X1, X2 ≥ 0\n\n"

        operador = "-" if self.es_maximizacion else "+"
        obj_expr = " ".join(f"{operador} {abs(coef)}X{i+1}" for i, coef in enumerate(self.funcion_objetivo))
        artificiales = []
        artificial_idx = 1
        for i, tipo in enumerate(self.tipo_restricciones):
            if tipo in (">=", "="):
                obj_expr += f" {operador} M*A{artificial_idx}"
                artificiales.append(f"A{artificial_idx}")
                artificial_idx += 1

        texto += f"Max \n{'Z' if self.es_maximizacion else '-Z'} {obj_expr} = 0\n"
        ecuacion = f"{'Z' if self.es_maximizacion else '-Z'} {obj_expr} = 0\n"

        slack_idx = 1
        exceso_idx = 1
        artificial_idx = 1
        nombres_vars = [f"X{i+1}" for i in range(num_vars)]

        for i, (rest, tipo, b_i) in enumerate(zip(self.restricciones, self.tipo_restricciones, self.rhs)):
            fila_txt = " + ".join(f"{coef}X{j+1}" for j, coef in enumerate(rest))

            if tipo == "<=":
                fila_txt += f" + S{slack_idx}"
                nombres_vars.append(f"S{slack_idx}")
                slack_idx += 1
            elif tipo == ">=":
                fila_txt += f" - E{exceso_idx} + A{artificial_idx}"
                nombres_vars += [f"E{exceso_idx}", f"A{artificial_idx}"]
                exceso_idx += 1
                artificial_idx += 1
            elif tipo == "=":
                fila_txt += f" + A{artificial_idx}"
                nombres_vars.append(f"A{artificial_idx}")
                artificial_idx += 1

            texto += f"{fila_txt} = {b_i}\n"
            ecuacion += f"{fila_txt} = {b_i}\n"

        texto += ", ".join(nombres_vars) + " ≥ 0"
        return texto, ecuacion
