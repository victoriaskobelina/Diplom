from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


ROLE_STUDENT = "student"
ROLE_TEACHER = "teacher"
ROLE_ADMINISTRATOR = "administrator"


def grade_from_percent(percent):
    if percent >= 90:
        return "5"
    if percent >= 75:
        return "4"
    if percent >= 60:
        return "3"
    return "2"


class UserManager(DjangoUserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", ROLE_ADMINISTRATOR)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return super().create_superuser(username, email=email, password=password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = ROLE_STUDENT, "Студент"
        TEACHER = ROLE_TEACHER, "Преподаватель"
        ADMINISTRATOR = ROLE_ADMINISTRATOR, "Администратор"

    email = models.EmailField("Электронная почта", unique=True)
    middle_name = models.CharField("Отчество", max_length=150, blank=True)
    phone = models.CharField("Телефон", max_length=32, blank=True)
    bio = models.TextField("О себе", blank=True)
    role = models.CharField(
        "Роль",
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
    )
    academic_group = models.ForeignKey(
        "AcademicGroup",
        on_delete=models.SET_NULL,
        related_name="students",
        blank=True,
        null=True,
        verbose_name="Учебная группа",
    )

    REQUIRED_FIELDS = ["email", "first_name", "last_name"]
    objects = UserManager()

    class Meta:
        ordering = ["last_name", "first_name", "username"]
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def save(self, *args, **kwargs):
        if self.role != self.Role.STUDENT:
            self.academic_group = None
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return " ".join(
            part for part in [self.last_name, self.first_name, self.middle_name] if part
        ) or self.username

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER

    @property
    def is_administrator(self):
        return self.role == self.Role.ADMINISTRATOR or self.is_superuser

    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()})"


class AcademicGroup(models.Model):
    name = models.CharField("Название группы", max_length=50, unique=True)
    description = models.TextField("Описание", blank=True)
    curator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="curated_groups",
        limit_choices_to={"role": ROLE_TEACHER},
        verbose_name="Куратор",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Учебная группа"
        verbose_name_plural = "Учебные группы"

    def __str__(self):
        return self.name


class Discipline(models.Model):
    name = models.CharField("Дисциплина", max_length=120, unique=True)
    code = models.CharField("Код", max_length=20, blank=True)
    description = models.TextField("Описание", blank=True)
    teachers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="disciplines_taught",
        blank=True,
        limit_choices_to={"role": ROLE_TEACHER},
        verbose_name="Преподаватели",
    )
    groups = models.ManyToManyField(
        AcademicGroup,
        related_name="disciplines",
        blank=True,
        verbose_name="Учебные группы",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Дисциплина"
        verbose_name_plural = "Дисциплины"

    def __str__(self):
        return self.name


class Test(models.Model):
    title = models.CharField("Название теста", max_length=200)
    description = models.TextField("Описание", blank=True)
    discipline = models.ForeignKey(
        Discipline,
        on_delete=models.CASCADE,
        related_name="tests",
        verbose_name="Дисциплина",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_tests",
        limit_choices_to={"role": ROLE_TEACHER},
        verbose_name="Автор",
    )
    groups = models.ManyToManyField(
        AcademicGroup,
        related_name="tests",
        blank=True,
        verbose_name="Доступные группы",
    )
    time_limit_minutes = models.PositiveIntegerField("Лимит времени (мин.)", default=30)
    max_attempts = models.PositiveIntegerField("Максимум попыток", default=1)
    allow_retake = models.BooleanField("Разрешить повторное прохождение", default=False)
    is_published = models.BooleanField("Опубликован", default=False)
    available_from = models.DateTimeField("Доступен с", blank=True, null=True)
    available_to = models.DateTimeField("Доступен до", blank=True, null=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        ordering = ["-updated_at", "title"]
        verbose_name = "Тест"
        verbose_name_plural = "Тесты"

    def clean(self):
        if self.available_from and self.available_to and self.available_to <= self.available_from:
            raise ValidationError("Дата окончания должна быть позже даты начала.")
        if self.max_attempts < 1:
            raise ValidationError("Количество попыток должно быть не меньше 1.")

    @property
    def question_count(self):
        return self.questions.count()

    @property
    def max_score(self):
        return sum(question.points for question in self.questions.all())

    def is_open_now(self):
        now = timezone.now()
        if self.available_from and now < self.available_from:
            return False
        if self.available_to and now > self.available_to:
            return False
        return True

    def completed_attempts_for(self, student):
        return self.attempts.filter(student=student, is_finished=True).count()

    def attempts_left_for(self, student):
        return max(self.max_attempts - self.completed_attempts_for(student), 0)

    def is_available_for(self, student):
        if not self.is_published or not self.is_open_now():
            return False
        if self.groups.exists():
            if not student.academic_group:
                return False
            if not self.groups.filter(pk=student.academic_group_id).exists():
                return False
        completed_attempts = self.completed_attempts_for(student)
        if not self.allow_retake and completed_attempts >= 1:
            return False
        return completed_attempts < self.max_attempts

    def __str__(self):
        return self.title


class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="questions", verbose_name="Тест")
    text = models.TextField("Текст вопроса")
    image = models.ImageField("Изображение", upload_to="questions/", blank=True, null=True)
    points = models.PositiveIntegerField("Баллы", default=1)
    order = models.PositiveIntegerField("Порядок", default=1)

    class Meta:
        ordering = ["order", "id"]
        unique_together = ("test", "order")
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"

    def __str__(self):
        return f"{self.test.title}: вопрос {self.order}"


class AnswerOption(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="options",
        verbose_name="Вопрос",
    )
    text = models.CharField("Вариант ответа", max_length=255)
    is_correct = models.BooleanField("Правильный", default=False)
    order = models.PositiveIntegerField("Порядок", default=1)

    class Meta:
        ordering = ["order", "id"]
        unique_together = ("question", "order")
        verbose_name = "Вариант ответа"
        verbose_name_plural = "Варианты ответов"

    def __str__(self):
        return self.text


class TestAttempt(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attempts",
        limit_choices_to={"role": ROLE_STUDENT},
        verbose_name="Студент",
    )
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="attempts", verbose_name="Тест")
    attempt_number = models.PositiveIntegerField("Номер попытки", default=1)
    score = models.PositiveIntegerField("Набрано баллов", default=0)
    max_score = models.PositiveIntegerField("Максимум баллов", default=0)
    grade = models.CharField("Оценка", max_length=2, blank=True)
    started_at = models.DateTimeField("Начало", auto_now_add=True)
    completed_at = models.DateTimeField("Окончание", blank=True, null=True)
    is_finished = models.BooleanField("Завершён", default=False)

    class Meta:
        ordering = ["-started_at"]
        unique_together = ("student", "test", "attempt_number")
        verbose_name = "Попытка прохождения"
        verbose_name_plural = "Попытки прохождения"

    @property
    def progress_percent(self):
        total = self.answers.count()
        if total == 0:
            return 0
        answered = self.answers.exclude(selected_option__isnull=True).count()
        return int(answered / total * 100)

    @property
    def is_expired(self):
        if not self.test.time_limit_minutes:
            return False
        return timezone.now() >= self.started_at + timedelta(minutes=self.test.time_limit_minutes)

    @property
    def remaining_seconds(self):
        if not self.test.time_limit_minutes:
            return None
        delta = self.started_at + timedelta(minutes=self.test.time_limit_minutes) - timezone.now()
        return max(int(delta.total_seconds()), 0)

    def ensure_answer_placeholders(self):
        for question in self.test.questions.all():
            StudentAnswer.objects.get_or_create(attempt=self, question=question)

    def recalculate_results(self):
        total_score = 0
        max_score = self.test.max_score
        for answer in self.answers.select_related("selected_option", "question"):
            answer.is_correct = bool(answer.selected_option and answer.selected_option.is_correct)
            if answer.is_correct:
                total_score += answer.question.points
            answer.save(update_fields=["is_correct", "answered_at"])
        percent = (total_score / max_score * 100) if max_score else 0
        self.score = total_score
        self.max_score = max_score
        self.grade = grade_from_percent(percent) if max_score else "-"

    def finish(self):
        self.ensure_answer_placeholders()
        self.recalculate_results()
        self.completed_at = timezone.now()
        self.is_finished = True
        self.save(update_fields=["score", "max_score", "grade", "completed_at", "is_finished"])

    def __str__(self):
        return f"{self.student.full_name} - {self.test.title} ({self.attempt_number})"


class StudentAnswer(models.Model):
    attempt = models.ForeignKey(
        TestAttempt,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="Попытка",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="Вопрос",
    )
    selected_option = models.ForeignKey(
        AnswerOption,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="selected_answers",
        verbose_name="Выбранный вариант",
    )
    is_correct = models.BooleanField("Правильный ответ", default=False)
    answered_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        ordering = ["question__order", "id"]
        unique_together = ("attempt", "question")
        verbose_name = "Ответ студента"
        verbose_name_plural = "Ответы студентов"

    def clean(self):
        if self.selected_option and self.selected_option.question_id != self.question_id:
            raise ValidationError("Выбранный вариант не относится к данному вопросу.")

    def save(self, *args, **kwargs):
        self.is_correct = bool(self.selected_option and self.selected_option.is_correct)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ответ на вопрос {self.question.order}"


class ActivityLog(models.Model):
    class ActionType(models.TextChoices):
        AUTH = "auth", "Авторизация"
        PROFILE = "profile", "Профиль"
        TEST = "test", "Тест"
        ANALYTICS = "analytics", "Аналитика"
        ADMIN = "admin", "Администрирование"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="activity_logs",
        verbose_name="Пользователь",
    )
    action_type = models.CharField("Тип действия", max_length=20, choices=ActionType.choices)
    description = models.CharField("Описание", max_length=255)
    details = models.JSONField("Детали", blank=True, null=True)
    ip_address = models.GenericIPAddressField("IP-адрес", blank=True, null=True)
    created_at = models.DateTimeField("Дата и время", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Журнал действия"
        verbose_name_plural = "Журнал действий"

    def __str__(self):
        return f"{self.get_action_type_display()}: {self.description}"
