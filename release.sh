#!/bin/bash

#python3 setup.py build_ext --inplace
if [ "$(id -u)" -ne 0 ]; then
       echo 'This script must be run by root' >&2
       exit 1
fi
source .env
make release 

rm -rf build/; rm -rf dist/;
rm -rf release
cp -rf ./ release
cd release 
for f in "hiddifypanel/panel/hiddify.py" "hiddifypanel/panel/admin/UserAdmin.py" "hiddifypanel/panel/admin/ProxyDetailsAdmin.py" $(find hiddifypanel/panel/api/  hiddifypanel/models/ hiddifypanel/panel/telegrambot/ -name "*.py");do 
    if [[ $(basename $f) != "__init__.py" ]];then
        mv $f ${f}x;
    fi
    echo "#واقعا برای 5 دلار میخوای کرک میکنی؟ حاجی ارزش وقت خودت بیشتره" > $(dirname $f)/read.py
    echo "#You want to crack it only for 5\$?" >> $(dirname $f)/read.py
done

cibuildwheel --platform linux --archs aarch64
# python3 setup.py bdist_wheel build_ext
# exit 1
if [[ $? == "0" ]];then
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=$TWINE_PASSWORD

pip install setuptools wheel twine cython cibuildwheel
rm wheelhouse/*
rm dist/*
rm build/*

twine upload wheelhouse/*
fi