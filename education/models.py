from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


ROLE_STUDENT = "student"
ROLE_TEACHER = "teacher"
ROLE_ADMINISTRATOR = "administrator"


# переводим процент выполнения теста в привычную пятибалльную оценку
def grade_from_percent(percent):
    if percent >= 85:
        return "5"
    if percent >= 70:
        return "4"
    if percent >= 55:
        return "3"
    return "2"


# менеджер гарантирует, что суперпользователь получает административную роль
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


# пользователь хранит роль в системе и дополнительные контактные данные
class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = ROLE_STUDENT, "Студент"
        TEACHER = ROLE_TEACHER, "Преподаватель"
        ADMINISTRATOR = ROLE_ADMINISTRATOR, "Администратор"

    email = models.EmailField("Электронная почта", blank=True, null=True)
    middle_name = models.CharField("Отчество", max_length=150, blank=True)
    phone = models.CharField("Телефон", max_length=32, blank=True)
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
        db_column="group_id",
        verbose_name="Учебная группа",
    )

    REQUIRED_FIELDS = ["first_name", "last_name"]
    objects = UserManager()

    class Meta:
        db_table = "users"
        ordering = ["last_name", "first_name", "username"]
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def save(self, *args, **kwargs):
        # нормализуем email и не держим учебную группу у преподавателей/администраторов
        if self.email:
            self.email = self.email.strip().lower()
        else:
            self.email = None
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


# учебная группа объединяет студентов и может иметь куратора-преподавателя
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
        db_table = "groups"
        ordering = ["name"]
        verbose_name = "Учебная группа"
        verbose_name_plural = "Учебные группы"

    def __str__(self):
        return self.name


# дисциплина связывает преподавателей, учебные группы и создаваемые тесты
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
        through="DisciplineGroup",
        through_fields=("discipline", "group"),
        related_name="disciplines",
        blank=True,
        verbose_name="Учебные группы",
    )

    class Meta:
        db_table = "disciplines"
        ordering = ["name"]
        verbose_name = "Дисциплина"
        verbose_name_plural = "Дисциплины"

    def __str__(self):
        return self.name


# явная связующая модель нужна для собственной таблицы disciplines_groups
class DisciplineGroup(models.Model):
    discipline = models.ForeignKey(
        Discipline,
        on_delete=models.CASCADE,
        db_column="discipline_id",
        related_name="group_links",
        verbose_name="Дисциплина",
    )
    group = models.ForeignKey(
        AcademicGroup,
        on_delete=models.CASCADE,
        db_column="group_id",
        related_name="discipline_links",
        verbose_name="Учебная группа",
    )

    class Meta:
        db_table = "disciplines_groups"
        unique_together = ("discipline", "group")
        verbose_name = "Связь дисциплины и группы"
        verbose_name_plural = "Связи дисциплин и групп"

    def __str__(self):
        return f"{self.discipline} - {self.group}"


# тест задает правила доступа, число попыток и привязку к группам
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
        through="TestGroup",
        through_fields=("test", "group"),
        related_name="tests",
        blank=True,
        verbose_name="Доступные группы",
    )
    max_attempts = models.PositiveIntegerField("Максимум попыток", default=1)
    available_from = models.DateTimeField("Доступен с", blank=True, null=True)
    available_to = models.DateTimeField("Доступен до", blank=True, null=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        db_table = "tests"
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
        return self.question_count

    def is_open_now(self):
        now = timezone.now()
        if self.available_from and now < self.available_from:
            return False
        if self.available_to and now > self.available_to:
            return False
        return True

    @property
    def is_published(self):
        return self.is_open_now()

    def completed_attempts_for(self, student):
        return self.attempts.filter(student=student, is_finished=True).count()

    def attempts_left_for(self, student):
        return max(self.max_attempts - self.completed_attempts_for(student), 0)

    def is_available_for(self, student):
        # тест доступен только в период публикации, нужной группе и при наличии попыток
        if not self.is_open_now():
            return False
        if self.groups.exists():
            if not student.academic_group:
                return False
            if not self.groups.filter(pk=student.academic_group_id).exists():
                return False
        return self.completed_attempts_for(student) < self.max_attempts

    def normalize_question_order(self):
        # после удаления вопроса восстанавливаем последовательную нумерацию
        for expected_order, question in enumerate(self.questions.order_by("order", "id"), start=1):
            if question.order != expected_order:
                self.questions.filter(pk=question.pk).update(order=expected_order)

    def __str__(self):
        return self.title


# явная связующая модель фиксирует доступность тестов для учебных групп
class TestGroup(models.Model):
    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        db_column="test_id",
        related_name="group_links",
        verbose_name="Тест",
    )
    group = models.ForeignKey(
        AcademicGroup,
        on_delete=models.CASCADE,
        db_column="group_id",
        related_name="test_links",
        verbose_name="Учебная группа",
    )

    class Meta:
        db_table = "tests_groups"
        unique_together = ("test", "group")
        verbose_name = "Связь теста и группы"
        verbose_name_plural = "Связи тестов и групп"

    def __str__(self):
        return f"{self.test} - {self.group}"


# вопрос хранит текст, необязательное изображение и позицию внутри теста
class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="questions", verbose_name="Тест")
    text = models.TextField("Текст вопроса")
    image = models.ImageField("Изображение", upload_to="questions/", blank=True, null=True)
    order = models.PositiveIntegerField("Порядок", default=1)

    class Meta:
        db_table = "questions"
        ordering = ["order", "id"]
        unique_together = ("test", "order")
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"

    def __str__(self):
        return f"{self.test.title}: вопрос {self.order}"


# вариант ответа отмечается как правильный и сортируется внутри вопроса
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
        db_table = "answer_options"
        ordering = ["order", "id"]
        unique_together = ("question", "order")
        verbose_name = "Вариант ответа"
        verbose_name_plural = "Варианты ответов"

    def __str__(self):
        return self.text


# попытка прохождения хранит прогресс студента и итоговую оценку
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
        db_table = "test_attempts"
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

    def ensure_answer_placeholders(self):
        # для каждого вопроса создается строка ответа, чтобы прогресс считался стабильно
        for question in self.test.questions.all():
            StudentAnswer.objects.get_or_create(attempt=self, question=question)

    def recalculate_results(self):
        # итоговый балл пересчитывается по выбранным вариантам при завершении попытки
        total_score = 0
        max_score = self.test.max_score
        for answer in self.answers.select_related("selected_option", "question"):
            answer.is_correct = bool(answer.selected_option and answer.selected_option.is_correct)
            if answer.is_correct:
                total_score += 1
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


# ответ студента связывает попытку, вопрос и выбранный вариант
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
        db_table = "student_answers"
        ordering = ["question__order", "id"]
        unique_together = ("attempt", "question")
        verbose_name = "Ответ студента"
        verbose_name_plural = "Ответы студентов"

    def clean(self):
        if self.selected_option and self.selected_option.question_id != self.question_id:
            raise ValidationError("Выбранный вариант не относится к данному вопросу.")

    def save(self, *args, **kwargs):
        # корректность ответа синхронизируется с выбранным вариантом при каждом сохранении
        self.is_correct = bool(self.selected_option and self.selected_option.is_correct)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ответ на вопрос {self.question.order}"


# журнал действий хранит важные события для администраторской аналитики
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
    ip_address = models.GenericIPAddressField("IP-адрес", blank=True, null=True)
    created_at = models.DateTimeField("Дата и время", auto_now_add=True)

    class Meta:
        db_table = "logs"
        ordering = ["-created_at"]
        verbose_name = "Журнал действия"
        verbose_name_plural = "Журнал действий"

    def __str__(self):
        return f"{self.get_action_type_display()}: {self.description}"
