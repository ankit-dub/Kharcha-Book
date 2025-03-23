from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.animation import Animation
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.switch import Switch
from kivy.uix.togglebutton import ToggleButton
from kivy.properties import BooleanProperty, ListProperty, StringProperty, ObjectProperty
from datetime import datetime, timedelta, date
import calendar
import os
import sys
import matplotlib.pyplot as plt
import csv
import sqlite3

os.environ['KIVY_AUDIO'] = 'sdl2'

# Date Picker Widget
class DatePicker(BoxLayout):
    """Custom Date Picker widget"""
    
    selected_date = ObjectProperty(None)
    
    def __init__(self, callback=None, **kwargs):
        super(DatePicker, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.callback = callback
        self.current_date = datetime.now()
        self.selected_date = self.current_date
        self.build_layout()
    
    def build_layout(self):
        """Build the date picker UI layout"""
        self.clear_widgets()
        
        # Header with month/year and navigation
        header = BoxLayout(orientation='horizontal', size_hint=(1, 0.2))
        prev_month = Button(text='<', size_hint=(0.15, 1))
        prev_month.bind(on_release=self.prev_month)
        
        month_year = Label(
            text=self.current_date.strftime('%B %Y'),
            size_hint=(0.7, 1),
            bold=True
        )
        
        next_month = Button(text='>', size_hint=(0.15, 1))
        next_month.bind(on_release=self.next_month)
        
        header.add_widget(prev_month)
        header.add_widget(month_year)
        header.add_widget(next_month)
        
        # Days of week header
        days_header = GridLayout(cols=7, size_hint=(1, 0.1))
        for day in ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']:
            days_header.add_widget(Label(text=day))
        
        # Calendar grid
        self.calendar_grid = GridLayout(cols=7, size_hint=(1, 0.6))
        
        # Draw the calendar
        self.draw_calendar()
        
        # Add to main layout
        self.add_widget(header)
        self.add_widget(days_header)
        self.add_widget(self.calendar_grid)
        
        # Add "Today" button at bottom
        today_btn = Button(
            text='Today',
            size_hint=(1, 0.1)
        )
        today_btn.bind(on_release=self.select_today)
        self.add_widget(today_btn)
    
    def draw_calendar(self):
        """Draw the days of the month in the grid"""
        self.calendar_grid.clear_widgets()
        
        # Get the first day of the month and number of days
        year = self.current_date.year
        month = self.current_date.month
        
        # Get the calendar for this month
        cal = calendar.monthcalendar(year, month)
        
        # Fill the calendar grid
        for week in cal:
            for day in week:
                if day == 0:
                    # Empty day at start/end of month
                    btn = Button(text='', background_color=(0, 0, 0, 0))
                    btn.disabled = True
                else:
                    # Check if this is the selected date
                    is_selected = (
                        self.selected_date.year == year and
                        self.selected_date.month == month and
                        self.selected_date.day == day
                    )
                    
                    # Check if this is today
                    is_today = (
                        datetime.now().year == year and
                        datetime.now().month == month and
                        datetime.now().day == day
                    )
                    
                    # Create the day button
                    btn = Button(
                        text=str(day),
                        background_color=(0.3, 0.6, 1, 1) if is_selected else (0.2, 0.7, 0.3, 1) if is_today else (1, 1, 1, 1)
                    )
                    
                    # Bind the button click
                    btn.day = day
                    btn.bind(on_release=lambda btn: self.select_date(btn.day))
                
                self.calendar_grid.add_widget(btn)
    
    def select_date(self, day):
        """Handle date selection"""
        self.selected_date = datetime(
            self.current_date.year,
            self.current_date.month,
            day
        )
        
        # Call the callback with formatted date
        if self.callback:
            # Format as M/DD/YY for the app
            formatted_date = self.selected_date.strftime("%m/%d/%y")
            self.callback(formatted_date)
    
    def prev_month(self, instance):
        """Go to previous month"""
        if self.current_date.month == 1:
            self.current_date = datetime(self.current_date.year - 1, 12, 1)
        else:
            self.current_date = datetime(self.current_date.year, self.current_date.month - 1, 1)
        self.build_layout()
    
    def next_month(self, instance):
        """Go to next month"""
        if self.current_date.month == 12:
            self.current_date = datetime(self.current_date.year + 1, 1, 1)
        else:
            self.current_date = datetime(self.current_date.year, self.current_date.month + 1, 1)
        self.build_layout()
    
    def select_today(self, instance):
        """Set date to today"""
        today = datetime.now()
        self.current_date = datetime(today.year, today.month, 1)
        self.selected_date = today
        self.build_layout()
        
        # Call the callback with today's date
        if self.callback:
            formatted_date = today.strftime("%m/%d/%y")
            self.callback(formatted_date)

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

    def check_budget_exceeded(self, user_id):
        """Check if the current month expenses exceed the set budget.
        Returns a tuple (exceeded, budget, expenses) where exceeded is a boolean."""
        budget = self.get_monthly_budget(user_id)
        expenses = self.get_monthly_expense_total(user_id)
        
        if budget > 0 and expenses > budget:
            return (True, budget, expenses)
        return (False, budget, expenses)


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
    dark_mode = BooleanProperty(True)  # Changed from False to True to enable dark mode by default
    background_color = ListProperty([0, 0, 0, 1])  # Changed initial color to dark

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
    def on_enter(self):
        """Called when the screen is entered, display budget and check if exceeded"""
        self.display_budget()
        self.check_budget_status()

    def check_budget_status(self):
        """Check if budget is exceeded and show notification if needed"""
        user_id = self.manager.current_user_id
        exceeded, budget, expenses = self.manager.db.check_budget_exceeded(user_id)
        
        if exceeded:
            # Show budget alert popup
            budget_alert = BudgetAlertPopup(budget, expenses)
            Clock.schedule_once(lambda dt: budget_alert.open(), 0.5)

    def display_budget(self):
        user_id = self.manager.current_user_id
        budget = self.manager.db.get_monthly_budget(user_id)
        budget_text = f"Monthly Budget: ₹{budget}" if budget else "No budget set"
        self.ids.budget_label.text = budget_text

    def add_expense_screen(self):
        """Navigate to Add Expense screen."""
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = "add_expense"

    def view_expenses(self):
        """Navigate to View Expenses screen."""
        self.manager.transition = SlideTransition(direction='left')
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
        self.display_budget()

    def save_budget(self, budget_input, popup):
        """Save the monthly budget."""
        if budget_input.isdigit():
            self.manager.db.set_monthly_budget(self.manager.current_user_id, float(budget_input))
            self.show_popup("Success", f"Monthly budget set to ₹{budget_input}")
            popup.dismiss()
        else:
            self.show_popup("Error", "Please enter a valid number!")
        self.display_budget()

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
    def __init__(self, **kwargs):
        super(AddExpenseScreen, self).__init__(**kwargs)
        
    def clear_fields(self):
        """Clear all input fields on the Add Expense screen."""
        self.ids.date_input.text = ""
        self.ids.amount_input.text = ""
        self.ids.category_input.text = ""

    def show_date_picker(self):
        """Display the date picker popup"""
        # Create content with the DatePicker widget
        content = DatePicker(callback=self.update_date)
        
        # Create popup with the date picker
        self.date_popup = Popup(
            title="Select Date",
            content=content,
            size_hint=(0.9, 0.9),
            auto_dismiss=True
        )
        self.date_popup.open()
    
    def update_date(self, selected_date):
        """Update date_input with the selected date and close popup"""
        self.ids.date_input.text = selected_date
        self.date_popup.dismiss()
    
    def save_expense(self):
        """Save the entered expense data."""
        amount = self.ids.amount_input.text
        category = self.ids.category_input.text
        date_input = self.ids.date_input.text
        db = self.manager.db

        if amount and category:
            try:
                # Try to parse the date input (M/DD/YY format)
                date_obj = datetime.strptime(date_input, "%m/%d/%y")
                formatted_date = date_obj.strftime("%Y-%m-%d")
            except ValueError:
                # If date format is invalid, use today's date
                formatted_date = datetime.now().strftime("%Y-%m-%d")
                self.show_popup("Date Format Error", "Invalid date format! Using today's date instead.")

            db.add_expense(
                self.manager.current_user_id,
                formatted_date,
                float(amount),
                category,
            )
            
            # Check if this expense pushed the user over their budget
            exceeded, budget, expenses = db.check_budget_exceeded(self.manager.current_user_id)
            if exceeded:
                # Show budget alert popup before returning to home screen
                budget_alert = BudgetAlertPopup(budget, expenses)
                budget_alert.open()
            
            self.manager.transition = SlideTransition(direction='right')
            self.manager.current = "home"
        else:
            self.show_popup("Error", "Please fill in all fields!")

    def on_pre_enter(self):
        """Set today's date as default when screen is shown."""
        today = datetime.now().strftime("%m/%d/%y")
        self.ids.date_input.text = today

    def back_to_home(self):
        """Return to the Home screen."""
        self.manager.transition = SlideTransition(direction='right')
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

        plt.figure(figsize=(10, 6))
        plt.bar(categories, amounts, color='skyblue')
        plt.xlabel('Categories')
        plt.ylabel('Amount (₹)')
        plt.title('Category-wise Expense Breakdown')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()

    

    def show_popup(self, title, message):
        """Reusable popup handler."""
        popup = Popup(title=title, content=Label(text=message), size_hint=(None, None), size=(400, 200))
        popup.open()


    def back_to_home(self):
        """Navigate back to the Home screen."""
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = "home"


# Budget Alert Popup
class BudgetAlertPopup(Popup):
    def __init__(self, budget, expenses, **kwargs):
        super(BudgetAlertPopup, self).__init__(**kwargs)
        self.title = "Budget Alert!"
        self.size_hint = (0.85, 0.4)
        
        # Calculate overspend amount and percentage
        overspend = expenses - budget
        percentage = (expenses / budget - 1) * 100 if budget > 0 else 0
        
        content = BoxLayout(orientation='vertical', spacing=10, padding=[20, 20])
        
        # Alert message with red color
        alert_message = Label(
            text=f"[color=ff5555]You've exceeded your monthly budget![/color]",
            markup=True,
            font_size='18sp',
            size_hint_y=None,
            height='40dp'
        )
        
        # Details 
        details = Label(
            text=(f"Budget: ₹{budget:.2f}\n"
                  f"Expenses: ₹{expenses:.2f}\n"
                  f"Overspent: ₹{overspend:.2f} ({percentage:.1f}%)"),
            halign='left',
            font_size='16sp',
            size_hint_y=None,
            height='80dp'
        )
        details.bind(size=details.setter('text_size'))
        
        # Tips for the user
        tips = Label(
            text="Consider revising your spending or adjusting your budget.",
            font_size='14sp',
            size_hint_y=None,
            height='40dp',
            italic=True
        )
        
        # Close button
        close_button = Button(
            text="Got it",
            size_hint=(0.5, None),
            height='50dp',
            pos_hint={'center_x': 0.5}
        )
        close_button.bind(on_release=self.dismiss)
        
        content.add_widget(alert_message)
        content.add_widget(details)
        content.add_widget(tips)
        content.add_widget(close_button)
        
        self.content = content


# 🚀 --- App Setup ---
class KharchaBookApp(App):
    def build(self):
        db = Database()
        # Remove default transition direction from ScreenManager initialization
        sm = ScreenManager()
        sm.db = db
        sm.current_user_id = None

        sm.add_widget(WelcomeScreen(name="welcome"))
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(RegisterScreen(name="register"))
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(AddExpenseScreen(name="add_expense"))
        sm.add_widget(ViewExpenseScreen(name="view_expense"))

        sm.current = "welcome"
        
        return sm
        
    def on_start(self):
        # Set dark mode as default for app background
        # This is called after the window is created
        self.root_window.clearcolor = (0, 0, 0, 1)

if __name__ == "__main__":
    KharchaBookApp().run()
