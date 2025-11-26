import json

class Escenario:
    def __init__(self):
        self.cosas_varias = 1
    
    def mostrar(self):
        print(f"soy un escenario {self.cosas_varias}")
    
    def to_dict(self):
        """Convierte el objeto a diccionario para serialización JSON"""
        return {
            'cosas_varias': self.cosas_varias
        }
    
    @classmethod
    def from_dict(cls, data):
        """Crea un objeto Escenario desde un diccionario"""
        escenario = cls()
        escenario.cosas_varias = data.get('cosas_varias', 1)
        return escenario

class Persistencia:
    def __init__(self):
        self.cantidad = 0
    
    def guardar(self, escenario):
        try:
            with open("miarchivo.json", 'w', encoding='utf-8') as fos:
                # Convertimos el objeto a diccionario y luego a JSON
                json.dump(escenario.to_dict(), fos, indent=2, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"Error al guardar: {e}")
    
    def rescatar(self):
        try:
            with open("miarchivo.json", 'r', encoding='utf-8') as fis:
                # Cargamos el JSON y convertimos a objeto Escenario
                data = json.load(fis)
                e_rescatado = Escenario.from_dict(data)
                e_rescatado.mostrar()  
                return e_rescatado
        except Exception as e:
            raise Exception(f"Error al rescatar: {e}")

# Prueba del código
e = Escenario()
p = Persistencia()
p.guardar(e)
e2 = p.rescatar()
e2.mostrar()