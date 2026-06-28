from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'un_secreto_local_gratis')
DB_FILE = 'database.db'

# Configuración inicial de la Base de Datos integrada y gratuita
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Tabla de Usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            altura REAL NOT NULL,
            region TEXT NOT NULL
        )
    ''')
    # Tabla de Historial (Pesa e IMC constante)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            peso REAL NOT NULL,
            imc REAL NOT NULL,
            dieta_sugerida TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
    ''')
    conn.commit()
    conn.close()

# Alimentos Nativos por Región (Filtro Inteligente)
ALIMENTOS = {
    "andina": ["Quinua", "Kiwicha", "Olluco", "Papa nativa"],
    "costa": ["Camote", "Pescado azul", "Pallar", "Lúcuma"],
    "selva": ["Camu camu", "Yuca", "Plátano bellaco", "Sacha inchi"]
}

def generar_guia_ia(imc, region):
    ingredientes = ALIMENTOS.get(region, ["Frutas locales", "Verduras locales"])
    if imc < 18.5:
        return f"Enfoque Ganancia Muscular. Dieta rica en carbohidratos complejos usando {ingredientes[0]} y proteínas como {ingredientes[1]}."
    elif 18.5 <= imc < 25.0:
        return f"Enfoque Balanceado y Rendimiento. Mantén tus niveles consumiendo {ingredientes[0]} y energía limpia de {ingredientes[2]}."
    else:
        return f"Enfoque Control de Peso (Déficit). Desayunos ligeros basados en {ingredientes[0]} y reducción de grasas utilizando {ingredientes[1]}."

@app.route('/')
def index():
    if 'usuario_id' in session:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE id = ?", (session['usuario_id'],))
        user = cursor.fetchone()
        
        cursor.execute("SELECT peso, imc, dieta_sugerida, fecha FROM historial WHERE usuario_id = ? ORDER BY fecha DESC", (session['usuario_id'],))
        historial = cursor.fetchall()
        conn.close()
        return f"<h2>Panel de {user[1]}</h2><p>Región: {user[3]}</p><a href='/actualizar'>Actualizar Peso</a> | <a href='/logout'>Cerrar</a><h3>Historial:</h3>{str(historial)}"
    
    return '''
        <form action="/registro" method="post">
            Nombre: <input type="text" name="nombre"><br>
            Altura (en metros, ej: 1.70): <input type="number" step="0.01" name="altura"><br>
            Peso (kg): <input type="number" step="0.1" name="peso"><br>
            Región (costa/andina/selva): <input type="text" name="region"><br>
            <input type="submit" value="Comenzar Plan Gratis">
        </form>
    '''

@app.route('/registro', methods=['POST'])
def registro():
    nombre = request.form['nombre']
    altura = float(request.form['altura'])
    peso = float(request.form['peso'])
    region = request.form['region'].lower().strip()
    
    imc = round(peso / (altura ** 2), 1)
    dieta = generar_guia_ia(imc, region)
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO usuarios (nombre, altura, region) VALUES (?, ?, ?)", (nombre, altura, region))
    usuario_id = cursor.lastrowid
    cursor.execute("INSERT INTO historial (usuario_id, peso, imc, dieta_sugerida) VALUES (?, ?, ?, ?)", (usuario_id, peso, imc, dieta))
    conn.commit()
    conn.close()
    
    session['usuario_id'] = usuario_id
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
