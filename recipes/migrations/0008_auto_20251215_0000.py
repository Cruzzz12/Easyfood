# recipes/migrations/000X_load_initial_data.py

from django.core import management
from django.db import migrations
import traceback


# Función que será ejecutada al aplicar la migración
def load_initial_data(apps, schema_editor):
    # Intentar cargar fixtures, pero no detener el deploy si el archivo está corrupto
    try:
        management.call_command('loaddata', 'fixtures/initial_data.json')
    except Exception as e:
        # Registrar y continuar (evitar fallos en el build por problemas de encoding)
        print('WARNING: no se pudo cargar fixtures/initial_data.json:', e)
        traceback.print_exc()

class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0007_recipestep'),
    ]

    operations = [
        # Esto ejecuta la función 'load_initial_data'
        migrations.RunPython(load_initial_data),
    ]