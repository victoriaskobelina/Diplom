import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet, inlineformset_factory

from .models import (
    AcademicGroup,
    ActivityLog,
    AnswerOption,
    Discipline,
    Question,
    Test,
    User,
)


def apply_form_styles(form):
    for field in form.fields.values():
        widget = field.widget
        css_class = widget.attrs.get("class", "")
        if isinstance(widget, forms.CheckboxInput):
            widget.attrs["class"] = f"{css_class} form-check-input".strip()
        elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
            widget.attrs["class"] = f"{css_class} form-select".strip()
            if isinstance(widget, forms.SelectMultiple):
                widget.attrs.setdefault("size", 6)
        elif isinstance(widget, forms.FileInput):
            widget.attrs["class"] = f"{css_class} form-control form-control-file".strip()
        else:
            widget.attrs["class"] = f"{css_class} form-control".strip()


class StyledFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_form_styles(self)


class LoginForm(StyledFormMixin, AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Введите правильные имя пользователя и пароль.",
    }


class SignUpForm(StyledFormMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "email",
            "last_name",
            "first_name",
            "middle_name",
            "phone",
            "academic_group",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["academic_group"].required = True
        self.fields["username"].help_text = ""
        self.fields["email"].required = False
        self.fields["email"].help_text = ""
        self.fields["email"].widget.attrs.update(
            {
                "data-mask": "email",
                "placeholder": "name@example.com",
                "inputmode": "email",
                "autocomplete": "email",
                "autocapitalize": "none",
                "spellcheck": "false",
            }
        )
        self.fields["phone"].widget.attrs.update(
            {
                "data-mask": "phone",
                "data-max-digits": "14",
                "placeholder": "+7 (___) ___-__-__",
                "inputmode": "numeric",
                "autocomplete": "tel",
                "maxlength": 22,
            }
        )
        for field_name, autocomplete in (
            ("last_name", "family-name"),
            ("first_name", "given-name"),
            ("middle_name", "additional-name"),
        ):
            self.fields[field_name].widget.attrs.update(
                {
                    "data-mask": "person-name",
                    "autocomplete": autocomplete,
                }
            )

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            return None
        qs = User.objects.filter(email__iexact=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Пользователь с такой почтой уже существует.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if not phone:
            return ""

        digits = re.sub(r"\D", "", phone)
        if digits.startswith("8"):
            digits = f"7{digits[1:]}"
        elif not digits.startswith("7"):
            digits = f"7{digits}"

        if len(digits) < 11 or len(digits) > 14 or not digits.startswith("7"):
            raise ValidationError("Введите телефон в формате +7 (900) 123-45-67, не более 14 цифр.")

        formatted = f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
        extension = digits[11:]
        if extension:
            formatted = f"{formatted} {extension}"
        return formatted

    def clean(self):
        cleaned_data = super().clean()
        group = cleaned_data.get("academic_group")
        if not group:
            self.add_error("academic_group", "Для студента необходимо указать учебную группу.")
        return cleaned_data


    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.STUDENT
        if commit:
            user.save()
            self.save_m2m()
        return user


class ProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "last_name",
            "first_name",
            "middle_name",
            "email",
            "phone",
        )

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            return None
        qs = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Пользователь с такой почтой уже существует.")
        return email

class TeacherTestForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Test
        fields = (
            "title",
            "description",
            "discipline",
            "groups",
            "time_limit_minutes",
            "max_attempts",
            "allow_retake",
            "is_published",
            "available_from",
            "available_to",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "available_from": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M",
                attrs={"type": "datetime-local"},
            ),
            "available_to": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M",
                attrs={"type": "datetime-local"},
            ),
        }

    def __init__(self, *args, teacher=None, show_published_field=True, **kwargs):
        super().__init__(*args, **kwargs)
        disciplines = Discipline.objects.all()
        groups = AcademicGroup.objects.all()
        if teacher:
            assigned_disciplines = teacher.disciplines_taught.all()
            if assigned_disciplines.exists():
                disciplines = assigned_disciplines
                groups = AcademicGroup.objects.filter(disciplines__in=assigned_disciplines).distinct()
        self.fields["discipline"].queryset = disciplines
        self.fields["groups"].queryset = groups
        if not show_published_field:
            self.fields.pop("is_published", None)
        self.fields["available_from"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["available_to"].input_formats = ["%Y-%m-%dT%H:%M"]

    def clean(self):
        cleaned_data = super().clean()
        available_from = cleaned_data.get("available_from")
        available_to = cleaned_data.get("available_to")
        if available_from and available_to and available_to <= available_from:
            self.add_error("available_to", "Дата окончания должна быть позже даты начала.")
        return cleaned_data


class QuestionForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Question
        fields = ("text", "image")
        widgets = {
            "text": forms.Textarea(attrs={"rows": 4}),
            "image": forms.FileInput(),
        }


class AnswerOptionForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = AnswerOption
        fields = ("text", "is_correct")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["is_correct"].widget.attrs["data-single-correct"] = "true"
        self.fields["is_correct"].widget.attrs["onclick"] = "window.enforceSingleCorrectCheckbox(this)"


class BaseAnswerOptionInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        active_forms = [
            form for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False)
        ]
        if len(active_forms) < 2:
            raise ValidationError("Для вопроса требуется минимум два варианта ответа.")
        correct_count = sum(1 for form in active_forms if form.cleaned_data.get("is_correct"))
        if correct_count != 1:
            raise ValidationError("Для вопроса должен быть выбран ровно один правильный вариант.")


    def save(self, commit=True):
        active_forms = [
            form for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False)
        ]
        deleted_instances = [
            form.instance for form in self.deleted_forms
            if form.instance.pk
        ]
        if commit:
            for obj in deleted_instances:
                obj.delete()

        instances = []
        for index, form in enumerate(active_forms, start=1):
            instance = form.save(commit=False)
            instance.question = self.instance
            instance.order = index
            if commit:
                instance.save()
            instances.append(instance)

        return instances


AnswerOptionFormSet = inlineformset_factory(
    Question,
    AnswerOption,
    form=AnswerOptionForm,
    formset=BaseAnswerOptionInlineFormSet,
    fields=("text", "is_correct"),
    extra=4,
    min_num=2,
    validate_min=True,
    can_delete=True,
)


class AdminUserForm(StyledFormMixin, forms.ModelForm):
    password1 = forms.CharField(
        required=False,
        widget=forms.PasswordInput,
        label="Пароль",
    )
    password2 = forms.CharField(
        required=False,
        widget=forms.PasswordInput,
        label="Подтверждение пароля",
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "last_name",
            "first_name",
            "middle_name",
            "phone",
            "role",
            "academic_group",
            "is_active",
        )

    def __init__(self, *args, **kwargs):
        self.is_create = kwargs.pop("is_create", False)
        self.show_active_field = kwargs.pop("show_active_field", True)
        super().__init__(*args, **kwargs)
        self.fields["academic_group"].required = False
        if not self.show_active_field:
            self.fields.pop("is_active", None)
        if self.is_create:
            self.fields["password1"].required = True
            self.fields["password2"].required = True

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            return None
        qs = User.objects.filter(email__iexact=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Пользователь с такой почтой уже существует.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        role = cleaned_data.get("role")
        group = cleaned_data.get("academic_group")
        if role == User.Role.STUDENT and not group:
            self.add_error("academic_group", "Для студента необходимо указать учебную группу.")
        if role != User.Role.STUDENT:
            cleaned_data["academic_group"] = None
        if password1 or password2:
            if password1 != password2:
                self.add_error("password2", "Пароли не совпадают.")
        elif self.is_create:
            self.add_error("password1", "Пароль обязателен для нового пользователя.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password1")
        if password:
            user.set_password(password)
        elif not user.pk:
            user.set_unusable_password()
        if commit:
            user.save()
            self.save_m2m()
        return user


class AdminPasswordResetForm(StyledFormMixin, forms.Form):
    password1 = forms.CharField(widget=forms.PasswordInput, label="Новый пароль")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Подтверждение пароля")

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password1") != cleaned_data.get("password2"):
            self.add_error("password2", "Пароли не совпадают.")
        return cleaned_data


class AcademicGroupForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = AcademicGroup
        fields = ("name", "description", "curator")
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class DisciplineForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Discipline
        fields = ("name", "code", "description", "teachers", "groups")
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class ActivityLogFilterForm(StyledFormMixin, forms.Form):
    action_type = forms.ChoiceField(
        choices=[("", "Все типы")] + list(ActivityLog.ActionType.choices),
        required=False,
        label="Тип действия",
    )
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        label="Пользователь",
        empty_label="Все пользователи",
    )
