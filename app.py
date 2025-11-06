from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from functools import wraps # Necesario para los decoradores
import database as db

app = Flask(__name__)
# Llave secreta, necesaria para el manejo de sesiones (login) y mensajes flash.
app.secret_key = 'mi_llave_secreta_pos_12345'


# --- DECORADORES DE AUTENTICACIÓN Y ROLES ---

def login_required(f):
    """Decorador para asegurar que el usuario esté logueado."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ... (después de la función 'login_required') ...

def rol_required(rol_necesario):
    """Decorador para asegurar que el usuario tenga un rol específico."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'rol' not in session or session['rol'] != rol_necesario:
                flash(f'No tienes permiso de {rol_necesario.upper()} para acceder a esta función.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function  # <- Este return es para 'decorator'
    return decorator


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Maneja el inicio de sesión."""
    if 'logged_in' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = db.get_db_connection()
        user = conn.execute(
            'SELECT * FROM usuario WHERE username = ? AND password = ?', 
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session['logged_in'] = True
            session['username'] = user['username']
            session['rol'] = user['rol']
            session['user_id'] = user['id']  # <-- ¡CAMBIO IMPORTANTE! Guardamos el ID
            
            flash(f'Bienvenido(a), {user["username"]} ({user["rol"].capitalize()}).', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Cierra la sesión del usuario."""
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('rol', None)
    session.pop('user_id', None) # Limpiamos el ID de la sesión
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('login'))


# --- Rutas de la Interfaz (HTML) ---

@app.route('/')
@login_required # Ambos roles acceden
def index():
    """Página principal del POS (para facturar)."""
    return render_template('index.html')

@app.route('/stock')
@login_required # Ambos roles acceden
def stock():
    """Página para ver y administrar el stock."""
    conn = db.get_db_connection()
    productos = conn.execute('SELECT * FROM producto ORDER BY nombre').fetchall()
    conn.close()
    return render_template('stock.html', productos=productos)

@app.route('/ventas')
@login_required # Ambos roles acceden
def ventas():
    """Página para ver el historial de ventas."""
    conn = db.get_db_connection()
    historial = conn.execute('''
        SELECT v.id, v.fecha, v.total, p.nombre, vd.cantidad, vd.precio_unitario
        FROM venta v
        JOIN venta_detalle vd ON v.id = vd.id_venta
        JOIN producto p ON p.id = vd.id_producto
        ORDER BY v.fecha DESC
    ''').fetchall()
    conn.close()
    return render_template('ventas.html', historial=historial)


# --- (NUEVO) RUTAS DE GESTIÓN DE USUARIOS (SOLO ADMIN) ---

@app.route('/usuarios')
@login_required
@rol_required('administrador')
def gestor_usuarios():
    """Muestra la página de gestión de usuarios."""
    conn = db.get_db_connection()
    # Obtenemos todos los usuarios para listarlos
    usuarios = conn.execute('SELECT * FROM usuario ORDER BY username').fetchall()
    conn.close()
    return render_template('gestor_usuarios.html', usuarios=usuarios)

@app.route('/usuarios/agregar', methods=['POST'])
@login_required
@rol_required('administrador')
def agregar_usuario():
    """Agrega un nuevo usuario a la base de datos."""
    username = request.form['username']
    password = request.form['password']
    rol = request.form['rol']

    if not username or not password or not rol:
        flash('Todos los campos son obligatorios.', 'danger')
        return redirect(url_for('gestor_usuarios'))

    conn = db.get_db_connection()
    try:
        conn.execute(
            'INSERT INTO usuario (username, password, rol) VALUES (?, ?, ?)',
            (username, password, rol)
        )
        conn.commit()
        flash('¡Usuario agregado con éxito!', 'success')
    except conn.IntegrityError:
        flash('Error: El nombre de usuario ya existe.', 'danger')
    except Exception as e:
        flash(f'Error al agregar usuario: {str(e)}', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('gestor_usuarios'))

@app.route('/usuarios/eliminar/<int:id>')
@login_required
@rol_required('administrador')
def eliminar_usuario(id):
    """Elimina un usuario."""
    
    # Verificación para evitar que el admin se elimine a sí mismo
    if id == session['user_id']:
        flash('No puedes eliminar a tu propio usuario.', 'danger')
        return redirect(url_for('gestor_usuarios'))

    conn = db.get_db_connection()
    try:
        conn.execute('DELETE FROM usuario WHERE id = ?', (id,))
        conn.commit()
        flash('Usuario eliminado con éxito.', 'success')
    except Exception as e:
        flash(f'Error al eliminar usuario: {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('gestor_usuarios'))

# --- FIN DE RUTAS DE GESTIÓN DE USUARIOS ---


# --- Rutas de Lógica (CRUD Avanzado) ---

@app.route('/venta/eliminar/<int:id_venta>')
@login_required
@rol_required('administrador') # 🛑 SOLO ADMINISTRADOR puede eliminar ventas
def eliminar_venta(id_venta):
    """Elimina una venta y devuelve el stock."""
    conn = db.get_db_connection()
    try:
        detalles = conn.execute(
            'SELECT id_producto, cantidad FROM venta_detalle WHERE id_venta = ?', 
            (id_venta,)
        ).fetchall()

        for item in detalles:
            conn.execute(
                'UPDATE producto SET existencia = existencia + ? WHERE id = ?',
                (item['cantidad'], item['id_producto'])
            )
        
        conn.execute('DELETE FROM venta_detalle WHERE id_venta = ?', (id_venta,))
        conn.execute('DELETE FROM venta WHERE id = ?', (id_venta,))
        
        conn.commit()
        flash(f'Venta #{id_venta} eliminada. El stock ha sido restaurado.', 'success')
    
    except Exception as e:
        conn.rollback() 
        flash(f'Error al eliminar la venta: {str(e)}', 'danger')
    
    finally:
        conn.close()
        
    return redirect(url_for('ventas'))

@app.route('/producto/editar/<int:id>')
@login_required
@rol_required('administrador') # 🛑 SOLO ADMINISTRADOR
def editar_producto(id):
    """Muestra el formulario para editar un producto existente."""
    conn = db.get_db_connection()
    producto = conn.execute('SELECT * FROM producto WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    if producto is None:
        flash('Producto no encontrado.', 'warning')
        return redirect(url_for('stock'))
        
    return render_template('editar_producto.html', producto=producto)

@app.route('/producto/eliminar/<int:id>')
@login_required
@rol_required('administrador') # 🛑 SOLO ADMINISTRADOR
def eliminar_producto(id):
    """Elimina un producto del inventario."""
    conn = db.get_db_connection()
    try:
        conn.execute('DELETE FROM producto WHERE id = ?', (id,))
        conn.commit()
        flash('Producto eliminado con éxito.', 'success')
    except conn.IntegrityError:
        flash('Error: No se puede eliminar el producto, ya está incluido en una venta.', 'danger')
    except Exception as e:
        flash(f'Error al eliminar: {str(e)}', 'danger')
    conn.close()
    return redirect(url_for('stock'))


# --- Rutas de API (Para Formularios y JS) ---

@app.route('/api/producto/buscar/<string:codigo>')
@login_required # Ambos roles
def buscar_producto(codigo):
    """Busca un producto por su código de barras (para la página de Venta)."""
    conn = db.get_db_connection()
    producto = conn.execute('SELECT * FROM producto WHERE codigo_barras = ?', (codigo,)).fetchone()
    conn.close()
    if producto:
        return jsonify(dict(producto))
    else:
        return jsonify({'error': 'Producto no encontrado'}), 404

@app.route('/api/stock/agregar', methods=['POST'])
@login_required # ✅ Ambos roles pueden agregar productos
def agregar_producto():
    """Agrega un nuevo producto al stock (desde el formulario de Stock)."""
    codigo = request.form['codigo_barras']
    nombre = request.form['nombre']
    precio = float(request.form['precio_venta'])
    existencia = int(request.form['existencia'])

    conn = db.get_db_connection()
    try:
        conn.execute(
            'INSERT INTO producto (codigo_barras, nombre, precio_venta, existencia) VALUES (?, ?, ?, ?)',
            (codigo, nombre, precio, existencia)
        )
        conn.commit()
        flash('¡Producto agregado con éxito!', 'success')
    except conn.IntegrityError:
        flash('Error: El código de barras ya existe.', 'danger')
    conn.close()
    return redirect(url_for('stock'))

@app.route('/api/venta/registrar', methods=['POST'])
@login_required # Ambos roles
def registrar_venta():
    """Registra una nueva venta (desde la página de Venta)."""
    datos = request.json
    carrito = datos['carrito']
    total_venta = datos['total']

    conn = db.get_db_connection()
    try:
        cursor = conn.execute('INSERT INTO venta (total) VALUES (?)', (total_venta,))
        id_venta_nueva = cursor.lastrowid

        for item in carrito:
            conn.execute(
                'INSERT INTO venta_detalle (id_venta, id_producto, cantidad, precio_unitario) VALUES (?, ?, ?, ?)',
                (id_venta_nueva, item['id'], item['cantidad'], item['precio'])
            )
            conn.execute(
                'UPDATE producto SET existencia = existencia - ? WHERE id = ?',
                (item['cantidad'], item['id'])
            )
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'id_venta': id_venta_nueva})
    
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/producto/actualizar/<int:id>', methods=['POST'])
@login_required
@rol_required('administrador') # 🛑 SOLO ADMINISTRADOR
def actualizar_producto(id):
    """Actualiza la información del producto (desde el formulario de Edición)."""
    codigo = request.form['codigo_barras']
    nombre = request.form['nombre']
    precio = float(request.form['precio_venta'])
    existencia = int(request.form['existencia'])

    conn = db.get_db_connection()
    try:
        conn.execute(
            'UPDATE producto SET codigo_barras = ?, nombre = ?, precio_venta = ?, existencia = ? WHERE id = ?',
            (codigo, nombre, precio, existencia, id)
        )
        conn.commit()
        flash('¡Producto actualizado con éxito!', 'success')
    except conn.IntegrityError:
        flash('Error: Ese código de barras ya pertenece a otro producto.', 'danger')
    conn.close()
    return redirect(url_for('stock'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')