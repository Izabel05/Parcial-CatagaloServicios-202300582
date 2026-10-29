"""Comprueba API y frontend reales dentro de la red del harness."""
import time
import urllib.request
for attempt in range(30):
    try:
        for url in ['http://localhost:8000/health','http://frontend:5173']:
            # Vite permite localhost; el alias DNS de Compose solo sirve para llegar al contenedor.
            request=urllib.request.Request(url,headers={'Host':'localhost:5173'} if 'frontend' in url else {})
            with urllib.request.urlopen(request,timeout=3) as response:
                assert response.status==200
        print('API y frontend HTTP 200; base conectada')
        break
    except Exception:
        if attempt==29:raise
        time.sleep(1)
