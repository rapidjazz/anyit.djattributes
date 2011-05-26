# -*- coding: utf-8 -*-
import os
DEBUG = True
TEMPLATE_DEBUG = DEBUG
STATIC_SERVE = True

ROOT_PATH = os.path.abspath(os.path.dirname(__file__))


ADMINS = (
     ('jah', 'jah@example.de'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE' : 'django.db.backends.sqlite3',           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'ado_mssql'.
        'NAME' : 'attr.db',             # Or path to database file if using sqlite3.
    },
}
SECRET_KEY = 'anysecretkey'
TIME_ZONE = 'Europe/Berlin'
SITE_ID = 1

USE_I18N = True

MEDIA_ROOT = os.path.join(ROOT_PATH,'static/media')
MEDIA_URL = 'http://127.0.0.1/site_media/'
ADMIN_MEDIA_PREFIX = '/admin_media/'

MIDDLEWARE_CLASSES = (
)

TEMPLATE_LOADERS = (
)

TEMPLATE_DIRS = (
)

TEMPLATE_CONTEXT_PROCESSORS = (
)

ROOT_URLCONF = 'djattributes.urls'

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'attributes',
)

INTERNAL_IPS = ['127.0.0.1',]

LANGUAGES = (
  #('de', _('German')),
  ('en', 'English'),
)

