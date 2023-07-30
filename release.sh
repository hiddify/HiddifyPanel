#!/bin/bash

#python3 setup.py build_ext --inplace
# if [ "$(id -u)" -ne 0 ]; then
#        # echo 'This script must be run by root' >&2
#        # exit 1
# fi
source .env

do_release=${1:-0}
if [[ $do_release == 1 ]];then
git status
make release 
fi
exit 
rm -rf build/; rm -rf dist/;
rm -rf ../tmp_release

# $(find hiddifypanel/panel/api/  hiddifypanel/models/ hiddifypanel/panel/telegrambot/ -name "*.py")
# bash ../HiddifyPanel/.github/cython_prepare.sh


# python3 setup.py bdist_wheel build_ext
# exit 1
# if [[ $? == "0" ]];then
mkdir -p ../tmp_release
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=$TWINE_PASSWORD
source ~/miniconda3/etc/profile.d/conda.sh

for pythonversion in 3.11 3.8 3.9 3.10 ;do
       
       cp -rf . ../tmp_release/$pythonversion
       pushd ../tmp_release/$pythonversion
      
       conda activate py$pythonversion
       
       # pip install setuptools wheel twine cython pyarmor==8.1.0 pyarmor.cli.core==2.1.0
       pip install setuptools wheel twine cython pyarmor==8.1.6 pyarmor.cli.core==2.1.6
       .github/pyarmor.sh || exit 1
       ls .github/
       echo "hhhhhhhhhhhhhhhhha" $pythonversion
       python3 --version
       if [ $do_release == 0 ];then
              pip3 install .
              flask run
              exit
       fi
       echo $(pwd)
       # ls
       python3 setup.py bdist_wheel --plat-name=manylinux2014_aarch64 build_ext --inplace
       twine upload dist/*
       rm dist/*
       rm build/*
       popd
done
conda deactivate


# fi
