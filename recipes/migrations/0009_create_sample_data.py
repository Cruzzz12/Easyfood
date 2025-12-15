from django.db import migrations


def create_sample_data(apps, schema_editor):
    Recipe = apps.get_model('recipes', 'Recipe')
    Ingredient = apps.get_model('recipes', 'Ingredient')
    RecipeStep = apps.get_model('recipes', 'RecipeStep')

    # Crear algunos ingredientes comunes
    i_pasta, _ = Ingredient.objects.get_or_create(name='pasta')
    i_ajo, _ = Ingredient.objects.get_or_create(name='ajo')
    i_pollo, _ = Ingredient.objects.get_or_create(name='pechuga de pollo')

    # Receta 1
    r1, created = Recipe.objects.get_or_create(
        title='Pasta cremosa con pollo y champiñones',
        defaults={
            'description': 'Pasta con salsa cremosa y trozos de pollo.',
            'preparation': 'Cocinar la pasta. Saltear pollo y champiñones. Mezclar con crema.',
            'estimated_time': 30,
        }
    )
    if created:
        r1.ingredients.set([i_pasta, i_ajo, i_pollo])
        RecipeStep.objects.create(recipe=r1, order=1, description='Cocer la pasta según instrucciones')
        RecipeStep.objects.create(recipe=r1, order=2, description='Saltear pechuga de pollo hasta dorar')
        RecipeStep.objects.create(recipe=r1, order=3, description='Mezclar todo con la salsa cremosa')

    # Receta 2
    r2, created = Recipe.objects.get_or_create(
        title='Tortilla de verduras',
        defaults={
            'description': 'Tortilla esponjosa con verduras mixtas.',
            'preparation': 'Batir huevos y cuajar con verduras.',
            'estimated_time': 20,
        }
    )
    if created:
        RecipeStep.objects.create(recipe=r2, order=1, description='Picar verduras')
        RecipeStep.objects.create(recipe=r2, order=2, description='Batir huevos y mezclar con verduras')
        RecipeStep.objects.create(recipe=r2, order=3, description='Cuajar en sartén')

    # Receta 3
    r3, created = Recipe.objects.get_or_create(
        title='Ensalada de quinoa',
        defaults={
            'description': 'Ensalada fresca de quinoa y vegetales.',
            'preparation': 'Cocinar quinoa y mezclar con vegetales frescos.',
            'estimated_time': 15,
        }
    )
    if created:
        RecipeStep.objects.create(recipe=r3, order=1, description='Cocinar la quinoa')
        RecipeStep.objects.create(recipe=r3, order=2, description='Mezclar con tomates y pepino')


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0008_auto_20251215_0000'),
    ]

    operations = [
        migrations.RunPython(create_sample_data),
    ]
