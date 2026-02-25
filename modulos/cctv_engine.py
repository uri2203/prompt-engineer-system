import base64

class CCTVEngine:
    def __init__(self):
        pass

    def generar_imagen(self, prompt_visual):
        # MODO STANDBY: A la espera de conexión con NVIDIA RTX 3050
        # Cortamos el prompt solo para propósitos de visualización en el SVG
        prompt_corto = prompt_visual[:70] + "..." if len(prompt_visual) > 70 else prompt_visual
        
        dummy_svg = f"""
        <svg width="1920" height="1080" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="#060b14"/>
            <text x="50%" y="45%" font-family="monospace" font-size="45" font-weight="bold" fill="#3b82f6" text-anchor="middle">
                [ MOTOR CLOUD DESACTIVADO ]
            </text>
            <text x="50%" y="52%" font-family="monospace" font-size="25" fill="#64748b" text-anchor="middle">
                A LA ESPERA DEL ENLACE CON NODO LOCAL (NVIDIA RTX 3050)
            </text>
            <text x="50%" y="65%" font-family="monospace" font-size="18" fill="#eab308" text-anchor="middle">
                PROMPT EXTRAÍDO Y LISTO PARA TRANSFERENCIA:
            </text>
            <text x="50%" y="70%" font-family="monospace" font-size="16" fill="#94a3b8" text-anchor="middle">
                "{prompt_corto}"
            </text>
            <circle cx="50" cy="50" r="15" fill="#ef4444">
                <animate attributeName="opacity" values="1;0;1" dur="2s" repeatCount="indefinite"/>
            </circle>
            <text x="80" y="56" font-family="monospace" font-size="18" fill="#ef4444">REC</text>
        </svg>
        """
        img_b64 = base64.b64encode(dummy_svg.encode('utf-8')).decode('utf-8')
        return f"data:image/svg+xml;base64,{img_b64}"
