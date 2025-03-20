import sqlite3
from datetime import datetime

class Database:
    def __init__(self):
        """Connect to the database and create tables if they don't exist."""
        self.conn = sqlite3.connect("kharcha_book.db")
        self.cursor = self.conn.cursor()
        self.create_tables()
        try:
            from database import Database
            db = Database()
        except (ImportError, Exception) as e:
            print(f"❌ Failed to load database module: {e}")
            exit()
            
    def create_tables(self):
        """Create users and expenses tables."""
        # ✅ Users table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        ''')

        # ✅ Expenses table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                notes TEXT DEFAULT ''
            )
        ''')

        self.conn.commit()

    # ✅ Register a new user
    def register_user(self, username, password):
        try:
            self.cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    # ✅ Login user check
    def login_user(self, username, password):
        self.cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
        user = self.cursor.fetchone()
        return user[0] if user else None

    # ✅ Add a new expense
    # Ensure dates are saved as YYYY-MM-DD format
    def add_expense(self, date, amount, category, notes=""):
        try:
            # Ensure the date is treated as a string
            if isinstance(date, int):  
                date = str(date)

            # Validate and format date as YYYY-MM-DD
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%Y-%m-%d")
            
            # Insert the expense data
            self.cursor.execute(
                "INSERT INTO expenses (date, amount, category, notes) VALUES (?, ?, ?, ?)",
                (formatted_date, amount, category, notes)
            )
            self.conn.commit()
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD!")
        except Exception as e:
            print(f"Failed to add expense: {e}")


        
    # ✅ Fetch unique years from expenses
    def get_unique_years(self):
        self.cursor.execute("SELECT DISTINCT date FROM expenses ORDER BY date DESC")
        dates = self.cursor.fetchall()
        
        # Extract valid years from dates
        years = set()
        for date in dates:
            try:
                year = int(date[0].split("-")[0])
                if 1900 <= year <= 2100:  # Ensure the year is reasonable
                    years.add(str(year))
            except (ValueError, IndexError):
                continue

        return sorted(years, reverse=True) if years else [str(datetime.now().year)]


    def fix_broken_dates(self):
        """Convert broken or empty dates to today's date."""
        self.cursor.execute("UPDATE expenses SET date = ? WHERE date IS NULL OR date = ''", (datetime.now().strftime("%Y-%m-%d"),))
        self.conn.commit()

    # ✅ Fetch expenses by year and month
    def get_expenses_by_month(self, year, month):
        self.cursor.execute(
            "SELECT date, amount, category, notes FROM expenses WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ? ORDER BY date ASC",
            (year, month)
        )
        results = self.cursor.fetchall()
        return results if results else []


    # ✅ Close the database connection
    def close(self):
        self.conn.close()
