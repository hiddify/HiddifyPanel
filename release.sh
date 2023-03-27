#!/bin/bash

#python3 setup.py build_ext --inplace
if [ "$(id -u)" -ne 0 ]; then
       echo 'This script must be run by root' >&2
       exit 1
fi
source .env

do_release=0
if [[ $do_release == 1 ]];then
make release 
fi
rm -rf build/; rm -rf dist/;
rm -rf ../tmp_release
cp -rf . ../tmp_release
cd ../tmp_release 

# $(find hiddifypanel/panel/api/  hiddifypanel/models/ hiddifypanel/panel/telegrambot/ -name "*.py")
bash ../HiddifyPanel/.github/cython_prepare.sh

export CIBW_SKIP='pp*'
python3 setup.py  build_ext --inplace
cibuildwheel --platform linux --archs aarch64
# python3 setup.py bdist_wheel build_ext
# exit 1
# if [[ $? == "0" ]];then
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=$TWINE_PASSWORD

pip install setuptools wheel twine cython cibuildwheel

twine upload wheelhouse/*
rm dist/*
rm build/*


# fi
