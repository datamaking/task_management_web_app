### Project Setup and Initialization

To get this project up and running, follow these steps:

1. Create a new Django project and app:

   django-admin startproject taskmanager .
   
   python manage.py startapp tasks

2. Create the necessary directories:

   mkdir -p templates static/css static/js

3. Copy all the files to their respective locations as shown in the file paths.

4. Run migrations to create the database:

   python manage.py makemigrations
   python manage.py migrate

5. Create a superuser to access the admin panel:

   python manage.py createsuperuser

6. Create user profiles with different roles:

After creating users through the admin panel or registration, assign them appropriate roles (admin, manager, or regular user) through the UserProfile model.

7. Run the development server:

   python manage.py runserver


### User Management

Since we're using Django's built-in authentication system, you'll need to create user profiles for each user. After creating a user, you should create a corresponding UserProfile with the appropriate role.
You can do this through the Django admin interface or by creating a signal to automatically create a profile when a user is created:

signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance, role='user')

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance, role='user')


Then register the signals in your app's apps.py:

apps.py

from django.apps import AppConfig

class TasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tasks'

    def ready(self):
        import tasks.signals

Make sure to update your __init__.py to include the app configuration:

### System Features

This task management system includes:

Role-based access control: Three user roles (admin, manager, regular user) with different permissions

Task categories and subcategories: Hierarchical organization of tasks

Task creation and assignment: Create tasks and assign them to users

Task management: Edit, update status, and delete tasks

Dashboard with metrics: Visual representation of task data using Chart.js

Filtering and searching: Find tasks based on various criteria

-------------------------------------------------------------------------------

pip install memory_profiler psutil

