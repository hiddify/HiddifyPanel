#!/bin/bash
# source .env
source /opt/hiddify-manager/common/utils.sh
activate_python_venv

PATH=/config/.local/bin:$PATH

python -c "
from hiddifypanel import models;
print(''.join([f'{{{{_(\"config.{c}.label\")}}}}\n{{{{_(\"config.{c}.description\")}}}}\n' for c in models.ConfigEnum]));print(''.join([f'{{{{_(\"config.{cat}.label\")}}}}{{{{_(\"config.{cat}.description\")}}}}\n' for cat in models.ConfigCategory]));
def print_enum(en):
  print(''.join([f'{{{{_(\"{item}\")}}}}\n' for item in en]))
print_enum(models.DomainType)
print_enum(models.UserMode)
" >../hiddifypanel/templates/fake.html


pybabel extract -F babel.cfg -k "_gettext lazy_gettext gettext _ __" -o messages.pot ../hiddifypanel

function update_json_po() {
    lang=$1
    python translate_utils.py update-json ../hiddifypanel/translations.i18n/${lang}.json messages.pot
    
    if [[ "$?" != "0" ]];then
        echo  "error in python3 translate_utils.py update-json ../hiddifypanel/translations.i18n/${lang}.json messages.pot "
        exit $?
    fi
    python translate_utils.py to-po ../hiddifypanel/translations.i18n/${lang}.json ../hiddifypanel/translations/${lang}/LC_MESSAGES/messages.po
    if [[ "$?" != "0" ]];then
        echo "error in python3 translate_utils.py to-po ../hiddifypanel/translations.i18n/${lang}.json ../hiddifypanel/translations/${lang}/LC_MESSAGES/messages.po"
        exit $?
    fi
}

update_json_po en
update_json_po fa
update_json_po pt
update_json_po ru
update_json_po zh


# wget -O hiddifypanel/translations/en/LC_MESSAGES/messages.po "https://localise.biz/api/export/locale/en-US.po?index=id&key=5Tqp1dLHQSk98s-twNF6RpwZu7lZSLLM"
# wget -O hiddifypanel/translations/fa/LC_MESSAGES/messages.po "https://localise.biz/api/export/locale/fa.po?index=id&key=5Tqp1dLHQSk98s-twNF6RpwZu7lZSLLM"
# wget -O hiddifypanel/translations/zh/LC_MESSAGES/messages.po "https://localise.biz/api/export/locale/zh.po?index=id&key=5Tqp1dLHQSk98s-twNF6RpwZu7lZSLLM"
# wget -O hiddifypanel/translations/pt/LC_MESSAGES/messages.po "https://localise.biz/api/export/locale/pt.po?index=id&key=Y1DZZCqzlzT8rgfKImXbNzr-jTLB6c7H"
# wget -O hiddifypanel/translations/ru/LC_MESSAGES/messages.po "https://localise.biz/api/export/locale/ru.po?index=id&key=Y1DZZCqzlzT8rgfKImXbNzr-jTLB6c7H"

# pybabel update -N -i messages.pot -d hiddifypanel/translations -l en

# pip install polib deep-translator
# python3 auto_translate.py fa en
# python3 auto_translate.py en fa
# python3 auto_translate.py en zh
# python3 auto_translate.py en pt
# python3 auto_translate.py en ru

# pybabel update -N -i messages.pot -d hiddifypanel/translations -l fa
# pybabel update -N -i messages.pot -d hiddifypanel/translations -l zh
# pybabel update -N -i messages.pot -d hiddifypanel/translations -l pt
# pybabel update -N -i messages.pot -d hiddifypanel/translations -l ru
pybabel compile -f -d ../hiddifypanel/translations

# function update_localise() {
#   lang=$1
#   curl "https://localise.biz/api/import/po?index=id&delete-absent=false&ignore-existing=false&locale=$lang&flag-new=Provisional&key=$LOCALIZ_KEY" \
#     -H 'Accept: application/json' \
#     --data-binary "@hiddifypanel/translations/$lang/LC_MESSAGES/messages.po" \
#     --compressed
# }

# function update_localise2() {
#   lang=$1
#   curl "https://localise.biz/api/import/po?index=id&delete-absent=false&ignore-existing=false&locale=$lang&flag-new=Provisional&key=$LOCALIZ_KEY2" \
#     -H 'Accept: application/json' \
#     --data-binary "@hiddifypanel/translations/$lang/LC_MESSAGES/messages.po" \
#     --compressed
# }
# function update_localise3() {
#   lang=$1
#   curl "https://localise.biz/api/import/po?index=id&delete-absent=false&ignore-existing=false&locale=$lang&flag-new=Provisional&key=$LOCALIZ_KEY3" \
#     -H 'Accept: application/json' \
#     --data-binary "@hiddifypanel/translations/$lang/LC_MESSAGES/messages.po" \
#     --compressed
# }

# update_localise fa
# update_localise en


# update_localise2 en
# update_localise2 pt
# update_localise2 ru

# update_localise3 en
# update_localise3 zh