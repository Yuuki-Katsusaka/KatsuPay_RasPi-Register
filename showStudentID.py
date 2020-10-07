# 学籍番号を表示するプログラム

import nfc
from binascii import hexlify
import binascii

# 学籍番号のサービスコード
card_service_code = 0x1A8B 

student_num = -1 # 学籍番号のグローバル変数

def on_connect(tag):
    print(type(tag))
    if isinstance(tag, nfc.tag.tt3.Type3Tag):
        try:
            idm, pmm = tag.polling(system_code=0xfe00)
            tag.idm, tag.pmm, tag.sys = idm, pmm, 0xfe00

            sc = nfc.tag.tt3.ServiceCode(card_service_code >> 6, card_service_code & 0x3f)
            bc = nfc.tag.tt3.BlockCode(0) # ブロック番号は0
            data = tag.read_without_encryption([sc], [bc])

            global student_num
            student_num = data[4:11].decode()
            
            print('あなたの学生番号は' + student_num + 'です．')
            
        except Exception as e:
            print("error: %s" % e)
            
    else:
        print("error: tag isn't Type3Tag")
    
    
def nfc_connection():
    with nfc.ContactlessFrontend('usb') as clf:
        clf.connect(rdwr={'on-connect': on_connect})


if __name__ == '__main__':
    nfc_connection()
