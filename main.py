from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.animation import Animation
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.switch import Switch
from kivy.uix.togglebutton import ToggleButton
from kivy.properties import BooleanProperty, ListProperty
from datetime import datetime
import os
import sys
import matplotlib.pyplot as plt
import csv
import sqlite3

os.environ['KIVY_AUDIO'] = 'sdl2'

# 🎯 --- Database Setup ---
class Database:
    def __init__(self):
        self.conn = sqlite3.connect("expenses.db")
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        """Create user, expenses, and budget tables."""
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                email TEXT)"""
        )
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date TEXT,
                amount REAL,
                category TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id))"""
        )
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS budget (
                user_id INTEGER PRIMARY KEY,
                monthly_budget REAL)"""
        )
        self.conn.commit()

    def register_user(self, username, password, email=""):
        """Register new user."""
        try:
            self.cursor.execute(
                "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                (username, password, email),
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def login_user(self, username, password):
        """Check login credentials."""
        self.cursor.execute(
            "SELECT id FROM users WHERE username = ? AND password = ?", (username, password)
        )
        user = self.cursor.fetchone()
        return user[0] if user else None

    def add_expense(self, user_id, date, amount, category):
        """Add new expense to DB."""
        self.cursor.execute(
            "INSERT INTO expenses (user_id, date, amount, category) VALUES (?, ?, ?, ?)",
            (user_id, date, amount, category),
        )
        self.conn.commit()

    def set_monthly_budget(self, user_id, budget):
        """Set monthly budget for a user."""
        self.cursor.execute(
            "REPLACE INTO budget (user_id, monthly_budget) VALUES (?, ?)", (user_id, budget)
        )
        self.conn.commit()

    def get_monthly_budget(self, user_id):
        """Retrieve the monthly budget for the user."""
        self.cursor.execute("SELECT monthly_budget FROM budget WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return float(result[0]) if result else 0

    def get_monthly_expense_total(self, user_id):
        """Calculate the total expenses for the current month."""
        current_month = datetime.now().strftime("%Y-%m")
        self.cursor.execute(
            "SELECT SUM(amount) FROM expenses WHERE user_id = ? AND date LIKE ?",
            (user_id, f"{current_month}%"),
        )
        total = self.cursor.fetchone()[0]
        return float(total) if total else 0


# --- Welcome Screen ---
class WelcomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        self.add_widget(layout)

        # Load and play the sound
        sound = SoundLoader.load("assets/welcome_chime.mp3")
        if sound:
            sound.play()
        else:
            print("Sound file not found!")

        # Schedule transition to LoginScreen after 5 seconds
        Clock.schedule_once(self.switch_to_login, 2.5)

    def switch_to_login(self, dt):
        self.manager.current = 'login'


# 🌟 --- Login Screen ---
class LoginScreen(Screen):
    dark_mode = BooleanProperty(False)
    background_color = ListProperty([1, 1, 1, 1])

    def login_user(self):
        """Handle user login."""
        username = self.ids.username.text
        password = self.ids.password.text

        user_id = self.manager.db.login_user(username, password)
        if user_id:
            self.manager.current_user_id = user_id
            self.manager.current = "home"
        else:
            self.show_popup("Login Failed", "Invalid username or password!")

    def register_user(self):
        """Navigate to the register screen."""
        self.manager.current = "register"

    def show_forgot_password_popup(self):
        """Forgot Password — reset with username & new password."""
        content = BoxLayout(orientation='vertical')
        username_input = TextInput(hint_text="Enter your username", multiline=False)
        new_password_input = TextInput(hint_text="Enter new password", password=True, multiline=False)
        reset_button = Button(text="Reset Password", size_hint=(1, 0.2))

        content.add_widget(Label(text="Enter your username:"))
        content.add_widget(username_input)
        content.add_widget(Label(text="Enter new password:"))
        content.add_widget(new_password_input)
        content.add_widget(reset_button)

        popup = Popup(title="Reset Password", content=content, size_hint=(0.8, 0.4))

        reset_button.bind(
            on_release=lambda *args: self.reset_password(username_input.text, new_password_input.text, popup)
        )
        popup.open()

    def reset_password(self, username, new_password, popup):
        """Reset password after checking if username exists."""
        if not username or not new_password:
            self.show_popup("Error", "Please fill in both fields!")
            return

        # Check if the user exists
        self.manager.db.cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = self.manager.db.cursor.fetchone()

        if user:
            self.manager.db.cursor.execute(
                "UPDATE users SET password = ? WHERE username = ?", (new_password, username)
            )
            self.manager.db.conn.commit()
            popup.dismiss()
            self.show_popup("Success", "Password reset successfully!")
        else:
            self.show_popup("Error", "Username not found!")

    def toggle_dark_mode(self, switch_instance, value):
        self.dark_mode = value
        if value:
            App.get_running_app().root_window.clearcolor = (0, 0, 0, 1)
            self.background_color = [0, 0, 0, 1]
            self.dark_mode = True
        else:
            App.get_running_app().root_window.clearcolor = (1, 1, 1, 1)
            self.background_color = [1, 1, 1, 1]
            self.dark_mode = False

    def on_dark_mode(self, instance, value):
        self.background_color = (0, 0, 0, 1) if value else (1, 1, 1, 1)

    def show_popup(self, title, message):
        """Reusable popup handler."""
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(None, None),
            size=(400, 200),
        )
        popup.open()


# 🌟 --- Register Screen ---
class RegisterScreen(Screen):
    def register_user(self):
        """Register a new user."""
        username = self.ids.reg_username.text
        password = self.ids.reg_password.text

        if self.manager.db.register_user(username, password):
            self.manager.current = "login"
            self.show_popup("Success", "User registered successfully!")
        else:
            self.show_popup("Error", "Username already exists!")

    def show_popup(self, title, message):
        """Reusable popup handler."""
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(None, None),
            size=(400, 200),
        )
        popup.open()

# 🏠 --- Home Screen ---
class HomeScreen(Screen):
    def add_expense_screen(self):
        """Navigate to Add Expense screen."""
        self.manager.current = "add_expense"

    def view_expenses(self):
        """Navigate to View Expenses screen."""
        self.manager.current = "view_expense"

    def set_budget(self):
        """Popup to set monthly budget."""
        content = BoxLayout(orientation='vertical')
        budget_input = TextInput(hint_text="Enter Monthly Budget (₹)")
        submit_button = Button(text="Set Budget", size_hint=(1, 0.2))

        content.add_widget(budget_input)
        content.add_widget(submit_button)

        popup = Popup(title="Set Monthly Budget", content=content, size_hint=(0.8, 0.4))

        submit_button.bind(
            on_release=lambda *args: self.save_budget(budget_input.text, popup)
        )
        popup.open()

    def save_budget(self, budget_input, popup):
        """Save the monthly budget."""
        if budget_input.isdigit():
            self.manager.db.set_monthly_budget(self.manager.current_user_id, float(budget_input))
            self.show_popup("Success", f"Monthly budget set to ₹{budget_input}")
            popup.dismiss()
        else:
            self.show_popup("Error", "Please enter a valid number!")

    def logout_user(self):
        """Log out and return to Login screen."""
        self.manager.current_user_id = None
        self.manager.current = "login"

    def show_popup(self, title, message):
        """Reusable popup handler."""
        popup = Popup(title=title, content=Label(text=message), size_hint=(None, None), size=(400, 200))
        popup.open()


# 💸 --- Add Expense Screen ---
class AddExpenseScreen(Screen):
    def save_expense(self):
        """Save the entered expense data."""
        amount = self.ids.amount_input.text
        category = self.ids.category_input.text
        db = self.manager.db

        if amount and category:
            db.add_expense(
                self.manager.current_user_id,
                datetime.now().strftime("%Y-%m-%d"),
                float(amount),
                category,
            )
            self.manager.current = "home"
        else:
            self.show_popup("Error", "Please fill in all fields!")

    def back_to_home(self):
        """Return to the Home screen."""
        self.manager.current = "home"

    def show_popup(self, title, message):
        """Reusable popup handler."""
        popup = Popup(title=title, content=Label(text=message), size_hint=(None, None), size=(400, 200))
        popup.open()


# 📊 --- View Expenses Screen ---
class ViewExpenseScreen(Screen):
    def on_enter(self):
        """Load expenses on screen entry."""
        self.load_expenses()

    def load_expenses(self, start_date=None, end_date=None):
        """Load and display expenses with optional date filtering."""
        self.ids.expense_list.text = ""
        db = self.manager.db
        user_id = self.manager.current_user_id

        query = "SELECT date, amount, category FROM expenses WHERE user_id = ?"
        params = [user_id]

        if start_date and end_date:
            query += " AND date BETWEEN ? AND ?"
            params.extend([start_date, end_date])

        query += " ORDER BY date DESC"
        db.cursor.execute(query, tuple(params))
        expenses = db.cursor.fetchall()

        if expenses:
            for exp in expenses:
                date, amount, category = exp
                self.ids.expense_list.text += f"{date} | ₹{amount} | {category}\n"
        else:
            self.ids.expense_list.text = "No expenses found for the selected dates!"

    def apply_filter(self):
        """Apply date filters to expenses."""
        start_date = self.ids.start_date.text
        end_date = self.ids.end_date.text

        try:
            start_date_obj = datetime.strptime(start_date, "%d-%m-%Y").strftime("%Y-%m-%d")
            end_date_obj = datetime.strptime(end_date, "%d-%m-%Y").strftime("%Y-%m-%d")
            self.load_expenses(start_date_obj, end_date_obj)
        except ValueError:
            self.show_popup("Error", "Date must be in DD-MM-YYYY format!")

    def export_to_csv(self):
        """Export filtered expenses to CSV file."""
        try:
            db = self.manager.db
            user_id = self.manager.current_user_id
            query = "SELECT date, amount, category FROM expenses WHERE user_id = ?"
            db.cursor.execute(query, (user_id,))
            expenses = db.cursor.fetchall()

            if not expenses:
                self.show_popup("Error", "No data to export!")
                return

            with open("expenses_export.csv", "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Date", "Amount", "Category"])
                writer.writerows(expenses)

            self.show_popup("Success", "Expenses exported to CSV successfully!")
        except Exception as e:
            self.show_popup("Error", f"Failed to export: {e}")

    def show_graph(self):
        """Display a category-wise expense graph."""
        db = self.manager.db
        user_id = self.manager.current_user_id
        db.cursor.execute(
            "SELECT category, SUM(amount) FROM expenses WHERE user_id = ? GROUP BY category",
            (user_id,),
        )
        data = db.cursor.fetchall()

        if not data:
            self.show_popup("Error", "No expenses to display!")
            return

        categories = [row[0] for row in data]
        amounts = [row[1] for row in data]

        plt.figure(figsize=(8, 6))
        plt.pie(amounts, labels=categories, autopct="%1.1f%%", startangle=140)
        plt.axis("equal")
        plt.title("Category-wise Expense Breakdown")
        plt.show()

    def show_popup(self, title, message):
        """Reusable popup handler."""
        popup = Popup(title=title, content=Label(text=message), size_hint=(None, None), size=(400, 200))
        popup.open()


    def back_to_home(self):
        """Navigate back to the Home screen."""
        self.manager.current = "home"


# 🚀 --- App Setup ---
class KharchaBookApp(App):
    def build(self):
        db = Database()
        sm = ScreenManager()
        sm.db = db
        sm.current_user_id = None

        sm.add_widget(WelcomeScreen(name="welcome"))
        # Assuming your login screen is already built and named 'login'
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(RegisterScreen(name="register"))
        sm.add_widget(HomeScreen(name="home"))  # Ensure HomeScreen exists
        sm.add_widget(AddExpenseScreen(name="add_expense"))
        sm.add_widget(ViewExpenseScreen(name="view_expense"))

        sm.current = "welcome"

        return sm

if __name__ == "__main__":
    KharchaBookApp().run()
