from django.conf.urls import patterns, include

from dashboard.urls import url
from dashboard.authorize_manage.views import get_login_view

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', get_login_view, name='get_login_view', method='get'),
    url(r'^auth/', include('openstack_auth.urls')),
    url(r'', include('dashboard.site_urls')),
    #url(r'^authorize/',include('dashboard.authorize.urls')),
    #url(r'^$','dashboard.login.views.splash',name='splash'),
    #url(r'^auth/',include('openstack_auth.urls')),
    # Examples:
    # url(r'^$', 'creeper.views.home', name='home'),
    # url(r'^creeper/', include('creeper.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

js_info_dict = {
    'packages': ('your.app.package',),
    }

urlpatterns += patterns('',
    url(r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict),
)
