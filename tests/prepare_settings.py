from django.conf import settings, global_settings

if not settings.configured:
    settings.configure(global_settings, TEST = 'TRUE') 