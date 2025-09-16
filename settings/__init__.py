from split_settings.tools import optional, include

include(
    'django.py',
    'rest.py',
    'project.py',
    'spectacular.py',
    optional('production.py'),
    optional('local_settings.py'),
)