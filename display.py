import time
from threading import Thread
import json

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.network.urlrequest import UrlRequest

from showStudentID import nfc_connection
from PayInfo import PayInfo, PayType
from ErrorInfo import ErrorInfo, ErrorMessage

STORE_ID = 2000001

class DatabaseInfo():
    IP_ADDRESS = "165.242.108.54"
    PORT = ":8090"
    HTTP = "http://" + IP_ADDRESS + PORT

class WindowManager(ScreenManager):
    pass

class CustomerWindow(Screen):
    def press_PaymentButton(self):
        PayInfo.set_payType(PayType.PAYMENT)
        pass
    
    def press_ChargeButton(self):
        PayInfo.set_payType(PayType.CHARGE)
        pass
    
    pass

class StoreWindow(Screen):
    pass


class SalesWindow(Screen):
    def on_enter(self):
        self.priceURL = DatabaseInfo.HTTP + "/account/sales/" +  str(STORE_ID)
        self.transURL = DatabaseInfo.HTTP + "/transaction/store/" + str(STORE_ID)

        self.pReq = UrlRequest(self.priceURL, on_success=self.printSelesPrice)
        self.tReq = UrlRequest(self.transURL, on_success=self.func)

    def on_leave(self):
        self.ids["tst"].clear_widgets()

    def printSelesPrice(self, req, result):
        self.ids["sales_price"].text = "売上金額：" + str(result)
    
    def func(self, req, result):
        for i in result:
            self.ids["tst"].add_widget(Label(text=str(i.items())))
            print(i)

    pass


class TestLayout(BoxLayout):
    pass


class CalculatorWindow(Screen):
    clear_bool = BooleanProperty(True)

    def on_leave(self):
        self.ids["display_input"].text = "0"

    def print_number(self, number):
        if self.clear_bool:
            self.clear_bool = False

        text = "{}{}".format(self.ids["display_input"].text, number)
        self.ids["display_input"].text = text

        print("数字「{}」を入力".format(number))


    def clear_display(self):
        self.ids["display_input"].text = ""
        self.clear_bool = True

        print("「c」を入力")


    def press_enter(self):
        if not self.clear_bool:
            self.money_val = int(self.ids["display_input"].text)
            print("金額の合計：{}".format(self.money_val))
            PayInfo.set_payVal(self.money_val)


class NFCWindow(Screen):
    isComplete = BooleanProperty(False)

    def on_enter(self):
        self.isComplete = False

        if self.getStudentID():
            self.ids["nfc_label"].text = "決済情報をデータベースに送信しています．．．"
            print("支払いの種類: ", PayInfo.get_payType(), "\n金額: ", PayInfo.get_payVal(), "\n学籍番号: ", PayInfo.get_studentID())
            
            self.URL = DatabaseInfo.HTTP + "/transaction"
            if PayInfo.get_payType() == PayType.PAYMENT:
                self.URL += "/payment"
            elif PayInfo.get_payType() == PayType.CHARGE:
                self.URL += "/charge"
            else:
                print("error: The payType is not correct.")
                self.openErrorPop(ErrorInfo.E0)

            rb = json.dumps({"customerId": "1000001", "storeId": "2000001","productIdList": "0010001$0010002$0010002", "price": "100000"})
            head = {"Content-Type": "application/json"}
            self.req = UrlRequest(self.URL,on_success=self.successRequest,req_body=rb,req_headers=head)
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
    


kv = Builder.load_file("register.kv")
class DisplayApp(App):
    def build(self):
        return kv

if __name__ == '__main__':
    DisplayApp().run()
