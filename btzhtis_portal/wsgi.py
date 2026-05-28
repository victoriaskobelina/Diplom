import os

from django.core.wsgi import get_wsgi_application

# wsgi-точка входа используется классическими Python веб-серверами
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'btzhtis_portal.settings')

application = get_wsgi_application()
