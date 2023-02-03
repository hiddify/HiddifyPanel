#!/bin/bash
source .env

PATH=/config/.local/bin:$PATH
pybabel extract -F babel.cfg -o messages.pot hiddifypanel

wget -O hiddifypanel/translations/en/LC_MESSAGES/messages.po  "https://localise.biz/api/export/locale/en-US.po?index=id&key=5Tqp1dLHQSk98s-twNF6RpwZu7lZSLLM"

wget -O hiddifypanel/translations/fa/LC_MESSAGES/messages.po "https://localise.biz/api/export/locale/fa.po?index=id&key=5Tqp1dLHQSk98s-twNF6RpwZu7lZSLLM"
wget -O hiddifypanel/translations/zh/LC_MESSAGES/messages.po "https://localise.biz/api/export/locale/zh.po?index=id&key=5Tqp1dLHQSk98s-twNF6RpwZu7lZSLLM"

pybabel update -N -i messages.pot -d hiddifypanel/translations -l en


pip install polib deep-translator
python3 auto_translate.py fa en
python3 auto_translate.py en fa
python3 auto_translate.py en zh

pybabel update -N -i messages.pot -d hiddifypanel/translations -l fa
pybabel update -N -i messages.pot -d hiddifypanel/translations -l zh
pybabel compile -f -d hiddifypanel/translations 

function update_localise(){
    lang=$1
curl "https://localise.biz/api/import/po?index=id&delete-absent=false&ignore-existing=false&locale=$lang&flag-new=Provisional&key=$LOCALIZ_KEY" \
  -H 'Accept: application/json' \
  --data-binary "@hiddifypanel/translations/$lang/LC_MESSAGES/messages.po" \
  --compressed
  }

update_localise fa
update_localise en
update_localise zh