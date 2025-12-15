# recipes/migrations/000X_load_initial_data.py

from django.core import management
from django.db import migrations

# Función que será ejecutada al aplicar la migración
def load_initial_data(apps, schema_editor):
    # La ruta 'fixtures/initial_data.json' debe ser relativa a donde Django busca archivos
    management.call_command('loaddata', 'fixtures/initial_data.json') 

class Migration(migrations.Migration):

    dependencies = [
        # Asegúrate de que esta dependencia sea la migración anterior a esta
        # (Ejemplo: '0001_initial' o la última migración de tablas que tengas)
    ]

    operations = [
        # Esto ejecuta la función 'load_initial_data'
        migrations.RunPython(load_initial_data),
    ]