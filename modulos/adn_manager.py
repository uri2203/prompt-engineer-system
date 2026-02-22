import json
import os

class ADNManager:  # <--- ESTE NOMBRE DEBE SER EXACTO
    def __init__(self):
        self.db_path = 'proyectos_db.json'
        self._inicializar()

    def _inicializar(self):
        if not os.path.exists(self.db_path):
            # ADN Inicial basado en tu arquitectura de Módulo 0
            adn_inicial = {
                "La Viuda": {"identidad": "Suspenso Inmersivo", "reglas_duras": "Voz baja, 4 fases, sin gore."},
                "Monkygraff": {"identidad": "Geopolítica", "reglas_duras": "Alta densidad, documental de guerra."},
                "TuIALista": {"identidad": "Corporate Tech", "reglas_duras": "Autoridad técnica."}
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
