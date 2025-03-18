from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse
from django.utils import timezone
from .models import TaskCategory, Task, UserProfile
from django.contrib.auth.models import User
from datetime import timedelta
import json
from django.contrib.auth import logout
from silk.profiling.profiler import silk_profile


from .decorators import profile_memory


@profile_memory
def sample_view(request):
    # Simulate memory consumption by creating a large list
    large_list = [i * 2 for i in range(1000000)]
    context = {
        'list_length': len(large_list)
    }
    return render(request, 'sample.html', context)

# Custom decorator for role-based access control
def role_required(roles=[]):
    def decorator(view_func):
        @login_required
        def wrapped_view(request, *args, **kwargs):
            try:
                user_profile = request.user.profile
                if user_profile.role in roles:
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, "You don't have permission to access this page.")
                    return redirect('dashboard')
            except UserProfile.DoesNotExist:
                messages.error(request, "User profile not found.")
                return redirect('login')
        return wrapped_view
    return decorator

@silk_profile(name="dashboard_view")
@login_required
def dashboard(request):
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    
    # Different dashboard views based on user role
    if user_profile.role in ['admin', 'manager']:
        # For admin and manager, show all tasks
        tasks = Task.objects.all()
        users = User.objects.all()
    else:
        # For regular users, show only their assigned tasks
        tasks = Task.objects.filter(assigned_to=user)
        users = User.objects.filter(id=user.id)
    
    # Task statistics
    total_tasks = tasks.count()
    pending_tasks = tasks.filter(status='pending').count()
    in_progress_tasks = tasks.filter(status='in_progress').count()
    completed_tasks = tasks.filter(status='completed').count()
    
    # Tasks by priority
    tasks_by_priority = {
        'low': tasks.filter(priority='low').count(),
        'medium': tasks.filter(priority='medium').count(),
        'high': tasks.filter(priority='high').count(),
        'urgent': tasks.filter(priority='urgent').count(),
    }
    
    # Tasks by category
    categories = TaskCategory.objects.filter(parent=None)
    tasks_by_category = []
    for category in categories:
        category_tasks = tasks.filter(category=category).count()
        subcategory_tasks = 0
        for subcategory in category.subcategories.all():
            subcategory_tasks += tasks.filter(category=subcategory).count()
        
        tasks_by_category.append({
            'name': category.name,
            'count': category_tasks + subcategory_tasks
        })
    
    # Tasks due soon (within 7 days)
    today = timezone.now()
    due_soon = tasks.filter(due_date__range=[today, today + timedelta(days=7)]).count()
    
    # Tasks by user (for admin and manager)
    tasks_by_user = []
    if user_profile.role in ['admin', 'manager']:
        for u in users:
            user_tasks = tasks.filter(assigned_to=u).count()
            tasks_by_user.append({
                'name': u.username,
                'count': user_tasks
            })
    
    context = {
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks,
        'tasks_by_priority': json.dumps(tasks_by_priority),
        'tasks_by_category': json.dumps([{'name': item['name'], 'count': item['count']} for item in tasks_by_category]),
        'due_soon': due_soon,
        'tasks_by_user': json.dumps([{'name': item['name'], 'count': item['count']} for item in tasks_by_user]),
        'recent_tasks': tasks.order_by('-created_at')[:5],
        'user_role': user_profile.role,
    }
    
    return render(request, 'dashboard.html', context)

@login_required
def task_list(request):
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    
    # Filter parameters
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    category_filter = request.GET.get('category', '')
    search_query = request.GET.get('search', '')
    
    # Different views based on user role
    if user_profile.role in ['admin', 'manager']:
        tasks = Task.objects.all()
    else:
        tasks = Task.objects.filter(assigned_to=user)
    
    # Apply filters
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    if category_filter:
        category = get_object_or_404(TaskCategory, id=category_filter)
        tasks = tasks.filter(category=category)
    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Get all categories for filter dropdown
    categories = TaskCategory.objects.all()
    
    context = {
        'tasks': tasks,
        'categories': categories,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'category_filter': category_filter,
        'search_query': search_query,
        'user_role': user_profile.role,
    }
    
    return render(request, 'task_list.html', context)

@role_required(roles=['admin', 'manager'])
def create_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        parent_id = request.POST.get('parent')
        
        if not name:
            messages.error(request, 'Category name is required.')
            return redirect('create_category')
        
        parent = None
        if parent_id:
            parent = get_object_or_404(TaskCategory, id=parent_id)
        
        TaskCategory.objects.create(
            name=name,
            description=description,
            parent=parent
        )
        
        messages.success(request, 'Category created successfully.')
        return redirect('create_category')
    
    # Get all categories for parent dropdown
    categories = TaskCategory.objects.all()
    
    return render(request, 'create_category.html', {'categories': categories})

@login_required
def create_task(request):
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    
    # Only admin and manager can assign tasks to any user
    if user_profile.role in ['admin', 'manager']:
        users = User.objects.all()
    else:
        users = User.objects.filter(id=user.id)
    
    categories = TaskCategory.objects.all()
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        assigned_to_id = request.POST.get('assigned_to')
        status = request.POST.get('status')
        priority = request.POST.get('priority')
        due_date = request.POST.get('due_date')
        
        # Validate required fields
        if not all([title, category_id, assigned_to_id, status, priority, due_date]):
            messages.error(request, 'All fields are required.')
            return redirect('create_task')
        
        category = get_object_or_404(TaskCategory, id=category_id)
        assigned_to = get_object_or_404(User, id=assigned_to_id)
        
        # Regular users can only assign tasks to themselves
        if user_profile.role == 'user' and assigned_to.id != user.id:
            messages.error(request, 'You can only create tasks for yourself.')
            return redirect('create_task')
        
        Task.objects.create(
            title=title,
            description=description,
            category=category,
            assigned_to=assigned_to,
            created_by=user,
            status=status,
            priority=priority,
            due_date=due_date
        )
        
        messages.success(request, 'Task created successfully.')
        return redirect('task_list')
    
    context = {
        'categories': categories,
        'users': users,
        'user_role': user_profile.role,
    }
    
    return render(request, 'create_task.html', context)

@login_required
def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    
    # Check permissions
    if user_profile.role == 'user' and task.assigned_to != user:
        messages.error(request, "You don't have permission to edit this task.")
        return redirect('task_list')
    
    # Only admin and manager can reassign tasks
    if user_profile.role in ['admin', 'manager']:
        users = User.objects.all()
    else:
        users = User.objects.filter(id=user.id)
    
    categories = TaskCategory.objects.all()
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        assigned_to_id = request.POST.get('assigned_to')
        status = request.POST.get('status')
        priority = request.POST.get('priority')
        due_date = request.POST.get('due_date')
        
        # Validate required fields
        if not all([title, category_id, assigned_to_id, status, priority, due_date]):
            messages.error(request, 'All fields are required.')
            return redirect('edit_task', task_id=task_id)
        
        category = get_object_or_404(TaskCategory, id=category_id)
        assigned_to = get_object_or_404(User, id=assigned_to_id)
        
        # Regular users can only assign tasks to themselves
        if user_profile.role == 'user' and assigned_to.id != user.id:
            messages.error(request, 'You can only assign tasks to yourself.')
            return redirect('edit_task', task_id=task_id)
        
        task.title = title
        task.description = description
        task.category = category
        task.assigned_to = assigned_to
        task.status = status
        task.priority = priority
        task.due_date = due_date
        task.save()
        
        messages.success(request, 'Task updated successfully.')
        return redirect('task_list')
    
    context = {
        'task': task,
        'categories': categories,
        'users': users,
        'user_role': user_profile.role,
    }
    
    return render(request, 'edit_task.html', context)

@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    
    # Check permissions
    if user_profile.role == 'user' and task.created_by != user:
        messages.error(request, "You don't have permission to delete this task.")
        return redirect('task_list')
    
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted successfully.')
        return redirect('task_list')
    
    return render(request, 'delete_task.html', {'task': task})

def logout_view(request):
    logout(request)
    return redirect('login') 