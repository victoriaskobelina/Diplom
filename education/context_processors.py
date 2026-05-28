# добавляет имя текущего маршрута во все шаблоны для подсветки активной навигации
def navigation_context(request):
    view_name = getattr(getattr(request, "resolver_match", None), "view_name", "")
    return {
        "current_view_name": view_name,
    }
