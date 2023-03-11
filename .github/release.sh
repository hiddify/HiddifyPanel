rm -rf release
mkdir -p release
cp -r * release/
pyarmor obfuscate --recursive  --output release/hiddifypanel/  hiddifypanel/__init__.py
cd release
python setup.py sdist bdist_wheel
twine upload dist/*

