#!/bin/bash

function git_wrapper {
    if [ -z "`which expect`" ]; then
	apt-get install -y --force-yes expect >/dev/null
    fi
    expect -c "spawn git clone $1
    	set timeout 100
        expect \"password\"
        send \"123456\r\n\"
        expect eof"
}

if [ -z "$1" ];then
    echo "############################"
    echo "usage:publish.sh <version>"
    echo "for example: publich.sh 2.0.6"
    exit 0
fi

if [ -z "$2" ]; then
    echo "****************************"
    echo "usage: publish.sh <BIG_VERSION> <SMALL_VERSION>"
    echo "for exmaple: publish.sh 2 4"
    echo "             version is 2.0.4"
    exit 0
fi

echo "################################"
echo "Start build the version file"

current_dir=`pwd`
#cd $current_dir
current_version=v$1.0.$2
current_version_outside=v$1.1.$2
#current_version_outside=v$1.0.$2

current_version_dir=$current_dir/$current_version
current_creeper_branch="creeper_base_20130404"

# #################
echo "Make the version($current_version) dir"
mkdir -p $current_version

cd $current_version
echo "clone git from creeper.git"
git_wrapper gaomeijie@192.168.0.5:/home/cloud/git_repo/creeper.git

cd creeper
echo "checkout branch($current_creeper_branch) from creeper.git"
git checkout $current_creeper_branch

cd tools/
chmod +x publish.sh
./publish.sh $1 $2

#Begin to copy setup script of grizzly
echo "Begin to pull the new tool for setting up openstack grizzly!"
cd $current_version_dir

echo "clone git from grizzly20130618.git"
git_wrapper gaomeijie@192.168.0.5:/home/cloud/git_repo/grizzly20130618.git


# xxxxx
cd grizzly20130618
rm .git/ -rf
rm .gitignore
cp ./* ../product -r

mkdir -p ../product/res/spice_proxy
mkdir -p ../product/res/creeper_proxy
mkdir -p ../product/res/license
#cd ../product/

# Add spice git repo
#cd $current_version_dir
#echo "Add spice proxy"
#git_wrapper gaomeijie@192.168.0.5:/home/cloud/git_repo/spice_proxy.git 
#cd spice_proxy
#rm .git/ -rf
#cp ./* ../product/res/spice_proxy -r

cd $current_version_dir
git_wrapper gaomeijie@192.168.0.5:/home/cloud/git_repo/monitor_proxy.git 
cd monitor_proxy
rm .git/ -rf
cp ./* ../product/res/creeper_proxy -r

echo "Add spice proxy and creeper proxy done"

echo "Add license code"
echo "Begin !!!!"

cd $current_version_dir
git_wrapper gaomeijie@192.168.0.5:/home/cloud/git_repo/license.git
cd license
rm .git/ -rf
cp ./* ../product/res/license -r

echo "Add license code done!"


cd $current_version_dir
# Begin to get the modify code from the support_exchange_base_grizzly0103
echo "clone git from support_exchange_base_grizzly0103.git"
git_wrapper gaomeijie@192.168.0.5:/home/cloud/git_repo/support_exchange_base_grizzly0103.git
cd support_exchange_base_grizzly0103
support_exchange_base_grizzly0103_modules="cinder nova keystone quantum glance"
for module in $support_exchange_base_grizzly0103_modules
do
    git checkout $module
    if [ -e "$module" ];then
        echo "cp $module from git repo"
        cp $module/ ../product/res/ -r
        if [ "$module" == "glance" ];then
            cp glanceclient/ ../product/res/ -r
        fi
    else
        echo "ignore $module because of empty"
    fi

done 

cd $current_version_dir/product/

# Done get the source code
echo "Begin to tar all the files to the version"
echo "First,get the binary sources"

binary_dir=`pwd`

#get binary source
function get_source() {
     resource_file=$binary_dir/res.command

     if [ ! -d "$resource_file" ]; then
	     rm -rf $resource_file
     fi

     touch $resource_file

 cat <<RESOURCE_COMMAND > $resource_file
	cd product
	cd version
	cd install
	cd ginstall
	get vrvcloudv3.1.4_install_guide.pdf vrvcloudv3.1.4_install_guide.pdf
	cd binary
	get g_source.tgz g_source.tgz
	exit
RESOURCE_COMMAND

     cat $binary_dir/res.command | smbclient //192.168.0.5/share -N -c 
}

echo "get binary sources from smb share(192.168.0.5)"
get_source


tar xvf g_source.tgz
rm g_source.tgz -rf
echo "Second,compress all the files"
if [ ! -d "res.command" ]; then
    rm -rf "res.command"
fi
tar zcvf $current_version_outside.tgz ./* 


#"###########################"
#"Put the file to server"

#Put the version source to server
current_path=`pwd`
md5_sum=`md5sum $current_version_outside.tgz`
echo "$md5_sum" > $current_version_outside.tgz.md5sum

function put_version_to_server() {
    resource_file=$current_path/res.command

    if [ ! -d "$resource_file" ]; then
        rm -rf $resource_file
    fi

    touch $resource_file

cat <<RESOURCE_COMMAND > $resource_file
    cd product
    cd version
    cd all
    cd g_version
    cd v3.1.4
    put $current_path/$current_version_outside.tgz.md5sum $current_version_outside.tgz.md5sum
    put $current_path/$current_version_outside.tgz $current_version_outside.tgz
    exit
RESOURCE_COMMAND

    cat $current_path/res.command | smbclient //192.168.0.5/share -N -c
}

echo "put version($current_version_outside.tgz) to smb share(192.168.0.5)"
put_version_to_server
echo "Done"
