# Base de datos persistente (Simulada para esta fase)
# En producción esto leerá de un usuarios_db.json
USUARIOS_DB = {
    "admin": {"pass": "admin1978", "nombre": "Administrador Master", "rol": "Master Control"}
}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username', '').strip()
        pw = request.form.get('password', '').strip()
        
        if user in USUARIOS_DB and USUARIOS_DB[user]['pass'] == pw:
            session['user'] = user
            return redirect(url_for('index'))
        else:
            flash('Acceso Denegado')
    return render_template('login.html')

@app.route('/api/get_usuarios')
@login_required
def api_get_usuarios():
    return jsonify(USUARIOS_DB)

@app.route('/api/crear_usuario', methods=['POST'])
@login_required
def api_crear_usuario():
    data = request.json
    # Inyectamos en la base de datos viva
    USUARIOS_DB[data['user']] = {
        "pass": data['pass'],
        "nombre": data['nombre'],
        "rol": data['rol']
    }
    return jsonify({"status": "success"})
