import os
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

app = Flask(__name__)

# Configuración de seguridad. La API Key se leerá desde el servidor (Render).
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

@app.route('/')
def dashboard():
    """Renderiza la interfaz gráfica del sistema."""
    return render_template('index.html')

def compilar_prompt(modulo, datos):
    """
    Motor central: Ensambla el prompt estricto dependiendo del módulo, 
    inyectando las reglas de negocio, retención y ventas ocultas.
    """
    if modulo == "mod_1_universal":
        return f"""
        [IDENTIDAD]: Actúa como un {datos.get('rol')}.
        [CONTEXTO]: Considera los siguientes datos como base inamovible: {datos.get('contexto')}.
        [TAREA]: Ejecuta la siguiente orden: {datos.get('peticion')}.
        [RESTRICCIONES]: Actúa con profesionalismo ejecutivo. Sé directo y estratégico. Cero relleno. Si generas código, debe ser funcional y completo para copiar y pegar.
        [FORMATO DE SALIDA]: Entrega el resultado estrictamente como {datos.get('formato')}.
        """

    elif modulo == "mod_2_guiones":
        return f"""
        [IDENTIDAD Y TONO]: Eres un guionista experto en retención. Escribe estrictamente bajo este arquetipo: {datos.get('arquetipo_marca')}.
        [CONTEXTO DE MARCA]: Respeta los siguientes límites inquebrantables: {datos.get('limites_marca')}. Cumplimiento absoluto de normas de monetización de YouTube.
        [TAREA]: Desarrolla un guion de longitud {datos.get('longitud')} basado en esta premisa: {datos.get('premisa')}.
        [ESTRUCTURA]: Aplica el framework narrativo: {datos.get('framework')}. Prohibido iniciar con saludos o introducciones genéricas. La primera línea debe atacar la curiosidad intelectual. Ritmo rápido, densidad alta.
        [FORMATO DE SALIDA]: Formato limpio, dividido por bloques visuales lógicos, listo para locución.
        """

    elif modulo == "mod_3_hooks":
        return f"""
        [IDENTIDAD]: Director de cinematografía generativa y experto en retención. Tono: {datos.get('arquetipo_marca')}.
        [SECUENCIA]: Bloque número {datos.get('num_bloque')}. Duración estricta: {datos.get('duracion')}.
        [CONTEXTO DE MEMORIA]: Continuación estricta de: {datos.get('memoria_raccord', 'N/A - Inicio absoluto')}. Mantén continuidad absoluta de personajes y voz.
        [TAREA]: Desarrolla este fragmento basado en: {datos.get('premisa')}.
        [RESTRICCIONES]: El texto de locución debe tener matemáticamente el límite de palabras asignado para {datos.get('duracion')}. Aplica disonancia cognitiva y vacío de información.
        [FORMATO DE SALIDA ESTRICTO]: 
        [AUDIO-VOZ]: (Texto exacto para el generador de voz).
        [PROMPT-VIDEO]: (Instrucción técnica en inglés, describiendo sujeto, cámara y continuidad visual).
        """

    elif modulo == "mod_4_empaquetado":
        return f"""
        [IDENTIDAD]: Estratega de contenido viral y experto SEO. Tono: {datos.get('arquetipo_marca')}.
        [CONTEXTO]: Analiza el siguiente contenido: {datos.get('guion')}.
        [TAREA]: Desarrolla el paquete de publicación para {datos.get('plataforma')} maximizando el CTR.
        [RESTRICCIONES]: 
        1. Títulos: No revelar la trama. Usar vacío de información y enfoque de {datos.get('enfoque_titulo')}.
        2. Imágenes: Solicitar estrictamente resolución 1920x1080 (--ar 16:9). Estilo de arte: {datos.get('estilo_visual')}. {datos.get('limites_marca')}. Prohibido generar formatos cuadrados.
        [FORMATO DE SALIDA ESTRICTO]:
        TÍTULOS: (5 opciones)
        PROMPT DE MINIATURA (En inglés): (1 instrucción técnica fotorrealista 16:9)
        DESCRIPCIÓN Y TAGS: (Párrafo SEO optimizado y etiquetas)
        """

    elif modulo == "mod_5_ugc_ventas":
        return f"""
        [ESTRATEGIA DE CAMPAÑA Y VENTAS]: Eres un Media Buyer Senior y experto en Neuro-Marketing. 
        [GATILLO PSICOLÓGICO]: Tu único objetivo es la conversión inmediata. Aplica la estrategia de: {datos.get('gatillo_ventas')}.
        [SECUENCIA]: Bloque {datos.get('num_bloque')}. Duración: {datos.get('duracion')}. Memoria de continuidad: {datos.get('memoria_raccord', 'Ninguna')}.
        [FASE 1: DISEÑO VISUAL]: Perfil de Avatar: {datos.get('perfil_avatar')}. El personaje debe ser 100% sintético. Integra el producto manteniendo proporciones y logotipos exactos.
        [FASE 2: ACCIÓN Y FÍSICA]: Modalidad: {datos.get('modalidad')}. Render 4K fotorrealista. Física inquebrantable: cero deformaciones del producto o anatomía. Formato estricto 9:16 (1080x1920).
        [FORMATO DE SALIDA ESTRICTO]:
        [PROMPT VISUAL - VIDEO]: (Instrucción técnica para IA de video).
        [GUION DE VENTA]: (Locución aplicando el sesgo psicológico para forzar urgencia de compra).
        """
        
    else:
        return "Error: Módulo no reconocido."

@app.route('/api/ejecutar', methods=['POST'])
def ejecutar_prompt():
    """Recibe la solicitud de la interfaz, ensambla el prompt y consulta a la IA."""
    try:
        payload = request.json
        modulo_id = payload.get('modulo_id')
        datos_usuario = payload.get('datos', {})

        if not modulo_id:
            return jsonify({'error': 'Falta el identificador del módulo.'}), 400

        # 1. Compilar el prompt con las reglas inyectadas
        prompt_blindado = compilar_prompt(modulo_id, datos_usuario)

        # 2. Ejecutar la llamada a la IA
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt_blindado)

        # 3. Devolver el resultado al usuario
        return jsonify({
            'status': 'success',
            'resultado_ia': response.text
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=puerto)
