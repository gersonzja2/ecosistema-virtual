import json
import os
import shutil
from ..Logica.Logica import Ecosistema

def guardar_partida(ecosistema: Ecosistema, ruta_archivo: str):
    """
    Guarda el estado del ecosistema de forma segura (atómica).
    1. Guarda en un archivo temporal.
    2. Si tiene éxito, reemplaza el archivo de guardado original.
    """
    directorio = os.path.dirname(ruta_archivo)
    ruta_temporal = ruta_archivo + ".tmp"
    ruta_respaldo = ruta_archivo + ".bak"

    if not os.path.exists(directorio):
        os.makedirs(directorio)

    try:
        # 1. Escribir en el archivo temporal
        with open(ruta_temporal, 'w', encoding='utf-8') as f:
            datos = ecosistema.to_dict()
            json.dump(datos, f, indent=2, ensure_ascii=False)

        # 2. Reemplazar el archivo original con el temporal de forma atómica
        # En sistemas POSIX, os.rename es atómico. En Windows, puede fallar si el destino existe.
        # shutil.move es una alternativa más portable y robusta.
        shutil.move(ruta_temporal, ruta_archivo)
        print(f"Partida guardada exitosamente en {ruta_archivo}")

    except (IOError, OSError, json.JSONDecodeError) as e:
        print(f"Error al guardar la partida: {e}")
        # Si el archivo temporal aún existe, lo eliminamos para no dejar basura.
        if os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)

def cargar_partida(ruta_archivo: str) -> Ecosistema:
    """
    Carga una partida desde un archivo JSON y la convierte en un objeto Ecosistema.
    Si el archivo no existe, devuelve un nuevo Ecosistema.
    """
    if not os.path.exists(ruta_archivo):
        # Si el archivo principal no existe, intenta cargar desde un respaldo.
        ruta_respaldo = ruta_archivo + ".bak"
        if os.path.exists(ruta_respaldo):
            print(f"Advertencia: No se encontró el archivo de guardado. Cargando desde respaldo {ruta_respaldo}")
            ruta_archivo = ruta_respaldo
        else:
            return None

    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            datos = json.load(f)
            return Ecosistema.from_dict(datos)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error al cargar la partida desde {ruta_archivo}: {e}. Se devolverá None.")
        return None

def obtener_lista_usuarios():
    """Devuelve una lista con los nombres de los directorios de usuario en 'saves'."""
    if not os.path.exists("saves"):
        return []
    try:
        return [d for d in os.listdir("saves") if os.path.isdir(os.path.join("saves", d))]
    except OSError:
        return []

def obtener_partidas_usuario(username: str):
    """Devuelve una lista de archivos de partida para un usuario."""
    user_path = os.path.join("saves", username)
    if not os.path.exists(user_path):
        return []
    return [f for f in os.listdir(user_path) if f.endswith(".json")]

def crear_usuario(username: str):
    """Crea un nuevo directorio de usuario si no existe."""
    user_path = os.path.join("saves", username)
    if not os.path.exists(user_path):
        os.makedirs(user_path)
        # La confirmación al usuario debe ser manejada por la capa de Vista,
        # a petición de la Lógica.