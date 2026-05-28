from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import ActivityLog, StudentAnswer, Test, TestAttempt, User
from .utils import forbidden_response, log_activity, role_required


# кабинет студента показывает только доступные тесты и историю попыток
@role_required(User.Role.STUDENT)
def student_dashboard(request):
    tests = Test.objects.select_related("discipline", "author").prefetch_related("groups")
    if request.user.academic_group:
        tests = tests.filter(Q(groups=request.user.academic_group) | Q(groups__isnull=True)).distinct()
    else:
        tests = tests.filter(groups__isnull=True)

    test_rows = []
    for test in tests:
        is_available = test.is_available_for(request.user)
        if not is_available:
            continue

        active_attempt = test.attempts.filter(student=request.user, is_finished=False).first()
        test_rows.append(
            {
                "test": test,
                "active_attempt": active_attempt,
                "can_start": active_attempt is None,
                "attempts_left": test.attempts_left_for(request.user),
                "status": "В процессе" if active_attempt else "Доступен",
            }
        )

    attempts = request.user.attempts.select_related("test", "test__discipline").all()
    return render(
        request,
        "education/student_dashboard.html",
        {
            "test_rows": test_rows,
            "attempts": attempts,
        },
    )


# перед стартом проверяем доступность теста и отсутствие незавершенной попытки
@role_required(User.Role.STUDENT)
def start_test(request, pk):
    test = get_object_or_404(Test.objects.prefetch_related("questions"), pk=pk)
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


# страница прохождения показывает один вопрос и сохраняет выбранный ответ
@role_required(User.Role.STUDENT)
def take_test(request, attempt_pk, order=1):
    attempt = get_object_or_404(
        TestAttempt.objects.select_related("test").prefetch_related("answers__selected_option"),
        pk=attempt_pk,
        student=request.user,
    )
    if attempt.is_finished:
        return redirect("education:attempt_result", attempt_pk=attempt.pk)

    questions = list(attempt.test.questions.prefetch_related("options"))
    current_index = max(0, min(order - 1, len(questions) - 1))
    question = questions[current_index]
    answer = attempt.answers.select_related("selected_option").get(question=question)
    return render(
        request,
        "education/take_test.html",
        {
            "attempt": attempt,
            "questions_total": len(questions),
            "question": question,
            "current_order": current_index + 1,
            "previous_order": current_index if current_index > 0 else None,
            "next_order": current_index + 2 if current_index + 1 < len(questions) else None,
            "is_last_question": current_index == len(questions) - 1,
            "answer": answer,
        },
    )


# ajax-сохранение ответа вызывается при выборе варианта на странице теста
@role_required(User.Role.STUDENT)
@require_POST
def save_answer(request, attempt_pk, question_pk):
    attempt = get_object_or_404(TestAttempt, pk=attempt_pk, student=request.user, is_finished=False)

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


# завершение попытки пересчитывает результат и переводит студента на итоговую страницу
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


# итог теста доступен студенту, автору теста и администратору
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
        return forbidden_response(request, "У вас нет доступа к результату этой попытки.")
    if not attempt.is_finished and is_owner:
        return redirect("education:take_test", attempt_pk=attempt.pk, order=1)

    return render(request, "education/test_result.html", {"attempt": attempt})
