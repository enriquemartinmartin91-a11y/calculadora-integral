from flask import Flask, render_template_string, request
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application, convert_xor
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io, base64

app = Flask(__name__)
x = sp.Symbol('x')
transformations = standard_transformations + (implicit_multiplication_application, convert_xor)

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Calculadora de Integrales IA</title>
<style>
body { font-family: sans-serif; max-width: 600px; margin: 20px auto; padding: 15px; background: #f5f7ff; }
.card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
input, select, button { padding: 12px; margin: 6px 0; border-radius: 10px; border: 1px solid #ccc; width: 100%; box-sizing: border-box; font-size:16px; }
button { background: #4f46e5; color: white; border: none; font-weight: bold; cursor: pointer; }
button:hover { background: #3730a3; }
.result { margin-top: 15px; background: #eef2ff; padding: 15px; border-radius: 10px; word-break: break-word; }
.tip { background:#fef9c3; padding:10px; border-radius:8px; margin-bottom:10px; font-size:14px; }
small { color: #666; }
</style>
</head>
<body>
<div class="card">
<h2>Calculadora de Integrales con IA</h2>
<div class="tip">✨ Ahora entiende español: prueba con "2x al cuadrado mas 5" o "seno de x por x"</div>
<form method="POST">
<label>Función:
<input type="text" name="funcion" value="{{funcion_str}}" placeholder="Ej: integral de x al cuadrado + 5">
</label>
<label>Tipo: 
<select name="tipo">
<option value="indefinida" {% if tipo=='indefinida' %}selected{% endif %}>Indefinida</option>
<option value="definida" {% if tipo=='definida' %}selected{% endif %}>Definida</option>
</select></label>
<div style="display:flex; gap:10px;">
<label style="flex:1">a: <input type="text" name="a" value="{{a}}"></label>
<label style="flex:1">b: <input type="text" name="b" value="{{b}}"></label>
</div>
<button type="submit">Calcular Integral</button>
</form>
{% if resultado %}
<div class="result"><b>Resultado:</b><br>{{resultado}}<br>
{% if grafica %}<img src="data:image/png;base64,{{grafica}}" style="width:100%; margin-top:10px; border-radius:10px;">{% endif %}
</div>
{% endif %}
{% if error %}
<div class="result" style="background:#fee2e2; color:#991b1b;"><b>Error:</b> {{error}}</div>
{% endif %}
</div>
</body>
</html>
"""

def traducir_natural(s):
    if not s: return s
    s = s.lower()
    s = s.replace("²", " al cuadrado ").replace("³", " al cubo ")
    dic = {
        "al cuadrado": "**2",
        "al cubo": "**3",
        "elevado al cuadrado": "**2",
        "cuadrada": "**2",
        "cúbica": "**3",
        "por": "*",
        "mas": "+",
        "más": "+",
        "menos": "-",
        "entre": "/",
        "sobre": "/",
        "seno": "sin",
        "sen": "sin",
        "coseno": "cos",
        "tangente": "tan",
        "raiz cuadrada de": "sqrt",
        "raiz de": "sqrt",
        "raiz": "sqrt",
        "logaritmo": "log",
        "exponencial": "exp",
        "integral de": "",
        "integral": "",
        "integrar": "",
        "de": " ",
        "la funcion": "",
        "funcion": ""
    }
    for k,v in dic.items():
        s = s.replace(k, v)
    s = s.replace("^", "**")
    return s.strip()

@app.route('/', methods=['GET','POST'])
def index():
    resultado = error = grafica = None
    funcion_str = "x al cuadrado mas 5"
    tipo = "indefinida"
    a_val = "0"
    b_val = "1"
    
    if request.method == 'POST':
        funcion_str = request.form.get('funcion','')
        tipo = request.form.get('tipo','indefinida')
        a_val = request.form.get('a','0')
        b_val = request.form.get('b','1')
        try:
            expr_str = traducir_natural(funcion_str)
            expr = parse_expr(expr_str, local_dict={'x': x, 'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan, 'sqrt': sp.sqrt, 'log': sp.log, 'exp': sp.exp}, transformations=transformations)
            
            if tipo == 'indefinida':
                res = sp.integrate(expr, x)
                resultado = f"∫ ({expr}) dx = {res} + C"
                f_lamb = sp.lambdify(x, expr, 'numpy')
                xs = np.linspace(-5, 5, 400)
                ys = f_lamb(xs)
            else:
                a = parse_expr(traducir_natural(a_val), transformations=transformations)
                b = parse_expr(traducir_natural(b_val), transformations=transformations)
                res = sp.integrate(expr, (x, a, b))
                try:
                    aprox = float(res.evalf())
                    resultado = f"∫[{a} a {b}] ({expr}) dx = {res} ≈ {aprox:.5f}"
                except:
                    resultado = f"∫[{a} a {b}] ({expr}) dx = {res}"
                f_lamb = sp.lambdify(x, expr, 'numpy')
                a_f = float(a.evalf()); b_f = float(b.evalf())
                xs = np.linspace(a_f-2, b_f+2, 400)
                ys = f_lamb(xs)

            fig, ax = plt.subplots()
            ax.plot(xs, ys, label=f"f(x)={expr}")
            if tipo == 'definida':
                xs_fill = np.linspace(float(a.evalf()), float(b.evalf()), 200)
                ax.fill_between(xs_fill, f_lamb(xs_fill), alpha=0.3)
            ax.grid(True, alpha=0.3); ax.legend()
            buf = io.BytesIO(); plt.savefig(buf, format='png', bbox_inches='tight'); plt.close(fig)
            buf.seek(0); grafica = base64.b64encode(buf.read()).decode()
            
        except Exception as e:
            error = f"No entendí '{funcion_str}'. Prueba con 'x^2+5' o 'x al cuadrado mas 5'. ({e})"
    
    return render_template_string(HTML, resultado=resultado, error=error, grafica=grafica, funcion_str=funcion_str, tipo=tipo, a=a_val, b=b_val)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
