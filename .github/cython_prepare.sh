DI=$( dirname -- "$0"; )

for l in $(cat $DI/cython_files.txt)  ;do 
    files=$(find $l -name '*.py')
    for f in  $files ;do 
        echo $l $f
        if [[ $(basename $f) != "__init__.py" ]];then
            mv $f ${f}x;
        fi
        cat $DI/comment.txt>$(dirname $f)/read.py
    done
done
