from enum import Enum


class IncomeSubcategory(str, Enum):
    SALARY = "Salary"
    SIDE = "Side"


class BillsSubcategory(str, Enum):
    RENT = "Rent"
    UTILITIES = "Utilities"
    INSURANCE = "Insurance"
    TELECOM = "Telecom"
    TAXES = "Taxes"
    FEES = "Fees"
    SUBSCRIPTIONS = "Subscriptions"


class EssentialsSubcategory(str, Enum):
    TRANSIT = "Transit"
    GROCERIES = "Groceries"


class DiningSubcategory(str, Enum):
    WORK = "Work"
    DATE = "Date"
    DELIVERY = "Delivery"
    SOCIAL = "Social"


class ShoppingSubcategory(str, Enum):
    CLOTHING = "Clothing"
    ELECTRONICS = "Electronics"
    MEDIA = "Media"
    GIFTS = "Gifts"


class HouseholdSubcategory(str, Enum):
    FURNITURE = "Furniture"
    APPLIANCES = "Appliances"
    DECOR = "Decor & Furnishings"
    CLEANING = "Cleaning"


class PersonalCareSubcategory(str, Enum):
    MEDICAL = "Medical"
    PERSONAL = "Personal Care"


class LeisureSubcategory(str, Enum):
    EVENTS = "Events"
    ACTIVITIES = "Activities"


class HobbiesSubcategory(str, Enum):
    BOULDERN = "Bouldern"
    SALSA = "Salsa"
    TECH = "Tech"


class TravelSubcategory(str, Enum):
    TRANSPORT = "Transport"
    ACCOMMODATION = "Accommodation"
    FOOD_ACTIVITIES = "Food & Activities"


class FinancialSubcategory(str, Enum):
    INVESTMENTS = "Investments"
    SAVINGS = "Savings"


class Category(str, Enum):
    INCOME = "Income"
    BILLS = "Bills"
    ESSENTIALS = "Essentials"
    DINING = "Dining"
    SHOPPING = "Shopping"
    HOUSEHOLD = "Household"
    PERSONAL_CARE = "Personal Care & Health"
    LEISURE = "Leisure"
    HOBBIES = "Hobbies"
    TRAVEL = "Travel"
    FINANCIAL = "Financial"
