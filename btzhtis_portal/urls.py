from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, reverse_lazy
from education import views as education_views

# общие маршруты авторизации и подключение маршрутов учебного приложения
urlpatterns = [
    path('accounts/login/', education_views.home, name='login'),
    path(
        'accounts/logout/',
        auth_views.LogoutView.as_view(next_page=reverse_lazy('education:home')),
        name='logout',
    ),
    path(
        'accounts/password_change/',
        auth_views.PasswordChangeView.as_view(
            template_name='registration/password_change_form.html',
            success_url=reverse_lazy('password_change_done'),
        ),
        name='password_change',
    ),
    path(
        'accounts/password_change/done/',
        auth_views.PasswordChangeDoneView.as_view(
            template_name='registration/password_change_done.html',
        ),
        name='password_change_done',
    ),
    path('accounts/password_reset/', education_views.password_reset_info, name='password_reset'),
    path('', include('education.urls')),
]

handler403 = 'education.views.permission_denied'

# в режиме разработки показываем Django admin и раздаем загруженные медиафайлы
if settings.DEBUG:
    urlpatterns.insert(0, path('django-admin/', admin.site.urls))
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
