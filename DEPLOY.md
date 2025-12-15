Pasos rápidos para desplegar en Render y asegurar que se muestren imágenes (MEDIA)

1) Asegúrate de que `requirements.txt` contiene `whitenoise==6.5.0` (ya fijado).

2) Push al repo remoto (desde la raíz del proyecto):

```bash
git add requirements.txt DEPLOY.md
git commit -m "Pin whitenoise and add deploy notes"
git push origin main
```

3) En Render: en la página del servicio, fuerza un "Manual Deploy" o espera al siguiente build.

4) Durante el build, Render instalará las dependencias con `pip install -r requirements.txt`.

5) Nota importante sobre `MEDIA` (imágenes de recetas):
- WhiteNoise sólo sirve `STATIC` (archivos estáticos). Para servir `MEDIA` en producción debes usar almacenamiento externo (S3, DigitalOcean Spaces, Google Cloud Storage) o configurar un servicio estático que sirva la carpeta `media`.
- Opciones recomendadas:
  - Subir las imágenes a un bucket S3 y usar `django-storages` (configurar `DEFAULT_FILE_STORAGE`).
  - Usar un servicio de archivos estáticos que Render provea (si aplicable) y apuntar `MEDIA_URL`/`MEDIA_ROOT` correctamente.

6) Comandos útiles para el deploy (localmente antes de push):

```bash
# (opcional) crear virtualenv e instalar deps
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# collectstatic (Render también puede ejecutar esto durante build)
python manage.py collectstatic --noinput
```

7) Después del despliegue en Render, revisa los logs (Build y Runtime) para confirmar que no haya errores 500 y que las imágenes se sirvan correctamente.

Si quieres, puedo:
- Añadir `django-storages` y un ejemplo de configuración para S3 en `settings.py` y `requirements.txt`.
- Preparar un pequeño script para migrar/volver a subir las imágenes actuales a S3.

Avisame qué prefieres que haga siguiente.