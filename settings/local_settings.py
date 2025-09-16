##################################
# Production only
# Generiraj SECRET_KEY sa:
#   python -c "from django.home_budget.management import utils; print(utils.get_random_secret_key())"
##################################
SECRET_KEY = 'django-insecure-#!a+y4l@wsrdo!jh9#o)pjw7t+3n1#tiu*wp5ztq2*2g3-we%6'

# Development only, DATABASES postavke idu u production.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'home_budget',
    },
}

PREDEFINED_CATEGORIES = [
    'Groceries',
    'Entertainment',
    'Bills',
    'Savings',
    'Health',
    'Travel',
]
