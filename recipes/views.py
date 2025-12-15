from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Avg
import re
from .models import Recipe, Ingredient
from .models import Comment
from .models import Rating
from .models import SavedRecipe
from .forms import RecipeForm
from .forms import RegisterForm
from django.forms import inlineformset_factory
from .models import RecipeStep
from .forms import RecipeStepForm
from django.core.paginator import Paginator
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse


# Vistas
def home(request):
    return render(request, 'recipes/home.html')


def _save_ingredients_for_recipe(recipe, ingredients_text):
    from .models import Ingredient
    if ingredients_text is None:
        return
    names = [i.strip() for i in ingredients_text.split(',') if i.strip()]
    if names:
        ings = []
        for name in names:
            ing, _ = Ingredient.objects.get_or_create(name=name)
            ings.append(ing)
        recipe.ingredients.set(ings)
    else:
        recipe.ingredients.clear()

def recipe_list(request):

    query = request.GET.get('q', '').strip()
    min_rating = request.GET.get('min_rating', '')

    qs = Recipe.objects.all().order_by('-created_at').select_related('author').prefetch_related('ingredients', 'ratings')

    min_time = None
    max_time = None
    text_query = query

    if query:
        range_match = re.search(r"(\d+)\s*[-–]\s*(\d+)", query)
        if range_match:
            try:
                min_time = int(range_match.group(1))
                max_time = int(range_match.group(2))
                text_query = re.sub(re.escape(range_match.group(0)), '', query).strip()
            except ValueError:
                min_time = None
                max_time = None
        else:
            nums = re.findall(r"\b(\d+)\b", query)
            if nums:
                try:
                    if len(nums) >= 2:
                        min_time = int(nums[0])
                        max_time = int(nums[1])
                       
                        text_query = re.sub(r"\b" + nums[0] + r"\b", '', query, count=1)
                        text_query = re.sub(r"\b" + nums[1] + r"\b", '', text_query, count=1).strip()
                    else:
                        max_time = int(nums[0])
                        text_query = re.sub(r"\b" + nums[0] + r"\b", '', query, count=1).strip()
                except ValueError:
                    min_time = None
                    max_time = None

    # Búsqueda de texto en título/ingredientes
    if text_query:
        qs = qs.filter(Q(title__icontains=text_query) | Q(ingredients__name__icontains=text_query))
    # Anotar calificación media
    qs = qs.annotate(avg_rating=Avg('ratings__value'))
    # filtrar por rating
    if min_rating:
        try:
            min_val = float(min_rating)
            qs = qs.filter(avg_rating__gte=min_val)
        except ValueError:
            pass


    if min_time is not None:
        qs = qs.filter(estimated_time__gte=min_time)
    if max_time is not None:
        qs = qs.filter(estimated_time__lte=max_time)

    qs = qs.distinct()

    # paginas (8 recetas por página)
    paginator = Paginator(qs, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Adjuntar calificación del usuario y marca de guardado a los elementos de la página
    saved_ids = set()
    recipe_ids = list(page_obj.object_list.values_list('id', flat=True))
    if request.user.is_authenticated and recipe_ids:
        saved_ids = set(SavedRecipe.objects.filter(user=request.user, recipe_id__in=recipe_ids).values_list('recipe_id', flat=True))

    for r in page_obj:
        r.avg_rating = getattr(r, 'avg_rating', None)
        if request.user.is_authenticated:
            ur = r.ratings.filter(user=request.user).first()
            r.user_rating = ur.value if ur else None
            r.saved = r.id in saved_ids
        else:
            r.user_rating = None
            r.saved = False

    rating_choices = [1, 2, 3, 4, 5]
    return render(request, 'recipes/recipe_list.html', {
        'recipes': page_obj,
        'q': query,
        'rating_choices': rating_choices,
        'min_rating': min_rating,
        'min_time': min_time,
        'max_time': max_time,
        'paginator': paginator,
    })


@login_required(login_url='recipes:login')
def saved_recipes_list(request):
    """Saved recipes"""
    qs = Recipe.objects.filter(savers__user=request.user).order_by('-created_at').select_related('author').prefetch_related('ingredients', 'ratings')
    qs = qs.annotate(avg_rating=Avg('ratings__value'))

    for r in qs:
        r.avg_rating = getattr(r, 'avg_rating', None)
        ur = r.ratings.filter(user=request.user).first()
        r.user_rating = ur.value if ur else None

    rating_choices = [1,2,3,4,5]
    return render(request, 'recipes/saved_list.html', {'recipes': qs, 'rating_choices': rating_choices})


@login_required(login_url='recipes:login')
def my_recipes(request):
    """User's recipes"""
    qs = Recipe.objects.filter(author=request.user).order_by('-created_at').select_related('author').prefetch_related('ingredients', 'ratings')
    qs = qs.annotate(avg_rating=Avg('ratings__value'))

    for r in qs:
        r.avg_rating = getattr(r, 'avg_rating', None)
        ur = r.ratings.filter(user=request.user).first()
        r.user_rating = ur.value if ur else None

    rating_choices = [1, 2, 3, 4, 5]
    return render(request, 'recipes/my_recipes.html', {'recipes': qs, 'rating_choices': rating_choices})


def recipe_detail(request, pk):
    # recetas
    recipe = get_object_or_404(Recipe, pk=pk)
    can_edit = request.user.is_authenticated and (request.user == recipe.author or request.user.is_superuser)

    # ratings
    ratings = recipe.ratings.all()
    avg_rating = None
    if ratings.exists():
        avg_rating = sum([r.value for r in ratings]) / ratings.count()
    user_rating = None
    if request.user.is_authenticated:
        try:
            user_rating = ratings.get(user=request.user).value
        except Rating.DoesNotExist:
            user_rating = None

    rating_choices = [1,2,3,4,5]
    saved = request.user.is_authenticated and SavedRecipe.objects.filter(user=request.user, recipe=recipe).exists()

    # comentariso
    comments = recipe.comments.select_related('author')[:50]
    from .forms import CommentForm
    comment_form = CommentForm()
    # pasos receta
    steps = recipe.steps.all()

    return render(request, 'recipes/recipe_detail.html', {
        'recipe': recipe,
        'can_edit': can_edit,
        'avg_rating': avg_rating,
        'user_rating': user_rating,
        'rating_choices': rating_choices,
        'saved': saved,
        'comments': comments,
        'comment_form': comment_form,
        'steps': steps,
    })



@login_required(login_url='recipes:login')
def add_comment(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method != 'POST':
        return redirect('recipes:detail', pk=pk)
    from .forms import CommentForm
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.recipe = recipe
        comment.save()

        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            html = f"<div class=\"mb-2\"><strong>{comment.author.username}</strong> <small class=\"text-muted\">{comment.created_at.strftime('%Y-%m-%d %H:%M')}</small><div>{comment.content}</div></div>"
            return JsonResponse({'success': True, 'html': html})
    return redirect('recipes:detail', pk=pk)


@login_required(login_url='recipes:login')
@login_required(login_url='recipes:login')
def recipe_create(request):
    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES)
        StepFormSet = inlineformset_factory(Recipe, RecipeStep, form=RecipeStepForm, fields=('order','description','image'), extra=0, can_delete=True)
        formset = StepFormSet(request.POST, request.FILES)
        if form.is_valid():

            recipe = form.save(commit=False)
            if request.user.is_authenticated:
                recipe.author = request.user

                if 'image' in request.FILES:
                    recipe.image = request.FILES['image']
                recipe.save()
                form.instance = recipe
                form.save()

                # save steps if provided
                if formset.is_valid():
                    formset.instance = recipe
                    formset.save()

                ingredients_text = request.POST.get('ingredients_text', '')
                _save_ingredients_for_recipe(recipe, ingredients_text)
                return redirect('recipes:list')
            else:
                return redirect('recipes:login')
    else:
        form = RecipeForm()
        StepFormSet = inlineformset_factory(Recipe, RecipeStep, form=RecipeStepForm, fields=('order','description','image'), extra=3, can_delete=True)
        formset = StepFormSet()
    return render(request, 'recipes/recipe_form.html', {'form': form, 'formset': formset})


@login_required(login_url='recipes:login')
def recipe_delete(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.user != recipe.author and not request.user.is_superuser:
        messages.error(request, 'No tienes permiso para eliminar esta receta.')
        return redirect('recipes:detail', pk=pk)
    if request.method == 'POST':
        recipe.delete()
        messages.success(request, 'Receta eliminada.')
        return redirect('recipes:list')
    # Confirm delete page
    return render(request, 'recipes/confirm_delete.html', {'recipe': recipe})

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('recipes:list')
    else:
        StepFormSet = inlineformset_factory(Recipe, RecipeStep, form=RecipeStepForm, fields=('order','description','image'), extra=3, can_delete=True)
        formset = StepFormSet()
        form = RegisterForm()
    return render(request, 'recipes/register.html', {'form': form})


def logout_view(request):
    
    auth_logout(request)
    return redirect('recipes:list')


@login_required(login_url='recipes:login')
def recipe_edit(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.user != recipe.author and not request.user.is_superuser:
        messages.error(request, 'No tienes permiso para editar esta receta.')
        return redirect('recipes:detail', pk=pk)
    StepFormSet = inlineformset_factory(Recipe, RecipeStep, form=RecipeStepForm, fields=('order','description','image'), extra=1, can_delete=True)

    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES, instance=recipe)
        formset = StepFormSet(request.POST, request.FILES, instance=recipe)
        if form.is_valid() and formset.is_valid():
            form.instance = recipe
            form.save()
            formset.save()

            ingredients_text = request.POST.get('ingredients_text', '')
            _save_ingredients_for_recipe(recipe, ingredients_text)
            messages.success(request, 'Receta actualizada correctamente.')
            return redirect('recipes:detail', pk=pk)
    else:
        initial = {'ingredients_text': ', '.join([i.name for i in recipe.ingredients.all()])}
        form = RecipeForm(instance=recipe, initial=initial)
        formset = StepFormSet(instance=recipe)

    return render(request, 'recipes/recipe_form.html', {'form': form, 'formset': formset})


def rate_recipe(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if not request.user.is_authenticated:
        return redirect('recipes:login')

    if request.method == 'POST':
        try:
            value = int(request.POST.get('rating'))
        except (TypeError, ValueError):
            messages.error(request, 'Valor de calificación inválido.')
            return redirect('recipes:detail', pk=pk)

        if value < 1 or value > 5:
            messages.error(request, 'La calificación debe estar entre 1 y 5.')
            return redirect('recipes:detail', pk=pk)

        obj, created = Rating.objects.update_or_create(recipe=recipe, user=request.user, defaults={'value': value})

    
        ratings = recipe.ratings.all()
        avg = None
        if ratings.exists():
            avg = sum([r.value for r in ratings]) / ratings.count()

    
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'avg': avg, 'user_rating': obj.value, 'pk': recipe.pk})

        messages.success(request, 'Gracias por calificar la receta.')
    return redirect('recipes:detail', pk=pk)


@login_required(login_url='recipes:login')
def toggle_save_recipe(request, pk):

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=400)
    recipe = get_object_or_404(Recipe, pk=pk)
    obj, created = SavedRecipe.objects.get_or_create(user=request.user, recipe=recipe)
    if not created:
        obj.delete()
        return JsonResponse({'success': True, 'saved': False})
    return JsonResponse({'success': True, 'saved': True})


@login_required(login_url='recipes:login')
@login_required(login_url='recipes:login')
def save_recipe_ajax(request):
  
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=400)

    
    pk = request.POST.get('pk') or request.POST.get('id')
    if pk:
       
        try:
            recipe = Recipe.objects.get(pk=int(pk))
        except (Recipe.DoesNotExist, ValueError):
            return JsonResponse({'success': False, 'error': 'Receta no encontrada.'}, status=404)
        if not (request.user == recipe.author or request.user.is_superuser):
            return JsonResponse({'success': False, 'error': 'No tienes permiso para editar esta receta.'}, status=403)
        form = RecipeForm(request.POST, request.FILES, instance=recipe)
        if not form.is_valid():
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
      
        recipe = form.save(commit=False)
        if 'image' in request.FILES:
            recipe.image = request.FILES['image']
        recipe.save()
        form.instance = recipe
        form.save()
        # procesar formset de pasos para actualización
        StepFormSet = inlineformset_factory(Recipe, RecipeStep, form=RecipeStepForm, fields=('order','description','image'), extra=0, can_delete=True)
        formset = StepFormSet(request.POST, request.FILES, instance=recipe)
        # Si el formset es inválido por falta de campos ocultos 'id', intentar autocompletarlos
        if not formset.is_valid():
            posted_keys = list(request.POST.keys())
            # detectar dinámicamente el prefijo del formset 
            prefix = None
            for k in posted_keys:
                if k.endswith('-TOTAL_FORMS'):
                    prefix = k[:-len('-TOTAL_FORMS')]
                    break
            if not prefix:
                prefix = 'form'
            try:
                total = int(request.POST.get(prefix + '-TOTAL_FORMS', 0))
            except (TypeError, ValueError):
                total = 0
            expected_ids = [f'{prefix}-{i}-id' for i in range(total)]
            missing_ids = [x for x in expected_ids if x not in posted_keys]
            if missing_ids:
                # intentar mapear por orden: obtener ids de pasos existentes indexados por orden
                existing = list(recipe.steps.order_by('order').values_list('id', 'order'))
                order_to_id = {o: sid for (sid, o) in existing}
                mutable = request.POST.copy()
                for i in range(total):
                    order_key = f'form-{i}-order'
                    try:
                        ord_val = mutable.get(order_key, None)
                        if ord_val is None or ord_val == '' :
                            continue
                        ord_int = int(ord_val)
                    except (TypeError, ValueError):
                        continue
                    if ord_int in order_to_id:
                        mutable[f'form-{i}-id'] = str(order_to_id[ord_int])
                # recrear formset con ids inyectados
                formset_try = StepFormSet(mutable, request.FILES, instance=recipe)
                if formset_try.is_valid():
                    formset_try.save()
                    # proceed normally
                else:
                    formset = formset_try
        # intento final: si el formset actual es válido, guardar
        if formset.is_valid():
            formset.save()
        else:
            flat = []
            for idx, ferr in enumerate(formset.errors):
                if not ferr:
                    continue
                parts = []
                for f, msgs in ferr.items():
                    if isinstance(msgs, (list, tuple)):
                        parts.append(f + ': ' + '; '.join(str(m) for m in msgs))
                    else:
                        parts.append(f + ': ' + str(msgs))
                flat.append('Paso %d - %s' % (idx+1, ' | '.join(parts)))
            if formset.non_form_errors():
                flat.extend([str(x) for x in formset.non_form_errors()])
            # incluir claves enviadas para depurar campos ocultos faltantes
            posted_keys = list(request.POST.keys())
            # detectar dinámicamente el prefijo del formset también para la info de depuración
            prefix = None
            for k in posted_keys:
                if k.endswith('-TOTAL_FORMS'):
                    prefix = k[:-len('-TOTAL_FORMS')]
                    break
            if not prefix:
                prefix = 'form'
            try:
                total = int(request.POST.get(prefix + '-TOTAL_FORMS', 0))
            except (TypeError, ValueError):
                total = 0
            expected_ids = [f'{prefix}-{i}-id' for i in range(total)]
            missing_ids = [x for x in expected_ids if x not in posted_keys]
            return JsonResponse({'success': False, 'errors': {'steps': flat}, 'posted_keys': posted_keys, 'missing_ids': missing_ids}, status=400)

        ingredients_text = request.POST.get('ingredients_text', '')
        _save_ingredients_for_recipe(recipe, ingredients_text)
        return JsonResponse({'success': True, 'pk': recipe.pk, 'title': recipe.title, 'updated': True})

  
    form = RecipeForm(request.POST, request.FILES)
    if not form.is_valid():
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    recipe = form.save(commit=False)
    recipe.author = request.user
    if 'image' in request.FILES:
        recipe.image = request.FILES['image']
    recipe.save()
    # procesar formset de pasos para creación
    StepFormSet = inlineformset_factory(Recipe, RecipeStep, form=RecipeStepForm, fields=('order','description','image'), extra=0, can_delete=True)
    formset = StepFormSet(request.POST, request.FILES, instance=recipe)
    if formset.is_valid():
        form.instance = recipe
        form.save()
        formset.save()
    else:
        # aún guardar la receta pero devolver errores aplanados sobre los pasos
        flat = []
        for idx, ferr in enumerate(formset.errors):
            if not ferr:
                continue
            parts = []
            for f, msgs in ferr.items():
                if isinstance(msgs, (list, tuple)):
                    parts.append(f + ': ' + '; '.join(str(m) for m in msgs))
                else:
                    parts.append(f + ': ' + str(msgs))
            flat.append('Paso %d - %s' % (idx+1, ' | '.join(parts)))
        if formset.non_form_errors():
            flat.extend([str(x) for x in formset.non_form_errors()])
        # información de depuración sobre lo enviado
        posted_keys = list(request.POST.keys())
        try:
            total = int(request.POST.get('form-TOTAL_FORMS', 0))
        except (TypeError, ValueError):
            total = 0
        expected_ids = [f'form-{i}-id' for i in range(total)]
        missing_ids = [x for x in expected_ids if x not in posted_keys]
        form.instance = recipe
        form.save()
        return JsonResponse({'success': False, 'errors': {'steps': flat}, 'posted_keys': posted_keys, 'missing_ids': missing_ids}, status=400)

    ingredients_text = request.POST.get('ingredients_text', '')
    _save_ingredients_for_recipe(recipe, ingredients_text)

    return JsonResponse({'success': True, 'pk': recipe.pk, 'title': recipe.title})
