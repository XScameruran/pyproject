from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Q, Sum, Count
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views import generic

from .forms import CourseForm, TaskForm, ReminderForm, StudyEventForm, SignUpForm, LoginForm
from .models import Course, Task, Reminder, StudyEvent


class UserLoginView(LoginView):
    template_name = 'registration/login.html'
    authentication_form = LoginForm

    def form_valid(self, form):
        messages.success(self.request, 'Добро пожаловать!')
        return super().form_valid(form)


class UserLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        messages.info(request, 'Вы вышли из системы.')
        return super().dispatch(request, *args, **kwargs)


class SignUpView(generic.CreateView):
    form_class = SignUpForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, 'Регистрация успешна. Добро пожаловать!')
        return response


class DashboardView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'planner/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        today = timezone.localdate()
        start_of_day = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
        end_of_day = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.max.time()))
        next_week = now + timedelta(days=7)

        context['tasks_today'] = Task.objects.filter(
            owner=self.request.user,
            deadline__range=(start_of_day, end_of_day)
        ).exclude(status=Task.Status.DONE)
        context['tasks_overdue'] = Task.objects.filter(
            owner=self.request.user,
            deadline__lt=now,
            status__in=[Task.Status.TODO, Task.Status.DOING],
        )
        context['tasks_next_7'] = Task.objects.filter(
            owner=self.request.user,
            deadline__gt=now,
            deadline__lte=next_week,
            status__in=[Task.Status.TODO, Task.Status.DOING],
        )
        week_start = today - timedelta(days=6)
        context['done_last_7'] = Task.objects.filter(
            owner=self.request.user,
            status=Task.Status.DONE,
            completed_at__date__gte=week_start,
            completed_at__date__lte=today,
        ).count()
        done_dates = set(Task.objects.filter(owner=self.request.user, status=Task.Status.DONE).values_list('completed_at__date', flat=True))
        streak = 0
        cursor = today
        while cursor in done_dates:
            streak += 1
            cursor -= timedelta(days=1)
        context['streak'] = streak
        return context


class CourseListView(LoginRequiredMixin, generic.ListView):
    model = Course
    template_name = 'planner/course_list.html'
    context_object_name = 'courses'

    def get_queryset(self):
        return Course.objects.filter(owner=self.request.user)


class CourseCreateView(LoginRequiredMixin, generic.CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'planner/course_form.html'
    success_url = reverse_lazy('course_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class CourseUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'planner/course_form.html'
    success_url = reverse_lazy('course_list')

    def get_queryset(self):
        return Course.objects.filter(owner=self.request.user)


class CourseDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Course
    template_name = 'planner/confirm_delete.html'
    success_url = reverse_lazy('course_list')

    def get_queryset(self):
        return Course.objects.filter(owner=self.request.user)


class TaskListView(LoginRequiredMixin, generic.ListView):
    model = Task
    template_name = 'planner/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 10

    def get_queryset(self):
        qs = Task.objects.filter(owner=self.request.user).select_related('course')
        status = self.request.GET.get('status')
        course = self.request.GET.get('course')
        deadline_range = self.request.GET.get('deadline')
        query = self.request.GET.get('q')

        if status:
            qs = qs.filter(status=status)
        if course:
            qs = qs.filter(course_id=course)
        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(description__icontains=query))

        now = timezone.now()
        today = timezone.localdate()
        start_of_day = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
        end_of_day = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.max.time()))
        if deadline_range == 'today':
            qs = qs.filter(deadline__range=(start_of_day, end_of_day))
        elif deadline_range == 'week':
            qs = qs.filter(deadline__gte=now, deadline__lte=now + timedelta(days=7))
        elif deadline_range == 'overdue':
            qs = qs.filter(deadline__lt=now)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses'] = Course.objects.filter(owner=self.request.user)
        context['now'] = timezone.now()
        tasks_page = context['tasks']
        task_ids = [task.id for task in tasks_page]
        reminders = Reminder.objects.filter(owner=self.request.user, task_id__in=task_ids).order_by('task_id', 'remind_at')
        nearest = {}
        for reminder in reminders:
            if reminder.task_id not in nearest:
                nearest[reminder.task_id] = reminder
        context['nearest_reminders'] = nearest
        return context


class TaskDetailView(LoginRequiredMixin, generic.DetailView):
    model = Task
    template_name = 'planner/task_detail.html'
    context_object_name = 'task'

    def get_queryset(self):
        return Task.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = self.object
        forecast = self._build_forecast(task)
        context['forecast'] = forecast
        context['now'] = timezone.now()
        return context

    def _build_forecast(self, task: Task) -> dict:
        if not task.deadline:
            return {'status': 'no_deadline'}

        now = timezone.now()
        if task.deadline <= now:
            return {'status': 'deadline_passed'}

        seven_days_ago = now - timedelta(days=7)
        done_minutes = Task.objects.filter(
            owner=self.request.user,
            status=Task.Status.DONE,
            completed_at__gte=seven_days_ago,
            completed_at__lte=now,
        ).aggregate(total=Sum('estimated_minutes'))['total'] or 0
        capacity_per_day = done_minutes / 7

        if capacity_per_day == 0:
            return {'status': 'no_data'}

        remaining_minutes = Task.objects.filter(
            owner=self.request.user,
            status__in=[Task.Status.TODO, Task.Status.DOING],
            deadline__gte=now,
            deadline__lte=task.deadline,
        ).aggregate(total=Sum('estimated_minutes'))['total'] or 0

        seconds_left = (task.deadline - now).total_seconds()
        days_left = max(1, int((seconds_left + 86399) // 86400))
        capacity_total = capacity_per_day * days_left

        return {
            'status': 'ok' if remaining_minutes <= capacity_total else 'risk',
            'remaining_minutes': remaining_minutes,
            'days_left': days_left,
            'capacity_per_day': capacity_per_day,
            'capacity_total': capacity_total,
        }


class TaskCreateView(LoginRequiredMixin, generic.CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'planner/task_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('task_list')


class TaskUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'planner/task_form.html'

    def get_queryset(self):
        return Task.objects.filter(owner=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('task_detail', kwargs={'pk': self.object.pk})


class TaskDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Task
    template_name = 'planner/confirm_delete.html'
    success_url = reverse_lazy('task_list')

    def get_queryset(self):
        return Task.objects.filter(owner=self.request.user)


class TaskToggleStatusView(LoginRequiredMixin, generic.View):
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, owner=request.user)
        if task.status == Task.Status.TODO:
            task.status = Task.Status.DOING
        elif task.status == Task.Status.DOING:
            task.status = Task.Status.DONE
        task.save()
        return redirect(request.META.get('HTTP_REFERER', reverse('task_list')))


class ReminderListView(LoginRequiredMixin, generic.ListView):
    model = Reminder
    template_name = 'planner/reminder_list.html'
    context_object_name = 'reminders'

    def get_queryset(self):
        return Reminder.objects.filter(owner=self.request.user).select_related('task')


class ReminderCreateView(LoginRequiredMixin, generic.CreateView):
    model = Reminder
    form_class = ReminderForm
    template_name = 'planner/reminder_form.html'
    success_url = reverse_lazy('reminder_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ReminderUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Reminder
    form_class = ReminderForm
    template_name = 'planner/reminder_form.html'
    success_url = reverse_lazy('reminder_list')

    def get_queryset(self):
        return Reminder.objects.filter(owner=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class ReminderDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Reminder
    template_name = 'planner/confirm_delete.html'
    success_url = reverse_lazy('reminder_list')

    def get_queryset(self):
        return Reminder.objects.filter(owner=self.request.user)


class CalendarWeekView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'planner/calendar_week.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        week_start_param = self.request.GET.get('week')
        if week_start_param:
            week_start = timezone.datetime.fromisoformat(week_start_param).date()
        else:
            today = timezone.localdate()
            week_start = today - timedelta(days=today.weekday())

        days = [week_start + timedelta(days=i) for i in range(7)]
        start_dt = timezone.make_aware(timezone.datetime.combine(days[0], timezone.datetime.min.time()))
        end_dt = timezone.make_aware(timezone.datetime.combine(days[-1], timezone.datetime.max.time()))

        events = StudyEvent.objects.filter(owner=self.request.user, start_at__range=(start_dt, end_dt)).order_by('start_at')
        grouped = {day: [] for day in days}
        for event in events:
            grouped[event.start_at.date()].append(event)

        context['week_start'] = week_start
        context['prev_week'] = week_start - timedelta(days=7)
        context['next_week'] = week_start + timedelta(days=7)
        context['days'] = days
        context['grouped_events'] = grouped
        return context


class StudyEventCreateView(LoginRequiredMixin, generic.CreateView):
    model = StudyEvent
    form_class = StudyEventForm
    template_name = 'planner/event_form.html'
    success_url = reverse_lazy('calendar_week')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class StudyEventUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = StudyEvent
    form_class = StudyEventForm
    template_name = 'planner/event_form.html'
    success_url = reverse_lazy('calendar_week')

    def get_queryset(self):
        return StudyEvent.objects.filter(owner=self.request.user)


class StudyEventDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = StudyEvent
    template_name = 'planner/confirm_delete.html'
    success_url = reverse_lazy('calendar_week')

    def get_queryset(self):
        return StudyEvent.objects.filter(owner=self.request.user)


class StatsView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'planner/stats.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        start_date = today - timedelta(days=13)

        done_qs = Task.objects.filter(
            owner=self.request.user,
            status=Task.Status.DONE,
            completed_at__date__gte=start_date,
            completed_at__date__lte=today,
        ).annotate(day=TruncDate('completed_at')).values('day').annotate(
            count=Count('id'),
            minutes=Sum('estimated_minutes'),
        )
        done_map = {row['day']: row for row in done_qs}

        daily = []
        for i in range(14):
            day = start_date + timedelta(days=i)
            row = done_map.get(day)
            daily.append({
                'day': day,
                'count': row['count'] if row else 0,
                'minutes': row['minutes'] if row else 0,
            })

        total_tasks = Task.objects.filter(owner=self.request.user).count()
        total_done = Task.objects.filter(owner=self.request.user, status=Task.Status.DONE).count()

        week_start = today - timedelta(days=6)
        done_last_7 = Task.objects.filter(
            owner=self.request.user,
            status=Task.Status.DONE,
            completed_at__date__gte=week_start,
            completed_at__date__lte=today,
        ).count()
        created_last_7 = Task.objects.filter(owner=self.request.user, created_at__date__gte=week_start, created_at__date__lte=today).count()
        completion_7 = int((done_last_7 / created_last_7) * 100) if created_last_7 else 0

        done_dates = set(Task.objects.filter(owner=self.request.user, status=Task.Status.DONE).values_list('completed_at__date', flat=True))
        streak = 0
        cursor = today
        while cursor in done_dates:
            streak += 1
            cursor -= timedelta(days=1)

        context['daily'] = daily
        context['total_tasks'] = total_tasks
        context['total_done'] = total_done
        context['completion_7'] = completion_7
        context['streak'] = streak
        return context
