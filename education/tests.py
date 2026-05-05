import shutil
import tempfile
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from .models import AcademicGroup, ActivityLog, AnswerOption, Discipline, Question, Test, TestAttempt, User


class PortalSmokeTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.media_override = override_settings(MEDIA_ROOT=self.media_root)
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)
        self.addCleanup(shutil.rmtree, self.media_root, ignore_errors=True)
        self.group = AcademicGroup.objects.create(name="ИС-21")
        self.teacher = User.objects.create_user(
            username="teacher1",
            password="StrongPass123",
            email="teacher@example.com",
            first_name="Иван",
            last_name="Петров",
            role=User.Role.TEACHER,
        )
        self.student = User.objects.create_user(
            username="student1",
            password="StrongPass123",
            email="student@example.com",
            first_name="Мария",
            last_name="Сидорова",
            role=User.Role.STUDENT,
            academic_group=self.group,
        )
        self.admin = User.objects.create_user(
            username="admin1",
            password="StrongPass123",
            email="admin@example.com",
            first_name="Алексей",
            last_name="Смирнов",
            role=User.Role.ADMINISTRATOR,
        )
        self.discipline = Discipline.objects.create(name="Информатика", code="INF-01")
        self.discipline.teachers.add(self.teacher)
        self.discipline.groups.add(self.group)
        self.test = Test.objects.create(
            title="Вводный тест",
            discipline=self.discipline,
            author=self.teacher,
            is_published=True,
            time_limit_minutes=30,
            max_attempts=2,
        )
        self.test.groups.add(self.group)
        self.question = Question.objects.create(
            test=self.test,
            text="Какой язык используется для серверной части проекта?",
            order=1,
        )
        self.correct_option = AnswerOption.objects.create(
            question=self.question,
            text="Python",
            is_correct=True,
            order=1,
        )
        AnswerOption.objects.create(
            question=self.question,
            text="Pascal",
            is_correct=False,
            order=2,
        )

    def _question_image_file(self):
        return SimpleUploadedFile(
            "question.gif",
            (
                b"GIF89a\x01\x00\x01\x00\x80\x00\x00"
                b"\x00\x00\x00\xff\xff\xff!\xf9\x04\x01"
                b"\x00\x00\x00\x00,\x00\x00\x00\x00\x01"
                b"\x00\x01\x00\x00\x02\x02D\x01\x00;"
            ),
            content_type="image/gif",
        )

    def test_home_page_loads(self):
        response = self.client.get(reverse("education:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Контроль знаний")
        self.assertContains(response, "Вход в систему")
        self.assertNotContains(response, "Что умеет система")
        self.assertNotContains(response, '>Главная</a>', html=False)

    def test_login_route_uses_home_page(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Вход в систему")

    def test_authenticated_user_is_redirected_from_home_page(self):
        self.client.login(username="student1", password="StrongPass123")
        response = self.client.get(reverse("education:home"))
        self.assertRedirects(response, reverse("education:student_dashboard"))

    def test_password_reset_page_is_informational_only(self):
        response = self.client.get(reverse("password_reset"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "centered-panel")
        self.assertContains(response, reverse("login"))
        self.assertNotContains(response, '>Р“Р»Р°РІРЅР°СЏ</a>', html=False)
        self.assertNotContains(response, 'name="email"')
        self.assertNotContains(response, "<form", html=False)

    def test_invalid_login_message_does_not_mention_case_sensitivity(self):
        response = self.client.post(
            reverse("login"),
            {"username": "student1", "password": "wrong-password"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Введите правильные имя пользователя и пароль.")
        self.assertNotContains(response, "чувствительны к регистру")

    def test_register_page_uses_single_column_form(self):
        response = self.client.get(reverse("education:register"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form-grid single-column")
        self.assertContains(response, '>Главная</a>', html=False)
        self.assertNotContains(response, 'name="role"')
        self.assertNotContains(response, 'name="photo"')
        self.assertNotContains(response, 'name="is_active"')
        self.assertNotContains(response, "Активный")
        self.assertContains(response, 'data-mask="email"')
        self.assertContains(response, 'data-mask="phone"')
        self.assertContains(response, 'data-max-digits="14"')
        self.assertContains(response, 'data-mask="person-name"')
        self.assertNotContains(response, "Используется для восстановления пароля.")
        self.assertNotContains(response, "Обязательное поле.")
        self.assertNotContains(response, "не более 14 цифр")

    def test_register_page_has_home_nav_button(self):
        response = self.client.get(reverse("education:register"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Главная")
        self.assertContains(response, 'href="/"', html=False)
        self.assertNotContains(response, "На главную")

    def test_registration_creates_student_even_if_role_is_posted(self):
        response = self.client.post(
            reverse("education:register"),
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "last_name": "Иванова",
                "first_name": "Анна",
                "middle_name": "Сергеевна",
                "phone": "+79000000000",
                "role": User.Role.TEACHER,
                "academic_group": self.group.pk,
                "password1": "NewStrongPass123",
                "password2": "NewStrongPass123",
            },
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="newuser")
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertEqual(user.academic_group, self.group)

    def test_registration_allows_empty_email(self):
        response = self.client.post(
            reverse("education:register"),
            {
                "username": "userwithoutemail",
                "email": "",
                "last_name": "Иванова",
                "first_name": "Анна",
                "middle_name": "Сергеевна",
                "phone": "+79000000000",
                "academic_group": self.group.pk,
                "password1": "NewStrongPass123",
                "password2": "NewStrongPass123",
            },
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="userwithoutemail")
        self.assertIsNone(user.email)

    def test_registration_normalizes_masked_phone(self):
        response = self.client.post(
            reverse("education:register"),
            {
                "username": "maskeduser",
                "email": "masked@example.com",
                "last_name": "Иванова",
                "first_name": "Анна",
                "middle_name": "Сергеевна",
                "phone": "8 (900) 123-45-67 890",
                "academic_group": self.group.pk,
                "password1": "NewStrongPass123",
                "password2": "NewStrongPass123",
            },
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="maskeduser")
        self.assertEqual(user.phone, "+7 (900) 123-45-67 890")

    def test_registration_normalizes_email(self):
        response = self.client.post(
            reverse("education:register"),
            {
                "username": "emailuser",
                "email": "Masked.User@Example.COM",
                "last_name": "Иванова",
                "first_name": "Анна",
                "middle_name": "Сергеевна",
                "phone": "8 (900) 123-45-67",
                "academic_group": self.group.pk,
                "password1": "NewStrongPass123",
                "password2": "NewStrongPass123",
            },
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="emailuser")
        self.assertEqual(user.email, "masked.user@example.com")

    def test_registration_rejects_phone_longer_than_14_digits(self):
        response = self.client.post(
            reverse("education:register"),
            {
                "username": "longphoneuser",
                "email": "longphone@example.com",
                "last_name": "Иванова",
                "first_name": "Анна",
                "middle_name": "Сергеевна",
                "phone": "8 (900) 123-45-67 8901",
                "academic_group": self.group.pk,
                "password1": "NewStrongPass123",
                "password2": "NewStrongPass123",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "не более 14 цифр")

    def test_teacher_dashboard_loads(self):
        self.client.login(username="teacher1", password="StrongPass123")
        response = self.client.get(reverse("education:teacher_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.test.title)
        self.assertNotContains(response, "Завершённых попыток")

    def test_report_detail_moves_student_attempts_below(self):
        self.client.login(username="teacher1", password="StrongPass123")
        response = self.client.get(reverse("education:report_detail", args=[self.test.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "dashboard-grid")
        self.assertContains(response, "panel panel-top-space")

    def test_new_test_page_uses_uniform_field_sizes(self):
        self.client.login(username="teacher1", password="StrongPass123")
        response = self.client.get(reverse("education:test_create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "uniform-field-sizes")
        self.assertContains(response, "form-grid single-column")
        self.assertNotContains(response, "Опубликован")
        self.assertNotContains(response, 'name="is_published"')

    def test_test_edit_page_keeps_publish_checkbox(self):
        self.client.login(username="teacher1", password="StrongPass123")
        response = self.client.get(reverse("education:test_update", args=[self.test.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Опубликован")
        self.assertContains(response, 'name="is_published"')

    def test_question_create_page_does_not_show_order_fields(self):
        self.client.login(username="teacher1", password="StrongPass123")
        response = self.client.get(reverse("education:question_create", args=[self.test.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Порядок")
        self.assertNotContains(response, "Баллы")
        self.assertNotContains(response, 'name="order"')
        self.assertNotContains(response, 'name="points"')
        self.assertNotContains(response, '-order"')
        self.assertContains(response, 'data-single-correct="true"')
        self.assertContains(response, 'window.enforceSingleCorrectCheckbox(this)')

    def test_question_create_assigns_order_automatically(self):
        self.client.login(username="teacher1", password="StrongPass123")
        response = self.client.post(
            reverse("education:question_create", args=[self.test.pk]),
            {
                "text": "Что используется для клиентской части проекта?",
                "options-TOTAL_FORMS": 4,
                "options-INITIAL_FORMS": 0,
                "options-MIN_NUM_FORMS": 0,
                "options-MAX_NUM_FORMS": 1000,
                "options-0-text": "JavaScript",
                "options-0-is_correct": "on",
                "options-1-text": "COBOL",
                "options-2-text": "",
                "options-3-text": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        question = Question.objects.get(text="Что используется для клиентской части проекта?")
        self.assertEqual(question.order, 2)
        self.assertEqual(list(question.options.values_list("order", flat=True)), [1, 2])

    def test_question_edit_page_uses_delete_button_for_image(self):
        self.question.image = self._question_image_file()
        self.question.save(update_fields=["image"])

        self.client.login(username="teacher1", password="StrongPass123")
        response = self.client.get(reverse("education:question_update", args=[self.test.pk, self.question.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Удалить изображение")
        self.assertContains(
            response,
            reverse("education:question_image_delete", args=[self.test.pk, self.question.pk]),
        )
        self.assertNotContains(response, "image-clear_id")
        self.assertContains(response, 'window.enforceSingleCorrectCheckbox(this)')

    def test_teacher_can_delete_question_image(self):
        self.question.image = self._question_image_file()
        self.question.save(update_fields=["image"])
        image_name = self.question.image.name

        self.client.login(username="teacher1", password="StrongPass123")
        response = self.client.post(
            reverse("education:question_image_delete", args=[self.test.pk, self.question.pk])
        )

        self.assertRedirects(response, reverse("education:question_update", args=[self.test.pk, self.question.pk]))
        self.question.refresh_from_db()
        self.assertFalse(self.question.image)
        self.assertFalse(Path(self.media_root, image_name).exists())

    def test_profile_page_shows_password_change_button(self):
        self.client.login(username="student1", password="StrongPass123")
        response = self.client.get(reverse("education:profile_edit"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Сменить пароль")
        self.assertNotContains(response, "Активный")
        self.assertNotContains(response, "Удалить фотографию")
        self.assertNotContains(response, '>Р“Р»Р°РІРЅР°СЏ</a>', html=False)
        self.assertNotContains(response, "remove-photo-button")
        self.assertNotContains(response, 'name="delete_photo"')
        self.assertNotContains(response, 'name="remove_photo"')
        self.assertNotContains(response, 'name="photo"')
        self.assertNotContains(response, "photo-clear_id")
        self.assertNotContains(response, "О себе")

    def test_dashboards_do_not_show_password_change_button(self):
        self.client.login(username="student1", password="StrongPass123")
        student_response = self.client.get(reverse("education:student_dashboard"))
        self.assertEqual(student_response.status_code, 200)
        self.assertNotContains(student_response, "Сменить пароль")

        self.client.login(username="teacher1", password="StrongPass123")
        teacher_response = self.client.get(reverse("education:teacher_dashboard"))
        self.assertEqual(teacher_response.status_code, 200)
        self.assertNotContains(teacher_response, "Сменить пароль")

        self.client.login(username="admin1", password="StrongPass123")
        admin_response = self.client.get(reverse("education:admin_dashboard"))
        self.assertEqual(admin_response.status_code, 200)
        self.assertNotContains(admin_response, "Сменить пароль")

    def test_admin_navigation_uses_administration_label(self):
        self.client.login(username="admin1", password="StrongPass123")
        response = self.client.get(reverse("education:home"))
        self.assertRedirects(response, reverse("education:admin_dashboard"))
        response = self.client.get(reverse("education:admin_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Администрирование")
        self.assertNotContains(response, ">Кабинет<", html=False)

    def test_admin_dashboard_does_not_show_attempts_stat(self):
        self.client.login(username="admin1", password="StrongPass123")
        response = self.client.get(reverse("education:admin_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Попытки")

    def test_admin_dashboard_shows_recent_previews_with_more_links(self):
        self.client.login(username="admin1", password="StrongPass123")
        created_users = []
        for index in range(6):
            created_users.append(
                User.objects.create_user(
                    username=f"recentuser{index}",
                    password="StrongPass123",
                    email=f"recent{index}@example.com",
                    first_name=f"Имя{index}",
                    last_name=f"Фамилия{index}",
                    role=User.Role.STUDENT,
                    academic_group=self.group,
                )
            )
        for index in range(6):
            ActivityLog.objects.create(
                user=self.admin,
                action_type=ActivityLog.ActionType.ADMIN,
                description=f"Запись журнала {index}",
            )

        response = self.client.get(reverse("education:admin_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "stats-strip-centered")
        self.assertContains(response, reverse("education:admin_user_list"))
        self.assertContains(response, reverse("education:activity_logs"))
        self.assertContains(response, "Подробнее", count=2)
        self.assertContains(response, created_users[-1].full_name)
        self.assertNotContains(response, created_users[0].full_name)
        self.assertContains(response, "Запись журнала 5")
        self.assertNotContains(response, "Запись журнала 0")

    def test_admin_can_delete_group(self):
        self.client.login(username="admin1", password="StrongPass123")
        group_list_response = self.client.get(reverse("education:group_list"))
        self.assertContains(group_list_response, reverse("education:group_delete", args=[self.group.pk]))
        response = self.client.post(reverse("education:group_delete", args=[self.group.pk]))
        self.assertRedirects(response, reverse("education:group_list"))
        self.assertFalse(AcademicGroup.objects.filter(pk=self.group.pk).exists())
        self.student.refresh_from_db()
        self.assertIsNone(self.student.academic_group)
        self.discipline.refresh_from_db()
        self.assertEqual(self.discipline.groups.count(), 0)

    def test_admin_dashboard_shows_only_three_recent_logs(self):
        self.client.login(username="admin1", password="StrongPass123")
        for index in range(6):
            ActivityLog.objects.create(
                user=self.admin,
                action_type=ActivityLog.ActionType.ADMIN,
                description=f"log-entry-{index}",
            )

        response = self.client.get(reverse("education:admin_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "log-entry-5")
        self.assertContains(response, "log-entry-4")
        self.assertContains(response, "log-entry-3")
        self.assertNotContains(response, "log-entry-2")

    def test_admin_can_delete_discipline(self):
        self.client.login(username="admin1", password="StrongPass123")
        discipline_list_response = self.client.get(reverse("education:discipline_list"))
        self.assertContains(
            discipline_list_response,
            reverse("education:discipline_delete", args=[self.discipline.pk]),
        )
        response = self.client.post(reverse("education:discipline_delete", args=[self.discipline.pk]))
        self.assertRedirects(response, reverse("education:discipline_list"))
        self.assertFalse(Discipline.objects.filter(pk=self.discipline.pk).exists())
        self.assertFalse(Test.objects.filter(pk=self.test.pk).exists())
        self.assertTrue(AcademicGroup.objects.filter(pk=self.group.pk).exists())
        self.assertTrue(User.objects.filter(pk=self.teacher.pk).exists())

    def test_admin_can_clear_activity_logs(self):
        self.client.login(username="admin1", password="StrongPass123")
        ActivityLog.objects.create(
            user=self.student,
            action_type=ActivityLog.ActionType.AUTH,
            description="Вход студента",
        )
        ActivityLog.objects.create(
            user=self.teacher,
            action_type=ActivityLog.ActionType.TEST,
            description="Создание теста",
        )

        response = self.client.get(reverse("education:activity_logs"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Очистить журнал")

        clear_response = self.client.post(reverse("education:activity_logs_clear"))
        self.assertEqual(clear_response.status_code, 302)
        self.assertEqual(ActivityLog.objects.count(), 0)

    def test_admin_user_form_does_not_show_about_field(self):
        self.client.login(username="admin1", password="StrongPass123")
        response = self.client.get(reverse("education:admin_user_create"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "О себе")
        self.assertNotContains(response, 'name="photo"')

    def test_admin_user_edit_uses_single_column_form(self):
        self.client.login(username="admin1", password="StrongPass123")
        response = self.client.get(reverse("education:admin_user_edit", args=[self.student.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form-grid single-column")
        self.assertNotContains(response, 'name="is_active"')
        self.assertNotContains(response, "Активный")

    def test_admin_can_delete_user(self):
        self.client.login(username="admin1", password="StrongPass123")
        list_response = self.client.get(reverse("education:admin_user_list"))
        self.assertContains(list_response, reverse("education:admin_user_delete", args=[self.student.pk]))

        response = self.client.post(reverse("education:admin_user_delete", args=[self.student.pk]))
        self.assertRedirects(response, reverse("education:admin_user_list"))
        self.assertFalse(User.objects.filter(pk=self.student.pk).exists())

    def test_admin_cannot_delete_own_account(self):
        self.client.login(username="admin1", password="StrongPass123")
        list_response = self.client.get(reverse("education:admin_user_list"))
        self.assertNotContains(list_response, reverse("education:admin_user_delete", args=[self.admin.pk]))
        response = self.client.post(reverse("education:admin_user_delete", args=[self.admin.pk]))
        self.assertRedirects(response, reverse("education:admin_user_list"))
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())

    def test_student_can_finish_test(self):
        self.client.login(username="student1", password="StrongPass123")
        response = self.client.get(reverse("education:start_test", args=[self.test.pk]))
        self.assertEqual(response.status_code, 302)
        attempt = TestAttempt.objects.get(student=self.student, test=self.test)
        save_response = self.client.post(
            reverse("education:save_answer", args=[attempt.pk, self.question.pk]),
            {"option_id": self.correct_option.pk},
        )
        self.assertJSONEqual(save_response.content, {"ok": True, "message": "Ответ сохранён"})
        finish_response = self.client.post(reverse("education:finish_attempt", args=[attempt.pk]))
        self.assertEqual(finish_response.status_code, 302)
        attempt.refresh_from_db()
        self.assertTrue(attempt.is_finished)
        self.assertEqual(attempt.score, 1)
