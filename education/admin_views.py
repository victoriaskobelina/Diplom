from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import (
    AcademicGroupForm,
    ActivityLogFilterForm,
    AdminPasswordResetForm,
    AdminUserForm,
    DisciplineForm,
)
from .models import AcademicGroup, ActivityLog, Discipline, User
from .utils import log_activity, role_required


# главная панель администратора показывает счетчики и последние действия
@role_required(User.Role.ADMINISTRATOR)
def admin_dashboard(request):
    return render(
        request,
        "education/admin_dashboard.html",
        {
            "stats": {
                "users": User.objects.count(),
                "students": User.objects.filter(role=User.Role.STUDENT).count(),
                "teachers": User.objects.filter(role=User.Role.TEACHER).count(),
                "admins": User.objects.filter(role=User.Role.ADMINISTRATOR).count(),
                "groups": AcademicGroup.objects.count(),
                "disciplines": Discipline.objects.count(),
            },
            "recent_users": User.objects.order_by("-id")[:5],
            "recent_logs": ActivityLog.objects.select_related("user").all()[:3],
        },
    )


# управление пользователями: список, фильтры, создание, редактирование и блокировка
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


# администратор не может удалить или заблокировать собственную учетную запись
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


# справочник групп используется для распределения студентов и назначения кураторов
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


# справочник дисциплин связывает преподавателей, группы и будущие тесты
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


# журнал действий фильтруется по типу события и ФИО пользователя
@role_required(User.Role.ADMINISTRATOR)
def activity_logs(request):
    logs = ActivityLog.objects.select_related("user").all()
    filter_form = ActivityLogFilterForm(request.GET or None)
    if filter_form.is_valid():
        action_type = filter_form.cleaned_data.get("action_type")
        user_query = (filter_form.cleaned_data.get("user_query") or "").strip()
        if action_type:
            logs = logs.filter(action_type=action_type)
        if user_query:
            for term in user_query.split():
                logs = logs.filter(
                    Q(user__last_name__icontains=term)
                    | Q(user__first_name__icontains=term)
                    | Q(user__middle_name__icontains=term)
                )

    return render(
        request,
        "education/activity_logs.html",
        {"logs": logs[:150], "filter_form": filter_form},
    )


# очистка журнала выполняется отдельным POST-действием
@role_required(User.Role.ADMINISTRATOR)
@require_POST
def activity_logs_clear(request):
    deleted_count, _ = ActivityLog.objects.all().delete()
    messages.success(request, f"Журнал действий очищен. Удалено записей: {deleted_count}.")
    return redirect("education:activity_logs")
