import os
import random
import requests
import json
import base64
import hashlib
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.core.window import Window

# ==========================================
# 1. НАСТРОЙКИ GITHUB ACTIONS BACKEND
# ==========================================
GITHUB_USER = "matveisem4-dot"  # Ваш логин
GITHUB_REPO = "db.json"    # Название репозитория
# Ограниченный Fine-Grained Token (права только на Workflows и Contents)
GITHUB_TOKEN = "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" 

SALT = "NeoBank_Secure_Salt_2026"

def hash_sensitive_data(data_string: str) -> str:
    return hashlib.sha256((data_string + SALT).encode('utf-8')).hexdigest()

def get_terminal_id():
    if os.path.exists("terminal_id.txt"):
        with open("terminal_id.txt", "r") as f:
            return f.read().strip()
    else:
        new_id = f"TERM-{random.randint(1000, 9999)}"
        with open("terminal_id.txt", "w") as f:
            f.write(new_id)
        return new_id

TERMINAL_ID = get_terminal_id()

# --- Отправка события в GitHub Actions ---
def trigger_github_action(event_type: str, payload: dict) -> bool:
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/dispatches"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    data = {
        "event_type": event_type,
        "client_payload": payload
    }
    try:
        res = requests.post(url, headers=headers, json=data, timeout=8)
        return res.status_code == 204 # 204 No Content означает успешный запуск
    except Exception as e:
        print("Ошибка сети при вызове GitHub Actions:", e)
        return False

# --- Чтение базы данных (из raw содержимого) ---
def fetch_github_db():
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/db.json"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    try:
        res = requests.get(url, headers=headers, timeout=6)
        if res.status_code == 200:
            content = res.json()
            raw_data = base64.b64decode(content['content']).decode('utf-8')
            return json.loads(raw_data)
    except Exception as e:
        print("Ошибка чтения db.json:", e)
    return None

# ==========================================
# 2. ИНТЕРФЕЙС И ЭКРАНЫ (KIVY)
# ==========================================
Window.clearcolor = (0.03, 0.07, 0.05, 1)

class GreenButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0, 0.63, 0.23, 1)
        self.color = (1, 1, 1, 1)
        self.font_size = '18sp'
        self.bold = True

class DarkButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0.08, 0.17, 0.12, 1)
        self.color = (0, 1, 0.38, 1)
        self.font_size = '18sp'

class BaseScreen(Screen):
    def on_enter(self):
        if not hasattr(self, 'lbl_terminal_id'):
            self.lbl_terminal_id = Label(
                text=f"ID Терминала: [b]{TERMINAL_ID}[/b]",
                markup=True,
                font_size='13sp',
                color=(0.5, 0.5, 0.5, 1),
                size_hint=(None, None),
                size=(220, 30),
                pos=(10, 5)
            )
            self.add_widget(self.lbl_terminal_id)


class MainMenuScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=15)
        
        layout.add_widget(Label(
            text='[b]NeoBank Shield[/b]\n(Backend: GitHub Actions)',
            markup=True, font_size='24sp', color=(0, 1, 0.38, 1), halign='center'
        ))

        btn_reg = GreenButton(text='📝 Зарегистрировать Терминал')
        btn_reg.bind(on_press=lambda x: setattr(self.manager, 'current', 'register'))
        layout.add_widget(btn_reg)

        btn_term = DarkButton(text='📱 POS Касса оплаты')
        btn_term.bind(on_press=lambda x: setattr(self.manager, 'current', 'terminal'))
        layout.add_widget(btn_term)

        btn_client = DarkButton(text='💳 Личный Кабинет Клиента')
        btn_client.bind(on_press=lambda x: setattr(self.manager, 'current', 'client'))
        layout.add_widget(btn_client)

        btn_admin = DarkButton(text='⚙️ Выпуск Карт & Управление')
        btn_admin.bind(on_press=lambda x: setattr(self.manager, 'current', 'admin'))
        layout.add_widget(btn_admin)

        self.add_widget(layout)


class RegisterTerminalScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=25, spacing=10)

        top_bar = BoxLayout(size_hint_y=0.1)
        btn_back = DarkButton(text='← Меню', size_hint_x=0.3)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main_menu'))
        top_bar.add_widget(btn_back)
        top_bar.add_widget(Label(text='Регистрация Терминала', font_size='20sp', bold=True, color=(0, 1, 0.38, 1)))
        layout.add_widget(top_bar)

        layout.add_widget(Label(text=f"Привязка устройства: [b]{TERMINAL_ID}[/b]", markup=True, size_hint_y=0.08))

        self.name_in = TextInput(hint_text="Название точки", multiline=False, size_hint_y=0.12)
        self.purpose_in = TextInput(hint_text="Назначение терминала", multiline=False, size_hint_y=0.12)
        
        btn_send = GreenButton(text="Отправить заявку в GitHub", size_hint_y=0.15)
        btn_send.bind(on_press=self.send_registration)

        layout.add_widget(self.name_in)
        layout.add_widget(self.purpose_in)
        layout.add_widget(btn_send)
        self.add_widget(layout)

    def send_registration(self, instance):
        payload = {
            "terminal_id": TERMINAL_ID,
            "name": self.name_in.text or "Касса",
            "purpose": self.purpose_in.text or "Продажи"
        }
        if trigger_github_action("register_terminal", payload):
            Popup(title="Запрос отправлен", content=Label(text="Запрос отправлен в GitHub Actions.\nОбработка займет ~15 секунд."), size_hint=(0.85, 0.3)).open()
            self.manager.current = 'main_menu'
        else:
            Popup(title="Ошибка", content=Label(text="Не удалось связаться с GitHub API"), size_hint=(0.85, 0.3)).open()


class TerminalScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.amount = "0"
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        top_bar = BoxLayout(size_hint_y=0.1)
        btn_back = DarkButton(text='← Меню', size_hint_x=0.3)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main_menu'))
        top_bar.add_widget(btn_back)
        top_bar.add_widget(Label(text='Приём Оплаты', font_size='20sp', bold=True, color=(0, 1, 0.38, 1)))
        layout.add_widget(top_bar)

        self.display = Label(text='0 ₽', font_size='42sp', bold=True, color=(0, 1, 0.38, 1), size_hint_y=0.18)
        layout.add_widget(self.display)

        keypad = GridLayout(cols=3, spacing=8, size_hint_y=0.52)
        for num in ['1','2','3','4','5','6','7','8','9','C','0','✓']:
            btn = DarkButton(text=num)
            btn.bind(on_press=self.on_key_press)
            keypad.add_widget(btn)
        layout.add_widget(keypad)

        btn_pay = GreenButton(text='💳 Списать через GitHub Action', size_hint_y=0.18)
        btn_pay.bind(on_press=self.pay_nfc)
        layout.add_widget(btn_pay)

        self.add_widget(layout)

    def on_key_press(self, instance):
        key = instance.text
        if key == 'C': self.amount = "0"
        elif key != '✓':
            if self.amount == "0": self.amount = key
            elif len(self.amount) < 6: self.amount += key
        self.display.text = f"{self.amount} ₽"

    def pay_nfc(self, instance):
        if float(self.amount) <= 0:
            return Popup(title="Ошибка", content=Label(text="Введите сумму оплаты"), size_hint=(0.8, 0.25)).open()

        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        uid_input = TextInput(hint_text="NFC UID карты (напр. 04:A2:8B:1A)", multiline=False)
        btn_confirm = GreenButton(text="Провести транзакцию")
        content.add_widget(uid_input)
        content.add_widget(btn_confirm)

        popup = Popup(title="Считывание карты...", content=content, size_hint=(0.85, 0.4))

        def execute_pay(btn):
            popup.dismiss()
            payload = {
                "terminal_id": TERMINAL_ID,
                "uid": uid_input.text.strip().upper(),
                "amount": float(self.amount)
            }
            if trigger_github_action("pay_transaction", payload):
                msg = f"⏳ Транзакция отправлена в GitHub!\nСумма: {self.amount} ₽\n\nСервер обработает её через ~15-20 сек."
                self.amount = "0"
                self.display.text = "0 ₽"
            else:
                msg = "❌ Ошибка отправки запроса в GitHub"

            Popup(title="Статус платежа", content=Label(text=msg), size_hint=(0.85, 0.35)).open()

        btn_confirm.bind(on_press=execute_pay)
        popup.open()


class ClientScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        top_bar = BoxLayout(size_hint_y=0.1)
        btn_back = DarkButton(text='← Меню', size_hint_x=0.3)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main_menu'))
        top_bar.add_widget(btn_back)
        top_bar.add_widget(Label(text='Личный Кабинет', font_size='20sp', bold=True, color=(0, 1, 0.38, 1)))
        layout.add_widget(top_bar)

        self.card_in = TextInput(hint_text="Номер карты", multiline=False, size_hint_y=0.12)
        self.pin_in = TextInput(hint_text="PIN-код", password=True, multiline=False, size_hint_y=0.12)
        self.cvc_in = TextInput(hint_text="CVC-код", password=True, multiline=False, size_hint_y=0.12)
        
        btn_log = GreenButton(text="Проверить баланс", size_hint_y=0.15)
        btn_log.bind(on_press=self.login)

        self.lbl_info = Label(text="", font_size='18sp', color=(0, 1, 0.38, 1))

        layout.add_widget(self.card_in)
        layout.add_widget(self.pin_in)
        layout.add_widget(self.cvc_in)
        layout.add_widget(btn_log)
        layout.add_widget(self.lbl_info)

        self.add_widget(layout)

    def login(self, instance):
        db = fetch_github_db()
        if not db:
            self.lbl_info.text = "❌ Ошибка соединения с GitHub"
            return

        card = self.card_in.text.strip()
        hashed_pin = hash_sensitive_data(self.pin_in.text.strip())
        hashed_cvc = hash_sensitive_data(self.cvc_in.text.strip())

        client = next((c for c in db.get('clients', []) if c['card'] == card and c['pin_hash'] == hashed_pin and c['cvc_hash'] == hashed_cvc), None)

        if client:
            self.lbl_info.text = f"👤 {client['name']}\n💳 {client['card']}\n💰 Баланс: {client['balance']} ₽"
        else:
            self.lbl_info.text = "❌ Неверные данные карты, PIN или CVC"


class AdminScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=8)

        top_bar = BoxLayout(size_hint_y=0.08)
        btn_back = DarkButton(text='← Меню', size_hint_x=0.3)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main_menu'))
        top_bar.add_widget(btn_back)
        top_bar.add_widget(Label(text='Администрирование', font_size='20sp', bold=True, color=(0, 1, 0.38, 1)))
        layout.add_widget(top_bar)

        layout.add_widget(Label(text="[b]Выпуск новой банковской карты:[/b]", markup=True, size_hint_y=0.05))
        
        self.name_in = TextInput(hint_text="ФИО Держателя", multiline=False, size_hint_y=0.08)
        self.pin_in = TextInput(hint_text="PIN", multiline=False, size_hint_y=0.08)
        self.cvc_in = TextInput(hint_text="CVC", multiline=False, size_hint_y=0.08)
        self.uid_in = TextInput(hint_text="NFC UID карты", multiline=False, size_hint_y=0.08)
        self.bal_in = TextInput(hint_text="Стартовый баланс (₽)", multiline=False, size_hint_y=0.08)

        btn_create = GreenButton(text="Выпустить карту", size_hint_y=0.1)
        btn_create.bind(on_press=self.create_card)

        layout.add_widget(self.name_in)
        layout.add_widget(self.pin_in)
        layout.add_widget(self.cvc_in)
        layout.add_widget(self.uid_in)
        layout.add_widget(self.bal_in)
        layout.add_widget(btn_create)

        layout.add_widget(Label(text="[b]Управление блокировками касс:[/b]", markup=True, size_hint_y=0.05))
        btn_refresh = DarkButton(text="🔄 Обновить список касс", size_hint_y=0.09)
        btn_refresh.bind(on_press=self.load_terminals)
        layout.add_widget(btn_refresh)

        self.term_list_box = BoxLayout(orientation='vertical', spacing=5)
        layout.add_widget(self.term_list_box)

        self.add_widget(layout)

    def create_card(self, instance):
        card_num = f"4276 {random.randint(1000,9999)} {random.randint(1000,9999)} {random.randint(1000,9999)}"
        payload = {
            "name": self.name_in.text.strip(),
            "card": card_num,
            "pin": self.pin_in.text.strip(),
            "cvc": self.cvc_in.text.strip(),
            "uid": self.uid_in.text.strip().upper(),
            "balance": float(self.bal_in.text.strip() or 0)
        }
        if trigger_github_action("create_card", payload):
            msg = f"✅ Запрос отправлен в GitHub!\nКарта: {card_num}\nПин и CVC будут зашифрованы на сервере."
            Popup(title="Успех", content=Label(text=msg), size_hint=(0.85, 0.35)).open()

    def load_terminals(self, instance):
        self.term_list_box.clear_widgets()
        db = fetch_github_db()
        if not db:
            return Popup(title="Ошибка", content=Label(text="Нет связи с GitHub"), size_hint=(0.8, 0.3)).open()

        for t_id, t_info in db.get('terminals', {}).items():
            row = BoxLayout(size_hint_y=None, height=40, spacing=10)
            status_str = "🛑 Заблокирован" if t_info.get('blocked') else "✅ Активен"
            lbl = Label(text=f"{t_id} | {t_info.get('name')} | {status_str}", font_size='12sp')
            
            btn_action = DarkButton(
                text="Разблок." if t_info.get('blocked') else "Заблокировать",
                size_hint_x=0.45
            )
            
            def make_toggle(target_id, block_val):
                return lambda x: self.toggle_block(target_id, block_val)
            
            btn_action.bind(on_press=make_toggle(t_id, not t_info.get('blocked')))
            
            row.add_widget(lbl)
            row.add_widget(btn_action)
            self.term_list_box.add_widget(row)

    def toggle_block(self, target_id, block_state):
        payload = {
            "terminal_id": target_id,
            "blocked": block_state
        }
        if trigger_github_action("toggle_terminal_block", payload):
            Popup(title="Отправлено", content=Label(text="Статус блокировки обновляется..."), size_hint=(0.8, 0.3)).open()

# --- ЗАПУСК ПРИЛОЖЕНИЯ ---
class NeoBankApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainMenuScreen(name='main_menu'))
        sm.add_widget(RegisterTerminalScreen(name='register'))
        sm.add_widget(TerminalScreen(name='terminal'))
        sm.add_widget(ClientScreen(name='client'))
        sm.add_widget(AdminScreen(name='admin'))
        return sm

if __name__ == '__main__':
    NeoBankApp().run()
