#-*- coding: utf-8 -*-
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import BooleanProperty


class CustomerScreen(Screen):
    pass


class StoreScreen(Screen):
    pass


class CalculatorScreen(Screen):

    clear_bool = BooleanProperty(False)

    def print_number(self, number):
        if self.clear_bool:
            self.clear_display()
        
        text = "{} {} ".format(self.diplay.text, number)
        self.display.text = text

        print("数字「{0}」を入力".format(number))

    def clear_display(self):
        self.clear_display.text = ""
        self.clear_bool = False

        print("「c」を入力")


class DisplayApp(App):
    def build(self):
        self.title = 'KatsuPay店舗用レジアプリ'
        self.sm = ScreenManager()
        self.sm.add_widget(CustomerScreen(name='customer'))
        self.sm.add_widget(StoreScreen(name='store'))
        self.sm.add_widget(CalculatorScreen(name='calculator'))
        return self.sm


if __name__ == '__main__':
    DisplayApp().run()
