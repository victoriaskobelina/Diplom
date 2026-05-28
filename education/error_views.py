from .utils import forbidden_response


def permission_denied(request, exception=None):
    message = str(exception) if exception else ""
    return forbidden_response(request, message or "У вас нет доступа к этому разделу.")
