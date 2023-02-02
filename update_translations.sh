#!/bin/bash
PATH=/config/.local/bin:$PATH
pybabel extract -F babel.cfg -o messages.pot hiddifypanel
pybabel update  -i messages.pot -d hiddifypanel/translations -l en

pip install polib deep-translator
python3 auto_translate.py fa en
python3 auto_translate.py en fa
python3 auto_translate.py en zh

pybabel update  -i messages.pot -d hiddifypanel/translations -l fa
pybabel update  -i messages.pot -d hiddifypanel/translations -l zh
pybabel compile -f -d hiddifypanel/translations 