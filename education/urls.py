from django.urls import path

from . import views

app_name = "education"

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/", views.profile_edit, name="profile_edit"),
    path("student/", views.student_dashboard, name="student_dashboard"),
    path("teacher/", views.teacher_dashboard, name="teacher_dashboard"),
    path("teacher/tests/new/", views.test_create, name="test_create"),
    path("teacher/tests/<int:pk>/", views.test_preview, name="test_preview"),
    path("teacher/tests/<int:pk>/edit/", views.test_update, name="test_update"),
    path("teacher/tests/<int:pk>/delete/", views.test_delete, name="test_delete"),
    path("teacher/tests/<int:test_pk>/questions/new/", views.question_create, name="question_create"),
    path(
        "teacher/tests/<int:test_pk>/questions/<int:question_pk>/edit/",
        views.question_update,
        name="question_update",
    ),
    path(
        "teacher/tests/<int:test_pk>/questions/<int:question_pk>/delete/",
        views.question_delete,
        name="question_delete",
    ),
    path("teacher/reports/<int:pk>/", views.report_detail, name="report_detail"),
    path("tests/<int:pk>/start/", views.start_test, name="start_test"),
    path("attempts/<int:attempt_pk>/question/<int:order>/", views.take_test, name="take_test"),
    path(
        "attempts/<int:attempt_pk>/answers/<int:question_pk>/save/",
        views.save_answer,
        name="save_answer",
    ),
    path("attempts/<int:attempt_pk>/finish/", views.finish_attempt, name="finish_attempt"),
    path("attempts/<int:attempt_pk>/result/", views.attempt_result, name="attempt_result"),
    path("admin-panel/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-panel/users/", views.admin_user_list, name="admin_user_list"),
    path("admin-panel/users/new/", views.admin_user_create, name="admin_user_create"),
    path("admin-panel/users/<int:user_pk>/edit/", views.admin_user_edit, name="admin_user_edit"),
    path(
        "admin-panel/users/<int:user_pk>/delete/",
        views.admin_user_delete,
        name="admin_user_delete",
    ),
    path(
        "admin-panel/users/<int:user_pk>/toggle-active/",
        views.admin_user_toggle_active,
        name="admin_user_toggle_active",
    ),
    path(
        "admin-panel/users/<int:user_pk>/reset-password/",
        views.admin_user_reset_password,
        name="admin_user_reset_password",
    ),
    path("admin-panel/groups/", views.group_list, name="group_list"),
    path("admin-panel/groups/new/", views.group_create, name="group_create"),
    path("admin-panel/groups/<int:pk>/edit/", views.group_edit, name="group_edit"),
    path("admin-panel/groups/<int:pk>/delete/", views.group_delete, name="group_delete"),
    path("admin-panel/disciplines/", views.discipline_list, name="discipline_list"),
    path("admin-panel/disciplines/new/", views.discipline_create, name="discipline_create"),
    path(
        "admin-panel/disciplines/<int:pk>/edit/",
        views.discipline_edit,
        name="discipline_edit",
    ),
    path(
        "admin-panel/disciplines/<int:pk>/delete/",
        views.discipline_delete,
        name="discipline_delete",
    ),
    path("admin-panel/logs/", views.activity_logs, name="activity_logs"),
    path("admin-panel/logs/clear/", views.activity_logs_clear, name="activity_logs_clear"),
]
