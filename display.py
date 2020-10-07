from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty
from kivy.uix.screenmanager import ScreenManager, Screen

# import nfc
# from binascii import hexlify
import showStudentID


class WindowManager(ScreenManager):
    pass

class CustomerWindow(Screen):
    pass

class StoreWindow(Screen):
    pass

class CalculatorWindow(Screen):
    
    clear_bool = BooleanProperty(True)

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


class NFCWindow(Screen):

    def on_enter(self):
        super().on_enter(self)
        self.getStudentID()

    def getStudentID(self):
        showStudentID.nfc_connection()
        print(showStudentID.student_num)
    

kv = Builder.load_file("display.kv")

class DisplayApp(App):
    def build(self):
        return kv

if __name__ == '__main__':
    DisplayApp().run()
