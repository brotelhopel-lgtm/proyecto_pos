import sqlite3

def get_db_connection():
    """Crea una conexión a la base de datos SQLite."""
    conn = sqlite3.connect('pos.db')
    conn.row_factory = sqlite3.Row  # Permite acceder a las columnas por nombre
    return conn

def init_db():
    """Inicializa la base de datos (tablas de POS y tabla de usuarios)."""
    conn = get_db_connection()
    
    # 1. Inicializar tablas principales (producto, venta, venta_detalle) desde schema.sql
    try:
        # Usamos utf-8 para compatibilidad
        with open('schema.sql', 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        print("Tablas principales (stock, ventas) verificadas desde schema.sql.")
    except FileNotFoundError:
        print("ERROR: No se encontró 'schema.sql'. Asegúrate de que el archivo existe.")
        conn.close()
        return
    except Exception as e:
        print(f"Error al leer schema.sql: {e}")
        conn.close()
        return
        
    
    # 2. Crear la tabla de usuarios
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS usuario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                rol TEXT NOT NULL CHECK(rol IN ('administrador', 'vendedor'))
            );
        ''')
    except Exception as e:
        print(f"Error al crear la tabla 'usuario': {e}")
        conn.close()
        return

    # 3. Insertar usuarios iniciales (si no existen)
    try:
        conn.execute("INSERT INTO usuario (username, password, rol) VALUES (?, ?, ?)",
                    ('admin', '1234', 'administrador'))
        conn.execute("INSERT INTO usuario (username, password, rol) VALUES (?, ?, ?)",
                    ('vendedor1', 'pass', 'vendedor'))
        conn.commit()
        print("Usuarios iniciales creados: admin/1234 (admin) y vendedor1/pass (vendedor).")
    except sqlite3.IntegrityError:
        print("Usuarios iniciales ya existen. No se agregaron.")
        pass
    except Exception as e:
        print(f"Error al insertar usuarios: {e}")
        
    conn.close()
    print("Base de datos inicializada y lista.")

if __name__ == '__main__':
    # Si ejecutas este archivo directamente, crea/actualiza la BD
    init_db()