from django.urls import path
import apps.core.views as core_views

app_name = 'core'

urlpatterns = [
    path('behavior/', core_views.behavior_view, name='behavior'),
    path('settings/', core_views.settings_view, name='settings'),
    path('chores/', core_views.chores_view, name='chores'),
    path('users/', core_views.users_view, name='users'),
    path('users/delete/<int:user_id>/', core_views.delete_user, name='delete_user'),
    path('users/change_password/<int:user_id>/', core_views.change_password, name='change_password'),
    path('chores/save/', core_views.save_chore, name='save_chore'),
    path('chores/delete/<int:chore_id>/', core_views.delete_chore, name='delete_chore'),
    path('chores/location/create/', core_views.create_location, name='create_location'),
    path('chores/location/save/', core_views.save_location, name='save_location'),
    path('chores/location/delete/<int:location_id>/', core_views.delete_location, name='delete_location'),
    path('chores/location/<int:location_id>/json/', core_views.location_detail_json, name='location_detail_json'),
    path('chores/equipment/create/', core_views.create_equipment, name='create_equipment'),
    path('chores/equipment/save/', core_views.save_equipment, name='save_equipment'),
    path('chores/equipment/delete/<int:equipment_id>/', core_views.delete_equipment, name='delete_equipment'),
    path('chores/equipment/<int:equipment_id>/json/', core_views.equipment_detail_json, name='equipment_detail_json'),
    path('chores/task/create/', core_views.create_task, name='create_task'),
    path('chores/task/<int:task_id>/json/', core_views.task_detail_json, name='task_detail_json'),
    path('chores/task/save/', core_views.save_task, name='save_task'),
    path('chores/task/<int:task_id>/delete/', core_views.delete_task, name='delete_task'),
]
