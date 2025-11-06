-- Borra las tablas si ya existen, para empezar de cero
DROP TABLE IF EXISTS producto;
DROP TABLE IF EXISTS venta;
DROP TABLE IF EXISTS venta_detalle;

-- Tabla de Productos (Inventario / Stock)
CREATE TABLE producto (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_barras TEXT NOTIQUE UNIQUE,
    nombre TEXT NOT NULL,
    precio_venta REAL NOT NULL,
    existencia INTEGER NOT NULL DEFAULT 0
);

-- Tabla de Ventas (Facturas)
CREATE TABLE venta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total REAL NOT NULL
);

-- Tabla de Detalles de Venta (Qué productos se vendieron en cada factura)
CREATE TABLE venta_detalle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_venta INTEGER NOT NULL,
    id_producto INTEGER NOT NULL,
    cantidad INTEGER NOT NULL,
    precio_unitario REAL NOT NULL,
    FOREIGN KEY (id_venta) REFERENCES venta(id),
    FOREIGN KEY (id_producto) REFERENCES producto(id)
);

-- Insertar algunos productos de ejemplo
INSERT INTO producto (codigo_barras, nombre, precio_venta, existencia) VALUES
('7501001', 'Coca-Cola 600ml', 18.50, 100),
('7501002', 'Gansito', 15.00, 200),
('7501003', 'Papas Fritas 45g', 17.00, 150);