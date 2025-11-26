import pygame
import os

# === BEGIN AUDIO INIT ===
# Reduce latencia y mejora estabilidad del mixer
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
try:
    if not pygame.mixer.get_init():
        pygame.mixer.init(44100, -16, 2, 512)
    pygame.mixer.set_num_channels(32)  # varios sonidos simultáneos
except Exception as e:
    print("Aviso: no se pudo inicializar pygame.mixer:", e)
class SoundBank:
    """
    Carga perezosa/cache de sonidos por especie.
    Busca en 'assets' y 'assets/Sonidos listos'.
    """
    _cache = {}
    _folders = ["assets", os.path.join("assets", "Sonidos listos"), os.path.join("assets", "Sounds"), "Sounds"]

    # Índices para los tipos de sonido
    APARECE, CAMINA, MUERE = 1, 2, 3
    _SOUND_INDICES = (APARECE, CAMINA, MUERE)

    # Mapa nombre de clase -> prefijo de archivo
    _alias = {
        "Cabra": "cabra",
        "Raton": "rata",      # clase Raton usa archivos "rata X.wav"
        "Halcon": "halcon",
        "Leopardo": "leopardo",
        "Conejo": "conejo",
        "Cerdo": "cerdo",
        "Mono": "mono",
        "Gato": "gato",
    }

    @classmethod
    def _find_file(cls, base, idx):
        name_patterns = [f"{base} {idx}", f"{base}{idx}", f"{base}_{idx}"]
        extensions = [".wav", ".mp3", ".ogg"]
        
        for folder in cls._folders:
            for name in name_patterns:
                for ext in extensions:
                    path = os.path.join(folder, name + ext)
                    if os.path.isfile(path):
                        return path
        print(f"[SoundBank] Aviso: No se encontró sonido para '{base}' (tipo {idx})")
        return None

    @classmethod
    def get_for(cls, class_name):
        if class_name not in cls._alias:
            return [None, None, None]
        key = cls._alias[class_name]
        if key in cls._cache:
            return cls._cache[key]

        sounds = [None] * len(cls._SOUND_INDICES)
        if pygame.mixer.get_init():
            for i in cls._SOUND_INDICES:
                path = cls._find_file(key, i)
                if path:
                    try:
                        s = pygame.mixer.Sound(path)
                        s.set_volume(0.65)  # volumen base
                        sounds[i - 1] = s
                    except Exception as e:
                        print(f"[SoundBank] No se pudo cargar {path}: {e}")
                        sounds[i-1] = None
        cls._cache[key] = sounds
        return sounds
# === END SOUNDBANK ===