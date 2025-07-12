# 🧮 Programación Lineal App
Hecho para la materia de Optimización 2025-1. Proyecto final.

Aplicación de escritorio en Python que permite resolver problemas de optimización lineal utilizando el **método gráfico**, **Simplex** y **método de la M grande**, todo desde una interfaz visual construida con **PyQt5**. También incluye **análisis de sensibilidad**.

---

<img width="491" height="429" alt="image" src="https://github.com/user-attachments/assets/415893f0-5cff-4e95-9e8f-85f5769e4313" />


## 🎯 Características principales

- ✅ Resolución de funciones objetivo de **maximización o minimización**.
- ✅ Soporte para restricciones con `<=`, `>=`, `=`.
- ✅ Transformación automática a forma estándar.
- ✅ Método gráfico si hay solo 2 variables.
- ✅ Método Simplex paso a paso o completo.
- ✅ Soporte para **variables artificiales con M** (método de la M grande).
- ✅ Muestra explicaciones simbólicas (ej. `0.4 - 1.1M`) usando SymPy.
- ✅ Análisis de sensibilidad tras resolver el modelo.
- ✅ Interfaz clara y responsiva con PyQt5.

---

## 🧠 Estructura del proyecto

ProgramacionLineal/
├── core/
│ ├── analisisSensibilidad.py # Módulo para análisis postóptimo
│ ├── estandarizar.py # Pasa el modelo a forma estándar
│ ├── graficador_lineal.py # Método gráfico (2D)
│ ├── granM.py # Método de la M grande (Z simbólica)
│ ├── simplex.py # Resolución Simplex sin M
│ ├── simplexGranM.py # Resolución Simplex con M paso a paso
├── gui/
│ └── VentanaPrincipal.py # Interfaz principal en PyQt5
├── main.py # Punto de entrada de la aplicación
├── requirements.txt # Dependencias del proyecto

---

## 🧑‍💻 Ejemplo de uso

**Función objetivo:**
0.4x + 0.5y


**Restricciones:**
0.3x + 0.1y <= 2.7
0.5x + 0.5y = 6
0.6x + 0.4y >= 6
x, y >= 0


📌 El sistema reconocerá la necesidad de variables artificiales (`A`) y aplicará automáticamente el método de la M grande.

---

## 🛠️ Instalación y ejecución

### 1. Clona el repositorio

```bash
git clone https://github.com/FredyHoyos/ProgramacionLineal.git
cd ProgramacionLineal
2. Crea un entorno virtual (opcional pero recomendado)
python -m venv venv
venv\Scripts\activate   # En Windows
source venv/bin/activate  # En Linux/macOS
3. Instala dependencias
pip install -r requirements.txt
4. Ejecuta la aplicación
python main.py
📦 Requisitos
Python 3.9 o superior

PyQt5

matplotlib

numpy

sympy

scipy

📊 Capturas de pantalla
<img width="795" height="659" alt="image" src="https://github.com/user-attachments/assets/2d3b8e29-bf86-417b-9190-fbe2a8a104f2" />
<img width="655" height="461" alt="image" src="https://github.com/user-attachments/assets/f7d002e2-3cc4-41b3-a7f7-532aa28d99b9" />
<img width="596" height="427" alt="image" src="https://github.com/user-attachments/assets/0b92c092-204f-4c50-a3f6-cfc7fcd8488c" />


🧑 Autores
👤 Fredy Cárdenas
👤 Andres Corcho
🔗 GitHub

