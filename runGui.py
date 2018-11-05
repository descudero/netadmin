'''
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.app import App
from LabelB import LabelB
from claseClaro import Claro
# esta


class LoginScreen(BoxLayout):

    def __init__(self, **kwargs):

        super(LoginScreen, self).__init__(**kwargs)

        self.orientation = "vertical"
        self.master_layout = BoxLayout(orientation="vertical", spacing=10)
        self.login_layout = BoxLayout(orientation="horizontal", spacing=10)
        self.login_layout.size_hint=(1, 0.05)
        self.label_user = LabelB(text='Usuario', bcolor=[0.5, 0.8, 0.2, 0.25])
        self.label_password = LabelB(text='Password', bcolor=[0.9, 0.1, 0.1, 0.5])
        self.login_layout.add_widget(self.label_user)
        self.username = TextInput(multiline=False)
        self.login_layout.add_widget(self.username)
        self.login_layout.add_widget(self.label_password)
        self.password = TextInput(password=True, multiline=False)
        self.login_layout.add_widget(self.password)
        self.refresh_button=Button(text="refrescar")
        self.refresh_button.bind(on_press=self.set_policy_layout)
        self.login_layout.add_widget(self.refresh_button)
        self.policy_layout=BoxLayout(orientation="vertical", size_hint=(1, .95))
        self.master_layout.add_widget(self.login_layout)
        self.master_layout.add_widget(self.policy_layout)
        self.add_widget(self.master_layout)
        self.claro = Claro()

    def set_policy_layout(self,*args, **kwargs):
        password = self.password.text
        username = self.username.text
        self.claro.set_master(password=password,username=username)
        self.claro.init_ipp()

        self.policy_layout.add_widget(self.claro.display_qos_ipp())

class MyApp(App):

    def build(self):
        return LoginScreen()


if __name__ == '__main__':
    MyApp().run()
'''
