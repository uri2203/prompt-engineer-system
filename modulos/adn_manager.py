import json
import os

class ADNManager:
    def __init__(self):
        self.db_path = 'proyectos_db.json'
        self._inicializar()

    def _inicializar(self):
        if not os.path.exists(self.db_path):
            # ADN base inamovible
            adn_inicial = {
                "La Viuda": {"estilo": "Suspenso", "tono": "Clínico", "reglas": "Voz baja, 4 fases."},
                "Monkygraff": {"estilo": "Geopolítica", "tono": "Guerra", "reglas": "Alta densidad."},
                "TuIALista": {"estilo": "Corporate Tech", "tono": "Software", "reglas": "Autoridad."},
                "Ezzenshop": {"estilo": "Hype", "tono": "Gamer", "reglas": "Energía."},
                "Yayika Digital": {"estilo": "Elegante", "tono": "Empático", "reglas": "Suavidad."},
                "Yayika Apparel": {"estilo": "Sátira", "tono": "Humor", "reglas": "TikTok."}
            }
            with open(self.db_path, 'w') as f:
                json.dump(adn_inicial, f)

    def cargar_todo(self):
        with open(self.db_path, 'r') as f: return json.load(f)

    def guardar(self, marca, adn):
        db = self.cargar_todo()
        db[marca] = adn
        with open(self.db_path, 'w') as f: json.dump(db, f)
        return {'status': 'success'}
