#!/bin/bash
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