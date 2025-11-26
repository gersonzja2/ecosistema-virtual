import json
import os
from Logica.Logica import Ecosistema

def guardar_partida(ecosistema: Ecosistema, ruta_archivo: str):
    """
    Convierte el estado del ecosistema a un diccionario y lo guarda como JSON.
    Crea el directorio si no existe.
    """
    try:
        directorio = os.path.dirname(ruta_archivo)
        if not os.path.exists(directorio):
            os.makedirs(directorio)
            
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            datos = ecosistema.to_dict()
            json.dump(datos, f, indent=2, ensure_ascii=False)
        print(f"Partida guardada exitosamente en {ruta_archivo}")
    except Exception as e:
        print(f"Error al guardar la partida en {ruta_archivo}: {e}")

def cargar_partida(ruta_archivo: str) -> Ecosistema:
    """
    Carga una partida desde un archivo JSON y la convierte en un objeto Ecosistema.
    Si el archivo no existe, devuelve un nuevo Ecosistema.
    """
    if not os.path.exists(ruta_archivo):
        print(f"No se encontró el archivo de guardado: {ruta_archivo}. Se creará una nueva partida.")
        return Ecosistema()
        
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            datos = json.load(f)
            print(f"Partida cargada exitosamente desde {ruta_archivo}")
            return Ecosistema.from_dict(datos)
    except Exception as e:
        print(f"Error crítico al cargar la partida desde {ruta_archivo}: {e}. Se creará una nueva partida.")
        return Ecosistema()

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
        print(f"Usuario '{username}' creado.")