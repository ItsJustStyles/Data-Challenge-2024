import tkinter as tk
from tkinter import ttk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime

ruta_archivo = 'Datos concurso/procedimientosiniciados.csv'

cedula_seleccionada = ""
nombre_institucion = ""

def buscar_datos():
    global cedula_seleccionada, nombre_institucion
    cedula_seleccionada = entry_identificador.get().strip()
    if not cedula_seleccionada:
        label_resultado.config(text="Por favor, introduce un identificador.")
        return

    conteo_total = 0
    chunk_size = 10000

    try:
        for chunk in pd.read_csv(ruta_archivo, chunksize=chunk_size, dtype={'cedula_institucion': str}):
            chunk['cedula_institucion'] = chunk['cedula_institucion'].astype(str).str.strip()
            conteo_bloque = chunk['cedula_institucion'].value_counts().get(cedula_seleccionada, 0)
            conteo_total += conteo_bloque

            if not nombre_institucion:
                institucion = chunk[chunk['cedula_institucion'] == cedula_seleccionada]['nombre_institucion']
                if not institucion.empty:
                    nombre_institucion = institucion.iloc[0]
        
        label_resultado.config(text=f"La cédula {cedula_seleccionada} aparece {conteo_total} veces.")
    
    except FileNotFoundError:
        label_resultado.config(text="Error: El archivo no se encuentra.")
    except KeyError:
        label_resultado.config(text="Error: La columna 'cedula_institucion' no se encuentra en el archivo.")
    except Exception as e:
        label_resultado.config(text=f"Error: {str(e)}")

def graficar_frecuencia_por_ano():
    if not cedula_seleccionada:
        label_resultado.config(text="Por favor, realiza primero una búsqueda para seleccionar una cédula.")
        return

    chunk_size = 10000
    frecuencia_por_ano = {}
    fechas = []

    try:
        meses_por_ano = {}

        for chunk in pd.read_csv(ruta_archivo, chunksize=chunk_size, dtype={'ano_publicacion': str, 'fecha_publicacion': str, 'cedula_institucion': str}):
            chunk['ano_publicacion'] = chunk['ano_publicacion'].astype(str).str.strip()
            chunk['fecha_publicacion'] = pd.to_datetime(chunk['fecha_publicacion'], errors='coerce')
            chunk['cedula_institucion'] = chunk['cedula_institucion'].astype(str).str.strip()
            
            chunk_filtrado = chunk[chunk['cedula_institucion'] == cedula_seleccionada]
            
            if not chunk_filtrado.empty:
                for _, row in chunk_filtrado.iterrows():
                    ano = row['ano_publicacion']
                    if pd.notna(row['fecha_publicacion']):
                        mes = row['fecha_publicacion'].month
                        fechas.append(row['fecha_publicacion'])  # Agregar fecha a la lista
                        if ano in meses_por_ano:
                            meses_por_ano[ano].append(mes)
                        else:
                            meses_por_ano[ano] = [mes]
        
        promedio_separacion_meses = {}
        for ano, meses in meses_por_ano.items():
            if len(meses) > 1:
                diferencias = [(meses[i] - meses[i - 1]) for i in range(1, len(meses))]
                promedio = sum(diferencias) / len(diferencias) if diferencias else 0
                promedio_separacion_meses[ano] = promedio
            else:
                promedio_separacion_meses[ano] = 0

        for ano, promedio in promedio_separacion_meses.items():
            print(f"Promedio de separación en meses para el año {ano}: {promedio:.2f}")
        
        frecuencia_por_ano = pd.Series([fecha.year for fecha in fechas]).value_counts().sort_index()

        ventana_grafico_frecuencia = tk.Toplevel(ventana)
        ventana_grafico_frecuencia.title("Frecuencia por Año")
        ventana_grafico_frecuencia.geometry("800x600")

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(frecuencia_por_ano.index, frecuencia_por_ano.values, color='lightcoral')
        ax.set_xlabel('Año')
        ax.set_ylabel('Frecuencia')
        ax.set_title(f'Frecuencia por Año para {nombre_institucion}')
        plt.xticks(rotation=45)
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=ventana_grafico_frecuencia)
        canvas.draw()
        canvas.get_tk_widget().pack(padx=10, pady=10)
        
        ventana_niveles = tk.Toplevel(ventana)
        ventana_niveles.title("Códigos y Descripciones")
        ventana_niveles.geometry("500x400")

        niveles = pd.read_csv(ruta_archivo, usecols=['Cod_Nivel1', 'Nivel1_producto']).drop_duplicates()
        niveles = niveles.dropna()
        
        tree = crear_treeview(ventana_niveles)

        for _, row in niveles.iterrows():
            tree.insert("", tk.END, values=(row['Cod_Nivel1'], row['Nivel1_producto']))
        
    except FileNotFoundError:
        label_resultado.config(text="Error: El archivo no se encuentra.")
    except KeyError:
        label_resultado.config(text="Error: Las columnas necesarias no se encuentran en el archivo.")
    except Exception as e:
        label_resultado.config(text=f"Error: {str(e)}")

def graficar_gastos_totales():
    if not cedula_seleccionada:
        label_resultado.config(text="Por favor, realiza primero una búsqueda para seleccionar una cédula.")
        return

    chunk_size = 10000
    gastos_por_ano = {}

    try:
        for chunk in pd.read_csv(ruta_archivo, chunksize=chunk_size, dtype={'ano_publicacion': str, 'monto_estimado_linea': float, 'cedula_institucion': str}):
            chunk['ano_publicacion'] = chunk['ano_publicacion'].astype(str).str.strip()
            chunk['monto_estimado_linea'] = chunk['monto_estimado_linea'].fillna(0)
            chunk['cedula_institucion'] = chunk['cedula_institucion'].astype(str).str.strip()
            
            chunk_filtrado = chunk[chunk['cedula_institucion'] == cedula_seleccionada]
            
            gastos_anuales = chunk_filtrado.groupby('ano_publicacion')['monto_estimado_linea'].sum()
            
            for ano, gasto in gastos_anuales.items():
                if ano in gastos_por_ano:
                    gastos_por_ano[ano] += gasto
                else:
                    gastos_por_ano[ano] = gasto

        anos_ordenados = sorted(gastos_por_ano.keys())
        gastos_totales = [gastos_por_ano[ano] for ano in anos_ordenados]
        
        print("Gastos Totales por Año:")
        for ano, gasto in zip(anos_ordenados, gastos_totales):
            print(f"Año {ano}: ₡{gasto:,.2f}")
        
        ventana_grafico_totales = tk.Toplevel(ventana)
        ventana_grafico_totales.title("Gastos Totales por Año")
        ventana_grafico_totales.geometry("800x600")

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(anos_ordenados, gastos_totales, color='skyblue')
        ax.set_xlabel('Año')
        ax.set_ylabel('Gasto Total (₡)')
        ax.set_title(f'Gasto Total por Año para {nombre_institucion}')
        ax.set_xticklabels(anos_ordenados, rotation=45)
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=ventana_grafico_totales)
        canvas.draw()
        canvas.get_tk_widget().pack(padx=10, pady=10)
        
        ventana_niveles = tk.Toplevel(ventana)
        ventana_niveles.title("Códigos y Descripciones")
        ventana_niveles.geometry("500x400")

        niveles = pd.read_csv(ruta_archivo, usecols=['Cod_Nivel1', 'Nivel1_producto']).drop_duplicates()
        niveles = niveles.dropna()
        
        tree = crear_treeview(ventana_niveles)

        for _, row in niveles.iterrows():
            tree.insert("", tk.END, values=(row['Cod_Nivel1'], row['Nivel1_producto']))
        
    except FileNotFoundError:
        label_resultado.config(text="Error: El archivo no se encuentra.")
    except KeyError:
        label_resultado.config(text="Error: Las columnas necesarias no se encuentran en el archivo.")
    except Exception as e:
        label_resultado.config(text=f"Error: {str(e)}")

def graficar_gastos_por_nivel():
    if not cedula_seleccionada:
        label_resultado.config(text="Por favor, realiza primero una búsqueda para seleccionar una cédula.")
        return

    chunk_size = 10000
    gastos_por_ano_y_nivel = {}

    try:
        for chunk in pd.read_csv(ruta_archivo, chunksize=chunk_size, dtype={'ano_publicacion': str, 'monto_estimado_linea': float, 'Cod_Nivel1': str, 'cedula_institucion': str}):
            chunk['ano_publicacion'] = chunk['ano_publicacion'].astype(str).str.strip()
            chunk['monto_estimado_linea'] = chunk['monto_estimado_linea'].fillna(0)
            chunk['Cod_Nivel1'] = chunk['Cod_Nivel1'].astype(str).str.strip()
            chunk['cedula_institucion'] = chunk['cedula_institucion'].astype(str).str.strip()
            
            chunk_filtrado = chunk[chunk['cedula_institucion'] == cedula_seleccionada]
            
            gastos_por_nivel = chunk_filtrado.groupby(['ano_publicacion', 'Cod_Nivel1'])['monto_estimado_linea'].sum()
            
            for (ano, nivel), gasto in gastos_por_nivel.items():
                if ano not in gastos_por_ano_y_nivel:
                    gastos_por_ano_y_nivel[ano] = {}
                if nivel in gastos_por_ano_y_nivel[ano]:
                    gastos_por_ano_y_nivel[ano][nivel] += gasto
                else:
                    gastos_por_ano_y_nivel[ano][nivel] = gasto

        for ano, niveles in gastos_por_ano_y_nivel.items():
            print(f"\nGastos por Nivel para el Año {ano}:")
            for nivel, gasto in niveles.items():
                print(f"Código Nivel {nivel}: ₡{gasto:,.2f}")
        
        ventana_grafico_nivel = tk.Toplevel(ventana)
        ventana_grafico_nivel.title("Gastos por Nivel")
        ventana_grafico_nivel.geometry("800x600")

        fig, ax = plt.subplots(figsize=(10, 6))
        for ano, niveles in gastos_por_ano_y_nivel.items():
            niveles_ordenados = sorted(niveles.keys())
            gastos_totales = [niveles[nivel] for nivel in niveles_ordenados]
            ax.bar(niveles_ordenados, gastos_totales, label=f'Año {ano}')

        ax.set_xlabel('Código Nivel')
        ax.set_ylabel('Gasto Total (₡)')
        ax.set_title(f'Gasto por Nivel para {nombre_institucion}')
        ax.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=ventana_grafico_nivel)
        canvas.draw()
        canvas.get_tk_widget().pack(padx=10, pady=10)
        
        ventana_niveles = tk.Toplevel(ventana)
        ventana_niveles.title("Códigos y Descripciones")
        ventana_niveles.geometry("500x400")

        niveles = pd.read_csv(ruta_archivo, usecols=['Cod_Nivel1', 'Nivel1_producto']).drop_duplicates()
        niveles = niveles.dropna()
        
        tree = crear_treeview(ventana_niveles)

        for _, row in niveles.iterrows():
            tree.insert("", tk.END, values=(row['Cod_Nivel1'], row['Nivel1_producto']))
        
    except FileNotFoundError:
        label_resultado.config(text="Error: El archivo no se encuentra.")
    except KeyError:
        label_resultado.config(text="Error: Las columnas necesarias no se encuentran en el archivo.")
    except Exception as e:
        label_resultado.config(text=f"Error: {str(e)}")

def crear_treeview(parent):
    frame_treeview = ttk.Frame(parent)
    frame_treeview.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    tree = ttk.Treeview(frame_treeview, columns=("Codigo", "Descripcion"), show="headings")
    tree.heading("Codigo", text="Código")
    tree.heading("Descripcion", text="Descripción")
    tree.column("Codigo", width=100, anchor="center")
    tree.column("Descripcion", width=300, anchor="w")

    scrollbar_vertical = ttk.Scrollbar(frame_treeview, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scrollbar_vertical.set)
    scrollbar_vertical.pack(side=tk.RIGHT, fill=tk.Y)

    scrollbar_horizontal = ttk.Scrollbar(frame_treeview, orient="horizontal", command=tree.xview)
    tree.configure(xscroll=scrollbar_horizontal.set)
    scrollbar_horizontal.pack(side=tk.BOTTOM, fill=tk.X)

    tree.pack(fill=tk.BOTH, expand=True)
    return tree

ventana = tk.Tk()
ventana.title("Buscador de Instituciones")
ventana.geometry("400x300")

label_identificador = tk.Label(ventana, text="Introduce un identificador de cédula:")
label_identificador.pack(pady=10)

entry_identificador = tk.Entry(ventana)
entry_identificador.pack(pady=5)

boton_buscar = tk.Button(ventana, text="Buscar", command=buscar_datos)
boton_buscar.pack(pady=10)

boton_graficar_frecuencia = tk.Button(ventana, text="Graficar Frecuencia por Año", command=graficar_frecuencia_por_ano)
boton_graficar_frecuencia.pack(pady=10)

boton_graficar_totales = tk.Button(ventana, text="Graficar Gastos Totales", command=graficar_gastos_totales)
boton_graficar_totales.pack(pady=10)

boton_graficar_nivel = tk.Button(ventana, text="Graficar Gastos por Nivel", command=graficar_gastos_por_nivel)
boton_graficar_nivel.pack(pady=10)

label_resultado = tk.Label(ventana, text="")
label_resultado.pack(pady=10)

ventana.mainloop()
