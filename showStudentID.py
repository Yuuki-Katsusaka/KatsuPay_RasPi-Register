# 学籍番号を表示するプログラム

import nfc
from binascii import hexlify
import binascii

from PayInfo import PayInfo


# 学籍番号のサービスコード
card_service_code = 0x1A8B 

is_valid_card = False

def on_connect(tag):
    
    global is_valid_card

    if (str(tag)[0:8] == "Type3Tag"):
        try:
            is_valid_card = True

            idm, pmm = tag.polling(system_code=0xfe00)
            tag.idm, tag.pmm, tag.sys = idm, pmm, 0xfe00

            sc = nfc.tag.tt3.ServiceCode(card_service_code >> 6, card_service_code & 0x3f)
            bc = nfc.tag.tt3.BlockCode(0) # ブロック番号は0
            data = tag.read_without_encryption([sc], [bc])

            PayInfo.set_studentID(data[4:11].decode())
            
            print('あなたの学生番号は' + PayInfo.get_studentID() + 'です．')
            
        except Exception as e:
            is_valid_card = False
            print("error: %s" % e)
            
    else:
        is_valid_card = False
        print("error: tag isn't Type3Tag")
    
    
def nfc_connection():
    with nfc.ContactlessFrontend('usb') as clf:
        clf.connect(rdwr={'on-connect': on_connect})


if __name__ == '__main__':
    nfc_connection()
