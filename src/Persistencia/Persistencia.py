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

def renombrar_usuario(old_name: str, new_name: str):
    """Renombra un directorio de usuario."""
    old_path = os.path.join("saves", old_name)
    new_path = os.path.join("saves", new_name)

    if not os.path.exists(old_path):
        print(f"Error: El usuario '{old_name}' no existe.")
        return False
    
    if os.path.exists(new_path):
        print(f"Error: El usuario '{new_name}' ya existe.")
        return False

    try:
        os.rename(old_path, new_path)
        print(f"Usuario renombrado de '{old_name}' a '{new_name}'.")
        return True
    except OSError as e:
        print(f"Error al renombrar usuario: {e}")
        return False

def eliminar_usuario(username: str):
    """Elimina un directorio de usuario y todo su contenido."""
    user_path = os.path.join("saves", username)
    if not os.path.exists(user_path):
        print(f"Error: El usuario '{username}' no existe para ser eliminado.")
        return False
    try:
        shutil.rmtree(user_path)
        print(f"Usuario '{username}' y todas sus partidas han sido eliminados.")
        return True
    except OSError as e:
        print(f"Error al eliminar el usuario '{username}': {e}")
        return False

def renombrar_partida(username: str, old_name: str, new_name: str):
    """Renombra un archivo de partida para un usuario."""
    user_path = os.path.join("saves", username)
    if not os.path.exists(user_path):
        print(f"Error: El directorio del usuario {username} no existe.")
        return False
    
    old_path = os.path.join(user_path, old_name)
    new_path = os.path.join(user_path, new_name)

    if os.path.exists(old_path):
        os.rename(old_path, new_path)
        print(f"Partida renombrada de {old_name} a {new_name}")
        return True
    return False

def eliminar_partida(username: str, save_name: str):
    """Elimina un archivo de partida para un usuario."""
    user_path = os.path.join("saves", username)
    save_path = os.path.join(user_path, save_name)

    if os.path.exists(save_path):
        try:
            os.remove(save_path)
            print(f"Partida '{save_name}' eliminada para el usuario '{username}'.")
            return True
        except OSError as e:
            print(f"Error al eliminar la partida '{save_name}': {e}")
            return False
    else:
        print(f"Error: No se encontró la partida '{save_name}' para eliminar.")
        return False

def obtener_fecha_guardado(ruta_archivo: str) -> str:
    """Lee solo la fecha de guardado de un archivo JSON sin cargar todo el contenido."""
    if not os.path.exists(ruta_archivo):
        return None
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            # Asumimos que la fecha está en las primeras líneas para una lectura rápida.
            # Esto es una optimización; para archivos grandes, cargar todo el JSON sería lento.
            data = json.load(f)
            return data.get("fecha_guardado")
    except (IOError, json.JSONDecodeError):
        return None

def obtener_ciclo_guardado(ruta_archivo: str) -> tuple:
    """Lee el día y la hora de un archivo de guardado."""
    if not os.path.exists(ruta_archivo):
        return None
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            data = json.load(f)
            dia = data.get("dia_total")
            hora = data.get("hora_actual")
            if dia is not None and hora is not None:
                return dia, hora
            return None
    except (IOError, json.JSONDecodeError):
        return None

def obtener_info_poblacion(ruta_archivo: str) -> tuple:
    """Lee la cantidad de animales y plantas de un archivo de guardado."""
    if not os.path.exists(ruta_archivo):
        return None
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            data = json.load(f)
            animales = data.get("cantidad_animales") # Esta clave ya incluye a los peces desde Logica.py
            plantas = data.get("cantidad_plantas")
            if animales is not None and plantas is not None:
                return animales, plantas
            return None
    except (IOError, json.JSONDecodeError):
        return None