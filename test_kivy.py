from kivy.app import App
from kivy.uix.label import Label

class TestApp(App):
    def build(self):
        return Label(text="Kivy Installed Successfully!")

TestApp().run()
