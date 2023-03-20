DI=$( dirname -- "$0"; )

for l in $(cat $DI/cython_files.txt)  ;do 
    for f in $(find $l -name '*.py')  ;do 
        echo $l $f
        if [[ $(basename $f) != "__init__.py" ]];then
            mv $f ${f}x;
        fi
        cat $DI/cython_files.txt>$(dirname $f)/read.py
    done
done
