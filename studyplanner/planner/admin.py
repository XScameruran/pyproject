from django.contrib import admin
from .models import Course, Task, Reminder, StudyEvent


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'color', 'created_at')
    search_fields = ('name', 'teacher')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'status', 'deadline', 'priority', 'estimated_minutes', 'created_at')
    list_filter = ('status', 'course')
    search_fields = ('title', 'description')


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ('task', 'remind_at', 'is_sent', 'created_at')
    list_filter = ('is_sent',)


@admin.register(StudyEvent)
class StudyEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_at', 'end_at', 'location')
    search_fields = ('title', 'location', 'notes')