# App Móvil SASA-01 INEA (Lista para Render y PWABuilder / .APK)

Este paquete incluye todos los archivos configurados para desplegar en la nube (Render) y empaquetar directamente como aplicación nativa Android (`.apk`) mediante **PWABuilder**.

## Contenido del Paquete
- `app.py`: Servidor Flask + generador de PDF milimétrico (`ReportLab`), historial y exportación a Excel/CSV.
- `templates/index.html`: Interfaz móvil responsiva con firma autógrafa digital y soporte PWA.
- `static/manifest.json` y `static/sw.js`: Manifiesto y Service Worker requeridos por PWABuilder.
- `static/icono-192.png` y `static/icono-512.png`: Íconos institucionales en guinda y blanco.
- `requirements.txt` y `Procfile`: Archivos de despliegue automático para Render con `gunicorn`.

## Despliegue Rápido
1. Sube todos estos archivos a un repositorio en **GitHub**.
2. En **Render.com**, crea un nuevo **Web Service** conectado a ese repositorio:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
3. Copia tu enlace `https://...onrender.com`, pégalo en **pwabuilder.com** y descarga tu `.apk`.
