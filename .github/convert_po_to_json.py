import polib
import json


def convert_to_nested(data):
    nested_data = {}
    for key, value in data.items():
        keys = key.split(".")
        if " " in key:
            keys = [key]
        current_dict = nested_data
        for k in keys[:-1]:
            if k not in current_dict:
                current_dict[k] = {}
            current_dict = current_dict[k]
        try:
            current_dict[keys[-1]] = value
        except Exception as e:
            print(keys, e)
            raise e
        print(keys)
    return nested_data


def po_to_json(po_file_path, json_file_path):
    po = polib.pofile(po_file_path)
    translations = {}
    for entry in po:
        translations[entry.msgid] = entry.msgstr
    translations = convert_to_nested(translations)
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(translations, json_file, ensure_ascii=False, indent=2)


lang = 'pt'
po_to_json(f'hiddifypanel/translations/{lang}/LC_MESSAGES/messages.po', f'hiddifypanel/translations.i18n/{lang}.json')
