############################################################################
modify .venv/local/lib/python2.7/site-packages/django/core/urlresolvers.py
line 293,314
@ 2013.1.31
############################################################################
diff --git a/.venv/local/lib/python2.7/site-packages/django/middleware/csrf.py b/.venv/local/lib/python2.7/site-packages/django/middleware/csrf.py
index 3ab70a0..3e74fa2 100755
--- a/.venv/local/lib/python2.7/site-packages/django/middleware/csrf.py
+++ b/.venv/local/lib/python2.7/site-packages/django/middleware/csrf.py
@@ -170,6 +170,16 @@ class CsrfViewMiddleware(object):
             if request.method == "POST":
                 request_csrf_token = request.POST.get('csrfmiddlewaretoken', '')
 
+            # add by tom for http method PUT and DELETE
+            # add begin
+            if request.method == "DELETE":
+                request_csrf_token = request.DELETE.get('csrfmiddlewaretoken', '')
+
+            if request.method == "PUT":
+                request_csrf_token = request.PUT.get('csrfmiddlewaretoken', '')
+
+            # add end
+
             if request_csrf_token == "":
                 # Fall back to X-CSRFToken, to make things easier for AJAX,
                 # and possible for PUT/DELETE.

@ 2013.1.31
#############################################################################
modify .venv/local/lib/python2.7/site-packages/django/core/handlers/base.py
line 100
@ 2013.1.31
#############################################################################
diff --git a/creeper/settings.py b/creeper/settings.py
index 00649d8..4ef37b3 100755
--- a/creeper/settings.py
+++ b/creeper/settings.py
@@ -59,12 +59,12 @@ USE_TZ = True
 
 # Absolute filesystem path to the directory that will hold user-uploaded files.
 # Example: "/home/media/media.lawrence.com/media/"
-MEDIA_ROOT = ''
+MEDIA_ROOT = os.path.abspath(os.path.join(ROOT_PATH,'media'))
 
 # URL that handles the media served from MEDIA_ROOT. Make sure to use a
 # trailing slash.
 # Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
-MEDIA_URL = ''
+MEDIA_URL = '/media/'
 
 # Absolute path to the directory static files should be collected to.
 # Don't put anything in this directory yourself; store your static files
@@ -81,6 +81,7 @@ STATICFILES_DIRS = (
     # Put strings here, like "/home/html/static" or "C:/www/django/static".
     # Always use forward slashes, even on Windows.
     # Don't forget to use absolute paths, not relative paths.
+    os.path.join(ROOT_PATH,'static'),
 )
 
 # List of finder classes that know how to find static files in
@@ -138,7 +139,8 @@ INSTALLED_APPS = (
     # Uncomment the next line to enable admin documentation:
     # 'django.contrib.admindocs',
     'dashboard',
-    'dashboard.control_manage'
+    'dashboard.control_manage',
+    'dashboard.node_manage',
 )
 
 try:
@ 2012.2.17 16:35
############################################################################
diff --git a/.venv/local/lib/python2.7/site-packages/novaclient/v1_1/usage.py b/.venv/local/lib/python2.7/site-packages/novaclient/v1_1/usage.py
index b55f159..0a08654 100644
--- a/.venv/local/lib/python2.7/site-packages/novaclient/v1_1/usage.py
+++ b/.venv/local/lib/python2.7/site-packages/novaclient/v1_1/usage.py
@@ -29,9 +29,11 @@ class UsageManager(base.ManagerWithFind):
                          instance whose usage is part of the report
         :rtype: list of :class:`Usage`.
         """
+        start = start.strftime('%Y-%m-%d %H:%M:%S.%f')
+        end = end.strftime('%Y-%m-%d %H:%M:%S.%f')
         return self._list(
                     "/os-simple-tenant-usage?start=%s&end=%s&detailed=%s" %
-                    (start.isoformat(), end.isoformat(), int(bool(detailed))),
+                    (start, end, int(bool(detailed))),
                     "tenant_usages")
 
     def get(self, tenant_id, start, end):
@@ -43,6 +45,8 @@ class UsageManager(base.ManagerWithFind):
         :param end: :class:`datetime.datetime` End date
         :rtype: :class:`Usage`
         """
+        start = start.strftime('%Y-%m-%d %H:%M:%S.%f')
+        end = end.strftime('%Y-%m-%d %H:%M:%S.%f')
         return self._get("/os-simple-tenant-usage/%s?start=%s&end=%s" %
-                         (tenant_id, start.isoformat(), end.isoformat()),
+                         (tenant_id, start, end),
                          "tenant_usage")
@ 2012.2.28 14:57
############################################################################
/.venv/local/lib/python2.7/site-packages/django/forms/forms.py
line22
-#NON_FIELD_ERRORS = '__all__' update by zhaolei
+NON_FIELD_ERRORS = ''
/.venv/local/lib/python2.7/site-packages/django/forms/util.py
line 44
-return '\n'.join(['* %s\n%s' % (k, '\n'.join(['  * %s' % force_text(i) for i in v])) for k, v in self.items()])
+return '\n'.join([' %s\n%s' % (k, '\n'.join(['   %s' % force_text(i) for i in v])) for k, v in self.items()])
@ 2013.7.10 16:35
############################################################################