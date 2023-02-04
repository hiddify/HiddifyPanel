import polib
from deep_translator import GoogleTranslator
import sys
if __name__ == "__main__":  
    src=sys.argv[1]
    dst=sys.argv[2]
    src_file=f'hiddifypanel/translations/{src}/LC_MESSAGES/messages.po'
    dst_file=f'hiddifypanel/translations/{dst}/LC_MESSAGES/messages.po'
    src_pofile = polib.pofile(src_file)
    dst_pofile = polib.pofile(dst_file)
    translator = GoogleTranslator(source=src, target=dst if dst !='zh' else "zh-CN")
    

    for entry in dst_pofile:
        # if "incomplete" in entry.flags:
        #     entry.flags.remove("incomplete")

        if entry.msgstr=="":
            src_prof=src_pofile.find(entry.msgid)
            
            if src_prof and src_prof.msgstr and 'fuzzy' not in src_prof.flags:
                entry.msgstr=translator.translate(src_prof.msgstr) 
                
                print(src_prof.msgid, src_prof.msgstr,entry.msgstr)
                # entry.flags.append("auto_translate")
                entry.flags.append("fuzzy")
            elif dst=='en':
                entry.msgstr=entry.msgid
                print(entry.msgid, 'use msgid',entry.msgstr)
                # entry.flags.append("auto_translate")
                entry.flags.append("fuzzy")

            

    dst_pofile.save(dst_file)