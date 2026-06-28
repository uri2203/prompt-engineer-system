# SISTEMA DE CLIPS DE VIDEO — ARQUITECTURA INDEPENDIENTE

## PRINCIPIO FUNDAMENTAL
Este sistema es **completamente independiente** del sistema actual (imágenes).
- El sistema actual (`nodo_xeon/worker_cpu.py`) NO se toca. Sigue funcionando igual.
- El sistema de clips vive en su propia carpeta: `nodo_clips/`.
- Se puede usar UNO U OTRO. Nunca se mezclan salvo que tú lo decidas (modo híbrido).
- Si el sistema de clips falla o no convence, se apaga y el de imágenes sigue intacto.

## LAS DOS OPCIONES QUE TENDRÁS
1. **OPCIÓN IMÁGENES (actual):** rápida, 15-20 videos largos/día. Lo que ya tienes.
2. **OPCIÓN CLIPS (nueva):** video real, ~2-3 videos largos/día (todo clips) o
   15-25/día (híbrido: clips solo en hook + momentos clave).

Tú eliges cuál corre, cambiando un solo parámetro al lanzar el lote.

---

## HARDWARE Y REPARTO DE TAREAS
- **RTX 3060 (12GB):** genera clips de video (modelo principal) + codificación final (NVENC).
- **RTX 3050 (8GB):** genera clips de video en paralelo (modelo más pequeño / clips cortos).
- **Máquina de voz (192.168.0.251):** genera la voz con XTTS, EN PARALELO con los clips.
- **Xeon:** coordina y ensambla (la codificación final se delega a la 3060 vía NVENC).

### Flujo en PARALELO (clave para no perder tanto tiempo)
```
   ┌─ 3060: genera clips de video ─┐
   ├─ 3050: genera clips de video ─┤ (en paralelo)
   └─ Voz (251): genera el audio ──┘ (en paralelo, no espera a los clips)
                  │
                  ▼
   Xeon ensambla (con codificación NVENC en la 3060)
```

---

## ESTRUCTURA DE CARPETAS (NUEVA, SEPARADA)
```
nodo_clips/                       ← TODO el sistema de clips, aparte
├── worker_clips.py               ← worker independiente (equivalente al worker_cpu pero para clips)
├── orquestador_clips.py          ← orquestador de lotes para clips
├── wan_server_3060.py            ← servidor de generación de clips en la 3060
├── wan_server_3050.py            ← servidor de generación de clips en la 3050
├── repartidor_clips.py           ← reparte los clips entre 3060 y 3050
├── ensamblador_nvenc.py          ← ensamblaje con codificación NVENC (3060)
└── config_clips.py               ← configuración (modelos, resoluciones, modo híbrido/completo)
```
NADA de esto toca `nodo_xeon/`. Son archivos nuevos.

---

## COMPONENTES (qué hace cada uno)

### 1. config_clips.py
Define todo lo configurable:
- MODO: "completo" (todo clips) o "hibrido" (clips solo en hook + N momentos).
- Modelo de video por tarjeta (WAN 2.2 5B u otro que quepa).
- Resolución y duración de clips (ajustable por VRAM).
- Cuántos clips en modo híbrido y en qué posiciones.
- IPs y puertos de los servidores.

### 2. wan_server_3060.py / wan_server_3050.py
Servidores Flask (como el motor_voz o el de SD) que reciben un prompt y devuelven
un clip de video. Uno por tarjeta. La 3050 usa modelo/resolución más ligeros.

### 3. repartidor_clips.py
Recibe la lista de clips a generar y los reparte entre las 2 tarjetas para que
trabajen en paralelo. Balancea según la velocidad de cada una.

### 4. worker_clips.py
El cerebro del sistema de clips. Equivalente al worker actual pero:
- Pide los clips a las tarjetas (vía repartidor).
- Pide la voz a la máquina 251 EN PARALELO.
- Cuando todo está listo, llama al ensamblador.
- Reutiliza TODA la lógica buena del worker actual: re-hooks, pronunciación,
  limpieza de asteriscos, estructura. Eso NO se reinventa, se copia.

### 5. ensamblador_nvenc.py
Toma los clips + el audio y arma el MP4 final usando NVENC (codificación en la
3060, mucho más rápida que el Xeon por CPU).

### 6. orquestador_clips.py
Como el orquestador actual: recibe el plan (qué canales, cuántos videos) y arma
la cola. Respeta el orden igual que el orquestador actual.

---

## PLAN DE IMPLEMENTACIÓN POR FASES
Se hace por partes, probando cada una antes de seguir. Nada a producción sin validar.

### FASE 0 — Preparación (sin generar nada todavía)
- [ ] Crear la carpeta `nodo_clips/` y `config_clips.py` con la estructura base.
- [ ] Confirmar qué modelo de video cabe en cada tarjeta (probar WAN 2.2 5B).
- [ ] Verificar que ComfyUI o el runtime de WAN está instalado en la PC GPU.

### FASE 1 — Generar UN clip (prueba mínima)
- [ ] wan_server_3060.py: que reciba un prompt y devuelva 1 clip.
- [ ] Probar generar 1 clip de 5s y medir cuánto tarda de verdad en TU 3060.
- [ ] Ver la calidad real (deformidades, movimiento).
- [ ] DECISIÓN: con el tiempo real medido, recalcular cuántos videos/día salen.

### FASE 2 — Las 2 tarjetas en paralelo
- [ ] wan_server_3050.py + repartidor_clips.py.
- [ ] Probar generar varios clips repartidos entre 3060 y 3050.
- [ ] Medir la mejora real de velocidad.

### FASE 3 — Ensamblaje con NVENC
- [ ] ensamblador_nvenc.py: juntar clips + audio con codificación en la 3060.
- [ ] Comparar tiempo vs el ensamblaje del Xeon actual.

### FASE 4 — Worker de clips completo
- [ ] worker_clips.py integrando: clips + voz en paralelo + ensamblaje.
- [ ] Copiar la lógica buena del worker actual (re-hooks, pronunciación, etc.).
- [ ] Generar 1 video completo de prueba (modo híbrido primero).

### FASE 5 — Orquestador y modo de elección
- [ ] orquestador_clips.py.
- [ ] Mecanismo para elegir: ¿este lote va por imágenes (actual) o por clips (nuevo)?

### FASE 6 — Pruebas y ajuste
- [ ] Probar los 6 canales con clips.
- [ ] Ajustar prompts de video por canal (como hicimos con las imágenes).
- [ ] Validar deformidades, sincronía, calidad.

---

## REGLAS DE SEGURIDAD (igual que siempre)
- El sistema de clips se desarrolla SOLO en la rama `diagnostico`, carpeta `nodo_clips/`.
- NO toca `nodo_xeon/` ni nada del sistema actual.
- NO es deploy de Render (corre en las máquinas locales, se descarga manual).
- Cada fase se valida antes de pasar a la siguiente.
- Si algo falla, el sistema de imágenes sigue funcionando intacto.

## NOTA DE EXPECTATIVAS (honesta)
- Modo COMPLETO (todo clips): ~2-3 videos largos/día. Para videos estrella.
- Modo HÍBRIDO (clips en hook + momentos): ~15-25 videos largos/día. Recomendado.
- La FASE 1 es la más importante: ahí medimos el tiempo REAL en tu 3060 y decidimos
  con números de verdad, no estimaciones.
