from cashewiss.core.models import CategoryMapping
from cashewiss.core.enums import *

MERCHANT_MAPPINGS = {
    "boulderlounge": CategoryMapping(
        category=Category.HOBBIES, subcategory=HobbiesSubcategory.BOULDERN
    ),
    "publibike": CategoryMapping(
        category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.TRANSIT
    ),
    "salsarica": CategoryMapping(
        category=Category.HOBBIES, subcategory=HobbiesSubcategory.SALSA
    ),
    "theater": CategoryMapping(
        category=Category.LEISURE, subcategory=LeisureSubcategory.EVENTS
    ),
    "kir": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "minimum": CategoryMapping(
        category=Category.HOBBIES, subcategory=HobbiesSubcategory.BOULDERN
    ),
    "minimum-": CategoryMapping(
        category=Category.HOBBIES, subcategory=HobbiesSubcategory.BOULDERN
    ),
    "gastro technopark zh": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.WORK
    ),
    "sv": CategoryMapping(category=Category.DINING, subcategory=DiningSubcategory.WORK),
    # "plaza": CategoryMapping(
    #    category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    # ),
    "too good to go": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.DATE
    ),
    "toogoodt": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.DATE
    ),
    "google": CategoryMapping(
        category=Category.SHOPPING, subcategory=ShoppingSubcategory.MEDIA
    ),
    "blue tomato": CategoryMapping(
        category=Category.SHOPPING, subcategory=ShoppingSubcategory.CLOTHING
    ),
    "burger king": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.DELIVERY
    ),
    "mcdonald's": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.DELIVERY
    ),
    "coiffeur": CategoryMapping(
        category=Category.PERSONAL_CARE,
        subcategory=PersonalCareSubcategory.PERSONAL,
    ),
    "ikea": CategoryMapping(
        category=Category.HOUSEHOLD, subcategory=HouseholdSubcategory.DECOR
    ),
    "pub": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "lokal": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "nelson": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "paddy's": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "mobility": CategoryMapping(
        category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.TRANSIT
    ),
    "sbb": CategoryMapping(
        category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.TRANSIT
    ),
    "zvv": CategoryMapping(
        category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.TRANSIT
    ),
    "swiss post": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.WORK
    ),
    "uber eats": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.DELIVERY
    ),
    "uber trip": CategoryMapping(
        category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.TRANSIT
    ),
    "openair": CategoryMapping(
        category=Category.LEISURE, subcategory=LeisureSubcategory.EVENTS
    ),
    "hallenstadion": CategoryMapping(
        category=Category.LEISURE, subcategory=LeisureSubcategory.EVENTS
    ),
    "gomore.ch": CategoryMapping(
        category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.TRANSIT
    ),
    "helvetia": CategoryMapping(
        category=Category.BILLS, subcategory=BillsSubcategory.INSURANCE
    ),
    "jumbo": CategoryMapping(
        category=Category.HOUSEHOLD, subcategory=HouseholdSubcategory.DECOR
    ),
    "jysk": CategoryMapping(
        category=Category.HOUSEHOLD, subcategory=HouseholdSubcategory.FURNITURE
    ),
    "bett0.ch": CategoryMapping(
        category=Category.HOUSEHOLD, subcategory=HouseholdSubcategory.FURNITURE
    ),
    "kkl": CategoryMapping(
        category=Category.LEISURE, subcategory=LeisureSubcategory.EVENTS
    ),
    "swiss international air lines": CategoryMapping(
        category=Category.TRAVEL, subcategory=TravelSubcategory.TRANSPORT
    ),
    "booking.com": CategoryMapping(
        category=Category.TRAVEL, subcategory=TravelSubcategory.ACCOMMODATION
    ),
    "ticketino": CategoryMapping(
        category=Category.LEISURE, subcategory=LeisureSubcategory.EVENTS
    ),
    "netflix": CategoryMapping(
        category=Category.BILLS, subcategory=BillsSubcategory.SUBSCRIPTIONS
    ),
    "spotify": CategoryMapping(
        category=Category.BILLS, subcategory=BillsSubcategory.SUBSCRIPTIONS
    ),
    "sky": CategoryMapping(
        category=Category.BILLS, subcategory=BillsSubcategory.SUBSCRIPTIONS
    ),
    "amavita": CategoryMapping(
        category=Category.PERSONAL_CARE, subcategory=PersonalCareSubcategory.MEDICAL
    ),
    "vitality": CategoryMapping(
        category=Category.PERSONAL_CARE, subcategory=PersonalCareSubcategory.MEDICAL
    ),
    "see tickets": CategoryMapping(
        category=Category.LEISURE, subcategory=LeisureSubcategory.EVENTS
    ),
    "gelateria": CategoryMapping(category=Category.DINING),
    "apotheke": CategoryMapping(
        category=Category.PERSONAL_CARE, subcategory=PersonalCareSubcategory.MEDICAL
    ),
    "microsoft": CategoryMapping(
        category=Category.SHOPPING, subcategory=ShoppingSubcategory.MEDIA
    ),
    "home 24": CategoryMapping(
        category=Category.HOUSEHOLD, subcategory=HouseholdSubcategory.DECOR
    ),
    "just eat": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.DELIVERY
    ),
    "swiss": CategoryMapping(
        category=Category.TRAVEL, subcategory=TravelSubcategory.TRANSPORT
    ),
    "easyjet": CategoryMapping(
        category=Category.TRAVEL, subcategory=TravelSubcategory.TRANSPORT
    ),
    "bitwarden.com": CategoryMapping(
        category=Category.BILLS, subcategory=BillsSubcategory.SUBSCRIPTIONS
    ),
    "xlch": CategoryMapping(
        category=Category.HOUSEHOLD, subcategory=HouseholdSubcategory.FURNITURE
    ),
    "aliexpress": CategoryMapping(
        category=Category.SHOPPING, subcategory=ShoppingSubcategory.ELECTRONICS
    ),
    "sunrise": CategoryMapping(
        category=Category.BILLS, subcategory=BillsSubcategory.TELECOM
    ),
    "elektrizitätswerk": CategoryMapping(
        category=Category.BILLS, subcategory=BillsSubcategory.UTILITIES
    ),
    "salär": CategoryMapping(
        category=Category.HOUSEHOLD, subcategory=HouseholdSubcategory.CLEANING
    ),
    "baugenossenschaft": CategoryMapping(
        category=Category.BILLS, subcategory=BillsSubcategory.RENT
    ),
    "serafe": CategoryMapping(
        category=Category.BILLS, subcategory=BillsSubcategory.UTILITIES
    ),
    "touring": CategoryMapping(
        category=Category.BILLS, subcategory=BillsSubcategory.INSURANCE
    ),
    "mensile": CategoryMapping(category=Category.INCOME),
    "sva": CategoryMapping(
        category=Category.BILLS, subcategory=BillsSubcategory.INSURANCE
    ),
    "helsana": CategoryMapping(
        category=Category.BILLS, subcategory=BillsSubcategory.INSURANCE
    ),
    # --- Swiss groceries ---
    "coop": CategoryMapping(
        category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.GROCERIES
    ),
    "migros": CategoryMapping(
        category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.GROCERIES
    ),
    "lidl": CategoryMapping(
        category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.GROCERIES
    ),
    "volg": CategoryMapping(
        category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.GROCERIES
    ),
    "aldi": CategoryMapping(
        category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.GROCERIES
    ),
    "denner": CategoryMapping(
        category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.GROCERIES
    ),
    "spar": CategoryMapping(
        category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.GROCERIES
    ),
    # --- Transit ---
    "lime": CategoryMapping(
        category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.TRANSIT
    ),
    "parking": CategoryMapping(
        category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.TRANSIT
    ),
    "taxi": CategoryMapping(
        category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.TRANSIT
    ),
    # --- Dining ---
    "brezel": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "stazione": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "kafi": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "confiseur": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "penisola": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "giro": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "donald": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.DELIVERY
    ),
    # --- Household ---
    "mr. green": CategoryMapping(
        category=Category.HOUSEHOLD, subcategory=HouseholdSubcategory.CLEANING
    ),
    "yubelky": CategoryMapping(
        category=Category.HOUSEHOLD, subcategory=HouseholdSubcategory.CLEANING
    ),
    # --- Shopping specifics ---
    "zalando": CategoryMapping(
        category=Category.SHOPPING, subcategory=ShoppingSubcategory.CLOTHING
    ),
    "claire's": CategoryMapping(
        category=Category.SHOPPING, subcategory=ShoppingSubcategory.CLOTHING
    ),
    "adc": CategoryMapping(
        category=Category.SHOPPING, subcategory=ShoppingSubcategory.ELECTRONICS
    ),
    "wos.ch": CategoryMapping(
        category=Category.SHOPPING, subcategory=ShoppingSubcategory.MEDIA
    ),
    "felfel": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.WORK
    ),
    "nooba": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "kebap": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "rice-go": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "ristorante": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "manora": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "tibits": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "noodlee": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "pizzeria": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "thai": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "bistro": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "higashi": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "john baker": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "mister cordon": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "rapido": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "selecta": CategoryMapping(category=Category.DINING),
    "amboss": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "oh my greek": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "caf bebek": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "my mythos": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "spusu": CategoryMapping(
        category=Category.BILLS, subcategory=BillsSubcategory.TELECOM
    ),
    "le mouton": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "eltruckdecapucho": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "bahnhofkiosk": CategoryMapping(category=Category.DINING),
    "migrolino": CategoryMapping(
        category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.GROCERIES
    ),
    "new asia market": CategoryMapping(
        category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.GROCERIES
    ),
    "manor ag": CategoryMapping(
        category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.GROCERIES
    ),
    "shell": CategoryMapping(
        category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.TRANSIT
    ),
    "avia": CategoryMapping(
        category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.TRANSIT
    ),
    "avec": CategoryMapping(
        category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.TRANSIT
    ),
    "ladestation": CategoryMapping(
        category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.TRANSIT
    ),
    "open ride": CategoryMapping(
        category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.TRANSIT
    ),
    "standing order": CategoryMapping(
        category=Category.BILLS, subcategory=BillsSubcategory.RENT
    ),
    "activ fitness": CategoryMapping(
        category=Category.BILLS, subcategory=BillsSubcategory.SUBSCRIPTIONS
    ),
    "rega": CategoryMapping(
        category=Category.BILLS, subcategory=BillsSubcategory.DONATIONS
    ),
    "zivilstandsamt": CategoryMapping(
        category=Category.BILLS, subcategory=BillsSubcategory.FEES
    ),
    "digitec": CategoryMapping(
        category=Category.SHOPPING, subcategory=ShoppingSubcategory.ELECTRONICS
    ),
    "nettoshop": CategoryMapping(
        category=Category.HOUSEHOLD, subcategory=HouseholdSubcategory.APPLIANCES
    ),
    "brack.ch": CategoryMapping(
        category=Category.SHOPPING, subcategory=ShoppingSubcategory.ELECTRONICS
    ),
    "jucker farm": CategoryMapping(
        category=Category.HOUSEHOLD, subcategory=HouseholdSubcategory.DECOR
    ),
    "gesundheitsmanagement": CategoryMapping(
        category=Category.PERSONAL_CARE, subcategory=PersonalCareSubcategory.MEDICAL
    ),
    "spital": CategoryMapping(
        category=Category.PERSONAL_CARE, subcategory=PersonalCareSubcategory.MEDICAL
    ),
    "treatwell": CategoryMapping(
        category=Category.PERSONAL_CARE,
        subcategory=PersonalCareSubcategory.PERSONAL,
    ),
    "apo doc": CategoryMapping(
        category=Category.PERSONAL_CARE, subcategory=PersonalCareSubcategory.MEDICAL
    ),
    "dr.andres": CategoryMapping(
        category=Category.PERSONAL_CARE, subcategory=PersonalCareSubcategory.MEDICAL
    ),
    "blue cinema": CategoryMapping(
        category=Category.LEISURE, subcategory=LeisureSubcategory.EVENTS
    ),
    "eventfrog": CategoryMapping(
        category=Category.LEISURE, subcategory=LeisureSubcategory.EVENTS
    ),
    "mountain adventures": CategoryMapping(
        category=Category.LEISURE, subcategory=LeisureSubcategory.ACTIVITIES
    ),
    "weisse arena": CategoryMapping(
        category=Category.LEISURE, subcategory=LeisureSubcategory.ACTIVITIES
    ),
    "qoqa": CategoryMapping(category=Category.SHOPPING),
    "deindeal": CategoryMapping(category=Category.SHOPPING),
    "suit supply": CategoryMapping(
        category=Category.SHOPPING, subcategory=ShoppingSubcategory.CLOTHING
    ),
    "keeper concept": CategoryMapping(
        category=Category.SHOPPING, subcategory=ShoppingSubcategory.CLOTHING
    ),
    "ursi's": CategoryMapping(
        category=Category.SHOPPING, subcategory=ShoppingSubcategory.CLOTHING
    ),
    "infomaniak": CategoryMapping(
        category=Category.BILLS, subcategory=BillsSubcategory.SUBSCRIPTIONS
    ),
    "fusion dance": CategoryMapping(
        category=Category.HOBBIES, subcategory=HobbiesSubcategory.SALSA
    ),
    "gameorama": CategoryMapping(
        category=Category.HOBBIES, subcategory=HobbiesSubcategory.TECH
    ),
    "wal cochin": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "qoqa": CategoryMapping(category=Category.SHOPPING),
    "deindeal": CategoryMapping(category=Category.DINING),
    "moser": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "menza": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.WORK
    ),
    "mensa": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.WORK
    ),
    "bachbuck": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "imranli": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "moschti": CategoryMapping(
        category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
    ),
    "leonard pjetraj": CategoryMapping(category=Category.INCOME),
    "pg 8152": CategoryMapping(
        category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.TRANSIT
    ),
    "alpinistica": CategoryMapping(
        category=Category.HOBBIES, subcategory=HobbiesSubcategory.BOULDERN
    ),
    # --- Financial ---
    "finpension": CategoryMapping(
        category=Category.FINANCIAL, subcategory=FinancialSubcategory.SAVINGS
    ),
    "terzo": CategoryMapping(
        category=Category.FINANCIAL, subcategory=FinancialSubcategory.SAVINGS
    ),
    "interactive brokers": CategoryMapping(
        category=Category.FINANCIAL, subcategory=FinancialSubcategory.INVESTMENTS
    ),
    # --- Bills (taxes & donations) ---
    "kanton": CategoryMapping(
        category=Category.BILLS, subcategory=BillsSubcategory.TAXES
    ),
    "steueramt": CategoryMapping(
        category=Category.BILLS, subcategory=BillsSubcategory.TAXES
    ),
    "caritas": CategoryMapping(
        category=Category.BILLS, subcategory=BillsSubcategory.DONATIONS
    ),
    # --- Travel ---
    "reka": CategoryMapping(category=Category.TRAVEL),
}
