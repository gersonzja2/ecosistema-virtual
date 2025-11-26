import pygame
import os

# === BEGIN SOUNDBANK ===
class SoundBank:
    """
    Carga perezosa/cache de 3 sonidos por especie:
    1=aparece, 2=camina, 3=muere
    Busca en 'assets' y 'assets/Sonidos listos'.
    """
    _cache = {}
    _folders = ["assets", os.path.join("assets", "Sonidos listos")]

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
        candidates = [f"{base} {idx}.wav", f"{base}{idx}.wav", f"{base}_{idx}.wav"]
        for folder in cls._folders:
            for name in candidates:
                path = os.path.join(folder, name)
                if os.path.isfile(path):
                    return path
        return None

    @classmethod
    def get_for(cls, class_name):
        if class_name not in cls._alias:
            return [None, None, None]
        key = cls._alias[class_name]
        if key in cls._cache:
            return cls._cache[key]

        sounds = [None, None, None]
        if pygame.mixer.get_init():
            for i in (1, 2, 3):
                path = cls._find_file(key, i)
                if path:
                    try:
                        s = pygame.mixer.Sound(path)
                        s.set_volume(0.65)  # volumen base
                        sounds[i-1] = s
                    except Exception as e:
                        print(f"[SoundBank] No se pudo cargar {path}: {e}")
                        sounds[i-1] = None
        cls._cache[key] = sounds
        return sounds
# === END SOUNDBANK ===