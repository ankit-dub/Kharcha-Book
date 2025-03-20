import re

# Sample predefined categories (You can expand this)
CATEGORY_KEYWORDS = {
    "Food": ["food", "restaurant", "pizza", "burger", "coffee", "dinner"],
    "Transport": ["uber", "bus", "metro", "train", "cab", "fuel", "petrol"],
    "Entertainment": ["netflix", "movie", "concert", "game", "music", "fun"],
    "Shopping": ["amazon", "flipkart", "clothes", "grocery", "mall"],
    "Bills": ["electricity", "wifi", "rent", "mobile recharge", "gas"],
    "Health": ["doctor", "hospital", "medicines", "gym", "yoga"],
    "Others": []  # Default category
}

def categorize_expense(description):
    """Categorize expense based on keywords in the description"""
    description = description.lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(re.search(r'\b' + word + r'\b', description) for word in keywords):
            return category

    return "Others"  # Default if no match found
