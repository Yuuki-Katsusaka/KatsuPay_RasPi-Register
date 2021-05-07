import sys
from threading import Thread
import json
import qrcode
import requests

import binascii
import nfc

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.clock import mainthread
from kivy.properties import ListProperty, ObjectProperty, BooleanProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, FallOutTransition
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
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


class NfcReader(Thread):
    __INTERVAL = 0.2  # 待受の飯能インターバル秒
    __TARGET_REQ_FELICA = nfc.clf.RemoteTarget('212F')
    __TARGET_REQ_NFC = nfc.clf.RemoteTarget('106A')
    __TARGET_SERVICE_CODE = 0x1A8B  # 学籍番号のサービスコード
    cancel_flag = False
    complete_flag = False

    def run(self):
        with nfc.ContactlessFrontend('usb') as clf:
            while True:
                if self.cancel_flag:
                    break

                res = clf.sense(self.__TARGET_REQ_NFC, self.__TARGET_REQ_FELICA, iteration=1, interval=self.__INTERVAL)
                if not res is None:
                    tag = nfc.tag.activate(clf, res)

                    if tag.type == "Type3Tag":
                        idm, pmm = tag.polling(system_code=0xfe00)
                        tag.idm, tag.pmm, tag.sys = idm, pmm, 0xfe00
                        sc = nfc.tag.tt3.ServiceCode(self.__TARGET_SERVICE_CODE >> 6, self.__TARGET_SERVICE_CODE & 0x3f)
                        bc = nfc.tag.tt3.BlockCode(0)
                        data = tag.read_without_encryption([sc], [bc])

                        PayInfo.set_studentID(data[4:11].decode())
                        self.complete_flag = True
                        break


class WindowManager(ScreenManager):
    pass

class LoginWindow(Screen):
    login_flag = False

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
            if not self.login_flag:
                PayInfo.set_storeID(self.usrID)
                self.login_flag = True
                self.ids.login_id.readonly = True
                self.ids['login_lay'].add_widget(Button(font_size=30, text='戻る', on_release=self.addButton))
                self.ids.login_pass.text = ''
                self.manager.current = 'customer'
            else:
                self.ids.login_pass.text = ''
                self.manager.current = 'store'
        else:
            self.openErrorPop(ErrorInfo.E3)
    
    def addButton(self, btn):
        self.manager.current = 'customer'

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
    id_dict = ['none','s_item','s_charge','s_signup']
    color = ListProperty([[],[0.8, 0, 0, 1], [1, 1, 1, 1], [1, 1, 1, 1]])
    active_btn = 0

    def on_enter(self):
        self.ids.sm_cus.current = 's_item'
    
    def on_leave(self):
        self.active_btn = 0
        self.ids.sm_cus.current = "none"

    def updateActiveBtn(self, sid):
        for i in range(len(self.color)):
            if i == int(sid):
                self.color[i] = [0.8, 0, 0, 1]
                self.changeScreen(i)
                self.active_btn = i
            else:
                self.color[i] = [1, 1, 1, 1]
    
    def changeScreen(self, id):
        if id != self.active_btn:
            if id > self.active_btn:
                self.ids.sm_cus.transition = SlideTransition(direction='left')
                self.ids.sm_cus.current = self.id_dict[id]
            else:
                self.ids.sm_cus.transition = SlideTransition(direction='right')
                self.ids.sm_cus.current = self.id_dict[id]


class ItemSelectingScreen(Screen):
    price_property = StringProperty('0')

    def on_enter(self):
        self.item_list = []
        self.cart_list = {}

        url = DatabaseInfo.HTTP + "/product/" + str(PayInfo.get_storeID())
        req = UrlRequest(url, on_success=self.updateItemWidget)

    def on_leave(self):
        self.price_property = '0'

        self.ids['items'].clear_widgets()
        self.ids['cart'].clear_widgets()

    def updateItemWidget(self, req, result):
        cnt = 0
        for item in result:
            if item['onSale'] == 'TRUE':
                self.item_list.append(item)

                item_txt = str(cnt) + ". " + str(item['name']) + "\n ¥" + str(item['price'])
                item_btn = Button(font_size=40, height=150, text_size=[self.size[0]/2, self.size[1]], halign='left', valign='middle', size_hint_y=None, text=item_txt, on_release=self.addCartList, background_color=(.3, .8, .9, 1))
                self.ids['items'].add_widget(item_btn)
                cnt += 1 

    def addCartList(self, btn):
        btn_product_id = self.item_list[int(btn.text[0])]['productId']
        if btn_product_id in self.cart_list.keys():
            self.cart_list[btn_product_id] += 1
            self.updateCartWidget()
        else:
            self.cart_list[btn_product_id] = 1
            self.updateCartWidget()
        
        self.price_property = str(int(self.price_property) + int(self.item_list[int(btn.text[0])]['price']))

    def updateCartWidget(self):
        self.ids['cart'].clear_widgets()

        for item in self.item_list:
            for key, num in self.cart_list.items():
                if item['productId'] == key:
                    cart_layout = BoxLayout(height=100, size_hint_y=None)
                    cart_txt = str(item['name']) + '\n ¥' + str(item['price'])
                    cart_lbl = Label(font_size=30, size_hint_x=0.8, text=cart_txt)
                    num_lbl = Label(font_size=30, size_hint_x=0.2, text=str(num))
                    cart_layout.add_widget(cart_lbl)
                    cart_layout.add_widget(num_lbl)
                    self.ids['cart'].add_widget(cart_layout)
    
    def pressEnterBtn(self):
        product_list = []
        for id, num in self.cart_list.items():
            for i in range(num):
                product_list.append(id)

        PayInfo.set_payType(PayType.PAYMENT)
        PayInfo.set_products(product_list)
        PayInfo.set_payVal(int(self.price_property))

        self.parent.transition = FallOutTransition()
        self.parent.current = 's_nfc'
    
    def pressCancelBtn(self):
        self.ids['cart'].clear_widgets()
        self.cart_list = {}
        self.price_property = '0'


class ChargeSelectingScreen(Screen):
    price_property = StringProperty('0')

    def on_leave(self):
        self.price_property = '0'

    def pressPriceBtn(self, s_price):
        self.price_property = str(int(self.price_property) + int(s_price))
    
    def pressEnterBtn(self):
        if not self.price_property == '0':
            PayInfo.set_payType(PayType.CHARGE)
            PayInfo.set_payVal(int(self.price_property))
            self.parent.transition = FallOutTransition()
            self.parent.current = 's_nfc'
        

    def pressCancelBtn(self):
        self.price_property = '0'


class SignupScreen(Screen):
    source = './img/nfc_touch.gif'

    def on_enter(self):
        self.pay_type = PayInfo.get_payType()

        self.nfc = NfcReader()
        self.nfc.setDaemon(True)
        self.nfc.start()

        self.observer = Thread(target=self.observeNfcReader, )
        self.observer.setDaemon(True)
        self.observer.start()
    
    def on_leave(self):
        self.nfc.cancel_flag = True
        self.ids.nfc_inf.text = "学生証をリーダにタッチしてください"
        self.ids.sign_img.source = "./img/nfc_touch.gif"

    def observeNfcReader(self):
        while True:
            if self.nfc.complete_flag:
                sudentID = PayInfo.get_studentID()
                cc = int(sudentID) ^ CryptoProtocol.QR_XOR_KEY
                qrImg = qrcode.make(str(cc))
                qrImg.save('studentQR.png')

                self.ids.nfc_inf.text = "スマホアプリでこのQRコードを読み撮ってください"
                self.source = "studentQR.png"
                self.displayQrImage()
                break
    
    @mainthread
    def displayQrImage(self):
        self.ids.sign_img.source = self.source

class NfcScreen(Screen):
    source = StringProperty("./img/nfc_touch.gif")

    def on_enter(self):
        self.pay_type = PayInfo.get_payType()

        self.nfc = NfcReader()
        self.nfc.setDaemon(True)
        self.nfc.start()

        self.observer = Thread(target=self.observeNfcReader, )
        self.observer.setDaemon(True)
        self.observer.start()

    def on_leave(self):
        self.nfc.cancel_flag = True
        PayInfo.clearInfo()
        self.ids.nfc_inf.text = "学生証をリーダにタッチしてください"
        self.ids.nfc_b.text = "取消"
        self.source = "./img/nfc_touch.gif"

        
    def pressCancelBtn(self):
        self.nfc.cancel_flag = True

        if self.pay_type == PayType.PAYMENT:
            self.parent.current = 's_item'
        elif self.pay_type == PayType.CHARGE:
            self.parent.current = 's_charge'
    
    def observeNfcReader(self):
        while True:
            if self.nfc.complete_flag:
                self.ids.nfc_inf.text = "決済情報をデータベースに送信中．．．"
                
                url = DatabaseInfo.HTTP + "/transaction"
                if self.pay_type == PayType.PAYMENT:
                    url += "/payment"
                    self.rb = json.dumps(PayInfo.get_DictPaymentInfo())
                elif self.pay_type == PayType.CHARGE:
                    url += "/charge"
                    self.rb = json.dumps(PayInfo.get_DictChargeInfo())
                    
                req = UrlRequest(url, on_success=self.successRequest, on_failure=self.failRequest, req_body=self.rb, req_headers=DatabaseInfo.HEADER)
                break
                
            if self.nfc.cancel_flag:
                break
    
    def successRequest(self, req, result):
        if result:
            self.ids.nfc_b.text = "OK"
            if self.pay_type == PayType.PAYMENT:
                self.ids.nfc_inf.text = "支払いが完了しました"
                self.source = "./img/pay.png"
            if self.pay_type == PayType.CHARGE:
                self.ids.nfc_inf.text = "チャージが完了しました"
                self.source = "./img/charge.png"
        else:
            print("Error: The payment could not be made due to insufficient balance.")
            self.failRequest(req, result)

    def failRequest(self, req, result):
        self.ids.nfc_inf.text = "エラーが発生しました．"
        self.ids.nfc_b.text = "戻る"
        self.source = "./img/error.png"

        print(result)
        print("Error: Http communication was not established.")


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


class ErrorPop(BoxLayout):
    closePopup = ObjectProperty(None)


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
