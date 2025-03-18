from django.contrib import admin
from .models import UserProfile, TaskCategory, Task

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')

class TaskCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'created_at')
    list_filter = ('parent',)
    search_fields = ('name', 'description')

class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status', 'priority', 'assigned_to', 'due_date', 'created_by')
    list_filter = ('status', 'priority', 'category', 'assigned_to')
    search_fields = ('title', 'description')
    date_hierarchy = 'due_date'

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(TaskCategory, TaskCategoryAdmin)
admin.site.register(Task, TaskAdmin) 