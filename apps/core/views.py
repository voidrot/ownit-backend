from django.shortcuts import render, get_object_or_404, redirect
from apps.users.models import User
from django.contrib.auth.models import Group
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib import messages
from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email
from allauth.account.models import EmailAddress
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_GET
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import reverse
from apps.chores.models import Chore, Location, Equipment, Task
from apps.chores.forms import ChoreForm, LocationForm, EquipmentForm, TaskForm
from django.http import HttpResponseBadRequest
from django.http import JsonResponse

class UserCreateForm(UserCreationForm):
    group = forms.ModelChoiceField(
        queryset=Group.objects.filter(name__in=['child', 'parent']),
        required=True,
        label="Role"
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'group')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add consistent widget classes so templates don't need add_class filter
        widgets = {
            'username': {'class': 'input input-bordered w-full'},
            'first_name': {'class': 'input input-bordered w-full'},
            'last_name': {'class': 'input input-bordered w-full'},
            'email': {'class': 'input input-bordered w-full'},
            'password1': {'class': 'input input-bordered w-full'},
            'password2': {'class': 'input input-bordered w-full'},
            'group': {'class': 'select select-bordered w-full'},
        }
        for name, attrs in widgets.items():
            if name in self.fields:
                existing = self.fields[name].widget.attrs
                existing.update(attrs)

# Create your views here.
@login_required
def settings_view(request):
    """View for user settings page."""
    return render(request, 'core/settings.html')

@login_required
def chores_view(request):
    """View for chores management page."""
    # Provide data for listing and creation forms
    chores = Chore.objects.select_related('location').prefetch_related('equipment', 'tasks').all()
    locations = Location.objects.all()
    equipment = Equipment.objects.all()
    tasks = Task.objects.all()
    # If ?edit=<id> is present, load that chore into the form for editing
    edit_id = request.GET.get('edit')
    if edit_id:
        edit_instance = get_object_or_404(Chore, id=edit_id)
        chore_form = ChoreForm(instance=edit_instance)
    else:
        chore_form = ChoreForm()
    # If ?edit_location=<id> is present, load that location into the location form for editing
    edit_loc_id = request.GET.get('edit_location')
    if edit_loc_id:
        try:
            edit_loc = get_object_or_404(Location, id=edit_loc_id)
            location_form = LocationForm(instance=edit_loc)
        except Exception:
            location_form = LocationForm()
    else:
        location_form = LocationForm()
    equipment_form = EquipmentForm()
    task_form = TaskForm()
    return render(
        request,
        'core/chores.html',
        {
            'chores': chores,
            'locations': locations,
            'equipment': equipment,
            'tasks': tasks,
            'chore_form': chore_form,
            'location_form': location_form,
            'equipment_form': equipment_form,
            'task_form': task_form,
        },
    )


@login_required
@require_POST
def save_chore(request):
    """Create or update a chore via POST. If 'id' present, update; else create."""
    data = request.POST.dict()
    chore_id = data.get('id')
    if chore_id:
        instance = get_object_or_404(Chore, id=chore_id)
        form = ChoreForm(request.POST, request.FILES, instance=instance)
    else:
        form = ChoreForm(request.POST, request.FILES)
    if form.is_valid():
        chore = form.save()
        # handle many-to-many from POST (equipment/tasks come as list)
        if 'equipment' in request.POST:
            chore.equipment.set(request.POST.getlist('equipment'))
        if 'tasks' in request.POST:
            chore.tasks.set(request.POST.getlist('tasks'))
        return redirect('core:chores')
    else:
        # Return the chores page with the bound form so validation errors are visible
        chores = Chore.objects.select_related('location').prefetch_related('equipment', 'tasks').all()
        locations = Location.objects.all()
        equipment = Equipment.objects.all()
        tasks = Task.objects.all()
        location_form = LocationForm()
        equipment_form = EquipmentForm()
        task_form = TaskForm()
        context = {
            'chores': chores,
            'locations': locations,
            'equipment': equipment,
            'tasks': tasks,
            'chore_form': form,
            'location_form': location_form,
            'equipment_form': equipment_form,
            'task_form': task_form,
        }
        return render(request, 'core/chores.html', context, status=400)


@login_required
@require_POST
def delete_chore(request, chore_id):
    chore = get_object_or_404(Chore, id=chore_id)
    chore.delete()
    messages.success(request, 'Chore deleted.')
    return redirect('core:chores')


@login_required
@require_GET
def location_detail_json(request, location_id):
    """Return JSON representation of a Location for client-side editing."""
    loc = get_object_or_404(Location, id=location_id)
    data = {
        'id': loc.id,
        'name': loc.name,
        'description': loc.description or '',
        'notes': loc.notes or [],
    }
    return JsonResponse(data)


@login_required
@require_POST
def delete_location(request, location_id):
    """Delete a location."""
    loc = get_object_or_404(Location, id=location_id)
    loc.delete()
    messages.success(request, 'Location deleted.')
    return redirect('core:chores')


@login_required
@require_POST
def create_location(request):
    form = LocationForm(request.POST)
    if form.is_valid():
        loc = form.save()
        return redirect('core:chores')
    # Return structured form errors to help debugging in client
    try:
        errors = form.errors.get_json_data()
    except Exception:
        errors = {k: form.errors.get(k) for k in form.errors}
    return JsonResponse({'errors': errors}, status=400)


@login_required
@require_POST
def save_location(request):
    """Create or update a location. If 'id' is present in POST, update the instance."""
    data = request.POST.dict()
    loc_id = data.get('id')
    if loc_id:
        instance = get_object_or_404(Location, id=loc_id)
        form = LocationForm(request.POST, instance=instance)
    else:
        form = LocationForm(request.POST)
    if form.is_valid():
        loc = form.save()
        # If this was an AJAX request, return JSON so the client can update the DOM
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
        if is_ajax:
            data = {
                'id': loc.id,
                'name': loc.name,
                'description': loc.description or '',
                'notes': loc.notes or [],
            }
            return JsonResponse({'success': True, 'location': data})
        return redirect('core:chores')
    try:
        errors = form.errors.get_json_data()
    except Exception:
        errors = {k: form.errors.get(k) for k in form.errors}
    return JsonResponse({'errors': errors}, status=400)


@login_required
@require_POST
def create_equipment(request):
    form = EquipmentForm(request.POST)
    if form.is_valid():
        eq = form.save()
        return redirect('core:chores')
    return HttpResponseBadRequest('Invalid equipment')


@login_required
@require_POST
def create_task(request):
    form = TaskForm(request.POST)
    if form.is_valid():
        t = form.save()
        return redirect('core:chores')
    return HttpResponseBadRequest('Invalid task')

@login_required
def behavior_view(request):
    """View for behavior management page."""
    return render(request, 'core/behavior.html')

@login_required
def users_view(request):
    """View for user management page."""
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            # Use django-allauth adapter to create/save the user so allauth hooks run
            adapter = get_adapter(request)
            user = adapter.new_user(request)
            # adapter.save_user knows how to populate the user from a form
            try:
                adapter.save_user(request, user, form, commit=True)
            except Exception:
                # Fallback: save minimal fields if adapter.save_user isn't available
                user.username = form.cleaned_data.get('username')
                user.email = form.cleaned_data.get('email')
                user.set_password(form.cleaned_data.get('password1'))
                user.save()

            group = form.cleaned_data['group']
            user.groups.add(group)

            # Ensure allauth EmailAddress is set up if available
            try:
                setup_user_email(request, user, [])
            except Exception:
                # ignore if allauth utility isn't available or fails
                pass

            # Mark the user's email as verified and primary in allauth
            try:
                email = (form.cleaned_data.get('email') or '').strip()
                if email:
                    obj, created = EmailAddress.objects.get_or_create(user=user, email=email)
                    obj.verified = True
                    obj.primary = True
                    obj.save()
            except Exception:
                # Don't block user creation on EmailAddress issues
                pass

            messages.success(request, 'User created successfully.')
            return redirect('core:users')
    else:
        form = UserCreateForm()
    # Exclude superusers from the management listing
    users = User.objects.prefetch_related('groups').exclude(is_superuser=True)
    return render(request, 'core/users.html', {'users': users, 'form': form})

@login_required
@require_POST
def delete_user(request, user_id):
    """Delete a user."""
    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.success(request, 'User deleted successfully.')
    return redirect('core:users')


@login_required
@require_POST
def change_password(request, user_id):
    """Allow privileged users (parents or superusers) to change another user's password via POST.

    Expects `password1` and `password2` in POST body. Returns JSON.
    """
    # permission: allow superusers or users in the 'parent' group
    if not (request.user.is_superuser or request.user.groups.filter(name='parent').exists()):
        return JsonResponse({'error': 'forbidden'}, status=403)

    target = get_object_or_404(User, id=user_id)
    if target.is_superuser:
        return JsonResponse({'error': 'cannot change superuser password'}, status=403)

    pw1 = (request.POST.get('password1') or '').strip()
    pw2 = (request.POST.get('password2') or '').strip()
    errors = []
    if not pw1:
        errors.append('Password is required.')
    if pw1 != pw2:
        errors.append('Passwords do not match.')
    if pw1 and len(pw1) < 8:
        errors.append('Password must be at least 8 characters.')
    if errors:
        return JsonResponse({'error': 'validation', 'messages': errors}, status=400)

    target.set_password(pw1)
    target.save()
    messages.success(request, f"Password for {target.username} updated.")
    return JsonResponse({'ok': True})