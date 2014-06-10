#!/bin/bash

CURRENT_DIR=`pwd`

. env.rc
echo "setup origin dashboard"
apt-get install -y --force-yes libapache2-mod-wsgi openstack-dashboard

echo "********************************************************"
echo "change own of fold MEDIA for uploading files "
mkdir $CURRENT_DIR/../creeper/media
chown www-data:www-data $CURRENT_DIR/../creeper/media -R
chmod 775 $CURRENT_DIR/../creeper/media -R

chown www-data:www-data $CURRENT_DIR/../creeper/license -R
chmod 755 $CURRENT_DIR/../creeper/license -R

# log dir for creeper
mkdir /var/log/creeper
chown www-data:www-data /var/log/creeper
chmod 755 -R /var/log/creeper
# log dir for proxy
mkdir /var/log/creeper_proxy
chmod 755 -R /var/log/creeper_proxy

echo "********************************************************"
echo "generate creeper.conf"
cat << EOF > ./creeper.conf
WSGIScriptAlias / $CURRENT_DIR/../creeper/wsgi.py
WSGIDaemonProcess creeper user=www-data group=www-data processes=3 threads=10
Alias /static $CURRENT_DIR/../creeper/static/
WSGIPythonPath $CURRENT_DIR/../.venv/local/lib/python2.7/site-packages
<Directory $CURRENT_DIR/../creeper>
<Files wsgi.py>
  Order deny,allow
  Allow from all
</Files>
</Directory>
EOF

echo "********************************************************"
OPENSTACK_APACHE2_CONFIG_PATH=${OPENSTACK_APACHE2_CONFIG_PATH:-"/etc/apache2/conf.d"}
echo "copy creeper.conf to $OPENSTACK_APACHE2_CONFIG_PATH"
mv $OPENSTACK_APACHE2_CONFIG_PATH/openstack-dashboard.conf $CURRENT_DIR/
cp $CURRENT_DIR/creeper.conf $OPENSTACK_APACHE2_CONFIG_PATH/

echo "********************************************************"
echo "change memcached backend"
LOCAL_SETTINGS_FILE=${LOCAL_SETTINGS_FILE:-"$CURRENT_DIR/../creeper/local/local_settings.py"}
sed -i '/CACHE_BACKEND =/d' $LOCAL_SETTINGS_FILE
sed -i "/CACHE_BACKED/a\CACHE_BACKEND = 'memcached://127.0.0.1:11211/'" $LOCAL_SETTINGS_FILE

echo "change admin token"
sed -i '/OPENSTACK_ADMIN_TOKEN =/d' $LOCAL_SETTINGS_FILE
sed -i "/Configure admin token/a\OPENSTACK_ADMIN_TOKEN = '$OPENSTACK_ADMIN_TOKEN'" $LOCAL_SETTINGS_FILE

echo "********************************************************"
echo "change auth backend"
sed -i '/OPENSTACK_HOST =/d' $LOCAL_SETTINGS_FILE
sed -i "/OPENSTACK_KEYSTONE_URL/i\OPENSTACK_HOST = '$AUTHORIZE_SERVER_IP'" $LOCAL_SETTINGS_FILE

echo "********************************************************"
echo "change voyage api url"
sed -i "/VOYAGE_BASE_URL = /d" $LOCAL_SETTINGS_FILE
sed -i "/VOYAGE_OBJECTS_URL/i\VOYAGE_BASE_URL = 'http:\/\/$AUTHORIZE_SERVER_IP:9257'" $LOCAL_SETTINGS_FILE

echo "********************************************************"
echo "change websocket api url"
sed -i "/VOYAGE_WEBSOCKET_ADDRESS = /d" $LOCAL_SETTINGS_FILE
sed -i "/VOYAGE_BASE_URL/i\VOYAGE_WEBSOCKET_ADDRESS = 'ws:\/\/$AUTHORIZE_SERVER_IP:9998'" $LOCAL_SETTINGS_FILE

echo "********************************************************"
echo "change database config"
SETTINGS_FILE=${SETTINGS_FILE:-"$CURRENT_DIR/../creeper/settings.py"}
sed -i "/'NAME'/d" $SETTINGS_FILE
sed -i "/'ENGINE'/a\        'NAME': '$CREEPER_DATABASE_NAME'," $SETTINGS_FILE
sed -i "/'USER'/d" $SETTINGS_FILE
sed -i "/'NAME'/a\        'USER': '$CREEPER_DATABASE_USER'," $SETTINGS_FILE
sed -i "/'PASSWORD'/d" $SETTINGS_FILE
sed -i "/'USER'/a\        'PASSWORD': '$CREEPER_DATABASE_PASSWD'," $SETTINGS_FILE
sed -i "/'HOST'/d" $SETTINGS_FILE
sed -i "/'PASSWORD'/a\        'HOST': '$MYSQL_SERVER_IP'," $SETTINGS_FILE

echo "********************************************************"
echo "chanage cache config"
sed -i "/'LOCATION'/d" $SETTINGS_FILE
sed -i "/'BACKEND'/a\        'LOCATION': '$CONTROL_NODE_IP:11211'," $SETTINGS_FILE

echo "********************************************************"
echo "Initialize node information"
INIT_NODE_INFORMATION_FILE=${INIT_NODE_INFORMATION_FILE:-"$CURRENT_DIR/../creeper/local/local_settings.py"}
CONTROLLER_NAME=`hostname`
sed -i "s/CONTROLLER_HOST_NAME.*/CONTROLLER_HOST_NAME = '$CONTROLLER_NAME'/g" $INIT_NODE_INFORMATION_FILE
sed -i "s/CONTROLLER_HOST_IP.*/CONTROLLER_HOST_IP = '$AUTHORIZE_SERVER_IP'/g" $INIT_NODE_INFORMATION_FILE

echo "********************************************************"
echo "setup python VENV"
VENV_ACTIVE_FILE=${VENV_ACTIVE_FILE:-"$CURRENT_DIR/../.venv/bin/activate"}
sed -i '/VIRTUAL_ENV=/d' $VENV_ACTIVE_FILE
sed -i "/export VIRTUAL_ENV/i\VIRTUAL_ENV=$CURRENT_DIR/../.venv" $VENV_ACTIVE_FILE
chmod a+x $CURRENT_DIR/../manage.py
source $VENV_ACTIVE_FILE
echo no | $CURRENT_DIR/../manage.py syncdb


rm /var/log/creeper/creeper.log

echo "********************************************************"
echo "restart service apache2"
service apache2 restart
