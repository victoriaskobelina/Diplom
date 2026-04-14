from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import (
    AcademicGroup,
    ActivityLog,
    AnswerOption,
    Discipline,
    Question,
    StudentAnswer,
    Test,
    TestAttempt,
    User,
)


class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 1


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 0


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "Дополнительная информация",
            {
                "fields": (
                    "middle_name",
                    "phone",
                    "photo",
                    "bio",
                    "role",
                    "academic_group",
                )
            },
        ),
    )
    list_display = (
        "username",
        "email",
        "last_name",
        "first_name",
        "role",
        "academic_group",
        "is_active",
    )
    list_filter = ("role", "is_active", "academic_group")


@admin.register(AcademicGroup)
class AcademicGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "curator")
    search_fields = ("name",)


@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    filter_horizontal = ("teachers", "groups")
    search_fields = ("name", "code")


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ("title", "discipline", "author", "is_published", "max_attempts")
    list_filter = ("is_published", "discipline")
    search_fields = ("title", "description")
    filter_horizontal = ("groups",)
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("test", "order", "points")
    inlines = [AnswerOptionInline]


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "test", "attempt_number", "score", "grade", "is_finished")
    list_filter = ("is_finished", "grade")


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ("attempt", "question", "selected_option", "is_correct")
    list_filter = ("is_correct",)


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action_type", "user", "description")
    list_filter = ("action_type",)
    search_fields = ("description",)
