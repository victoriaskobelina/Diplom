from django.test import TestCase
from django.urls import reverse

from .models import AcademicGroup, AnswerOption, Discipline, Question, Test, TestAttempt, User


class PortalSmokeTests(TestCase):
    def setUp(self):
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
            points=2,
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

    def test_home_page_loads(self):
        response = self.client.get(reverse("education:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Контроль знаний")
        self.assertContains(response, "Вход в систему")

    def test_login_route_uses_home_page(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Вход в систему")

    def test_teacher_dashboard_loads(self):
        self.client.login(username="teacher1", password="StrongPass123")
        response = self.client.get(reverse("education:teacher_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.test.title)

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
        self.assertEqual(attempt.score, 2)
