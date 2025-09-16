from settings.django import INSTALLED_APPS
from version import get_git_version

GIT_VERSION = get_git_version()

INSTALLED_APPS.extend([
    'home_budget',
])
