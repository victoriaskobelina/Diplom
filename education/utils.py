from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from .models import ActivityLog


def log_activity(request, user, action_type, description):
    ip_address = None
    if request:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        ip_address = forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR")
    ActivityLog.objects.create(
        user=user,
        action_type=action_type,
        description=description,
        ip_address=ip_address,
    )


def dashboard_url_for(user):
    if getattr(user, "is_administrator", False):
        return "education:admin_dashboard"
    if getattr(user, "is_teacher", False):
        return "education:teacher_dashboard"
    return "education:student_dashboard"


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")
            if request.user.is_superuser or request.user.role in roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, "У вас нет доступа к данному разделу.")
            return redirect(dashboard_url_for(request.user))

        return _wrapped_view

    return decorator
