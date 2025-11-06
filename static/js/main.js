// Espera a que el documento HTML esté cargado
document.addEventListener('DOMContentLoaded', () => {

    // --- LÓGICA PARA LA PÁGINA DE VENTA (index.html) ---
    let carrito = [];

    const inputCodigo = document.getElementById('codigo-barras-input');
    const btnBuscar = document.getElementById('buscar-btn');
    const tablaCarrito = document.getElementById('carrito-tabla');
    const displayTotal = document.getElementById('total-display');
    const btnCobrar = document.getElementById('cobrar-btn');
    const divError = document.getElementById('mensaje-error');

    // Asignar eventos solo si los elementos existen (estamos en la página de Venta)
    if (btnBuscar) {
        btnBuscar.addEventListener('click', buscarProducto);
        inputCodigo.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault(); // Evita que el formulario se envíe
                buscarProducto();
            }
        });
    }

    if (btnCobrar) {
        btnCobrar.addEventListener('click', registrarVenta);
    }

    async function buscarProducto() {
        const codigo = inputCodigo.value;
        if (!codigo) return;

        divError.classList.add('d-none');

        try {
            const response = await fetch(`/api/producto/buscar/${codigo}`);
            
            if (!response.ok) {
                mostrarError('Producto no encontrado.');
                return;
            }

            const producto = await response.json();
            agregarAlCarrito(producto);
            inputCodigo.value = '';
            inputCodigo.focus();

        } catch (error) {
            console.error('Error:', error);
            mostrarError('Error al conectar con el servidor.');
        }
    }

    function agregarAlCarrito(producto) {
        const itemExistente = carrito.find(item => item.id === producto.id);

        if (itemExistente) {
            if (itemExistente.cantidad < producto.existencia) {
                itemExistente.cantidad++;
            } else {
                alert('No hay más stock disponible.');
            }
        } else {
            if (producto.existencia > 0) {
                carrito.push({
                    id: producto.id,
                    nombre: producto.nombre,
                    precio: producto.precio_venta,
                    cantidad: 1
                });
            } else {
                alert('Producto agotado.');
            }
        }
        actualizarVistaCarrito();
    }

    function actualizarVistaCarrito() {
        if (!tablaCarrito) return; // Salir si no estamos en la página de venta

        tablaCarrito.innerHTML = '';
        let totalGeneral = 0;

        carrito.forEach((item, index) => {
            const subtotal = item.cantidad * item.precio;
            totalGeneral += subtotal;

            const fila = document.createElement('tr');
            fila.innerHTML = `
                <td>${item.nombre}</td>
                <td>
                    <input type="number" class="form-control form-control-sm" value="${item.cantidad}" min="1" data-index="${index}" style="width: 70px;">
                </td>
                <td>Q${item.precio.toFixed(2)}</td>
                <td>Q${subtotal.toFixed(2)}</td>
                <td>
                    <button class="btn btn-danger btn-sm" data-index="${index}">X</button>
                </td>
            `;

            fila.querySelector('button').addEventListener('click', (e) => {
                quitarDelCarrito(e.target.dataset.index);
            });
            fila.querySelector('input').addEventListener('change', (e) => {
                actualizarCantidad(e.target.dataset.index, e.target.value);
            });

            tablaCarrito.appendChild(fila);
        });

        displayTotal.textContent = `Q${totalGeneral.toFixed(2)}`;
    }

    function quitarDelCarrito(index) {
        carrito.splice(index, 1);
        actualizarVistaCarrito();
    }

    function actualizarCantidad(index, nuevaCantidad) {
        const cantidad = parseInt(nuevaCantidad);
        if (cantidad > 0) {
            carrito[index].cantidad = cantidad;
        }
        actualizarVistaCarrito();
    }

    async function registrarVenta() {
        if (carrito.length === 0) {
            alert('El carrito está vacío.');
            return;
        }

        const total = carrito.reduce((sum, item) => sum + (item.cantidad * item.precio), 0);

        try {
            const response = await fetch('/api/venta/registrar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ carrito: carrito, total: total })
            });

            const resultado = await response.json();

            if (resultado.success) {
                alert(`Venta #${resultado.id_venta} registrada con éxito.`);
                carrito = [];
                actualizarVistaCarrito();
            } else {
                alert('Error al registrar la venta: ' + resultado.error);
            }

        } catch (error) {
            console.error('Error:', error);
            mostrarError('Error de conexión al registrar la venta.');
        }
    }

    function mostrarError(mensaje) {
        if (!divError) return;
        divError.textContent = mensaje;
        divError.classList.remove('d-none');
    }

    // --- LÓGICA PARA EL BUSCADOR EN LA PÁGINA DE STOCK (stock.html) ---
    
    const buscadorStock = document.getElementById('buscador-stock');
    const tablaInventario = document.getElementById('tabla-inventario');

    if (buscadorStock && tablaInventario) {
        buscadorStock.addEventListener('keyup', () => {
            const textoBusqueda = buscadorStock.value.toLowerCase();
            const filas = tablaInventario.getElementsByClassName('fila-producto');

            for (const fila of filas) {
                const textoFila = fila.textContent.toLowerCase();
                if (textoFila.includes(textoBusqueda)) {
                    fila.style.display = ''; 
                } else {
                    fila.style.display = 'none'; 
                }
            }
        });
    }

});