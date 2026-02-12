from django import forms
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Course, Task, Reminder, StudyEvent

DT_FORMAT = '%Y-%m-%dT%H:%M'


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'teacher', 'color']
        widgets = {
            'color': forms.TextInput(attrs={'placeholder': '#RRGGBB'}),
        }


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['course', 'title', 'description', 'deadline', 'priority', 'estimated_minutes', 'status']
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format=DT_FORMAT),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['deadline'].input_formats = [DT_FORMAT]
        if self.user:
            self.fields['course'].queryset = Course.objects.filter(owner=self.user)

    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        if not deadline:
            return deadline
        created_at = self.instance.created_at or timezone.now()
        if deadline < created_at:
            raise forms.ValidationError('Deadline cannot be earlier than created_at.')
        return deadline

    def clean_priority(self):
        priority = self.cleaned_data.get('priority')
        if priority is None:
            return priority
        if priority < 1 or priority > 5:
            raise forms.ValidationError('Priority must be between 1 and 5.')
        return priority


class ReminderForm(forms.ModelForm):
    class Meta:
        model = Reminder
        fields = ['task', 'remind_at', 'is_sent']
        widgets = {
            'remind_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format=DT_FORMAT),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['remind_at'].input_formats = [DT_FORMAT]
        if self.user:
            self.fields['task'].queryset = Task.objects.filter(owner=self.user)


class StudyEventForm(forms.ModelForm):
    class Meta:
        model = StudyEvent
        fields = ['title', 'start_at', 'end_at', 'location', 'notes']
        widgets = {
            'start_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format=DT_FORMAT),
            'end_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format=DT_FORMAT),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_at'].input_formats = [DT_FORMAT]
        self.fields['end_at'].input_formats = [DT_FORMAT]

    def clean(self):
        cleaned = super().clean()
        start_at = cleaned.get('start_at')
        end_at = cleaned.get('end_at')
        if start_at and end_at and end_at < start_at:
            raise forms.ValidationError('End time must be after start time.')
        return cleaned


class SignUpForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})