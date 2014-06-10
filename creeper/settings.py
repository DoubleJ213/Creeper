 # Django settings for creeper project.

import os
import logging

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.abspath(os.path.join(ROOT_PATH, '..', 'bin'))
SERIAL_BIN = os.path.abspath(os.path.join(ROOT_PATH, '../tools/create_serial'))
DECRYPT_BIN = os.path.abspath(os.path.join(ROOT_PATH, '../tools/creeper_decrypt'))
SERIAL_FILE = os.path.abspath(os.path.join(ROOT_PATH, 'license/serial.txt'))
LICENSE_FILE = os.path.abspath(os.path.join(ROOT_PATH, 'license/license.txt'))
LICENSE_TMP_FILE = os.path.abspath(os.path.join(ROOT_PATH, 'license/tmp.txt'))

PRODUCT_NAME = 'creeper'
PRODUCT_VERSION = 'V2.1.6'
INTERNAL_VERSION = 'V2.0.6'
PRODUCT_TIME = '2013-01-17 14:40'

ADMINS = (
    # ('tangjun', 'tangjun@jointlab.org'),
)

MANAGERS = ADMINS

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'creeper',
        'USER': 'creeper',
        'PASSWORD': '123456',
        'HOST': '192.168.0.8',
        'default-character-set':'utf-8',# Set to empty string for default. Not used with sqlite3.
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '192.168.0.8:11211',
        'TIMEOUT': 0,
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Asia/Shanghai'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'zh-cn'

LOGIN_URL = '/authorize_manage/login/'
LOGOUT_URL = '/authorize_manage/logout/'
LOGIN_REDIRECT_URL = '/'
AUTHENTICATION_BACKENDS = ('openstack_auth.backend.KeystoneBackend',)
SITE_ID = 1

OPENSTACK_KEYSTONE_DEFAULT_ROLE = 'Member'


SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
SESSION_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SECURE = False

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.abspath(os.path.join(ROOT_PATH,'media'))
DOC_ROOT = os.path.abspath(os.path.join(ROOT_PATH,'doc'))
EXPORTS_ROOT = os.path.abspath(os.path.join(ROOT_PATH,'log_exports'))
# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# URL that handles the logs served from EXPORTS_ROOT.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'
DOC_URL = '/doc/'
DOC_FILE = 'doc.odt'
EXPORTS_URL = '/log_exports/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(ROOT_PATH,'')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(STATIC_ROOT, 'static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '#rn!%(d_aqz9%ku4-f9*cekzlbc40aevzealk35qrm*v6#yzy^'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'dashboard.loaders.TemplateLoader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
#    'dashboard.middleware..HorizonMiddleware',
    #'django.middleware.doc.XViewMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'dashboard.middleware.DashboardMiddleware',
    'dashboard.middleware.WantAuthorizedMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'dashboard.middleware.X_http_methodoverride_middleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'dashboard.middleware.ExpiredTimeMiddleware',
)

ROOT_URLCONF = 'creeper.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'creeper.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'dashboard',
    'dashboard.control_manage',
    'dashboard.node_manage',
    'dashboard.software_manage',
    'dashboard.log_manage',
    'dashboard.instance_manage',
    'dashboard.securitygroup_manage',
    'dashboard.notice_manage',
    'dashboard.hard_template_manage',
    'dashboard.volume_manage',
    #'dashboard.thresholds_manage',
    'dashboard.image_template_manage',
    'openstack_auth',
    'dashboard.virtual_address_manage',
    'dashboard.virtual_network_manage',
    'dashboard.virtual_network_topology',
    'dashboard.virtual_router_manage',
    'dashboard.virtual_keypairs_manage',
    'dashboard.role_manage',
    'dashboard.prepare_manage',
    'dashboard.check_manage',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    #'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.request',
    #'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
    'dashboard.context_processors.creeper_prcessor',
    )


FILE_UPLOAD_HANDLERS = (
    "dashboard.utils.uploadhandler.LogFileUploadHandler",
    "dashboard.software_manage.utils.SoftwareFileUploadHandler",
    "django.core.files.uploadhandler.MemoryFileUploadHandler",
    "django.core.files.uploadhandler.TemporaryFileUploadHandler",
)


try:
    from dashboard.site_logs import *
    LOG_INFORMATIONS = generate_informations()
except ImportError:
    logging.warning("No logs configuration file found.")

try:
    from local.local_settings import *
except ImportError:
    logging.warning("No local_settings file found.")

if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
    from django.contrib.messages import constants as message_constants
    MESSAGE_LEVEL = message_constants.DEBUG
