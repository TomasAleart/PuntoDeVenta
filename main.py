import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import win32print
from PIL import Image, ImageTk
import win32ui
from datetime import datetime
import sys, os
import shutil 
import os
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import tempfile
import os
import subprocess
from datetime import datetime
from tkinter import messagebox
import difflib
from datetime import datetime, time


# --- (Tu función resource_path original está bien, la mantendremos) ---
def resource_path(relative_path):
    # ... (Tu código para resource_path) ...
    try:
        base_path = sys._MEIPASS
    except Exception:
        # MEJORADO: Usa el directorio del script, más robusto que solo "."
        base_path = os.path.abspath(os.path.dirname(__file__)) 
        
    return os.path.join(base_path, relative_path)

def conectar():
    # 1. Definir la ruta PERSISTENTE (AQUÍ USAS EL NOMBRE ÚNICO)
    app_folder_name = "SistemaMinimarketVE" 
    db_name = "productos.db"

    # Rutas absolutas
    app_data_dir = os.path.join(os.environ.get('APPDATA'), app_folder_name)
    persistent_db_path = os.path.join(app_data_dir, db_name)

    # LÍNEA DE DEBUGGING CRUCIAL
    print(f"DEBUG: Intentando conectar/escribir en la ruta: {persistent_db_path}") 

    # 2. Verificar si la base de datos persistente ya existe
    if not os.path.exists(persistent_db_path):
        
        # Lógica de PRIMERA EJECUCIÓN (Copia la plantilla)
        os.makedirs(app_data_dir, exist_ok=True) 
        source_db_path = resource_path(db_name)
        
        try:
            shutil.copyfile(source_db_path, persistent_db_path)
            print(f"DEBUG: Base de datos TEMPORAL copiada a ruta PERSISTENTE: {persistent_db_path}")
        except Exception as e:
            # Esto maneja fallos si PyInstaller no incluyó la DB original
            print(f"ERROR: Falló la copia de la DB plantilla. {e}")
            persistent_db_path = source_db_path # Fallback a ruta temporal (solo para ver el error)

    # 3. Conectarse a la ruta PERMANENTE
    conn = sqlite3.connect(persistent_db_path)
    return conn

def actualizar_stock_y_precio(codigo, nuevo_stock=None, nuevo_precio=None):
    """
    Si nuevo_stock no es None, fija el stock a ese valor (no suma).
    Si nuevo_precio no es None, fija el precio.
    """
    conn = conectar()
    cursor = conn.cursor()
    if nuevo_stock is not None:
        cursor.execute("UPDATE productos SET stock = ? WHERE codigo_barras = ?", (int(nuevo_stock), codigo))
    if nuevo_precio is not None:
        cursor.execute("UPDATE productos SET precio = ? WHERE codigo_barras = ?", (float(nuevo_precio), codigo))
    conn.commit()
    conn.close()

def buscar_producto(codigo):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, precio, stock, PrecioKilo FROM productos WHERE codigo_barras = ?", (codigo,))
    producto = cursor.fetchone()
    conn.close()
    return producto

def ajustar_stock(codigo, delta):
    """
    Suma (o resta) 'delta' unidades al stock actual del producto.
    delta puede ser negativo (para descontar) o positivo (para ingresar).
    """
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT stock FROM productos WHERE codigo_barras = ?", (codigo,))
    fila = cursor.fetchone()
    if not fila:
        messagebox.showerror("Error", "El código ingresado no existe en la base de datos.")
        conn.close()
        return 1

    if fila:
        stock_actual = fila[0]
        if delta == '':
            delta = "0"  
        stock_nuevo = stock_actual + int(delta)
        if stock_nuevo < 0:
            stock_nuevo = 0  # evita stock negativo
        cursor.execute("UPDATE productos SET stock = ? WHERE codigo_barras = ?", (stock_nuevo, codigo))
    conn.commit()
    conn.close()

def ajustar_precio(codigo, delta):

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT precio FROM productos WHERE codigo_barras = ?", (codigo,))
    fila = cursor.fetchone()
    if not fila:
        messagebox.showerror("Error", "El código ingresado no existe en la base de datos.")
        conn.close()
        return 1
    if delta == '':
        delta = "0"  
    precio_nuevo = int(delta)
    if precio_nuevo < 0:
        precio_nuevo = 0  # evita precio negativo
    cursor.execute("UPDATE productos SET precio = ? WHERE codigo_barras = ?", (precio_nuevo, codigo))
    conn.commit()
    conn.close()

def ajustar_precioKg(codigo, delta):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT PrecioKilo FROM productos WHERE codigo_barras = ?", (codigo,))
    fila = cursor.fetchone()
    if not fila:
        messagebox.showerror("Error", "El código ingresado no existe en la base de datos.")
        conn.close()
        return 1
    if delta == '':
        delta = "0"  
    preciokg_nuevo = int(delta)
    if preciokg_nuevo < 0:
        preciokg_nuevo = 0  # evita precio negativo
    cursor.execute("UPDATE productos SET PrecioKilo = ? WHERE codigo_barras = ?", (preciokg_nuevo, codigo))
    conn.commit()
    conn.close()

def obtener_productos():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT codigo_barras, nombre, precio, PrecioKilo, stock FROM productos")
    productos = cursor.fetchall()
    conn.close()
    return productos

def agregar_producto(codigo, nombre, precio, stock, precioKg):
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO productos VALUES (?, ?, ?, ?, ?)", (codigo, nombre, precio, stock, precioKg))
        conn.commit()
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Ya existe un producto con ese código de barras.")
    conn.close()

def agregar_usuario(nombre, contraseña, jerarquia):    
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (usuario, contrasena, jerarquia) VALUES (?, ?, ?)", (nombre, contraseña, jerarquia))
        conn.commit()
        messagebox.showinfo("Éxito", f"Usuario '{nombre}' agregado correctamente.")
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Ya existe un usuario con ese nombre.")
    conn.close()

def registrar_venta(usuario):
    conn = conectar()
    cursor = conn.cursor()

    # ================= TOTAL =================
    subtotal = sum(item["subtotal"] for item in carrito.values())

    try:
        desc = float(entrada_descuento.get())
    except ValueError:
        desc = 0.0

    desc = max(0, min(desc, 100))
    total_final = subtotal * (1 - desc / 100)

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ================= OBTENER CAJA REAL ACTUAL =================

    # Última venta
    cursor.execute("""
        SELECT fecha, caja_inicial + total
        FROM ventas
        ORDER BY fecha DESC
        LIMIT 1
    """)
    venta = cursor.fetchone()

    # Última caja (inicial o movimiento)
    cursor.execute("""
        SELECT fecha_inicio, caja_final
        FROM caja
        ORDER BY fecha_inicio DESC
        LIMIT 1
    """)
    caja = cursor.fetchone()

    if venta and caja:
        # elegir el evento más reciente
        if venta[0] > caja[0]:
            caja_actual = venta[1]
        else:
            caja_actual = caja[1]
    elif venta:
        caja_actual = venta[1]
    elif caja:
        caja_actual = caja[1]
    else:
        caja_actual = 0

    # ================= INSERTAR VENTA =================
    cursor.execute("""
        INSERT INTO ventas (fecha, total, vendedor, caja_inicial)
        VALUES (?, ?, ?, ?)
    """, (fecha, total_final, usuario, caja_actual))

    id_venta = cursor.lastrowid

    # ================= DETALLE =================
    for item in carrito.values():
        cursor.execute("""
            INSERT INTO ventas_detalle
            (id_venta, codigo, nombre, cantidad, peso,
             precio_unitario, subtotal, promo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            id_venta,
            item["codigo"],
            item["nombre"],
            item["cantidad"],
            item["peso"],
            item["precio_unitario"],
            item["subtotal"],
            item.get("promo")
        ))

    conn.commit()
    conn.close()

# ======================================
# GESTIÓN DE STOCK Y PRECIOS
# ======================================
def abrir_gestion_stock(jerarquia):
    ventana_stock = tk.Toplevel(ventana)
    ventana_stock.state("zoomed")
    ventana_stock.title("Gestión de Stock y Precios")
    ventana_stock.geometry("780x600")

    frame_tablaG = tk.Frame(ventana_stock)
    frame_tablaG.pack(fill="both", expand=True)

    tk.Label(ventana_stock, text="GESTIÓN DE STOCK Y PRECIOS", font=("Arial", 16, "bold")).pack(pady=10)

    columnas = ("codigo", "nombre", "precio", "precio x kg", "stock")
    tabla = ttk.Treeview(frame_tablaG, columns=columnas, show="headings", height=14)
    for col in columnas:
        tabla.heading(col, text=col.capitalize())
        tabla.column(col, width=150)
    tabla.pack(side= "left", fill="both", expand=True, padx=10, pady=10)

    scrollbar = ttk.Scrollbar(
        frame_tablaG,
        orient="vertical",
        command=tabla.yview
    )

    scrollbar.pack(side="right", fill="y")

    tabla.configure(yscrollcommand=scrollbar.set)

    frame_busqueda = tk.Frame(ventana_stock)
    frame_busqueda.pack(fill="x", padx=10)

    tk.Label(frame_busqueda, text="Buscar:", font=("Arial", 12)).pack(side="left")

    entry_buscar = tk.Entry(frame_busqueda, font=("Arial", 12), width=30)
    entry_buscar.pack(side="right", padx=5)

    def refrescar():
        tabla.delete(*tabla.get_children())
        for prod in obtener_productos():
            tabla.insert("", "end", values=prod)

    refrescar()

    frame_actualizar = tk.LabelFrame(ventana_stock, text="Actualizar producto existente", font=("Arial", 12), padx=10, pady=10)
    frame_actualizar.pack(fill="x", padx=10, pady=5)

    tk.Label(frame_actualizar, text="Código:", font=("Arial", 12)).grid(row=0, column=0)
    entry_cod_upd = tk.Entry(frame_actualizar, font=("Arial", 12))
    entry_cod_upd.grid(row=0, column=1, padx=5)
    tk.Label(frame_actualizar, text="Nuevo precio:", font=("Arial", 12)).grid(row=0, column=2)
    entry_precio_upd = tk.Entry(frame_actualizar, font=("Arial", 12), width=10)
    entry_precio_upd.grid(row=0, column=3, padx=5)
    tk.Label(frame_actualizar, text="Editar stock:", font=("Arial", 12)).grid(row=0, column=4)
    entry_stock_upd = tk.Entry(frame_actualizar, font=("Arial", 12), width=10)
    entry_stock_upd.grid(row=0, column=5, padx=5)
    tk.Label(frame_actualizar, text="Nuevo Precio X Kg:", font=("Arial", 12)).grid(row=0, column=6)
    entry_PrecioKg_upd = tk.Entry(frame_actualizar, font=("Arial", 12), width=10)
    entry_PrecioKg_upd.grid(row=0, column=7, padx=5)

    def actualizar():
        codigo = entry_cod_upd.get().strip()
        nuevo_precio = entry_precio_upd.get().strip()
        nuevo_stock = entry_stock_upd.get().strip()
        nuevo_PrecioKg = entry_PrecioKg_upd.get().strip()

        if not codigo:
            messagebox.showwarning("Atención", "Ingrese un código de producto.")   
            return
        try:
            precio_val = float(nuevo_precio) if nuevo_precio else None
            stock_val = int(nuevo_stock) if nuevo_stock else None
            PrecioKgVal = float(nuevo_PrecioKg) if nuevo_PrecioKg else None 
        except ValueError:
            messagebox.showerror("Error", "Valores inválidos.")
            return
        if precio_val is None and stock_val is None and PrecioKgVal is None:
            messagebox.showwarning("Atención", "Ingrese al menos un valor a actualizar.")
            return
        if stock_val is not None:
            if jerarquia == "admin":
                ban1 = ajustar_stock(codigo, nuevo_stock)
                if ban1 != 1:
                    messagebox.showinfo("Éxito", "Stock actualizado correctamente.")
            else:
                messagebox.showwarning("Atención", "No tienes permisos para editar el stock.")
                return

        if precio_val is not None:
           ban2 = ajustar_precio(codigo, nuevo_precio)
           if ban2 != 1:
               messagebox.showinfo("Éxito", "Precio actualizado correctamente.")
        if PrecioKgVal is not None:
            ban3 = ajustar_precioKg(codigo, nuevo_PrecioKg)
            if ban3 != 1:
                messagebox.showinfo("Éxito", "Precio X Kg actualizado correctamente.")
        refrescar()
        entry_cod_upd.delete(0, tk.END)
        entry_precio_upd.delete(0, tk.END)
        entry_stock_upd.delete(0, tk.END)
        entry_PrecioKg_upd.delete(0, tk.END)

    tk.Button(frame_actualizar, text="Actualizar", font=("Arial", 12), command=actualizar, bg="#2196F3", fg="white").grid(row=0, column=8, padx=10)

    frame_agregar = tk.LabelFrame(ventana_stock, text="Agregar/Eliminar producto", font=("Arial", 12), padx=10, pady=10)
    frame_agregar.pack(fill="x", padx=10, pady=10)

    # permitir expansión de columnas para grid
    for i in range(12):
        frame_agregar.columnconfigure(i, weight=1)


    tk.Label(frame_agregar, text="Código:", font=("Arial", 12)).grid(row=0, column=0)
    entry_cod_new = tk.Entry(frame_agregar, font=("Arial", 12))
    entry_cod_new.grid(row=0, column=1, padx=5)
    tk.Label(frame_agregar, text="Nombre:", font=("Arial", 12)).grid(row=0, column=2)
    entry_nom_new = tk.Entry(frame_agregar, font=("Arial", 12))
    entry_nom_new.grid(row=0, column=3, padx=5)
    tk.Label(frame_agregar, text="Precio:", font=("Arial", 12)).grid(row=1, column=0)
    entry_precio_new = tk.Entry(frame_agregar, font=("Arial", 12))
    entry_precio_new.grid(row=1, column=1, padx=5)
    tk.Label(frame_agregar, text="Stock:", font=("Arial", 12)).grid(row=1, column=2)
    entry_stock_new = tk.Entry(frame_agregar, font=("Arial", 12))
    entry_stock_new.grid(row=1, column=3, padx=5)
    tk.Label(frame_agregar, text="Precio Kilo:", font=("Arial", 12)).grid(row=2, column=0)
    entry_precioKg_new = tk.Entry(frame_agregar, font=("Arial", 12))
    entry_precioKg_new.grid(row=2, column=1, padx=5)
    tk.Label(frame_agregar, text="Eliminar código:", font=("Arial", 12)).grid(row=0, column=4, padx=5)
    entry_eliminar_codigo = tk.Entry(frame_agregar, font=("Arial", 12), width=12)
    entry_eliminar_codigo.grid(row=0, column=5, padx=5)

    def buscar_productos(*args):
        texto = entry_buscar.get().strip().lower()

        # Si está vacío → refrescar todo
        if texto == "":
            refrescar()
            return

        productos = obtener_productos()

        # Filtrar los que coinciden parcialmente
        filtrados = []
        for prod in productos:
            codigo, nombre, precio, precio_kg, stock = prod
            campo_completo = f"{codigo} {nombre}".lower()

            if texto in campo_completo:
                # Calcular la similitud
                score = difflib.SequenceMatcher(None, texto, campo_completo).ratio()
                filtrados.append((score, prod))

        # Ordenar por score descendente (más similares arriba)
        filtrados.sort(key=lambda x: x[0], reverse=True)

        # Limpiar tabla
        tabla.delete(*tabla.get_children())

        # Insertar
        for score, prod in filtrados:
            tabla.insert("", "end", values=prod)
    
    entry_buscar.bind("<KeyRelease>", buscar_productos)
    entry_buscar.bind("<Return>", buscar_productos)


    def agregar_nuevo():
        cod = entry_cod_new.get().strip()
        nom = entry_nom_new.get().strip()
        pre_str = entry_precio_new.get().strip()
        preKg_str = entry_precioKg_new.get().strip()
        stk_str = entry_stock_new.get().strip()

    # --- BLOQUE DE DEBUGGING A AÑADIR ---
        print("--- DEBUG INPUTS ---")
        print(f"COD: '{cod}' (Longitud: {len(cod)})")
        print(f"NOM: '{nom}' (Longitud: {len(nom)})")
        print(f"PRECIO: '{pre_str}' (Longitud: {len(pre_str)})")
        print(f"P X KG: '{preKg_str}' (Longitud: {len(preKg_str)})")
        print(f"STOCK: '{stk_str}' (Longitud: {len(stk_str)})")
        print("--------------------")
        # ------------------------------------

        if not cod or not nom or not pre_str or not stk_str:
            messagebox.showwarning("Atención", "Complete todos los campos.")
            return
        try:
            pre = float(pre_str)
            stk = int(stk_str)
        except ValueError:
            messagebox.showerror("Error", "Precio o stock no válidos.")
            return
        agregar_producto(cod, nom, pre, stk, preKg_str)
        messagebox.showinfo("Éxito", f"Producto '{nom}' agregado correctamente.")
        refrescar()
        entry_cod_new.delete(0, tk.END)
        entry_nom_new.delete(0, tk.END)
        entry_precio_new.delete(0, tk.END)
        entry_stock_new.delete(0, tk.END)
        entry_precioKg_new.delete(0, tk.END)

    def eliminar_producto_por_codigo(codigo):
        if not codigo:
            messagebox.showerror("Error", "Debe ingresar un código.")
            return
        
        conn = conectar()
        c = conn.cursor()

        c.execute("SELECT * FROM productos WHERE codigo_barras = ?", (codigo,))
        if not c.fetchone():
            messagebox.showerror("Error", "El producto no existe.")
            conn.close()
            return

        c.execute("DELETE FROM productos WHERE codigo_barras = ?", (codigo,))
        conn.commit()
        conn.close()

        messagebox.showinfo("Éxito", "Producto eliminado correctamente.")
        refrescar()
        entry_eliminar_codigo.delete(0, tk.END)

    tk.Button(frame_agregar, text="Agregar producto", font=("Arial", 12), command=agregar_nuevo, bg="#2196F3", fg="white").grid(row=2, column=3, columnspan=1, pady=10)
    btn_eliminar_producto = tk.Button(frame_agregar, text="Eliminar", font=("Arial", 12),
                                    command=lambda: eliminar_producto_por_codigo(entry_eliminar_codigo.get()))
    btn_eliminar_producto.grid(row=2, column=5, padx=10)

    tk.Button(frame_agregar, text="Gestionar Promociones", font=("Arial", 12), command=abrir_gestion_promos, bg="#2196F3", fg="white").grid(row=1, column=9)

    frame_agregar_us = tk.LabelFrame(ventana_stock, text="Agregar nuevo usuario", font=("Arial", 12), padx=10, pady=10)
    frame_agregar_us.pack(fill="x", padx=10, pady=10)

    if jerarquia == "admin":
        tk.Label(frame_agregar_us,text="Eliminar usuario:", font=("Arial", 12)).grid(row=0, column=6, padx=5)

        entry_user_delete = tk.Entry(frame_agregar_us, font=("Arial", 12))
        entry_user_delete.grid(row=0, column=7, padx=5)

        btn_delete_user = tk.Button(frame_agregar_us, text="Eliminar", font=("Arial", 12),
                                    command=lambda: eliminar_usuario(entry_user_delete.get()))
        btn_delete_user.grid(row=2, column=7, padx=5)

    tk.Label(frame_agregar_us, text="Nombre:", font=("Arial", 12)).grid(row=0, column=0)
    entry_nomb_new = tk.Entry(frame_agregar_us, font=("Arial", 12))
    entry_nomb_new.grid(row=0, column=1, padx=5)
    tk.Label(frame_agregar_us, text="Contraseña:", font=("Arial", 12)).grid(row=0, column=2)
    entry_contra_new = tk.Entry(frame_agregar_us, font=("Arial", 12))
    entry_contra_new.grid(row=0, column=3, padx=5)
    tk.Label(frame_agregar_us, text="Jerarquia:", font=("Arial", 12)).grid(row=1, column=0)
    entry_jerar_new = tk.Entry(frame_agregar_us, font=("Arial", 12))
    entry_jerar_new.grid(row=1, column=1, padx=5)

    def agregar_nuevo_Usuario(jerarquia):
        nom = entry_nomb_new.get().strip()
        contra = entry_contra_new.get().strip()
        jerar = entry_jerar_new.get().strip()
        try:
            nomb = str(entry_nomb_new.get())
            contr = int(entry_contra_new.get())
            jerarq = str(entry_jerar_new.get())
        except ValueError:
            messagebox.showerror("Error", "valores no válidos.")
            return
        if not contra or not nom or not jerar:
            messagebox.showwarning("Atención", "Complete todos los campos.")
            return
        if jerarquia == "admin":
            agregar_usuario(nomb, contr, jerarq)
        else:
            messagebox.showwarning("Atención", "No tienes permisos para agregar usuarios.")
            return
        refrescar()
        entry_cod_new.delete(0, tk.END)
        entry_nomb_new.delete(0, tk.END)
        entry_precio_new.delete(0, tk.END)
        entry_stock_new.delete(0, tk.END)

    def eliminar_usuario(nombre):
        if not nombre:
            messagebox.showerror("Error", "Debe ingresar un nombre para eliminar.")
            return
        
        if nombre == "admin":
            messagebox.showerror("Error", "No puedes eliminar al usuario administrador principal.")
            return
        
        conn = conectar()
        c = conn.cursor()

        c.execute("SELECT * FROM usuarios WHERE usuario=?", (nombre,))
        if not c.fetchone():
            messagebox.showerror("Error", "El usuario no existe.")
            conn.close()
            return

        c.execute("DELETE FROM usuarios WHERE usuario=?", (nombre,))
        conn.commit()
        conn.close()
        entry_user_delete.delete(0, tk.END)
        messagebox.showinfo("Éxito", "Usuario eliminado correctamente.")

    tk.Button(frame_agregar_us, text="Agregar usuario", font=("Arial", 12), command=lambda: agregar_nuevo_Usuario(jerarquia), bg="#2196F3", fg="white").grid(row=2, column=2, columnspan=1, pady=10)
# ======================================
# ======================================
# FUNCIONES DE IMPRESIÓN (Windows)
def generar_ticket_pdf(texto):
    # Crear archivo PDF temporal
    temp_dir = tempfile.gettempdir()
    pdf_path = os.path.join(temp_dir, "ticket_minimarket.pdf")

    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    y = height - 40  # margen superior

    for linea in texto.split("\n"):
        c.drawString(40, y, linea)
        y -= 14  # espacio entre líneas

        if y < 40:  # salto de página
            c.showPage()
            y = height - 40

    c.save()
    return pdf_path

import subprocess

def imprimir_con_hp(pdf_path, printer_name):
    comando = [
        "powershell",
        "-Command",
        f"(New-Object -ComObject Shell.Application).Namespace(0).ParseName('{pdf_path}').InvokeVerb('print')"
    ]

    try:
        subprocess.run(comando, check=True)
        return True
    except Exception as e:
        print("ERROR PS:", e)
        return False

import os
import tempfile
from datetime import datetime
from tkinter import messagebox

# Las variables 'carrito' y 'entrada_descuento' deben estar definidas 
# en el ámbito global o ser pasadas como argumentos.
# La función 'calcular_totales_ticket' se mantiene como la proporcionaste.

def calcular_totales_ticket():
    # Depende de la variable global 'carrito' y 'entrada_descuento'
    subtotal = sum(item["precio"] * item["cantidad"] for item in carrito.values())

    try:
        descuento_porcentaje = float(entrada_descuento.get())
    except:
        descuento_porcentaje = 0

    descuento = subtotal * (descuento_porcentaje / 100)
    total_final = subtotal - descuento

    return subtotal, descuento, total_final


def imprimir_ticket():
    ahora = datetime.now()
    fecha = ahora.strftime("%d/%m/%Y")
    hora = ahora.strftime("%H:%M")

    lineas = []
    lineas.append("-----------------------------------------------")
    lineas.append("             MINIMARKET V&E")
    lineas.append("-----------------------------------------------")
    lineas.append("               Ticket de Venta")
    lineas.append(f"Fecha: {fecha}  Hora: {hora}")
    lineas.append("-----------------------------------------------")
    lineas.append("Cant/Peso  Descripción            Precio     Subtotal")
    lineas.append("-----------------------------------------------")

    # ================= DETALLE =================
    for item in carrito.values():

        nombre = item["nombre"][:22]  # recorte seguro
        subtotal = item["subtotal"]

        if item["tipo"] == "unidad":
            cant_txt = f"{item['cantidad']}"
            precio_txt = f"${item['precio_unitario']:.2f}"

        else:  # peso
            cant_txt = f"{item['peso']:.3f}kg"
            precio_txt = f"${item['precio_unitario']:.2f}/kg"

        linea = (
            f"{cant_txt:<10}"
            f"{nombre:<22}"
            f"{precio_txt:>10}"
            f"{subtotal:>11.2f}"
        )
        lineas.append(linea)
        # si tiene promoción aplicada la mostramos
        if item.get("promo"):
            lineas.append(f"   PROMO: {item['promo']}")


    lineas.append("-----------------------------------------------")

    # ================= TOTALES =================
    subtotal = sum(item["subtotal"] for item in carrito.values())

    try:
        desc = float(entrada_descuento.get())
    except ValueError:
        desc = 0.0

    desc = max(0, min(desc, 100))
    descuento = subtotal * (desc / 100)
    total_final = subtotal - descuento

    lineas.append(f"Subtotal:{subtotal:>37.2f}")
    lineas.append(f"Descuento:{descuento:>36.2f}")
    lineas.append(f"TOTAL:{total_final:>40.2f}")
    lineas.append("-----------------------------------------------")
    lineas.append("DOCUMENTO NO VALIDO COMO FACTURA")
    lineas.append("\n\n\n")

    contenido_final = "\r\n".join(lineas)

    # ================= GUARDAR TXT =================
    txt_path = os.path.join(tempfile.gettempdir(), "ticket_minimarket.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(contenido_final)

    # ================= ABRIR EN BLOC DE NOTAS =================
    try:
        os.startfile(txt_path)
        messagebox.showinfo(
            "Ticket abierto",
            "El ticket se abrió en el Bloc de Notas.\nUse Archivo → Imprimir o Ctrl + P."
        )
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir el ticket:\n{e}")


# ======================================
# FUNCIONES DE INFORME
# ======================================
def imprimir_informe(tree, total_ventas):
    """
    Genera un archivo TXT con el informe completo (ventas + caja)
    y lo abre en el Bloc de Notas para impresión manual.
    """

    lineas = []
    lineas.append("=" * 61)
    lineas.append("                    INFORME DE MOVIMIENTOS")
    lineas.append("=" * 61)
    lineas.append("")
    lineas.append(
    f"{'Fecha y hora':<20} {'Tipo':<6} {'Usuario':<12} "
    f"{'Detalle':<22} {'Importe':>12}"
    )
    lineas.append("-" * 61)

    # Recorrer TreeView
    for item_id in tree.get_children():
        fecha, tipo, detalle, usuario, importe = tree.item(item_id)["values"]

        linea = (
            f"{fecha:<20} "
            f"{tipo:<6} "
            f"{str(usuario):<12} "
            f"{detalle:<22} "
            f"{float(importe):>12.2f}"
        )
        lineas.append(linea)

    lineas.append("-" * 61)
    lineas.append(f"TOTAL VENTAS: ${total_ventas:.2f}")
    lineas.append("=" * 61)
    lineas.append("\n")

    contenido = "\n".join(lineas)

    # Guardar TXT temporal
    txt_path = os.path.join(
        tempfile.gettempdir(),
        "informe_minimarket.txt"
    )

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(contenido)

    # Abrir en Bloc de Notas
    try:
        os.startfile(txt_path)
        messagebox.showinfo(
            "Informe abierto",
            "El informe se abrió en el Bloc de Notas.\n"
            "Use Archivo → Imprimir o Ctrl+P."
        )
    except Exception as e:
        messagebox.showerror(
            "Error",
            f"No se pudo abrir el informe:\n{e}"
        )

def ver_detalle(tree):
    seleccion = tree.selection()
    if not seleccion:
        messagebox.showerror("Error", "Seleccione una venta para ver el detalle.")
        return

    item = tree.item(seleccion[0])
    fecha, tipo, detalle, usuario, importe = item["values"]

    if tipo != "VENTA":
        messagebox.showwarning(
            "Atención",
            "Solo se puede ver el detalle de una venta.\n"
            "Los movimientos de caja no tienen detalle."
        )
        return

    conn = conectar()
    c = conn.cursor()

    # Obtener ID real de la venta
    c.execute("""
        SELECT id, total
        FROM ventas
        WHERE fecha = ?
        LIMIT 1
    """, (fecha,))
    row = c.fetchone()

    if not row:
        conn.close()
        messagebox.showerror("Error", "No se pudo encontrar la venta.")
        return

    id_venta, total = row

    ventana_det = tk.Toplevel()
    ventana_det.title("Detalle de Venta")
    ventana_det.geometry("1200x450")
    ventana_det.minsize(950, 450)

    tk.Label(ventana_det, text=f"Fecha: {fecha}", font=("Arial", 14)).pack(pady=5)
    tk.Label(
        ventana_det,
        text=f"Total: ${float(total):.2f}",
        font=("Arial", 14, "bold")
    ).pack(pady=5)

    tree_det = ttk.Treeview(
        ventana_det,
        columns=("codigo", "nombre", "cantidad", "precio", "subtotal", "promo"),
        show="headings"
    )
    tree_det.pack(fill="both", expand=True)

    tree_det.heading("codigo", text="Código")
    tree_det.heading("nombre", text="Nombre")
    tree_det.heading("cantidad", text="Cantidad")
    tree_det.heading("precio", text="Precio")
    tree_det.heading("subtotal", text="Subtotal")
    tree_det.heading("promo", text="Promo")

    tree_det.column("promo", width=130)
    tree_det.column("cantidad", anchor="center")
    tree_det.column("precio", anchor="e")
    tree_det.column("subtotal", anchor="e")

    # ================= DETALLES =================
    c.execute("""
        SELECT codigo, nombre, cantidad, peso, precio_unitario, subtotal, promo
        FROM ventas_detalle
        WHERE id_venta = ?
    """, (id_venta,))

    for codigo, nombre, cantidad, peso, precio_unit, subtotal, promo in c.fetchall():

        # Producto por peso (cantidad decimal)
        if peso is not None:
            cantidad_txt = f"{peso:.3f} kg"
            precio_txt = f"${precio_unit:.2f} x kg"
        else:
            cantidad_txt = str(int(cantidad))
            precio_txt = f"${precio_unit:.2f}"

        tree_det.insert(
            "",
            "end",
            values=(
                codigo,
                nombre,
                cantidad_txt,
                precio_txt,
                f"${subtotal:.2f}",
                promo if promo else ""
            )
        )




    conn.close()

def abrir_informe():
    ventana_inf = tk.Toplevel()
    ventana_inf.title("Informe de Ventas Mensuales")
    ventana_inf.geometry("650x390")

    frame = tk.Frame(ventana_inf)
    frame.pack(pady=20)

    tk.Label(frame, text="Hora desde (HH:MM):", font=("Arial", 14)).grid(
        row=0, column=0, padx=10, pady=10, sticky="e"
    )
    entry_hora_desde = tk.Entry(frame, font=("Arial", 14), width=8)
    entry_hora_desde.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(frame, text="Hora hasta (HH:MM):", font=("Arial", 14)).grid(
        row=0, column=2, padx=10, pady=10, sticky="e"
    )
    entry_hora_hasta = tk.Entry(frame, font=("Arial", 14), width=8)
    entry_hora_hasta.grid(row=0, column=3, padx=10, pady=5)


    tk.Label(frame, text="Día desde (DD):", font=("Arial", 14)).grid(row=1, column=0, padx=10, pady=10, sticky="e")
    entry_dia_desde = tk.Entry(frame, font=("Arial", 14), width=8)
    entry_dia_desde.grid(row=1, column=1, padx=10, pady=5)

    tk.Label(frame, text="Día hasta (DD):", font=("Arial", 14)).grid(row=1, column=2, padx=10, pady=10, sticky="e")
    entry_dia_hasta = tk.Entry(frame, font=("Arial", 14), width=8)
    entry_dia_hasta.grid(row=1, column=3, padx=10, pady=5)

    tk.Label(frame, text="Mes desde (MM):", font=("Arial", 14)).grid(row=2, column=0, padx=10, pady=10, sticky="e")
    entry_mes_desde = tk.Entry(frame, font=("Arial", 14), width=8)
    entry_mes_desde.grid(row=2, column=1, pady=10)

    tk.Label(frame, text="Mes hasta (MM):", font=("Arial", 14)).grid(row=2, column=2, padx=10, pady=10, sticky="e")
    entry_mes_hasta = tk.Entry(frame, font=("Arial", 14), width=8)
    entry_mes_hasta.grid(row=2, column=3, pady=10)

    tk.Label(frame, text="Año desde (YYYY):", font=("Arial", 14)).grid(row=3, column=0, padx=10, pady=10, sticky="e")
    entry_anio_desde = tk.Entry(frame, font=("Arial", 14), width=8)
    entry_anio_desde.grid(row=3, column=1, pady=10)

    tk.Label(frame, text="Año hasta (YYYY):", font=("Arial", 14)).grid(row=3, column=2, padx=10, pady=10, sticky="e")
    entry_anio_hasta = tk.Entry(frame, font=("Arial", 14), width=8)
    entry_anio_hasta.grid(row=3, column=3, pady=10)

    tk.Label(frame, text="Vendedor:", font=("Arial", 14)).grid(row=4, column=0, padx=10, pady=10, sticky="e")
    entry_vendedor = tk.Entry(frame, font=("Arial", 14), width=8)
    entry_vendedor.grid(row=4, column=1, pady=10)

    def generar():
        # ================= ENTRADAS =================
        hora_desde = entry_hora_desde.get().strip() or "00:00"
        hora_hasta = entry_hora_hasta.get().strip() or "23:59"

        dia_desde  = entry_dia_desde.get().strip() or "01"
        dia_hasta  = entry_dia_hasta.get().strip() or "31"

        mes_desde  = entry_mes_desde.get().strip() or "01"
        mes_hasta  = entry_mes_hasta.get().strip() or "12"

        anio_desde = entry_anio_desde.get().strip() or "0001"
        anio_hasta = entry_anio_hasta.get().strip() or "9999"

        vendedor = entry_vendedor.get().strip()

        # ================= DATETIME =================
        try:
            fecha_desde_dt = datetime(
                int(anio_desde), int(mes_desde), int(dia_desde),
                int(hora_desde[:2]), int(hora_desde[3:]), 0
            )
            fecha_hasta_dt = datetime(
                int(anio_hasta), int(mes_hasta), int(dia_hasta),
                int(hora_hasta[:2]), int(hora_hasta[3:]), 59
            )
        except:
            messagebox.showerror("Error", "Fecha u hora inválida")
            return

        fecha_desde = fecha_desde_dt.strftime("%Y-%m-%d %H:%M:%S")
        fecha_hasta = fecha_hasta_dt.strftime("%Y-%m-%d %H:%M:%S")

        # ================= UI =================
        ventana_result = tk.Toplevel(ventana_inf)
        ventana_result.title("Resultados del Informe")
        ventana_result.geometry("1050x500")

        frame_tabla = tk.Frame(ventana_result)
        frame_tabla.pack(fill="both", expand=True, padx=10, pady=10)

        tree = ttk.Treeview(
            frame_tabla,
            columns=("fecha", "tipo", "detalle", "usuario", "importe"),
            show="headings"
        )

        tree.heading("fecha", text="Fecha")
        tree.heading("tipo", text="Tipo")
        tree.heading("detalle", text="Detalle")
        tree.heading("usuario", text="Usuario")
        tree.heading("importe", text="Importe $")

        tree.column("importe", anchor="e")
        tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)

        # ================= DATOS =================
        conn = conectar()
        c = conn.cursor()

        query = """
            SELECT fecha, 'VENTA', 'Venta', vendedor, total
            FROM ventas
            WHERE fecha BETWEEN ? AND ?
        """
        params = [fecha_desde, fecha_hasta]

        if vendedor:
            query += " AND vendedor = ?"
            params.append(vendedor)

        query += """
            UNION ALL
            SELECT fecha_inicio, 'CAJA',
                CASE
                    WHEN tipo='INICIAL' THEN 'Caja inicial del sistema'
                    ELSE 'Movimiento de caja'
                END,
                usuario,
                CASE
                    WHEN tipo='INICIAL' THEN caja_inicial
                    ELSE (caja_final - caja_inicial)
                END
            FROM caja
            WHERE fecha_inicio BETWEEN ? AND ?
            ORDER BY fecha
        """

        params.extend([fecha_desde, fecha_hasta])

        c.execute(query, params)
        eventos = c.fetchall()

        if not eventos:
            conn.close()
            messagebox.showinfo("Informe", "No hay movimientos en ese período.")
            return

        eventos.sort(key=lambda x: x[0])

        # ================= CAJA INICIAL MOSTRADA =================
        primer_evento = eventos[0]

        if primer_evento[1] == "CAJA":
            caja_inicial_mostrada = float(primer_evento[4])
        else:
            c.execute(
                "SELECT caja_inicial FROM ventas WHERE fecha = ? LIMIT 1",
                (primer_evento[0],)
            )
            row = c.fetchone()
            caja_inicial_mostrada = float(row[0]) if row else 0.0

        # ================= BASE DE CÁLCULO =================
        c.execute("""
            SELECT fecha_inicio, caja_inicial
            FROM caja
            WHERE tipo='INICIAL'
            AND fecha_inicio <= ?
            ORDER BY fecha_inicio DESC
            LIMIT 1
        """, (fecha_hasta,))

        row = c.fetchone()

        if row:
            fecha_base, caja_base = row
        else:
            fecha_base = None
            caja_base = caja_inicial_mostrada

        # ================= MOSTRAR Y SUMAR =================
        total_ventas_periodo = 0.0
        total_ventas_computadas = 0.0
        total_movimientos = 0.0

        for fecha, tipo, detalle, usuario, importe in eventos:
            importe = float(importe)

            tree.insert(
                "",
                "end",
                values=(fecha, tipo, detalle, usuario, f"{importe:.2f}")
            )

            if tipo == "VENTA":
                total_ventas_periodo += importe

                if fecha_base is None or fecha >= fecha_base:
                    total_ventas_computadas += importe

            elif tipo == "CAJA" and detalle != "Caja inicial del sistema":
                total_movimientos += importe

        caja_final = caja_base + total_ventas_computadas + total_movimientos

        conn.close()

        # ================= RESUMEN =================
        frame_resumen = tk.Frame(ventana_result)
        frame_resumen.pack(pady=5)

        tk.Label(
            frame_resumen,
            text=f"CAJA INICIAL DEL PERÍODO: ${caja_inicial_mostrada:.2f}",
            font=("Arial", 14)
        ).pack()

        tk.Label(
            frame_resumen,
            text=f"TOTAL VENTAS DEL PERÍODO: ${total_ventas_periodo:.2f}",
            font=("Arial", 14)
        ).pack()

        tk.Label(
            frame_resumen,
            text=f"CAJA FINAL: ${caja_final:.2f}",
            font=("Arial", 16, "bold")
        ).pack(pady=5)

        # ================= BOTONES =================
        frame_botones = tk.Frame(ventana_result)
        frame_botones.pack(pady=15)

        tk.Button(
            frame_botones,
            text="Ver detalle",
            font=("Arial", 14),
            bg="#2196F3",
            fg="white",
            command=lambda: ver_detalle(tree)
        ).grid(row=0, column=0, padx=10)

        tk.Button(
            frame_botones,
            text="Imprimir Informe",
            font=("Arial", 14),
            bg="#4CAF50",
            fg="white",
            command=lambda: imprimir_informe(tree, total_ventas_periodo)
        ).grid(row=0, column=1, padx=10)

        tk.Button(
            frame_botones,
            text="Eliminar Venta",
            font=("Arial", 14),
            bg="#E53935",
            fg="white",
            command=lambda: eliminar_venta(tree, None)
        ).grid(row=0, column=2, padx=10)

    def eliminar_venta(tree, label_total):
        if jerarquia != "admin":
            messagebox.showerror(
                "Permiso denegado",
                "Solo un usuario con jerarquía ADMIN puede eliminar ventas."
            )
            return

        seleccion = tree.selection()
        if not seleccion:
            messagebox.showerror("Error", "Seleccione una venta para eliminar.")
            return

        item = tree.item(seleccion[0])
        fecha, tipo, detalle, usuario, importe = item["values"]

        if tipo != "VENTA":
            messagebox.showwarning(
                "Atención",
                "No se pueden eliminar movimientos de caja.\n"
                "Solo se pueden eliminar ventas."
            )
            return

        if not messagebox.askyesno(
            "Confirmar",
            "¿Seguro que desea eliminar esta venta?\nEsta acción no se puede deshacer."
        ):
            return

        conn = conectar()
        c = conn.cursor()

        # ================= BUSCAR ID REAL =================
        c.execute("""
            SELECT id
            FROM ventas
            WHERE fecha = ?
            LIMIT 1
        """, (fecha,))

        row = c.fetchone()
        if not row:
            conn.close()
            messagebox.showerror("Error", "No se pudo encontrar la venta.")
            return

        id_venta = row[0]

        # ================= ELIMINAR DETALLE Y VENTA =================
        c.execute("DELETE FROM ventas_detalle WHERE id_venta = ?", (id_venta,))
        c.execute("DELETE FROM ventas WHERE id = ?", (id_venta,))

        conn.commit()
        conn.close()

        # ================= ACTUALIZAR UI =================
        tree.delete(seleccion[0])

        # Recalcular total de ventas visibles (solo visual)
        total = 0
        for row_id in tree.get_children():
            valores = tree.item(row_id)["values"]
            if valores[1] == "VENTA":
                total += float(valores[4])

        if label_total:
            label_total.config(text=f"TOTAL VENTAS: ${total:.2f}")

        messagebox.showinfo("Éxito", "Venta eliminada correctamente.")

    tk.Button(ventana_inf, text="Generar Informe", command=generar,
              font=("Arial", 14), bg="#4CAF50", fg="white").pack(pady=20)


# ======================================
# ARQUEO DE CAJA
# ======================================

def abrir_arqueo():
    ventana = tk.Toplevel()
    ventana.title("Arqueo de Caja")
    ventana.geometry("350x220")
    ventana.grab_set()

    tk.Label(ventana, text="Caja real contada:", font=("Arial", 12)).pack(pady=10)
    entry_real = tk.Entry(ventana, font=("Arial", 12))
    entry_real.pack()

    def guardar():
        try:
            caja_real = float(entry_real.get())
        except ValueError:
            messagebox.showerror("Error", "Ingrese un número válido")
            return

        conn = conectar()
        caja_sis = obtener_caja_actual(conn)
        diferencia = caja_real - caja_sis

        c = conn.cursor()
        c.execute("""
            INSERT INTO arqueos (fecha, usuario, caja_sistema, caja_real, diferencia)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            usuario_actual,
            caja_sis,
            caja_real,
            diferencia
        ))
        conn.commit()
        conn.close()

        messagebox.showinfo(
            "Arqueo registrado",
            f"Caja sistema: ${caja_sis:.2f}\n"
            f"Caja real: ${caja_real:.2f}\n"
            f"Diferencia:  ${diferencia:.2f}"
        )

        ventana.destroy()

    frame_botones = tk.Frame(ventana)
    frame_botones.pack(pady=20)

    tk.Button(
        frame_botones,
        text="Confirmar",
        font=("Arial", 12),
        width=12,
        bg="#4CAF50",
        fg="white",
        command=guardar
    ).pack(side="left", padx=10)

    tk.Button(
        frame_botones,
        text="Ver arqueos",
        font=("Arial", 12),
        width=12,
        bg="#2196F3",
        fg="white",
        command=ver_arqueos
    ).pack(side="left", padx=10)


def imprimirArqueos():
    conn = conectar()
    c = conn.cursor()

    c.execute("""
        SELECT fecha, usuario, caja_sistema, caja_real, diferencia
        FROM arqueos
        ORDER BY fecha ASC
    """)
    filas = c.fetchall()
    conn.close()

    if not filas:
        messagebox.showinfo("Arqueos", "No hay registros de arqueo.")
        return

    lineas = [
        "-----------------------------------------------",
        "              INFORME DE ARQUEOS",
        "-----------------------------------------------",
        "Fecha                Usuario    Sis   Real   Dif",
        "-----------------------------------------------"
    ]

    for fecha, usuario, sis, real, dif in filas:
        lineas.append(
            f"{fecha:<19} {usuario:<10} {sis:>6.2f} {real:>6.2f} {dif:>6.2f}"
        )

    lineas.append("-----------------------------------------------")

    contenido = "\n".join(lineas)

    path = os.path.join(tempfile.gettempdir(), "reporte_arqueos.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(contenido)

    try:
        os.startfile(path)
        messagebox.showinfo(
            "Arqueos",
            "Informe abierto en Bloc de Notas.\nPuede imprimir desde allí."
        )
    except Exception as e:
        messagebox.showerror("Error", str(e))


def ver_arqueos():
    ventana = tk.Toplevel()
    ventana.title("Consulta de Arqueos")
    ventana.geometry("750x480")
    ventana.grab_set()

    tk.Label(
        ventana,
        text="Filtrar Arqueos",
        font=("Arial", 16, "bold")
    ).pack(pady=5)

    # ================= FILTROS =================
    frame_filtros = tk.Frame(ventana)
    frame_filtros.pack(pady=5)

    tk.Label(frame_filtros, text="Desde (YYYY-MM-DD):").grid(row=0, column=0, padx=5)
    entry_desde = tk.Entry(frame_filtros, width=12)
    entry_desde.grid(row=0, column=1, padx=5)

    tk.Label(frame_filtros, text="Hasta (YYYY-MM-DD):").grid(row=0, column=2, padx=5)
    entry_hasta = tk.Entry(frame_filtros, width=12)
    entry_hasta.grid(row=0, column=3, padx=5)

    tk.Label(frame_filtros, text="Usuario:").grid(row=0, column=4, padx=5)
    entry_usuario = tk.Entry(frame_filtros, width=10)
    entry_usuario.grid(row=0, column=5, padx=5)

    # ================= TABLA =================
    frame_tabla = tk.Frame(ventana)
    frame_tabla.pack(fill="both", expand=True, pady=5)

    columnas = ("fecha", "usuario", "sistema", "real", "diferencia")
    tabla = ttk.Treeview(frame_tabla, columns=columnas, show="headings")

    for col in columnas:
        tabla.heading(col, text=col.capitalize())
        tabla.column(col, width=130)

    tabla.pack(side="left", fill="both", expand=True)

    sb = ttk.Scrollbar(frame_tabla, orient="vertical", command=tabla.yview)
    sb.pack(side="right", fill="y")
    tabla.configure(yscrollcommand=sb.set)

    label_totales = tk.Label(ventana, text="", font=("Arial", 12))
    label_totales.pack(pady=4)

    # ================= BUSCAR =================
    def buscar():
        tabla.delete(*tabla.get_children())

        desde = entry_desde.get().strip()
        hasta = entry_hasta.get().strip()
        usuario = entry_usuario.get().strip()

        query = """
            SELECT fecha, usuario, caja_sistema, caja_real, diferencia
            FROM arqueos
            WHERE 1=1
        """
        params = []

        if desde:
            query += " AND fecha >= ?"
            params.append(desde + " 00:00:00")

        if hasta:
            query += " AND fecha <= ?"
            params.append(hasta + " 23:59:59")

        if usuario:
            query += " AND usuario = ?"
            params.append(usuario)

        conn = conectar()
        c = conn.cursor()
        c.execute(query, params)

        total_pos = 0
        total_neg = 0

        for fecha, user, sis, real, dif in c.fetchall():
            tabla.insert("", "end", values=(fecha, user, sis, real, dif))
            if dif >= 0:
                total_pos += dif
            else:
                total_neg += dif

        conn.close()

        label_totales.config(
            text=f"Diferencia positiva total: ${total_pos:.2f}   -   Diferencia negativa total: ${total_neg:.2f}"
        )

    # ================= IMPRIMIR =================
    def imprimir_arqueos():
        filas = tabla.get_children()
        if not filas:
            messagebox.showwarning("Sin datos", "No hay arqueos para imprimir.")
            return

        contenido = ["====== INFORME DE ARQUEOS ======\n"]
        for fila in filas:
            contenido.append(" | ".join(map(str, tabla.item(fila)["values"])))
        contenido.append("\n================================")

        path = os.path.join(tempfile.gettempdir(), "arqueos_filtrados.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(contenido))

        try:
            os.startfile(path)
        except:
            pass

    # ================= BOTONES =================
    frame_botones = tk.Frame(ventana)
    frame_botones.pack(pady=10)

    tk.Button(
        frame_botones,
        text="Buscar",
        font=("Arial", 12),
        width=14,
        bg="#2196F3",
        fg="white",
        command=buscar
    ).pack(side="left", padx=10)

    tk.Button(
        frame_botones,
        text="Imprimir arqueos",
        font=("Arial", 12),
        width=18,
        bg="#4CAF50",
        fg="white",
        command=imprimir_arqueos
    ).pack(side="left", padx=10)



# ======================================
# FUNCIONES DE LA VENTANA PRINCIPAL
# ======================================
carrito = {}

def procesar_codigo(event=None):
    """Procesa el código de barras escaneado o ingresado manualmente."""
    codigo = entry_codigo.get().strip()
    if not codigo:
        return

    # Buscar el producto en la BD
    producto = buscar_producto(codigo)
    if not producto:
        # producto no existe
        label_nombre.config(text="Producto no encontrado", fg="red")
        label_precio.config(text="")
        entry_codigo.delete(0, tk.END)
        return

    nombre, precio, stock, precioKilo = producto

    # Verificamos stock *antes* de realizar la venta/descuento
    if stock is None or stock <= 0:
        messagebox.showwarning("Cuidado", "no queda stock del producto")
        entry_codigo.delete(0, tk.END)
        return

    if stock is None or stock <= 1:
        messagebox.showwarning("Cuidado", "ultimo stock ")
        entry_codigo.delete(0, tk.END)
    # Si hay stock, descontamos 1 unidad usando ajustar_stock (delta = -1)

    # PRODUCTOS POR KILO
    if producto[3] != "":
        resultado = abrir_ventana_Kg(precioKilo, codigo)
        if resultado is None:
            return

        peso, subtotal_basico = resultado

        clave = f"{codigo}_{datetime.now().timestamp()}"

        # construimos item temporal para calcular promo
        item_tmp = {
            "codigo": codigo,
            "nombre": nombre,
            "tipo": "peso",
            "cantidad": None,
            "peso": peso,
            "precio_unitario": precioKilo
        }

        subtotal_final, promo_txt = calcular_subtotal_item(item_tmp)

        carrito[clave] = {
            **item_tmp,
            "subtotal": subtotal_final,
            "promo": promo_txt
        }

    # PRODUCTOS POR UNIDAD
    else:
        ajustar_stock(codigo, -1)

        # ===== PRODUCTO POR UNIDAD =====
        if codigo in carrito:
            carrito[codigo]["cantidad"] += 1
        else:
            carrito[codigo] = {
                "codigo": codigo,
                "nombre": nombre,
                "tipo": "unidad",
                "cantidad": 1,
                "peso": None,
                "precio_unitario": precio
            }

        # recalcular subtotal con promo
        subtotal, promo_txt = calcular_subtotal_item(carrito[codigo])
        carrito[codigo]["subtotal"] = subtotal
        carrito[codigo]["promo"] = promo_txt

    # Actualizar interfaz
    actualizar_lista()
    actualizar_total()

    # limpiar campo y dejar foco para el siguiente escaneo
    entry_codigo.delete(0, tk.END)
    entry_codigo.focus_set()

    # DEBUG: mostrar stock real en consola (opcional, útil para pruebas)
    prod_ok = buscar_producto(codigo)
    if prod_ok:
        _, _, stock_real, _ = prod_ok
        print(f"[DEBUG] Stock real de '{nombre}' ahora: {stock_real}")

def abrir_ventana_Kg(precioKilo, codigo):
    kilos = tk.Toplevel()
    kilos.title("Ingreso de Kilos")
    kilos.geometry("350x220")
    kilos.resizable(False, False)

    resultado = {}

    tk.Label(kilos, text="Peso (kg):", font=("Arial", 14)).pack(pady=5)
    entry_kg = tk.Entry(kilos, font=("Arial", 14))
    entry_kg.pack()

    def aceptar():
        try:
            peso = float(entry_kg.get())
        except ValueError:
            messagebox.showerror("Error", "Peso inválido.")
            return

        if peso <= 0:
            messagebox.showerror("Error", "El peso debe ser mayor a 0.")
            return

        ajustar_stock(codigo, -peso)

        resultado["peso"] = peso
        resultado["subtotal"] = peso * precioKilo
        kilos.destroy()

    tk.Button(kilos, text="Aceptar", font=("Arial", 14), command=aceptar).pack(pady=20)

    kilos.grab_set()
    kilos.wait_window()

    if not resultado:
        return None

    return resultado["peso"], resultado["subtotal"]


def actualizar_lista():
    for i in lista_productos.get_children():
        lista_productos.delete(i)

    for clave, item in carrito.items():

        if item["tipo"] == "unidad":
            cantidad_txt = str(item["cantidad"])
            precio_txt = f"${item['precio_unitario']:.2f}"

        else:  # peso
            cantidad_txt = f"{item['peso']:.3f} kg"
            precio_txt = f"${item['precio_unitario']:.2f} x kg"

        lista_productos.insert(
            "",
            "end",
            iid=clave,  # 👈 CLAVE REAL
            values=(
                item["codigo"],
                item["nombre"],
                cantidad_txt,
                precio_txt,
                f"${item['subtotal']:.2f} {item.get('promo','') or ''}"

            )
        )



def actualizar_total(event=None):
    total = sum(item["subtotal"] for item in carrito.values())

    try:
        descuento = float(entrada_descuento.get())
    except ValueError:
        descuento = 0.0

    descuento = max(0, min(descuento, 100))
    total_final = total * (1 - descuento / 100)

    label_total.config(text=f"Total: ${total_final:.2f}")
    return total_final


def eliminar_producto():
    seleccion = lista_productos.selection()
    if not seleccion:
        messagebox.showwarning("Atención", "Seleccione un producto para eliminar.")
        return

    clave = seleccion[0]  # 👈 clave real del carrito
    item = carrito.get(clave)

    if not item:
        return

    # ===== PRODUCTO POR UNIDAD =====
    if item["tipo"] == "unidad":
        item["cantidad"] -= 1
       # volver a calcular subtotal con promo
        subtotal, promo_txt = calcular_subtotal_item(item)
        item["subtotal"] = subtotal
        item["promo"] = promo_txt


        if item["cantidad"] <= 0:
            del carrito[clave]

        # devolver stock
        producto = buscar_producto(item["codigo"])
        if producto:
            _, _, stock, _ = producto
            actualizar_stock_y_precio(item["codigo"], stock + 1, None)

    # ===== PRODUCTO POR PESO =====
    else:
        # devolver todo el peso al stock
        producto = buscar_producto(item["codigo"])
        if producto:
            _, _, stock, _ = producto
            actualizar_stock_y_precio(item["codigo"], stock + item["peso"], None)

        del carrito[clave]

    actualizar_lista()
    actualizar_total()

def eliminar_todo_producto():
    seleccion = lista_productos.selection()
    if not seleccion:
        messagebox.showwarning("Atención", "Seleccione un producto para eliminar.")
        return

    clave = seleccion[0]
    item = carrito.get(clave)

    if not item:
        return

    producto = buscar_producto(item["codigo"])
    if producto:
        _, _, stock, _ = producto

        if item["tipo"] == "unidad":
            actualizar_stock_y_precio(
                item["codigo"],
                stock + item["cantidad"],
                None
            )
        else:
            actualizar_stock_y_precio(
                item["codigo"],
                stock + item["peso"],
                None
            )

    del carrito[clave]

    actualizar_lista()
    actualizar_total()


def calcular_vuelto(event=None):
    try:
        pago = float(entry_pago.get())
    except ValueError:
        messagebox.showerror("Error", "Monto inválido.")
        return
    total_final = actualizar_total()
    if pago < total_final:
        messagebox.showwarning("Atención", "El monto es insuficiente.")
        return
    vuelto = pago - total_final
    label_vuelto.config(text=f"VUELTO: ${vuelto:.2f}", fg="blue", font=("Arial", 18, "bold"))

def finalizar_compra():
    if not carrito:
        messagebox.showwarning("Atención", "No hay productos en el carrito.")
        return

    registrar_venta(usuario_actual)  # ← guarda venta + usuario
    limpiar_lista()  # ← vacía carrito y limpia pantalla


def limpiar_lista():
    carrito.clear()
    for i in lista_productos.get_children():
        lista_productos.delete(i)
    entry_pago.delete(0, tk.END)
    label_vuelto.config(text="")
    label_nombre.config(text="")
    label_precio.config(text="")
    entry_codigo.focus_set()
    actualizar_total()
    entrada_descuento.delete(0, tk.END)

# ======================================
# PROMOCIONES
#=======================================

def obtener_promocion(codigo_producto):
    """
    Devuelve dict con info de la promoción activa
    o None si no existe/promoción no activa.
    """
    conn = conectar()
    c = conn.cursor()

    c.execute("""
        SELECT tipo, cantidad_min, precio_promo, descuento
        FROM promociones
        WHERE codigo_producto = ?
          AND activa = 1
        LIMIT 1
    """, (codigo_producto,))

    row = c.fetchone()
    conn.close()

    if not row:
        return None

    def to_float(value):
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    return {
        "tipo": row[0],
        "cantidad_min": to_float(row[1]),
        "precio_promo": to_float(row[2]),
        "descuento": to_float(row[3])
    }



def calcular_subtotal_item(item):
    """
    Calcula subtotal real considerando promo.
    Devuelve: (subtotal_final, texto_promo)
    """

    codigo = item["codigo"]
    cantidad = item.get("cantidad", 0)
    peso = item.get("peso", 0)
    precio_unit = item.get("precio_unitario", 0)


    promo = obtener_promocion(codigo)

    # ==========================================
    # SIN PROMO
    # ==========================================
    if not promo:
        if item["tipo"] == "unidad":
            return cantidad * precio_unit, None
        else:
            return peso * precio_unit, None

    # ==========================================
    # PROMO POR CANTIDAD (unidad)
    # ==========================================
    if promo["tipo"] == "cantidad" and item["tipo"] == "unidad":
        if cantidad < promo["cantidad_min"]:
            return cantidad * precio_unit, None

        packs = cantidad // promo["cantidad_min"]
        resto = cantidad % promo["cantidad_min"]

        subtotal = packs * promo["precio_promo"] + resto * precio_unit
        txt = f"{promo['cantidad_min']}x${promo['precio_promo']}"

        return subtotal, txt

    # ==========================================
    # PROMO POR PESO (kg)
    # ==========================================
    if promo["tipo"] == "peso" and item["tipo"] == "peso":
        if peso < promo["cantidad_min"]:
            return peso * precio_unit, None

        # precio especial por kg si supera min
        subtotal = peso * promo["precio_promo"]
        txt = f"{promo['precio_promo']}/kg PROMO"

        return subtotal, txt

    # ==========================================
    # PROMO POR PORCENTAJE (% OFF)
    # ==========================================
    if promo["tipo"] == "porcentaje":
        if item["tipo"] == "unidad":
            base = cantidad * precio_unit
        else:
            base = peso * precio_unit

        desc = base * (promo["descuento"] / 100)
        subtotal = base - desc
        txt = f"{promo['descuento']}% OFF"

        return subtotal, txt

    # fallback seguro
    if item["tipo"] == "unidad":
        return cantidad * precio_unit, None
    else:
        return peso * precio_unit, None

def abrir_gestion_promos():
    ventana_promo = tk.Toplevel()
    ventana_promo.title("Gestión de Promociones")
    ventana_promo.state("zoomed")

    tk.Label(
        ventana_promo,
        text="GESTIÓN DE PROMOCIONES",
        font=("Arial", 18, "bold")
    ).pack(pady=10)

    # ===================== TABLA =====================
    frame_tabla = tk.Frame(ventana_promo)
    frame_tabla.pack(fill="both", expand=True)

    cols = ("id","codigo","tipo","cantidad_min","precio_promo","descuento","activa")
    tabla = ttk.Treeview(frame_tabla, columns=cols, show="headings")
    
    for col in cols:
        tabla.heading(col, text=col.capitalize())
        tabla.column(col, width=120)

    tabla.pack(side="left", fill="both", expand=True)

    scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=tabla.yview)
    scrollbar.pack(side="right", fill="y")
    tabla.configure(yscrollcommand=scrollbar.set)

    # ===================== REFRESCAR BD =====================
    def refrescar():
        tabla.delete(*tabla.get_children())
        conn = conectar()
        c = conn.cursor()
        c.execute("""
            SELECT id, codigo_producto, tipo, cantidad_min,
                   precio_promo, descuento, activa
            FROM promociones
        """)
        for fila in c.fetchall():
            tabla.insert("", "end", values=fila)
        conn.close()

    # ===================== FORM =====================
    frame_form = tk.LabelFrame(ventana_promo, text="Agregar / Editar promoción",
                               font=("Arial", 12), padx=10, pady=10)
    frame_form.pack(fill="x", padx=10, pady=10)

    labels = ["Código producto", "Tipo", "Cantidad mín.",
              "Precio promo", "Descuento (%)", "Activa (1/0)"]

    entries = []
    for i, label in enumerate(labels):
        tk.Label(frame_form, text=label, font=("Arial", 12)).grid(row=0, column=i)
        entry = tk.Entry(frame_form, font=("Arial", 12), width=12)
        entry.grid(row=1, column=i, padx=5)
        entries.append(entry)

    entry_codigo, entry_tipo, entry_cant, entry_precio, entry_desc, entry_activa = entries

    # ===================== BOTONES CRUD =====================

    def guardar_promo():   # insertar
        conn = conectar()
        c = conn.cursor()
        c.execute("""
            INSERT INTO promociones
            (codigo_producto,tipo,cantidad_min,precio_promo,descuento,activa)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            entry_codigo.get().strip(),
            entry_tipo.get().strip(),
            entry_cant.get().strip(),
            entry_precio.get().strip(),
            entry_desc.get().strip(),
            entry_activa.get().strip() or "1"
        ))
        conn.commit()
        conn.close()
        refrescar()

    def eliminar_promo():
        sel = tabla.selection()
        if not sel:
            return
        id_promo = tabla.item(sel[0])["values"][0]
        conn = conectar()
        c = conn.cursor()
        c.execute("DELETE FROM promociones WHERE id=?", (id_promo,))
        conn.commit()
        conn.close()
        refrescar()

    def cargar_campos(event=None):   # al seleccionar
        sel = tabla.selection()
        if not sel:
            return

        row = tabla.item(sel[0])["values"]
        entry_codigo.delete(0, tk.END)
        entry_tipo.delete(0, tk.END)
        entry_cant.delete(0, tk.END)
        entry_precio.delete(0, tk.END)
        entry_desc.delete(0, tk.END)
        entry_activa.delete(0, tk.END)

        entry_codigo.insert(0, row[1])
        entry_tipo.insert(0, row[2])
        entry_cant.insert(0, row[3])
        entry_precio.insert(0, row[4])
        entry_desc.insert(0, row[5])
        entry_activa.insert(0, row[6])

    tabla.bind("<<TreeviewSelect>>", cargar_campos)

    def editar_promo():   # update
        sel = tabla.selection()
        if not sel:
            return
        id_promo = tabla.item(sel[0])["values"][0]
        conn = conectar()
        c = conn.cursor()
        c.execute("""
            UPDATE promociones
            SET codigo_producto=?, tipo=?, cantidad_min=?, 
                precio_promo=?, descuento=?, activa=?
            WHERE id=?
        """, (
            entry_codigo.get().strip(),
            entry_tipo.get().strip(),
            entry_cant.get().strip(),
            entry_precio.get().strip(),
            entry_desc.get().strip(),
            entry_activa.get().strip(),
            id_promo
        ))
        conn.commit()
        conn.close()
        refrescar()

    # ===================== BOTONES UI =====================
    frame_botones = tk.Frame(frame_form)
    frame_botones.grid(row=2, column=0, columnspan=6, pady=10)

    tk.Button(frame_botones, text="Guardar",
            font=("Arial", 14), bg="#4CAF50", fg="white",
            command=guardar_promo).pack(side="left", padx=15)

    tk.Button(frame_botones, text="Editar",
            font=("Arial", 14), bg="#FF9800", fg="white",
            command=editar_promo).pack(side="left", padx=15)

    tk.Button(frame_botones, text="Eliminar",
            font=("Arial", 14), bg="#E53935", fg="white",
            command=eliminar_promo).pack(side="left", padx=15)


    refrescar()

# ======================================
# CAJA
#=======================================
def obtener_caja_actual(conn):
    c = conn.cursor()

    # Última caja registrada (inicial o movimiento)
    c.execute("""
        SELECT fecha_inicio, caja_final
        FROM caja
        ORDER BY fecha_inicio DESC
        LIMIT 1
    """)
    ultima_caja = c.fetchone()

    if not ultima_caja:
        return 0

    fecha_caja, caja_base = ultima_caja

    # Sumar ventas posteriores a esa caja
    c.execute("""
        SELECT COALESCE(SUM(total), 0)
        FROM ventas
        WHERE fecha > ?
    """, (fecha_caja,))

    total_ventas = c.fetchone()[0]

    return caja_base + total_ventas
    
def actualizar_caja():
    ventana = tk.Toplevel()
    ventana.title("Actualizar Caja")
    ventana.geometry("300x220")
    ventana.grab_set()

    tk.Label(ventana, text="Monto (+ suma / - resta)", font=("Arial", 12)).pack(pady=10)
    entry_monto = tk.Entry(ventana, font=("Arial", 12))
    entry_monto.pack()

    def guardar():
        try:
            monto = float(entry_monto.get())
        except ValueError:
            messagebox.showerror("Error", "Ingrese un número válido")
            return

        conn = conectar()
        caja_actual = obtener_caja_actual(conn)

        caja_nueva = caja_actual + monto

        c = conn.cursor()
        c.execute("""
            INSERT INTO caja (fecha_inicio, caja_inicial, caja_final, usuario, tipo)
            VALUES (?, ?, ?, ?, 'MOVIMIENTO')
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            caja_actual,
            caja_nueva,
            usuario_actual
        ))

        conn.commit()
        conn.close()

        messagebox.showinfo(
            "Caja actualizada",
            f"Caja anterior: ${caja_actual:.2f}\nCaja nueva: ${caja_nueva:.2f}"
        )

        ventana.destroy()

    tk.Button(
        ventana,
        text="Confirmar",
        font=("Arial", 12),
        bg="#4CAF50",
        fg="white",
        command=guardar
    ).pack(pady=15)


def obtener_float(entry, nombre="valor"):
    try:
        return float(entry.get())
    except ValueError:
        messagebox.showerror(
            "Error",
            f"El {nombre} debe ser un número válido"
        )
        return None

def preguntar_caja_inicial():
    ventana = tk.Toplevel()
    ventana.title("Caja Inicial")
    ventana.geometry("300x150")
    ventana.grab_set()
    ventana.transient()
    ventana.focus_force()
    ventana.protocol("WM_DELETE_WINDOW", lambda: None)

    tk.Label(ventana, text="Ingrese el monto inicial de caja:", font=("Arial", 12)).pack(pady=10)
    entry = tk.Entry(ventana, font=("Arial", 12))
    entry.pack()

    def guardar(event=None):
        monto = obtener_float(entry, "caja inicial")
        if monto is None:
            return
        conn = conectar()
        c = conn.cursor()
        c.execute("""
            INSERT INTO caja (fecha_inicio, caja_inicial, caja_final, usuario, tipo)
            VALUES (?, ?, ?, ?, 'INICIAL')
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            monto,
            monto,
            usuario_actual
        ))

        conn.commit()
        conn.close()
        ventana.destroy()

    tk.Button(ventana, text="Aceptar", command=guardar, font=("Arial", 12)).pack(pady=10)
    entry.bind("<Return>", guardar)
    ventana.wait_window()
# ==============================
# LOGIN
# ==============================

def abrir_login():
    login = tk.Tk()
    login.title("Inicio de Sesión")
    login.geometry("350x220")
    login.resizable(False, False)

    tk.Label(login, text="Usuario:", font=("Arial", 14)).pack(pady=5)
    entry_user = tk.Entry(login, font=("Arial", 14))
    entry_user.pack()

    tk.Label(login, text="Contraseña:", font=("Arial", 14)).pack(pady=5)
    entry_pass = tk.Entry(login, font=("Arial", 14), show="*")
    entry_pass.pack()

    label_error = tk.Label(login, text="", fg="red", font=("Arial", 12))
    label_error.pack()

    def validar_login(event=None):
        user = entry_user.get().strip()
        pwd = entry_pass.get().strip()

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND contrasena=?", (user, pwd))
        fila = cursor.fetchone()
        conn.close()

        if fila:
            global usuario_actual, jerarquia
            id, usuario_actual, contra, jerarquia  = fila
            login.destroy()
            abrir_ventana_principal(usuario_actual, jerarquia)
        else:
            label_error.config(text="Usuario o contraseña incorrectos")

    tk.Button(login, text="Ingresar", font=("Arial", 14), bg="#4CAF50", fg="white",
              command=validar_login).pack(pady=10)

    entry_pass.bind("<Return>", validar_login)

    login.mainloop()

# ==============================
# INTERFAZ PRINCIPAL - REDISEÑADA *CON SECCIONES*
# ==============================

def abrir_ventana_principal(usuario, jerarquia):
    global ventana, entry_codigo, entrada_descuento, entry_pago, lista_productos, label_vuelto, label_nombre, label_precio, label_total
    ventana = tk.Tk()
    ventana.title("Minimarket V&E")
    ventana.state('zoomed')
    ventana.config(bg="#f0f0f0")

    # --- SECCIÓN SUPERIOR (HEADER) ---
    frame_top = tk.Frame(ventana, bg="#f0f0f0", height=220)
    frame_top.pack(fill="x")
    frame_top.pack_propagate(False)

    # CONFIGURAR 3 COLUMNAS (IZQ - CENTRO - DER)
    frame_top.grid_columnconfigure(0, weight=1)
    frame_top.grid_columnconfigure(1, weight=2)
    frame_top.grid_columnconfigure(2, weight=1)

    # ---------------- IZQUIERDA ----------------
    frame_left = tk.Frame(frame_top, bg="#f0f0f0")
    frame_left.grid(row=0, column=0, sticky="nw", padx=40, pady=20)

    label_titulo = tk.Label(frame_left, text="Minimarket V&E",
                            font=("Arial", 26, "bold"), bg="#f0f0f0")
    label_titulo.pack(anchor="center")

    try:
        logo_path = resource_path("LOGO.JPG")
        base_logo = Image.open(logo_path)
        base_logo_resized = base_logo.resize((150, 150))
        logo_tk = ImageTk.PhotoImage(base_logo_resized)

        label_logo = tk.Label(frame_left, image=logo_tk, bg="#f0f0f0")
        label_logo.image = logo_tk
        label_logo.pack(anchor="center", pady=10)

    except Exception as e:
        print("Error cargando logo:", e)

    # ---------------- CENTRO — ENTRY + INFO DEL PRODUCTO ----------------
    frame_center = tk.Frame(frame_top, bg="#f0f0f0")
    frame_center.grid(row=0, column=1, sticky="n", pady=20)

    entry_codigo = tk.Entry(frame_center, font=("Arial", 22),
                            width=18, justify="center")
    entry_codigo.pack(pady=(10, 10))
    entry_codigo.bind("<Return>", procesar_codigo)

    label_nombre = tk.Label(frame_center, text="",
                            font=("Arial", 16), bg="#f0f0f0")
    label_nombre.pack()

    label_precio = tk.Label(frame_center, text="",
                            font=("Arial", 22, "bold"), bg="#f0f0f0")
    label_precio.pack()

    # ---------------- DERECHA – USUARIO EN USO ----------------
    frame_right = tk.Frame(frame_top, bg="#f0f0f0")
    frame_right.grid(row=0, column=2, sticky="ne", padx=40, pady=30)

    label_usuario = tk.Label(frame_right,
                            text=f"Usuario en uso: {usuario} ({jerarquia})",
                            font=("Arial", 16, "bold"),
                            bg="#f0f0f0",
                            fg="#333")
    label_usuario.pack(anchor="e")

    # ========================================
    # SECCIÓN CENTRAL (LISTA DE PRODUCTOS)
    # ========================================

    frame_center = tk.Frame(ventana, bg="#f0f0f0")
    frame_center.pack(fill="both", expand=True)

    cols = ("Código", "Nombre", "Cantidad", "Precio Unit.", "Subtotal")
    lista_productos = ttk.Treeview(frame_center, columns=cols, show="headings")
    for col in cols:
        lista_productos.heading(col, text=col)
        lista_productos.column(col, anchor="center", width=200)

    lista_productos.pack(fill="both", expand=True, padx=20, pady=10)

    # ========================================
    # SECCIÓN INFERIOR (TOTALES + BOTONES)
    # ========================================

    frame_bottom = tk.Frame(ventana, bg="#e8e8e8", height=220)
    frame_bottom.pack(fill="x")
    frame_bottom.pack_propagate(False)

    # Bloque totales
    frame_pago = tk.Frame(frame_bottom, bg="#e8e8e8")
    frame_pago.pack(side="left", padx=40, pady=20)

    label_total = tk.Label(frame_pago, text="Total: $0.00", font=("Arial", 24, "bold"), bg="#e8e8e8")
    label_total.grid(row=0, column=0, columnspan=2, pady=10)

    tk.Label(frame_pago, text="Descuento (%):", font=("Arial", 16), bg="#e8e8e8").grid(row=1, column=0)
    entrada_descuento = tk.Entry(frame_pago, font=("Arial", 16), width=10)
    entrada_descuento.grid(row=1, column=1)
    entrada_descuento.insert(0, "")
    entrada_descuento.bind("<Return>", actualizar_total)

    tk.Label(frame_pago, text="Pago:", font=("Arial", 16), bg="#e8e8e8").grid(row=2, column=0)
    entry_pago = tk.Entry(frame_pago, font=("Arial", 16), width=10)
    entry_pago.grid(row=2, column=1)
    entry_pago.bind("<Return>", calcular_vuelto)

    label_vuelto = tk.Label(frame_pago, text="", font=("Arial", 20, "bold"), bg="#e8e8e8", fg="blue")
    label_vuelto.grid(row=3, column=0, columnspan=2, pady=10)

    # Botones
    frame_botones = tk.Frame(frame_bottom, bg="#e8e8e8")
    frame_botones.pack(side="right", padx=40)

    botones = [
        ("Nueva compra", finalizar_compra, "#607D8B"),
        ("Imprimir Ticket", imprimir_ticket, "#607D8B"),
        ("Gestionar", lambda: abrir_gestion_stock(jerarquia), "#607D8B"),
        ("Arqueo de Caja", abrir_arqueo, "#607D8B"),
        ("Eliminar todo", eliminar_todo_producto, "#607D8B"),
        ("Eliminar 1", eliminar_producto, "#607D8B"),
        ("Actualizar Caja", actualizar_caja, "#607D8B"),
        ("Informe", abrir_informe, "#607D8B"),
    ]

    # --- BOTONES EN 2 COLUMNAS ---
    boton_refs = []  # guardará referencias para medir después

    for i, (texto, comando, color) in enumerate(botones):
        fila = (i // 4)
        col = i % 4

        b = tk.Button(
            frame_botones,
            text=texto,
            command=comando,
            font=("Arial", 14, "bold"),
            bg=color,
            fg="white",
            width=18,
            height=2
        )
        b.grid(row=fila, column=col, padx=10, pady=10)

        boton_refs.append(b)
    # llamarlo antes de entrar al mainloop:
    preguntar_caja_inicial()
    ventana.mainloop()

abrir_login()