import sys
import time
from threading import Thread
import json
import qrcode
import subprocess
import requests

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.network.urlrequest import UrlRequest
Window.size = (1024, 600)
Window.fullscreen = True

from showStudentID import nfc_connection
from PayInfo import PayInfo, PayType
from ErrorInfo import ErrorInfo, ErrorMessage


class DatabaseInfo():
    IP_ADDRESS = "165.242.108.54"
    PORT = ":8090"
    HTTP = "http://" + IP_ADDRESS + PORT
    HEADER = {"Content-Type": "application/json"}


class CryptoProtocol():
    QR_XOR_KEY = 0b101101000101011011000101


class WindowManager(ScreenManager):
    pass

class LoginWindow(Screen):
    def checkID(self):
        self.usrID = self.ids['login_id'].text
        self.usrPass = self.ids['login_pass'].text

        data = json.dumps({"storeId": str(self.usrID), "password": str(self.usrPass)})

        self.url = DatabaseInfo.HTTP + "/store/login"
        self.lReq = UrlRequest(self.url, on_success=self.checkReq, on_failure=(lambda req, result: self.openErrorPop(ErrorInfo.E3)), req_body=data, req_headers=DatabaseInfo.HEADER)

    def checkReq(self, req, result):
        if not result:
            self.openErrorPop(ErrorInfo.E3)
        elif (result['storeId'] == str(self.usrID) and (result['password'] == str(self.usrPass))):
            PayInfo.set_storeID(self.usrID)
            self.manager.current = 'customer'
        else:
            self.openErrorPop(ErrorInfo.E3)

    def openErrorPop(self, error):
        content = ErrorPop(closePopup=self.closePopup)
        self.popup = Popup(title='Error', content=content, size_hint=(0.5, 0.5), auto_dismiss=False)
        self.popup.open()

    def closePopup(self):
        self.popup.dismiss()
        self.manager.current = 'login'
    
    def sysExit(self):
        sys.exit(0)


class CustomerWindow(Screen):
    def press_PaymentButton(self):
        PayInfo.set_payType(PayType.PAYMENT)
    
    def press_ChargeButton(self):
        PayInfo.set_payType(PayType.CHARGE)


class StoreWindow(Screen):
    def sysExit(self):
        sys.exit(0)


class SalesWindow(Screen):
    def on_enter(self):
        self.priceURL = DatabaseInfo.HTTP + "/account/sales/" +  str(PayInfo.get_storeID())
        self.transURL = DatabaseInfo.HTTP + "/transaction/store/" + str(PayInfo.get_storeID())

        self.pReq = UrlRequest(self.priceURL, on_success=self.printSelesPrice)
        self.tReq = UrlRequest(self.transURL, on_success=self.func)

    def on_leave(self):
        self.ids["tran"].clear_widgets()

    def printSelesPrice(self, req, result):
        self.ids["sales_price"].text = "売上金額：" + str(result)
    
    def func(self, req, result):
        cnt = 1
        for plist in result:
            self.txt = ""
            if plist['charge']:
                self.txt = "--- 取引情報(チャージ)" + str(cnt) + " ---\n" + "消費者ID：" + str(plist['customerId'] + "\n店舗ID：" + str(plist['storeId'] + "\n取引時間：" + str(plist['transactionTime'] + "\n金額：" + str(plist['price']))))
            else:
                self.txt = "--- 取引情報(決済)" + str(cnt) + " ---\n" + "消費者ID：" + str(plist['customerId']) + "\n店舗ID：" + str(plist['storeId']) + "\n取引時間：" + str(plist['transactionTime']) + "\n金額：" + str(plist['price']) + "\n購入品：\n"
                cnt2 = 0
                for pInfList in plist['productInfoList']:
                    self.txt += str(pInfList)
                    if cnt2 % 3 == 0:
                        self.txt += "\n"
                    else:
                        self.txt += ", "
                    cnt += 1
            self.ids["tran"].add_widget(Label(font_size=20, height=300, size_hint_y=None, text=self.txt))
            cnt += 1


class CalculatorWindow(Screen):
    clear_bool = True
    total = 0
    
    def on_leave(self):
        self.total = 0
        self.ids["display_input"].text = '(金額を入力)'

    def print_number(self, val):
        if self.clear_bool:
            self.clear_bool = False

        self.total += int(val)
        self.ids["display_input"].text = str(self.total) + "円"

    def clear_display(self):
        self.total = 0
        self.ids["display_input"].text = "(金額を入力)"
        self.clear_bool = True

    def press_enter(self):
        if not self.clear_bool:
            money_val = int(self.total)
            PayInfo.set_payVal(money_val)
            self.manager.current = 'nfc'


class SelectProductWindow(Screen):
    def on_enter(self):
        self.sumPrice = 0
        self.itemList = []
        self.selectItem = []

        url = DatabaseInfo.HTTP + "/product/" + str(PayInfo.get_storeID())
        self.req = UrlRequest(url, on_success=self.addText)

    def on_leave(self):
        self.ids['products'].clear_widgets()
        self.ids['s_price'].text = '小計：0円'


    def addText(self, req, result):
        cnt = 0
        for i in result:
            if i['onSale'] == 'TRUE':
                self.itemList.append(i)
                self.ids['products'].add_widget(Button(font_size=20, height=300, width=300, size_hint=(None, None), text=(str(cnt)+"："+str(i['name']+"\n"+str(i['price'])+"円")), on_release=self.updatePrice))
                cnt += 1

    def updatePrice(self, btn):
        self.selectItem.append(self.itemList[int(btn.text[0])]['productId'])
        self.sumPrice += self.itemList[int(btn.text[0])]['price']
        self.ids['s_price'].text = "小計：" + str(self.sumPrice) + "円"
    
    def pressEnter(self):
        PayInfo.set_payVal(self.sumPrice)
        PayInfo.set_products(self.selectItem)
        self.manager.current = 'nfc'


class NFCWindow(Screen):
    isComplete = False

    def on_enter(self):
        self.isComplete = False

        if self.getStudentID():
            self.ids["nfc_label"].text = "決済情報をデータベースに送信しています．．．"
            print("支払いの種類: ", PayInfo.get_payType(), "\n金額: ", PayInfo.get_payVal(), "\n学籍番号: ", PayInfo.get_studentID())
            
            self.URL = DatabaseInfo.HTTP + "/transaction"
            if PayInfo.get_payType() == PayType.PAYMENT:
                self.URL += "/payment"
                self.rb = json.dumps(PayInfo.get_DictPaymentInfo())
            elif PayInfo.get_payType() == PayType.CHARGE:
                self.URL += "/charge"
                self.rb = json.dumps(PayInfo.get_DictChargeInfo())
            else:
                print("error: The payType is not correct.")
                self.openErrorPop(ErrorInfo.E0)
        
            self.req = UrlRequest(self.URL, on_success=self.successRequest, on_failure=self.failRecuest, req_body=self.rb,req_headers=DatabaseInfo.HEADER)
        else:
            print("error:The ID card held over the card reader is not a student ID card")
            self.openErrorPop(ErrorInfo.E2)

    def on_leave(self):
        self.ids["nfc_label"].text = '学生証をリーダにタッチしてください'

    def getStudentID(self):
        nfc_connection()
        if (PayInfo.get_studentID() != None):
            return True
        else:
            return False
    
    def successRequest(self, req, result):
        if result == True:
            self.ids["nfc_label"].text = "決済が完了しました．"
            self.isComplete = True
        else:
            print("error:The payment could not be made due to insufficient balance.")
            self.openErrorPop(ErrorInfo.E1)
    
    def failRecuest(self, req, result):
        print("An invalid ID card has been detected.")
        self.openErrorPop(ErrorInfo.E2)

    def openErrorPop(self, error):
        content = ErrorPop(closePopup=self.closePopup)
        self.popup = Popup(title='Error', content=content, size_hint=(0.5, 0.5), auto_dismiss=False)
        self.popup.open()
    
    def closePopup(self):
        self.popup.dismiss()
        self.manager.current = 'customer'
    
    def backWindow(self):
        if self.isComplete:
            PayInfo.clearInfo()
            self.manager.current = 'customer'

        return True


class ErrorPop(BoxLayout):
    closePopup = ObjectProperty(None)


class QRWindow(Screen):
    def on_enter(self):
        nfc_connection()
        self.genQrcode()
    
    def on_leave(self):
        self.ids['qr_label'].text = '学生証をタッチしてください'
        self.ids['qr_png'].source = ''
    
    def genQrcode(self):
        sudentID = PayInfo.get_studentID()
        cc = int(sudentID) ^ CryptoProtocol.QR_XOR_KEY
        print("   " + str(bin(int(sudentID))))
        print(str(bin(CryptoProtocol.QR_XOR_KEY)))
        print(str(bin(cc)))
        qrImg = qrcode.make(str(cc))
        qrImg.save('studentQR.png')
        self.ids['qr_label'].text = 'KatsuPayスマホアプリで\nこのQRコードを読み撮ってください．'
        self.ids['qr_png'].source = 'studentQR.png'


class ProductEditWindow(Screen):
    products = []
    selectProduct = None
    eventPush = False
    isEdit = False
    isAdd = False
    isReadOnly = BooleanProperty(True)

    def on_enter(self):
        url = DatabaseInfo.HTTP + "/product/" + str(PayInfo.get_storeID())
        self.req = UrlRequest(url, on_success=self.saveProductsData)
    
    def on_leave(self):
        self.products.clear()
        self.selectProduct = None
        self.ids['prod'].clear_widgets()
        self.eventPush = False
        self.isReadOnly = True
        self.isAdd = False
        self.isEdit = False
        self.ids['edit_b'].text = "編集"
        self.ids['delete_b'].text = "削除"
        self.ids['warning'].text = '編集・削除したい商品を\n選択してください'

    def saveProductsData(self, req, result):
        cnt = 0
        self.ids['prod'].add_widget(Button(font_size=20, height=150, size_hint_y=None, text="商品追加", on_release=self.addProduct))
        for plist in result:
            if (plist['onSale'] == 'TRUE'):
                self.products.append(plist)
                pbutton = Button(font_size=20, height=150, size_hint_y=None, text=(str(cnt) + ". " + str(plist['name']) + "\n" + str(plist['price']) + "円"), on_release=self.showProductInfo)
                self.ids['prod'].add_widget(pbutton)
                cnt += 1
    
    def addProduct(self, btn):
        self.ids['warning'].text = "商品情報を記入し，\n適用ボタンを押してください"
        self.ids['edit_b'].text = "追加"
        self.ids['delete_b'].text = "キャンセル"
        self.ids['p_id'].text = "(自動で割振)"
        self.ids['name'].text = ""
        self.ids['price'].text = ""
        self.isAdd = True
        self.isReadOnly = False

    def showProductInfo(self, btn):
        self.selectProduct = self.products[int(btn.text[0])]
        self.ids['p_id'].text = str(self.selectProduct['productId'])
        self.ids['name'].text = str(self.selectProduct['name'])
        self.ids['price'].text = str(self.selectProduct['price'])
    
    def editEvent(self):
        if self.isAdd:
            self.ids['edit_b'].text = "編集"
            self.ids['delete_b'].text = "削除"
            self.ids['warning'].text = "データ送信中..."
            data = json.dumps({"name": str(self.ids['name'].text), "price": str(self.ids['price'].text), "onSale": "TRUE"})
            url = DatabaseInfo.HTTP + '/product/' + str(PayInfo.get_storeID())
            self.req = UrlRequest(url, on_success=self.successAdd, on_failure=self.failAdd, req_body=data, req_headers=DatabaseInfo.HEADER)
        elif not self.eventPush:
            self.ids['warning'].text = "商品情報を編集し，\n適用ボタンを押してください"
            self.ids['edit_b'].text = "適用"
            self.ids['delete_b'].text = "キャンセル"
            self.eventPush = True
            self.isEdit = True
            self.isReadOnly = False
        else:
            self.ids['edit_b'].text = "編集"
            self.ids['delete_b'].text = "削除"
            self.ids['warning'].text = "データ送信中..."
            self.eventPush = False
            self.isReadOnly = True
            if self.isEdit:
                self.data = {'productId': str(self.selectProduct['productId']), 'name': str(self.ids['name'].text), 'price':str(self.ids['price'].text), 'onSale': 'TRUE'}
            else:
                self.data = {'productId': str(self.selectProduct['productId']), 'name': str(self.selectProduct['name']), 'price':str(self.selectProduct['price']), 'onSale': 'FALSE'}
            url = DatabaseInfo.HTTP + "/product"
            req = requests.put(url, json=self.data)
            if (req.status_code == 200):
                self.products.clear()
                self.ids['prod'].clear_widgets()
                url = DatabaseInfo.HTTP + "/product/" + str(PayInfo.get_storeID())
                self.req = UrlRequest(url, on_success=self.saveProductsData)
                self.ids['warning'].text = '商品情報を更新しました'
            else:
                self.ids['warning'].text = 'エラー発生\n商品情報が更新できませんでした'
            self.isEdit = False

    def deleteEvent(self):
        if self.isAdd:
            self.ids['edit_b'].text = "編集"
            self.ids['delete_b'].text = "削除"
            self.ids['warning'].text = '編集・削除したい商品を\n選択してください'
            self.eventPush = False
            self.isReadOnly = True
            self.isAdd = False
        elif not self.eventPush:
            self.ids['warning'].text = "本当に商品を削除しますか？"
            self.ids['edit_b'].text = "適用"
            self.ids['delete_b'].text = "キャンセル"
            self.eventPush = True
        else:
            self.ids['edit_b'].text = "編集"
            self.ids['delete_b'].text = "削除"
            self.ids['warning'].text = '編集・削除したい商品を\n選択してください'
            self.eventPush = False
            self.isReadOnly = True
    
    def successAdd(self, req, result):
        self.isAdd = False
        self.isEdit = False
        self.isReadOnly = True
        self.products.clear()
        self.ids['prod'].clear_widgets()
        url = DatabaseInfo.HTTP + "/product/" + str(PayInfo.get_storeID())
        self.req = UrlRequest(url, on_success=self.saveProductsData)
        self.ids['warning'].text = "商品を追加しました"

    def failAdd(self, req, result):
        self.isAdd = False
        self.isEdit = False
        self.isReadOnly = True
        self.ids['warning'].text = "エラー発生\n商品情報が追加できませんでした"

kv = Builder.load_file("register.kv")
class DisplayApp(App):
    def build(self):
        return kv

if __name__ == '__main__':
    DisplayApp().run()
