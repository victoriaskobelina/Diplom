import os

from django.core.asgi import get_asgi_application

# asgi-точка входа используется асинхронными серверами приложения
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'btzhtis_portal.settings')

application = get_asgi_application()
