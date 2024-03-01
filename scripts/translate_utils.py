import click
import sys
import json
import polib
import os


def loadI18N(json_path):
    with open(json_path, 'r', encoding='utf-8') as json_file:
        json_data = json.load(json_file)
    return json_data


def flatten(data, parent_key='', sep='.'):
    items = []
    for k, v in data.items():
        new_key = f'{parent_key}{sep}{k}' if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


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
            print("Error!", keys, e)
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


def json_to_po(json_path, po_path):
    # Load JSON data
    json_data = loadI18N(json_path)
    flattened_data = flatten(json_data)

    po = polib.POFile()
    for key, value in flattened_data.items():
        if isinstance(value, str):
            entry = polib.POEntry(msgid=key, msgstr=value)
            po.append(entry)
    po.save(po_path)


def update_json_from_po(json_path, po_path):
    po = polib.pofile(po_path)
    translations = {}
    for entry in po:
        translations[entry.msgid] = entry.msgstr

    json_data = flatten(loadI18N(json_path))

    res = {k: json_data.get(k, "") for k in translations}
    res = convert_to_nested(res)
    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump(res, json_file, ensure_ascii=False, indent=2)


@click.group()
def main():
    pass


@main.command()
@click.argument('po_file_path', type=click.Path(exists=True))
@click.argument('json_file_path', type=click.Path())
def to_json(po_file_path, json_file_path):
    po_to_json(po_file_path, json_file_path)


@main.command()
@click.argument('json_file_path', type=click.Path(exists=True))
@click.argument('po_file_path', type=click.Path())
def to_po(json_file_path, po_file_path):
    json_to_po(json_file_path, po_file_path)


@main.command()
@click.argument('json_file_path', type=click.Path())
@click.argument('po_file_path', type=click.Path())
def update_json(json_file_path, po_file_path):
    update_json_from_po(json_file_path, po_file_path)


if __name__ == "__main__":
    main()
