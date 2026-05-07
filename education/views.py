from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Max, Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import (
    AcademicGroupForm,
    ActivityLogFilterForm,
    AdminPasswordResetForm,
    AdminUserForm,
    AnswerOptionFormSet,
    DisciplineForm,
    LoginForm,
    ProfileForm,
    QuestionForm,
    SignUpForm,
    TeacherTestForm,
)
from .models import (
    AcademicGroup,
    ActivityLog,
    Discipline,
    Question,
    StudentAnswer,
    Test,
    TestAttempt,
    User,
)
from .utils import dashboard_url_for, log_activity, role_required


LEGAL_DOCUMENTS = {
    "privacy_policy": {
        "title": "Политика конфиденциальности",
        "subtitle": "Порядок обработки и защиты персональных данных пользователей веб-системы контроля учебного процесса БТЖТиС.",
        "sections": [
            {
                "title": "1. Общие положения",
                "paragraphs": [
                    "Настоящая Политика конфиденциальности определяет порядок обработки, хранения и защиты персональных данных пользователей веб-системы контроля учебного процесса БТЖТиС.",
                    "Использование системы означает ознакомление пользователя с настоящей Политикой и согласие с её условиями в части, относящейся к обработке персональных данных.",
                ],
            },
            {
                "title": "2. Какие данные обрабатываются",
                "paragraphs": [
                    "Система может обрабатывать следующие данные: имя пользователя, фамилию, имя, отчество, учебную группу, адрес электронной почты, номер телефона, сведения о прохождении тестов, результатах обучения и действиях в системе.",
                    "Электронная почта и телефон используются только в объёме, который пользователь указывает самостоятельно при регистрации или редактировании профиля.",
                ],
            },
            {
                "title": "3. Цели обработки данных",
                "paragraphs": [
                    "Персональные данные обрабатываются для регистрации и идентификации пользователей, организации доступа к учебным материалам, проведения тестирования, хранения результатов, анализа успеваемости и обеспечения информационной безопасности системы.",
                    "Также данные могут использоваться для администрирования учебных групп, дисциплин и прав доступа внутри образовательной платформы.",
                ],
            },
            {
                "title": "4. Порядок обработки и хранения",
                "paragraphs": [
                    "Обработка персональных данных осуществляется с использованием средств автоматизации и без их использования, если это необходимо для работы системы.",
                    "Доступ к персональным данным предоставляется только уполномоченным пользователям системы в пределах их роли: студенту, преподавателю или администратору.",
                    "Персональные данные хранятся не дольше, чем этого требуют цели их обработки, либо до момента удаления учётной записи и связанных с ней данных в установленном порядке.",
                ],
            },
            {
                "title": "5. Права пользователя",
                "paragraphs": [
                    "Пользователь вправе уточнять свои персональные данные, изменять их в профиле, а также обращаться к ответственным лицам образовательной организации по вопросам обработки и защиты персональных данных.",
                    "Пользователь вправе запросить прекращение обработки персональных данных, если это не противоречит требованиям законодательства и задачам образовательного процесса.",
                ],
            },
            {
                "title": "6. Заключительные положения",
                "paragraphs": [
                    "Администрация системы принимает необходимые организационные и технические меры для защиты персональных данных от неправомерного доступа, изменения, раскрытия или уничтожения.",
                    "Актуальная редакция настоящей Политики размещается в системе и применяется с момента публикации.",
                ],
            },
        ],
    },
    "personal_data_consent": {
        "title": "Согласие на обработку персональных данных",
        "subtitle": "Документ определяет объём и цели обработки персональных данных пользователя при работе с веб-системой БТЖТиС.",
        "sections": [
            {
                "title": "1. Предмет согласия",
                "paragraphs": [
                    "Пользователь, проходящий регистрацию в веб-системе контроля учебного процесса БТЖТиС, выражает согласие на обработку своих персональных данных в объёме, необходимом для функционирования системы.",
                ],
            },
            {
                "title": "2. Перечень персональных данных",
                "paragraphs": [
                    "К персональным данным относятся: имя пользователя, фамилия, имя, отчество, учебная группа, адрес электронной почты, номер телефона, сведения о результатах тестирования, а также технические и служебные записи о действиях в системе.",
                ],
            },
            {
                "title": "3. Цели обработки",
                "paragraphs": [
                    "Обработка персональных данных осуществляется в целях регистрации пользователя, предоставления доступа к учебному контенту, организации тестирования, фиксации результатов, анализа успеваемости и администрирования платформы.",
                ],
            },
            {
                "title": "4. Действия с персональными данными",
                "paragraphs": [
                    "Пользователь даёт согласие на сбор, запись, систематизацию, накопление, хранение, уточнение, использование, передачу в пределах образовательной организации, обезличивание, блокирование и удаление персональных данных в рамках целей, указанных в настоящем документе.",
                ],
            },
            {
                "title": "5. Срок действия согласия",
                "paragraphs": [
                    "Согласие действует с момента подтверждения при регистрации и сохраняет силу на период использования учётной записи, а также в течение срока, необходимого для выполнения целей обработки данных и требований законодательства.",
                ],
            },
            {
                "title": "6. Отзыв согласия",
                "paragraphs": [
                    "Пользователь вправе отозвать согласие на обработку персональных данных путём обращения к администрации образовательной организации. Отзыв согласия может повлечь ограничение или прекращение доступа к системе, если обработка данных необходима для её работы.",
                ],
            },
        ],
    },
}


def home(request):
    if request.user.is_authenticated:
        return redirect(dashboard_url_for(request.user))

    login_form = None
    next_url = request.POST.get("next") or request.GET.get("next")
    if request.method == "POST":
        login_form = LoginForm(request, data=request.POST)
        if login_form.is_valid():
            user = login_form.get_user()
            login(request, user)
            log_activity(
                request,
                user,
                ActivityLog.ActionType.AUTH,
                "Пользователь вошёл в систему",
            )
            messages.success(request, "Вход выполнен успешно.")
            if not url_has_allowed_host_and_scheme(
                next_url or "",
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                next_url = None
            return redirect(next_url or dashboard_url_for(user))
    else:
        login_form = LoginForm(request)

    context = {"login_form": login_form, "next_url": next_url}
    return render(request, "education/home.html", context)


def password_reset_info(request):
    return render(request, "registration/password_reset_form.html")


def privacy_policy(request):
    context = {
        **LEGAL_DOCUMENTS["privacy_policy"],
    }
    return render(request, "education/legal_document.html", context)


def personal_data_consent(request):
    context = {
        **LEGAL_DOCUMENTS["personal_data_consent"],
    }
    return render(request, "education/legal_document.html", context)


def register(request):
    if request.user.is_authenticated:
        return redirect(dashboard_url_for(request.user))

    if request.method == "POST":
        form = SignUpForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            log_activity(
                request,
                user,
                ActivityLog.ActionType.AUTH,
                "Новая регистрация в системе",
                {"role": user.role},
            )
            messages.success(request, "Регистрация выполнена успешно.")
            return redirect(dashboard_url_for(user))
    else:
        form = SignUpForm()

    return render(
        request,
        "education/form_page.html",
        {
            "title": "Регистрация",
            "subtitle": "Создание учетной записи в системе контроля учебного процесса.",
            "form": form,
            "submit_label": "Зарегистрироваться",
            "single_column_form": True,
        },
    )


@login_required
def dashboard(request):
    return redirect(dashboard_url_for(request.user))


@login_required
def profile_edit(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            log_activity(
                request,
                request.user,
                ActivityLog.ActionType.PROFILE,
                "Пользователь обновил профиль",
            )
            messages.success(request, "Профиль обновлён.")
            return redirect(dashboard_url_for(request.user))
    else:
        form = ProfileForm(instance=request.user)

    return render(
        request,
        "education/form_page.html",
        {
            "title": "Профиль",
            "subtitle": "Редактирование персональных данных.",
            "form": form,
            "submit_label": "Сохранить изменения",
            "cancel_url": dashboard_url_for(request.user),
            "show_password_change": True,
        },
    )


@role_required(User.Role.STUDENT)
def student_dashboard(request):
    tests = Test.objects.filter(is_published=True).select_related("discipline", "author").prefetch_related("groups")
    if request.user.academic_group:
        tests = tests.filter(Q(groups=request.user.academic_group) | Q(groups__isnull=True)).distinct()
    else:
        tests = tests.filter(groups__isnull=True)

    test_rows = []
    for test in tests:
        active_attempt = test.attempts.filter(student=request.user, is_finished=False).first()
        test_rows.append(
            {
                "test": test,
                "active_attempt": active_attempt,
                "can_start": test.is_available_for(request.user) and active_attempt is None,
                "attempts_left": test.attempts_left_for(request.user),
                "status": (
                    "В процессе"
                    if active_attempt
                    else "Доступен"
                    if test.is_available_for(request.user)
                    else "Недоступен"
                ),
            }
        )

    attempts = request.user.attempts.select_related("test", "test__discipline").all()
    average_score = attempts.filter(is_finished=True).aggregate(avg=Avg("score")).get("avg") or 0
    context = {
        "test_rows": test_rows,
        "attempts": attempts,
        "average_score": round(average_score, 1),
    }
    return render(request, "education/student_dashboard.html", context)


@role_required(User.Role.TEACHER)
def teacher_dashboard(request):
    tests = (
        request.user.created_tests.select_related("discipline")
        .annotate(
            attempts_total=Count("attempts", filter=Q(attempts__is_finished=True), distinct=True),
            avg_score=Avg("attempts__score", filter=Q(attempts__is_finished=True)),
        )
        .all()
    )
    assigned_disciplines = request.user.disciplines_taught.prefetch_related("groups")
    assigned_groups = AcademicGroup.objects.filter(disciplines__teachers=request.user).distinct()
    context = {
        "tests": tests,
        "assigned_disciplines": assigned_disciplines,
        "assigned_groups": assigned_groups,
        "summary": {
            "tests_total": tests.count(),
            "published_total": tests.filter(is_published=True).count(),
        },
    }
    return render(request, "education/teacher_dashboard.html", context)


@role_required(User.Role.ADMINISTRATOR)
def admin_dashboard(request):
    context = {
        "stats": {
            "users": User.objects.count(),
            "students": User.objects.filter(role=User.Role.STUDENT).count(),
            "teachers": User.objects.filter(role=User.Role.TEACHER).count(),
            "admins": User.objects.filter(role=User.Role.ADMINISTRATOR).count(),
            "groups": AcademicGroup.objects.count(),
            "disciplines": Discipline.objects.count(),
            "tests": Test.objects.count(),
        },
        "recent_users": User.objects.order_by("-id")[:5],
        "recent_logs": ActivityLog.objects.select_related("user").all()[:3],
    }
    return render(request, "education/admin_dashboard.html", context)


@role_required(User.Role.TEACHER)
def test_create(request):
    if request.method == "POST":
        form = TeacherTestForm(request.POST, teacher=request.user, show_published_field=False)
        if form.is_valid():
            test = form.save(commit=False)
            test.author = request.user
            test.save()
            form.save_m2m()
            log_activity(
                request,
                request.user,
                ActivityLog.ActionType.TEST,
                f"Создан тест «{test.title}»",
            )
            messages.success(request, "Тест создан. Теперь добавьте вопросы.")
            return redirect("education:test_preview", pk=test.pk)
    else:
        form = TeacherTestForm(teacher=request.user, show_published_field=False)

    return render(
        request,
        "education/form_page.html",
        {
            "title": "Новый тест",
            "subtitle": "Задайте параметры тестирования и опубликуйте тест после подготовки вопросов.",
            "form": form,
            "submit_label": "Сохранить тест",
            "cancel_url": "education:teacher_dashboard",
            "uniform_field_sizes": True,
            "single_column_form": True,
        },
    )


@role_required(User.Role.TEACHER)
def test_update(request, pk):
    test = get_object_or_404(Test, pk=pk, author=request.user)
    if request.method == "POST":
        form = TeacherTestForm(request.POST, instance=test, teacher=request.user)
        if form.is_valid():
            form.save()
            log_activity(
                request,
                request.user,
                ActivityLog.ActionType.TEST,
                f"Обновлён тест «{test.title}»",
            )
            messages.success(request, "Изменения сохранены.")
            return redirect("education:test_preview", pk=test.pk)
    else:
        form = TeacherTestForm(instance=test, teacher=request.user)

    return render(
        request,
        "education/form_page.html",
        {
            "title": "Редактирование теста",
            "subtitle": "Измените параметры публикации, времени и попыток.",
            "form": form,
            "submit_label": "Сохранить",
            "cancel_url": "education:test_preview",
            "cancel_kwargs": {"pk": test.pk},
        },
    )


@role_required(User.Role.TEACHER)
@require_POST
def test_delete(request, pk):
    test = get_object_or_404(Test, pk=pk, author=request.user)
    title = test.title
    test.delete()
    log_activity(request, request.user, ActivityLog.ActionType.TEST, f"Удалён тест «{title}»")
    messages.success(request, "Тест удалён.")
    return redirect("education:teacher_dashboard")


@role_required(User.Role.TEACHER)
def test_preview(request, pk):
    test = get_object_or_404(
        Test.objects.select_related("discipline", "author").prefetch_related("questions__options", "groups"),
        pk=pk,
        author=request.user,
    )
    return render(request, "education/test_preview.html", {"test": test})


@role_required(User.Role.TEACHER)
def question_create(request, test_pk):
    test = get_object_or_404(Test, pk=test_pk, author=request.user)
    if request.method == "POST":
        form = QuestionForm(request.POST, request.FILES)
        formset = AnswerOptionFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            question = form.save(commit=False)
            question.test = test
            question.order = (test.questions.aggregate(max_order=Max("order")).get("max_order") or 0) + 1
            question.save()
            formset.instance = question
            formset.save()
            log_activity(
                request,
                request.user,
                ActivityLog.ActionType.TEST,
                f"Добавлен вопрос в тест «{test.title}»",
            )
            messages.success(request, "Вопрос добавлен.")
            return redirect("education:test_preview", pk=test.pk)
    else:
        form = QuestionForm()
        formset = AnswerOptionFormSet()

    return render(
        request,
        "education/form_page.html",
        {
            "title": "Добавление вопроса",
            "subtitle": "Укажите текст вопроса, изображение и варианты ответов.",
            "form": form,
            "formset": formset,
            "submit_label": "Сохранить вопрос",
            "cancel_url": "education:test_preview",
            "cancel_kwargs": {"pk": test.pk},
        },
    )


@role_required(User.Role.TEACHER)
def question_update(request, test_pk, question_pk):
    test = get_object_or_404(Test, pk=test_pk, author=request.user)
    question = get_object_or_404(Question, pk=question_pk, test=test)
    if request.method == "POST":
        form = QuestionForm(request.POST, request.FILES, instance=question)
        formset = AnswerOptionFormSet(request.POST, instance=question)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            log_activity(
                request,
                request.user,
                ActivityLog.ActionType.TEST,
                f"Изменён вопрос в тесте «{test.title}»",
            )
            messages.success(request, "Вопрос обновлён.")
            return redirect("education:test_preview", pk=test.pk)
    else:
        form = QuestionForm(instance=question)
        formset = AnswerOptionFormSet(instance=question)

    return render(
        request,
        "education/form_page.html",
        {
            "title": "Редактирование вопроса",
            "subtitle": "Измените формулировку, изображение и правильный вариант ответа.",
            "form": form,
            "formset": formset,
            "submit_label": "Сохранить изменения",
            "cancel_url": "education:test_preview",
            "cancel_kwargs": {"pk": test.pk},
            "file_delete_field": "image",
            "file_delete_label": "Удалить изображение",
            "file_delete_url": "education:question_image_delete",
            "file_delete_kwargs": {"test_pk": test.pk, "question_pk": question.pk},
        },
    )


@role_required(User.Role.TEACHER)
@require_POST
def question_image_delete(request, test_pk, question_pk):
    test = get_object_or_404(Test, pk=test_pk, author=request.user)
    question = get_object_or_404(Question, pk=question_pk, test=test)
    if question.image:
        question.image.delete(save=False)
        question.image = None
        question.save(update_fields=["image"])
        log_activity(
            request,
            request.user,
            ActivityLog.ActionType.TEST,
            f"Удалено изображение вопроса в тесте «{test.title}»",
        )
        messages.success(request, "Изображение вопроса удалено.")
    else:
        messages.info(request, "У вопроса нет изображения для удаления.")
    return redirect("education:question_update", test_pk=test.pk, question_pk=question.pk)


@role_required(User.Role.TEACHER)
@require_POST
def question_delete(request, test_pk, question_pk):
    test = get_object_or_404(Test, pk=test_pk, author=request.user)
    question = get_object_or_404(Question, pk=question_pk, test=test)
    question.delete()
    test.normalize_question_order()
    log_activity(
        request,
        request.user,
        ActivityLog.ActionType.TEST,
        f"Удалён вопрос из теста «{test.title}»",
    )
    messages.success(request, "Вопрос удалён.")
    return redirect("education:test_preview", pk=test.pk)


@role_required(User.Role.TEACHER, User.Role.ADMINISTRATOR)
def report_detail(request, pk):
    test = get_object_or_404(Test.objects.select_related("discipline", "author"), pk=pk)
    if request.user.is_teacher and test.author != request.user:
        return HttpResponseForbidden("Доступ запрещён.")

    attempts = (
        test.attempts.filter(is_finished=True)
        .select_related("student")
        .prefetch_related("answers__question", "answers__selected_option")
    )
    question_stats = []
    for question in test.questions.all():
        total_answers = StudentAnswer.objects.filter(
            question=question,
            attempt__test=test,
            attempt__is_finished=True,
        ).exclude(selected_option__isnull=True)
        answers_count = total_answers.count()
        correct_count = total_answers.filter(is_correct=True).count()
        question_stats.append(
            {
                "question": question,
                "answers_count": answers_count,
                "correct_rate": int(correct_count / answers_count * 100) if answers_count else 0,
            }
        )

    context = {
        "test": test,
        "attempts": attempts,
        "question_stats": question_stats,
        "summary": {
            "attempts": attempts.count(),
            "average_score": round(attempts.aggregate(avg=Avg("score")).get("avg") or 0, 1),
        },
    }
    return render(request, "education/report_detail.html", context)


@role_required(User.Role.STUDENT)
def start_test(request, pk):
    test = get_object_or_404(Test.objects.prefetch_related("questions"), pk=pk, is_published=True)
    active_attempt = test.attempts.filter(student=request.user, is_finished=False).first()
    if active_attempt:
        messages.info(request, "У вас уже есть незавершённая попытка.")
        return redirect("education:take_test", attempt_pk=active_attempt.pk, order=1)

    if not test.is_available_for(request.user):
        messages.error(request, "Тест недоступен для прохождения.")
        return redirect("education:student_dashboard")

    if test.questions.count() == 0:
        messages.error(request, "Тест пока не содержит вопросов.")
        return redirect("education:student_dashboard")

    attempt = TestAttempt.objects.create(
        student=request.user,
        test=test,
        attempt_number=test.completed_attempts_for(request.user) + 1,
    )
    attempt.ensure_answer_placeholders()
    log_activity(
        request,
        request.user,
        ActivityLog.ActionType.TEST,
        f"Начато прохождение теста «{test.title}»",
    )
    return redirect("education:take_test", attempt_pk=attempt.pk, order=1)


@role_required(User.Role.STUDENT)
def take_test(request, attempt_pk, order=1):
    attempt = get_object_or_404(
        TestAttempt.objects.select_related("test").prefetch_related("answers__selected_option"),
        pk=attempt_pk,
        student=request.user,
    )
    if attempt.is_finished:
        return redirect("education:attempt_result", attempt_pk=attempt.pk)

    if attempt.is_expired:
        attempt.finish()
        log_activity(
            request,
            request.user,
            ActivityLog.ActionType.TEST,
            f"Тест «{attempt.test.title}» завершён по таймеру",
        )
        messages.warning(request, "Время вышло, тест завершён автоматически.")
        return redirect("education:attempt_result", attempt_pk=attempt.pk)

    questions = list(attempt.test.questions.prefetch_related("options"))
    current_index = max(0, min(order - 1, len(questions) - 1))
    question = questions[current_index]
    answer = attempt.answers.select_related("selected_option").get(question=question)
    context = {
        "attempt": attempt,
        "questions_total": len(questions),
        "question": question,
        "current_order": current_index + 1,
        "previous_order": current_index if current_index > 0 else None,
        "next_order": current_index + 2 if current_index + 1 < len(questions) else None,
        "is_last_question": current_index == len(questions) - 1,
        "answer": answer,
    }
    return render(request, "education/take_test.html", context)


@role_required(User.Role.STUDENT)
@require_POST
def save_answer(request, attempt_pk, question_pk):
    attempt = get_object_or_404(TestAttempt, pk=attempt_pk, student=request.user, is_finished=False)
    if attempt.is_expired:
        attempt.finish()
        return JsonResponse({"ok": False, "expired": True}, status=400)

    answer = get_object_or_404(StudentAnswer, attempt=attempt, question_id=question_pk)
    option_id = request.POST.get("option_id")
    if option_id:
        option = get_object_or_404(answer.question.options, pk=option_id)
        answer.selected_option = option
        answer.save()
        return JsonResponse({"ok": True, "message": "Ответ сохранён"})

    answer.selected_option = None
    answer.save()
    return JsonResponse({"ok": True, "message": "Ответ очищен"})


@role_required(User.Role.STUDENT)
@require_POST
def finish_attempt(request, attempt_pk):
    attempt = get_object_or_404(TestAttempt, pk=attempt_pk, student=request.user)
    if not attempt.is_finished:
        attempt.finish()
        log_activity(
            request,
            request.user,
            ActivityLog.ActionType.TEST,
            f"Завершено прохождение теста «{attempt.test.title}»",
        )
    return redirect("education:attempt_result", attempt_pk=attempt.pk)


@login_required
def attempt_result(request, attempt_pk):
    attempt = get_object_or_404(
        TestAttempt.objects.select_related("student", "test", "test__discipline").prefetch_related(
            "answers__question",
            "answers__selected_option",
            "answers__question__options",
        ),
        pk=attempt_pk,
    )
    is_owner = attempt.student == request.user
    is_teacher_owner = request.user.is_teacher and attempt.test.author == request.user
    is_admin = request.user.is_administrator or request.user.is_superuser
    if not (is_owner or is_teacher_owner or is_admin):
        return HttpResponseForbidden("Доступ запрещён.")
    if not attempt.is_finished and is_owner:
        return redirect("education:take_test", attempt_pk=attempt.pk, order=1)

    return render(request, "education/test_result.html", {"attempt": attempt})


@role_required(User.Role.ADMINISTRATOR)
def admin_user_list(request):
    users = User.objects.select_related("academic_group").all()
    role = request.GET.get("role")
    search = request.GET.get("search")
    if role:
        users = users.filter(role=role)
    if search:
        users = users.filter(
            Q(username__icontains=search)
            | Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(email__icontains=search)
        )
    return render(
        request,
        "education/admin_user_list.html",
        {
            "users": users,
            "role": role or "",
            "search": search or "",
            "role_choices": User.Role.choices,
        },
    )


@role_required(User.Role.ADMINISTRATOR)
def admin_user_create(request):
    if request.method == "POST":
        form = AdminUserForm(
            request.POST,
            request.FILES,
            is_create=True,
            show_active_field=False,
        )
        if form.is_valid():
            user = form.save()
            log_activity(
                request,
                request.user,
                ActivityLog.ActionType.ADMIN,
                f"Создан пользователь {user.username}",
            )
            messages.success(request, "Пользователь создан.")
            return redirect("education:admin_user_list")
    else:
        form = AdminUserForm(is_create=True, show_active_field=False)

    return render(
        request,
        "education/form_page.html",
        {
            "title": "Новый пользователь",
            "subtitle": "Создание учётной записи, назначение роли и учебной группы.",
            "form": form,
            "submit_label": "Создать пользователя",
            "cancel_url": "education:admin_user_list",
            "single_column_form": True,
        },
    )


@role_required(User.Role.ADMINISTRATOR)
def admin_user_edit(request, user_pk):
    managed_user = get_object_or_404(User, pk=user_pk)
    if request.method == "POST":
        form = AdminUserForm(
            request.POST,
            request.FILES,
            instance=managed_user,
            show_active_field=False,
        )
        if form.is_valid():
            form.save()
            log_activity(
                request,
                request.user,
                ActivityLog.ActionType.ADMIN,
                f"Обновлён пользователь {managed_user.username}",
            )
            messages.success(request, "Изменения пользователя сохранены.")
            return redirect("education:admin_user_list")
    else:
        form = AdminUserForm(instance=managed_user, show_active_field=False)

    return render(
        request,
        "education/form_page.html",
        {
            "title": "Редактирование пользователя",
            "subtitle": "Измените роль и контактные данные пользователя.",
            "form": form,
            "submit_label": "Сохранить",
            "cancel_url": "education:admin_user_list",
        },
    )


@role_required(User.Role.ADMINISTRATOR)
@require_POST
def admin_user_delete(request, user_pk):
    managed_user = get_object_or_404(User, pk=user_pk)
    if managed_user == request.user:
        messages.error(request, "Нельзя удалить собственную учётную запись.")
        return redirect("education:admin_user_list")

    deleted_username = managed_user.username
    managed_user.delete()
    log_activity(
        request,
        request.user,
        ActivityLog.ActionType.ADMIN,
        f"Удалён пользователь {deleted_username}",
    )
    messages.success(request, "Пользователь удалён.")
    return redirect("education:admin_user_list")


@role_required(User.Role.ADMINISTRATOR)
@require_POST
def admin_user_toggle_active(request, user_pk):
    managed_user = get_object_or_404(User, pk=user_pk)
    if managed_user == request.user:
        messages.error(request, "Нельзя заблокировать собственную учётную запись.")
        return redirect("education:admin_user_list")
    managed_user.is_active = not managed_user.is_active
    managed_user.save(update_fields=["is_active"])
    log_activity(
        request,
        request.user,
        ActivityLog.ActionType.ADMIN,
        f"{'Разблокирован' if managed_user.is_active else 'Заблокирован'} пользователь {managed_user.username}",
    )
    messages.success(request, "Статус пользователя обновлён.")
    return redirect("education:admin_user_list")


@role_required(User.Role.ADMINISTRATOR)
def admin_user_reset_password(request, user_pk):
    managed_user = get_object_or_404(User, pk=user_pk)
    if request.method == "POST":
        form = AdminPasswordResetForm(request.POST)
        if form.is_valid():
            managed_user.set_password(form.cleaned_data["password1"])
            managed_user.save(update_fields=["password"])
            log_activity(
                request,
                request.user,
                ActivityLog.ActionType.ADMIN,
                f"Сброшен пароль пользователя {managed_user.username}",
            )
            messages.success(request, "Пароль пользователя обновлён.")
            return redirect("education:admin_user_list")
    else:
        form = AdminPasswordResetForm()

    return render(
        request,
        "education/form_page.html",
        {
            "title": "Сброс пароля",
            "subtitle": f"Установка нового пароля для пользователя {managed_user.full_name}.",
            "form": form,
            "submit_label": "Сохранить пароль",
            "cancel_url": "education:admin_user_list",
        },
    )


@role_required(User.Role.ADMINISTRATOR)
def group_list(request):
    groups = AcademicGroup.objects.annotate(
        students_total=Count("students", distinct=True),
        disciplines_total=Count("disciplines", distinct=True),
    )
    return render(request, "education/group_list.html", {"groups": groups})


@role_required(User.Role.ADMINISTRATOR)
def group_create(request):
    if request.method == "POST":
        form = AcademicGroupForm(request.POST)
        if form.is_valid():
            group = form.save()
            log_activity(
                request,
                request.user,
                ActivityLog.ActionType.ADMIN,
                f"Создана группа {group.name}",
            )
            messages.success(request, "Группа создана.")
            return redirect("education:group_list")
    else:
        form = AcademicGroupForm()

    return render(
        request,
        "education/form_page.html",
        {
            "title": "Новая группа",
            "subtitle": "Создание учебной группы и назначение куратора.",
            "form": form,
            "submit_label": "Создать группу",
            "cancel_url": "education:group_list",
        },
    )


@role_required(User.Role.ADMINISTRATOR)
def group_edit(request, pk):
    group = get_object_or_404(AcademicGroup, pk=pk)
    if request.method == "POST":
        form = AcademicGroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            log_activity(
                request,
                request.user,
                ActivityLog.ActionType.ADMIN,
                f"Обновлена группа {group.name}",
            )
            messages.success(request, "Группа обновлена.")
            return redirect("education:group_list")
    else:
        form = AcademicGroupForm(instance=group)

    return render(
        request,
        "education/form_page.html",
        {
            "title": "Редактирование группы",
            "subtitle": "Изменение описания и куратора группы.",
            "form": form,
            "submit_label": "Сохранить",
            "cancel_url": "education:group_list",
        },
    )


@role_required(User.Role.ADMINISTRATOR)
@require_POST
def group_delete(request, pk):
    group = get_object_or_404(AcademicGroup, pk=pk)
    group_name = group.name
    group.delete()
    log_activity(
        request,
        request.user,
        ActivityLog.ActionType.ADMIN,
        f"Удалена группа {group_name}",
    )
    messages.success(request, f"Группа {group_name} удалена.")
    return redirect("education:group_list")


@role_required(User.Role.ADMINISTRATOR)
def discipline_list(request):
    disciplines = Discipline.objects.annotate(
        tests_total=Count("tests", distinct=True),
        teachers_total=Count("teachers", distinct=True),
        groups_total=Count("groups", distinct=True),
    )
    return render(request, "education/discipline_list.html", {"disciplines": disciplines})


@role_required(User.Role.ADMINISTRATOR)
def discipline_create(request):
    if request.method == "POST":
        form = DisciplineForm(request.POST)
        if form.is_valid():
            discipline = form.save()
            log_activity(
                request,
                request.user,
                ActivityLog.ActionType.ADMIN,
                f"Создана дисциплина {discipline.name}",
            )
            messages.success(request, "Дисциплина создана.")
            return redirect("education:discipline_list")
    else:
        form = DisciplineForm()

    return render(
        request,
        "education/form_page.html",
        {
            "title": "Новая дисциплина",
            "subtitle": "Добавьте дисциплину, назначьте преподавателей и учебные группы.",
            "form": form,
            "submit_label": "Создать дисциплину",
            "cancel_url": "education:discipline_list",
        },
    )


@role_required(User.Role.ADMINISTRATOR)
def discipline_edit(request, pk):
    discipline = get_object_or_404(Discipline, pk=pk)
    if request.method == "POST":
        form = DisciplineForm(request.POST, instance=discipline)
        if form.is_valid():
            form.save()
            log_activity(
                request,
                request.user,
                ActivityLog.ActionType.ADMIN,
                f"Обновлена дисциплина {discipline.name}",
            )
            messages.success(request, "Дисциплина обновлена.")
            return redirect("education:discipline_list")
    else:
        form = DisciplineForm(instance=discipline)

    return render(
        request,
        "education/form_page.html",
        {
            "title": "Редактирование дисциплины",
            "subtitle": "Настройте описание дисциплины, группы и преподавателей.",
            "form": form,
            "submit_label": "Сохранить",
            "cancel_url": "education:discipline_list",
        },
    )


@role_required(User.Role.ADMINISTRATOR)
@require_POST
def discipline_delete(request, pk):
    discipline = get_object_or_404(Discipline, pk=pk)
    discipline_name = discipline.name
    discipline.delete()
    log_activity(
        request,
        request.user,
        ActivityLog.ActionType.ADMIN,
        f"Удалена дисциплина {discipline_name}",
    )
    messages.success(request, f"Дисциплина {discipline_name} удалена.")
    return redirect("education:discipline_list")


@role_required(User.Role.ADMINISTRATOR)
def activity_logs(request):
    logs = ActivityLog.objects.select_related("user").all()
    filter_form = ActivityLogFilterForm(request.GET or None)
    if filter_form.is_valid():
        action_type = filter_form.cleaned_data.get("action_type")
        user = filter_form.cleaned_data.get("user")
        if action_type:
            logs = logs.filter(action_type=action_type)
        if user:
            logs = logs.filter(user=user)

    return render(
        request,
        "education/activity_logs.html",
        {"logs": logs[:150], "filter_form": filter_form},
    )


@role_required(User.Role.ADMINISTRATOR)
@require_POST
def activity_logs_clear(request):
    deleted_count, _ = ActivityLog.objects.all().delete()
    messages.success(request, f"Журнал действий очищен. Удалено записей: {deleted_count}.")
    return redirect("education:activity_logs")
