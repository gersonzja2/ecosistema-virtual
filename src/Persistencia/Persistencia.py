import json
import os
import shutil
from datetime import datetime
from ..Logica.Logica import Ecosistema

# Versión actual del simulador. Cambiar si la estructura de guardado se modifica.
SIMULATOR_VERSION = "1.0"

def guardar_partida(ecosistema: Ecosistema, ruta_archivo: str, autosave=False, sim_speed_multiplier=None, autosave_interval=None):
    """
    Guarda el estado del ecosistema de forma segura (atómica).
    1. Crea un backup del archivo de guardado existente.
    1. Guarda en un archivo temporal.
    2. Si tiene éxito, reemplaza el archivo de guardado original.
    """
    directorio = os.path.dirname(ruta_archivo)
    ruta_temporal = ruta_archivo + ".tmp"
    ruta_respaldo = ruta_archivo + ".bak"

    if not os.path.exists(directorio):
        os.makedirs(directorio)

    try:
        # 1. Crear un backup del archivo de guardado existente antes de sobrescribir.
        if os.path.exists(ruta_archivo):
            shutil.copy2(ruta_archivo, ruta_respaldo)
            print(f"Copia de seguridad creada en {ruta_respaldo}")

        # 2. Escribir en el archivo temporal
        with open(ruta_temporal, 'w', encoding='utf-8') as f:
            datos = ecosistema.to_dict(sim_speed_multiplier, autosave_interval)
            datos['metadata'] = {
                "save_date": datetime.now().isoformat(),
                "in_game_day": ecosistema.dia_total,
                "animal_count": len(ecosistema.animales)
            }
            datos['simulator_version'] = SIMULATOR_VERSION # Añadir la versión al guardar
            json.dump(datos, f, indent=2, ensure_ascii=False)

        # 3. Reemplazar el archivo original con el temporal de forma atómica
        # En sistemas POSIX, os.rename es atómico. En Windows, puede fallar si el destino existe.
        # shutil.move es una alternativa más portable y robusta.
        shutil.move(ruta_temporal, ruta_archivo)
        
        if not autosave:
            # Solo mostramos el mensaje de guardado exitoso para guardados manuales,
            # el autoguardado ya imprime su propio mensaje desde el controlador.
            print(f"Partida guardada exitosamente en: {ruta_archivo}")

    except (IOError, OSError, json.JSONDecodeError) as e:
        print(f"Error al guardar la partida: {e}")
    finally:
        # Si el archivo temporal aún existe, lo eliminamos para no dejar basura.
        if os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)
            print(f"Archivo temporal limpiado: {ruta_temporal}")

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
            return None, None, None

    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            datos = json.load(f)
            
            # Validación de versión
            # La metadata se añadió después, así que no la validamos para compatibilidad hacia atrás
            version_guardado = datos.get("simulator_version")
            if version_guardado and version_guardado != SIMULATOR_VERSION:
                print(f"Error: El archivo de guardado es de una versión incompatible.")
                print(f"  Versión del guardado: {version_guardado or 'Desconocida'}")
                print(f"  Versión del simulador: {SIMULATOR_VERSION}")
                print("  No se puede cargar la partida para evitar errores.")
                return None, None, None

            return Ecosistema.from_dict(datos)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error al cargar la partida desde {ruta_archivo}: {e}. Se devolverá None.")
        return None, None, None

def obtener_lista_usuarios():
    """Devuelve una lista con los nombres de los directorios de usuario en 'saves'."""
    if not os.path.exists("saves"):
        return []
    try:
        return [d for d in os.listdir("saves") if os.path.isdir(os.path.join("saves", d))]
    except OSError:
        return []

def obtener_metadatos_partida(ruta_archivo: str):
    """Lee y devuelve solo los metadatos de un archivo de guardado."""
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            datos = json.load(f)
            return datos.get("metadata")
    except (IOError, json.JSONDecodeError):
        return None

def obtener_partidas_usuario(username: str):
    """
    Devuelve una lista de diccionarios, cada uno con el nombre de archivo
    y los metadatos de una partida para un usuario.
    """
    user_path = os.path.join("saves", username)
    if not os.path.exists(user_path):
        return []
    
    partidas = []
    for filename in os.listdir(user_path):
        if filename.endswith(".json"):
            ruta_completa = os.path.join(user_path, filename)
            metadata = obtener_metadatos_partida(ruta_completa)
            partidas.append({"filename": filename, "metadata": metadata})
    
    return partidas

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
            datos = json.load(f)
            metadata = datos.get("metadata", {})
            return metadata.get("save_date")
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

def limpiar_archivos_temporales_antiguos(directorio_saves="saves"):
    """
    Busca y elimina archivos temporales (.tmp) en el directorio de guardado y sus subdirectorios.
    Ideal para ejecutar al inicio de la aplicación.
    """
    if not os.path.exists(directorio_saves):
        return

    for root, _, files in os.walk(directorio_saves):
        for file in files:
            if file.endswith(".tmp"):
                ruta_completa = os.path.join(root, file)
                print(f"Limpiando archivo temporal antiguo: {ruta_completa}")
                try:
                    os.remove(ruta_completa)
                except OSError as e:
                    print(f"Error al eliminar archivo temporal {ruta_completa}: {e}")