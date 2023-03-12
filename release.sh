#!/bin/bash
if [ "$(id -u)" -ne 0 ]; then
       echo 'This script must be run by root' >&2
       exit 1
fi
source .env
make release 
cibuildwheel --platform linux --archs aarch64
if [[ $? == "0" ]];then
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=$TWINE_PASSWORD

pip install setuptools wheel twine cython cibuildwheel
rm wheelhouse/*
rm dist/*
rm build/*

twine upload wheelhouse/*
fi