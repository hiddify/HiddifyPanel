DI=$( dirname -- "$0"; )

for l in $(cat $DI/cython_files.txt)  ;do 
    for f in $(find $l -name '*.py')  ;do 
        echo $l $f
        if [[ $(basename $f) != "__init__.py" ]];then
            mv $f ${f}x;
        fi
        echo "#واقعا برای 5 دلار میخوای کرک میکنی؟ حاجی ارزش وقت خودت بیشتره" > $(dirname $f)/read.py
        echo "#Email hiddify@gmail.com for free permium version. \$?" >> $(dirname $f)/read.py
    done
done
