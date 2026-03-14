# Configuración Gunicorn para Render
# Aumenta el timeout para que las llamadas a Gemini no maten el worker

timeout = 300        # 5 minutos — suficiente para 3 llamadas a Gemini
workers = 1          # 1 worker — plan gratuito tiene RAM limitada
threads = 2          # 2 threads — permite polling mientras genera
worker_class = "sync"
