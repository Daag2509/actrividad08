import psycopg2
from playwright.sync_api import sync_playwright
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import dearpygui.dearpygui as dpg

# Conexión a la Base de Datos
def conectar_db():
    conn = psycopg2.connect(
        host="localhost",
        database="actividad08",
        user="postgres",
        password="30214055"
    )
    return conn

def crear_tabla():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id SERIAL PRIMARY KEY,
            descripcion TEXT NOT NULL,
            precio DECIMAL NOT NULL
        );
    """)
    conn.commit()
    cursor.close()
    conn.close()

def insertar_producto(descripcion, precio):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO productos (descripcion, precio) VALUES (%s, %s)", (descripcion, precio))
    conn.commit()
    cursor.close()
    conn.close()

def obtener_productos():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos;")
    productos = cursor.fetchall()
    cursor.close()
    conn.close()
    return productos

def eliminar_todos_productos():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM productos;")
    conn.commit()
    cursor.close()
    conn.close()

def extraer_datos(n_paginas):
    datos_productos = []

    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=True)
        pagina = navegador.new_page()

        for i in range(1, n_paginas + 1):
            url = f"https://listado.mercadolibre.com.ve/computacion/_Container_hcl-computacion-laptops_NoIndex_True?page={i}"
            pagina.goto(url)

            # Extraer descripciones y precios
            productos = pagina.query_selector_all('.ui-search-result__wrapper')
            for producto in productos:
                # Verifica si el selector para la descripción existe
                descripcion_elemento = producto.query_selector('.ui-search-item__title')
                if descripcion_elemento:
                    descripcion = descripcion_elemento.inner_text().strip()
                else:
                    descripcion = "Descripción no disponible"

                # Verifica si el selector para el precio existe
                precio_elemento = producto.query_selector('.price-tag-fraction')
                if precio_elemento:
                    precio_texto = precio_elemento.inner_text().strip().replace('.', '')
                    precio = float(precio_texto)
                else:
                    precio = 0.0  # O algún valor por defecto

                datos_productos.append({'descripcion': descripcion, 'precio': precio})

        navegador.close()

    return datos_productos

# Generación de PDF
def generar_pdf(productos):
    c = canvas.Canvas("productos.pdf", pagesize=letter)

    c.drawString(100, 750, "Listado de Productos")

    y_position = 730
    for producto in productos:
        c.drawString(100, y_position, f"Descripción: {producto[1]}, Precio: {producto[2]}")
        y_position -= 20

    c.save()

# Interfaz Gráfica con DearPyGui
def mostrar_productos():
   dpg.delete_item("ListaProductos", children=True)
   productos = obtener_productos()

   for producto in productos:
       dpg.add_text(f"ID: {producto[0]}, Descripción: {producto[1]}, Precio: {producto[2]}", parent="ListaProductos")

def eliminar_registros():
   eliminar_todos_productos()
   mostrar_productos()

def generar_pdf_gui():
   productos = obtener_productos()

   if productos:
       generar_pdf(productos)

def copiar_datos_gui(sender, app_data):
   n_paginas = dpg.get_value("NumeroPaginas")
   datos_nuevos = extraer_datos(n_paginas)

   for dato in datos_nuevos:
       insertar_producto(dato['descripcion'], dato['precio'])

   mostrar_productos()

dpg.create_context()

with dpg.window(label="MercadoLibre Scraper"):
   dpg.add_input_int(label="Número de Páginas", default_value=1, tag="NumeroPaginas")
   dpg.add_button(label="Copiar datos", callback=copiar_datos_gui)
   dpg.add_button(label="Eliminar Todos los Registros", callback=eliminar_registros)
   dpg.add_button(label="Generar PDF", callback=generar_pdf_gui)

   with dpg.child_window(label="ListaProductos", height=300):
       pass

dpg.create_viewport(title='Scraper MercadoLibre', width=600, height=400)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()

