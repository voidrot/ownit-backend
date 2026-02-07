from django.urls import path
from apps.core.views import behavior_view, settings_view, chores_view, users_view, delete_user, change_password
from apps.core.views import save_chore, delete_chore, create_location, create_equipment, create_task, delete_location, save_location, location_detail_json

app_name = 'core'

urlpatterns = [
    path('behavior/', behavior_view, name='behavior'),
    path('settings/', settings_view, name='settings'),
    path('chores/', chores_view, name='chores'),
    path('users/', users_view, name='users'),
    path('users/delete/<int:user_id>/', delete_user, name='delete_user'),
    path('users/change_password/<int:user_id>/', change_password, name='change_password'),
    path('chores/save/', save_chore, name='save_chore'),
    path('chores/delete/<int:chore_id>/', delete_chore, name='delete_chore'),
    path('chores/location/create/', create_location, name='create_location'),
    path('chores/location/save/', save_location, name='save_location'),
    path('chores/location/delete/<int:location_id>/', delete_location, name='delete_location'),
    path('chores/location/<int:location_id>/json/', location_detail_json, name='location_detail_json'),
    path('chores/equipment/create/', create_equipment, name='create_equipment'),
    path('chores/task/create/', create_task, name='create_task'),
]
