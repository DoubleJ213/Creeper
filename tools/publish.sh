#!/bin/bash

if [ -z "$1" ]; then
    echo "****************************"
    echo "usage: publish.sh <BIG_VERSION> <SMALL_VERSION>"
    echo "for exmaple: publish.sh 2 4"
    echo "             version is 2.0.4"
    exit 0
fi

if [ -z "$2" ]; then
    echo "****************************"
    echo "usage: publish.sh <BIG_VERSION> <SMALL_VERSION>"
    echo "for exmaple: publish.sh 2 4"
    echo "             version is 2.0.4"
    exit 0
fi

PROJECT_NAME='creeper'

echo "mkdir product fold for generate tgz"
CURRENT_DIR=`pwd`
cd $CURRENT_DIR/../../
mkdir -p product

cd product
PRODUCT_DIR=`pwd`

echo "copy product"
cp ../creeper . -vR

echo "remove pycharm project folder .idea"
rm -rf $PROJECT_NAME/.idea

echo "remove lib_change_list.rst"
rm -rf $PROJECT_NAME/lib_change_list.rst

echo "remove .gitignore "
rm -rf $PROJECT_NAME/.gitignore

echo "remove .git"
rm -rf $PROJECT_NAME/.git

echo "remove pre_config"
rm -rf $PROJECT_NAME/pre_config

echo "empty upload fold"
rm -rf $PROJECT_NAME/creeper/media/*

echo "remove debs,connection.py,publish.sh because cloud system has debs published"
rm -rf $PROJECT_NAME/tools/publish.sh

echo "change version with creeper"
echo "use big VERSION $1"
echo "use small VERSION $2"
SETTINGS_FILE=${SETTINGS_FILE:-"$PROJECT_NAME/creeper/settings.py"}
sed -i "/PRODUCT_VERSION =/d" $SETTINGS_FILE
sed -i "/PRODUCT_NAME =/a\PRODUCT_VERSION = 'v$1.1.$2'" $SETTINGS_FILE
sed -i "/INTERNAL_VERSION =/d" $SETTINGS_FILE
sed -i "/PRODUCT_VERSION =/a\INTERNAL_VERSION = 'v$1.0.$2'" $SETTINGS_FILE
sed -i "/PRODUCT_TIME =/d" $SETTINGS_FILE
CURRENT_TIME=`date "+%Y-%m-%d %H:%M:%S"`
sed -i "/INTERNAL_VERSION =/a\PRODUCT_TIME = '$CURRENT_TIME'" $SETTINGS_FILE

echo "compile *.py for project"
python -c "import compileall;compileall.compile_dir('${PRODUCT_DIR}', 100000000000 , force=True );"

echo "cancel *.py for code protected"
find $PROJECT_NAME/dashboard -name "*.py" | xargs rm -rf
find $PROJECT_NAME/.venv -name "*.pyc" | xargs rm -rf

echo "package version"
tar zcvf creeper.tgz $PROJECT_NAME/

echo "remove copy"
rm -rf $PROJECT_NAME
