import json
import os
from Logica.Logica import Ecosistema

def guardar_partida(ecosistema: Ecosistema, ruta_archivo: str):
    """
    Convierte el estado del ecosistema a un diccionario y lo guarda como JSON.
    Crea el directorio si no existe.
    """
    # Lanza excepciones (p. ej. IOError, OSError) que deben ser manejadas por la capa de Lógica.
    directorio = os.path.dirname(ruta_archivo)
    if not os.path.exists(directorio):
        os.makedirs(directorio)
        
    with open(ruta_archivo, 'w', encoding='utf-8') as f:
        datos = ecosistema.to_dict()
        json.dump(datos, f, indent=2, ensure_ascii=False)

def cargar_partida(ruta_archivo: str) -> Ecosistema:
    """
    Carga una partida desde un archivo JSON y la convierte en un objeto Ecosistema.
    Si el archivo no existe, devuelve un nuevo Ecosistema.
    """
    if not os.path.exists(ruta_archivo):
        # Es responsabilidad de la capa de Lógica decidir qué hacer si el archivo no existe.
        # Podría crear un nuevo Ecosistema o lanzar un error. Aquí devolvemos None.
        return None
        
    with open(ruta_archivo, 'r', encoding='utf-8') as f:
        datos = json.load(f)
        return Ecosistema.from_dict(datos)

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