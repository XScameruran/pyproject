from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from planner.models import Course, Task, StudyEvent


class Command(BaseCommand):
    help = 'Load demo data for StudyPlanner'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default=None, help='Username to attach demo data to')

    def handle(self, *args, **options):
        username = options.get('username')
        User = get_user_model()

        user = None
        if username:
            user = User.objects.filter(username=username).first()
            if not user:
                user = User.objects.create_user(username=username, password='demo_pass12345')
        if not user:
            user = User.objects.filter(is_superuser=True).first() or User.objects.first()
        if not user:
            user = User.objects.create_user(username='demo_user', password='demo_pass12345')

        Task.objects.filter(owner=user).delete()
        StudyEvent.objects.filter(owner=user).delete()
        Course.objects.filter(owner=user).delete()

        course1 = Course.objects.create(owner=user, name='Математика', teacher='Иванов И.И.', color='#FF6B6B')
        course2 = Course.objects.create(owner=user, name='История', teacher='Петрова А.А.', color='#4D96FF')

        now = timezone.now()
        tasks = [
            Task(owner=user, course=course1, title='Домашка 1', description='Алгебра: задачи 1-10', deadline=now + timezone.timedelta(days=2), priority=3, estimated_minutes=90),
            Task(owner=user, course=course1, title='Контрольная подготовка', description='Повторить темы 1-3', deadline=now + timezone.timedelta(days=6), priority=4, estimated_minutes=120),
            Task(owner=user, course=course1, title='Проект по геометрии', description='Сделать чертежи', deadline=now + timezone.timedelta(days=9), priority=2, estimated_minutes=180),
            Task(owner=user, course=course2, title='Конспект лекции', description='Лекция 5', deadline=now + timezone.timedelta(days=1), priority=2, estimated_minutes=45),
            Task(owner=user, course=course2, title='Реферат', description='Тема: революции', deadline=now + timezone.timedelta(days=10), priority=5, estimated_minutes=240),
            Task(owner=user, course=None, title='Общая задача', description='Повторить английские слова', deadline=now + timezone.timedelta(days=3), priority=1, estimated_minutes=30),
            Task(owner=user, course=None, title='Короткая заметка', description='Записать идеи', deadline=None, priority=1, estimated_minutes=20),
            Task(owner=user, course=course1, title='Практика', description='Дополнительные задачи', deadline=now + timezone.timedelta(days=4), priority=3, estimated_minutes=60),
            Task(owner=user, course=course2, title='Подготовка к тесту', description='Тест по теме', deadline=now + timezone.timedelta(days=5), priority=4, estimated_minutes=90),
            Task(owner=user, course=course2, title='Чтение главы', description='Глава 8', deadline=now + timezone.timedelta(days=7), priority=2, estimated_minutes=50),
        ]
        Task.objects.bulk_create(tasks)

        events = [
            StudyEvent(owner=user, title='Лекция по математике', start_at=now + timezone.timedelta(days=1, hours=2), end_at=now + timezone.timedelta(days=1, hours=3), location='Аудитория 101'),
            StudyEvent(owner=user, title='Семинар по истории', start_at=now + timezone.timedelta(days=3, hours=1), end_at=now + timezone.timedelta(days=3, hours=2), location='Аудитория 202'),
            StudyEvent(owner=user, title='Самостоятельная работа', start_at=now + timezone.timedelta(days=5, hours=4), end_at=now + timezone.timedelta(days=5, hours=6), location='Библиотека'),
        ]
        StudyEvent.objects.bulk_create(events)

        self.stdout.write(self.style.SUCCESS(f'Demo data created for {user.username}.'))