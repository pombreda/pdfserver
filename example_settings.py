# Django settings for pdfserver project.

import os

# pdfserver serves static files in debug mode
DEBUG = True

# Pdfserver supports l10n
USE_I18N = True
USE_L10N = True

# Sessions are needed for referencing files. They are currently not written to and thus not
#   created. Also, we want to lose the files once gone from the site.
SESSION_SAVE_EVERY_REQUEST = True;
SESSION_EXPIRE_AT_BROWSER_CLOSE = True;

DIRNAME = os.path.dirname(__file__)

# Directory holding js and css files
MEDIA_ROOT = os.path.abspath(os.path.join(DIRNAME, 'media'))

# Upload parent directory directory. Uploads will go to UPLOAD_TO/uploads
UPLOAD_TO = MEDIA_ROOT

# If you don't have other applications installed set you can set this
ROOT_URLCONF = '[YOUR_PROJECT].pdfserver.urls'

# pdfserver needs Sessions and supports Locales
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
)

# pdfserver needs the Sessions application
INSTALLED_APPS = (
    'django.contrib.sessions',
    'pdfserver',
)
