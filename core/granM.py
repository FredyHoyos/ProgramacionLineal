import re

class MetodoGranM:
    def __init__(self, entrada_texto):
        self.lineas = [line.strip() for line in entrada_texto.strip().split('\n') if line.strip()]
        self.funcion_objetivo = self.lineas[0]
        self.restricciones = self.lineas[1:]
        self.ajustada = ""
        self.vars_artificiales = []
        self.reemplazos = {}
        self.resultado = []

    def procesar(self):
        self.detectar_artificiales()
        if not self.vars_artificiales:
            # No se aplica método Gran M, devolver texto tal cual
            return '\n'.join(self.lineas)

        self.despejar_artificiales()
        self.reemplazar_en_objetivo()
        self.resultado = [self.ajustada] + self.restricciones
        return '\n'.join(self.resultado)

    def detectar_artificiales(self):
        for restriccion in self.restricciones:
            artificiales = re.findall(r'\bA\d+\b', restriccion)
            for art in artificiales:
                if art not in self.vars_artificiales:
                    self.vars_artificiales.append(art)

    def despejar_artificiales(self):
        usadas = set()

        for art in self.vars_artificiales:
            for i, restr in enumerate(self.restricciones):
                if art in restr and i not in usadas:
                    usadas.add(i)
                    lhs, rhs = restr.split('=')
                    lhs = lhs.strip()
                    rhs = rhs.strip()
                    partes = re.findall(r'([+-]?\s*\d*\.?\d*)\s*([A-Za-z]\d*)', lhs)

                    coeficientes = {var: self._parse_num(coef) for coef, var in partes}
                    if art not in coeficientes:
                        continue

                    divisor = coeficientes.pop(art)
                    nueva_expr = f"{rhs}"
                    for var, coef in coeficientes.items():
                        nuevo_coef = -coef / divisor
                        signo = '+' if nuevo_coef >= 0 else '-'
                        nueva_expr += f" {signo} {abs(nuevo_coef)}{var}"

                    self.reemplazos[art] = f"({nueva_expr})"
                    break


    def reemplazar_en_objetivo(self):
        expr = self.funcion_objetivo.replace(" ", "")
        z_lado, rhs = expr.split('=')

        coef_var = re.findall(r'([+-]?\d*\.?\d*)?([A-Za-z]\d*)', z_lado)

        nueva_z = "-Z"

        for coef, var in coef_var:
            coef = coef if coef not in ["", "+", "-"] else coef + "1" if coef in ["+", "-"] else "1"
            coef_num = self._parse_num(coef)

            if var.startswith("A"):
                if var in self.reemplazos:
                    expr_reemplazo = self.reemplazos[var]
                    nueva_z += f" + M*{expr_reemplazo}"
            else:
                nueva_z += f" + {coef_num}{var}"
        
        nueva_z = nueva_z.replace(" + 1.0M", "")
        nueva_z = nueva_z.replace(" + -1.0Z", "")
        nueva_z = nueva_z.replace(" + 1.0Z", "")
        self.ajustada = self._expandir_m(nueva_z) + " = " + self._expandir_constante()


    def _expandir_m(self, expr):
        expr = expr.replace(' ', '')
        resultado = "-Z"
        coef_puros = {}
        coef_m = {}
        constante_m = 0

        # Encontrar expresiones M*(...)
        m_terms = re.findall(r'M\*\(([^)]+)\)', expr)
        for term in m_terms:
            # Simplificar coeficientes dentro de paréntesis
            term = term.replace('1.0M', 'M').replace('-1.0M', '-M')
            partes = re.findall(r'([+-]?\s*\d*\.?\d*)\s*([A-Za-z]\d+)?', term)
            for coef, var in partes:
                coef_num = self._parse_num(coef)
                if var:
                    coef_m[var] = coef_m.get(var, 0) + coef_num
                else:
                    constante_m += coef_num

        # Eliminar las expresiones M*() para dejar solo los coeficientes puros
        expr_sin_m = re.sub(r'M\*\([^)]+\)', '', expr)
        normales = re.findall(r'([+-]?\d*\.?\d*)\s*(X\d+)', expr_sin_m)
        for coef, var in normales:
            coef_puros[var] = coef_puros.get(var, 0) + self._parse_num(coef)

        # Combinar en resultado
        for var in sorted(set(coef_puros.keys()).union(coef_m.keys()), key=lambda v: (not v.startswith("X"), v)):
            val_puro = coef_puros.get(var, 0)
            val_m = coef_m.get(var, 0)

            # Simplificar coeficientes de M
            if val_m != 0 and val_puro != 0:
                if abs(val_m) == 1:
                    resultado += f" + ({val_puro} {'+' if val_m >= 0 else '-'} M){var}"
                else:
                    resultado += f" + ({val_puro} {'+' if val_m >= 0 else '-'} {abs(val_m)}M){var}"
            elif val_m != 0:
                if abs(val_m) == 1:
                    resultado += f" + {'+' if val_m >= 0 else '-'} M{var}"
                else:
                    resultado += f" + {'+' if val_m >= 0 else '-'} {abs(val_m)}M{var}"
            elif val_puro != 0:
                resultado += f" + ({val_puro}){var}"

        self.constante_m = constante_m
        return resultado


    def _expandir_constante(self):
        suma = 0
        for expr in self.reemplazos.values():
            term = expr.strip("()")
            # Dividir por operadores, luego filtrar los términos que no contienen letras
            terminos = re.split(r'(?=[+-])', term)  # divide por signos + o -
            for t in terminos:
                t = t.strip()
                if not re.search(r'[A-Za-z]', t) and t:
                    suma += self._parse_num(t)
        
        # Simplificar el coeficiente de M
        suma = float(f"{suma:g}")  # Eliminar ceros decimales innecesarios
        if abs(suma) == 1.0:
            return "M" if suma >= 0 else "-M"
        return f"{suma}M"


    def _parse_num(self, txt):
        txt = txt.replace(' ', '')
        if txt in ('+', ''):
            return 1
        elif txt == '-':
            return -1
        try:
            return float(txt)
        except:
            return 0.0
