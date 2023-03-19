rm -rf release
#mkdir -p release
cp -r ./ release/

# pyarmor runtime -O release/dist/share --enable-suffix 1
# pyarmor obfuscate --recursive --with-runtime @release/dist/share --output release/hiddifypanel/  hiddifypanel/__init__.py
echo "vaghe"
for f in $(find hiddifypanel/models -name "*.py");do
    echo $f
    cat .github/comment.txt > release/$f
    # pyminifier --replacement-length=50  -O --obfuscate-builtins --obfuscate-import-methods --nonlatin  $f >>release/$f
    #pyminifier -O --nonlatin  $f >>release/$f
    
    sed -i "s|# Created by pyminifier (https://github.com/liftoff/pyminifier)||g" release/$f
done
#cd release
#python3 setup.py sdist bdist_wheel
#twine upload dist/*

