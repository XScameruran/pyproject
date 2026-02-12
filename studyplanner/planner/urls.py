from django.urls import path
from . import views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),

    path('courses/', views.CourseListView.as_view(), name='course_list'),
    path('courses/add/', views.CourseCreateView.as_view(), name='course_add'),
    path('courses/<int:pk>/edit/', views.CourseUpdateView.as_view(), name='course_edit'),
    path('courses/<int:pk>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),

    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('tasks/add/', views.TaskCreateView.as_view(), name='task_add'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('tasks/<int:pk>/edit/', views.TaskUpdateView.as_view(), name='task_edit'),
    path('tasks/<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),
    path('tasks/<int:pk>/toggle/', views.TaskToggleStatusView.as_view(), name='task_toggle'),

    path('reminders/', views.ReminderListView.as_view(), name='reminder_list'),
    path('reminders/add/', views.ReminderCreateView.as_view(), name='reminder_add'),
    path('reminders/<int:pk>/edit/', views.ReminderUpdateView.as_view(), name='reminder_edit'),
    path('reminders/<int:pk>/delete/', views.ReminderDeleteView.as_view(), name='reminder_delete'),

    path('calendar/', views.CalendarWeekView.as_view(), name='calendar_week'),
    path('calendar/add/', views.StudyEventCreateView.as_view(), name='event_add'),
    path('calendar/<int:pk>/edit/', views.StudyEventUpdateView.as_view(), name='event_edit'),
    path('calendar/<int:pk>/delete/', views.StudyEventDeleteView.as_view(), name='event_delete'),

    path('stats/', views.StatsView.as_view(), name='stats'),

    path('accounts/login/', views.UserLoginView.as_view(), name='login'),
    path('accounts/logout/', views.UserLogoutView.as_view(), name='logout'),
    path('accounts/signup/', views.SignUpView.as_view(), name='signup'),
]