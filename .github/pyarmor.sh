DI=$( dirname -- "$0"; )

mv hiddifypanel/VERSION VERSION
pyarmor gen -r -O . -e 60 --assert-call hiddifypanel || exit(1)
mv VERSION hiddifypanel/VERSION 
files=$(find . -name '*.py')
for f in  $files ;do 
    echo $l $f
    sed -i "s|Pyarmor 8.1.0 (trial), 000000,||g" $f
    cat $DI/comment.txt>> $f
done

