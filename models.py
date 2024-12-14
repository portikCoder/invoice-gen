from dataclasses import dataclass
from typing import List


@dataclass
class Business:
    name: str
    tax_number: str
    reg_number: str
    address: str
    city_province_country: str
    postal_code: str
    iban: str
    swift: str
    email: str


@dataclass
class Customer:
    name: str
    tax_number: str
    reg_number: str
    address: str
    city_province_country: str
    postal_code: str
    phone: str
    email: str
    currency: str


@dataclass
class Item:
    description: str
    # details: List[str]
    unit: str
    amount: int
    unit_price: float
    value: float  # Compute the value based on hours and rate
    vat_percent: float
    total: float  # With VAT

    def __post_init__(self):
        """Automatically calculate the total after initialization."""
        self.calculate_values()

    def calculate_values(self):
        """Calculate the total&value for this item based on amount, unit price, and VAT."""
        self.value = self.amount * self.unit_price
        self.total = self.value * (1 + self.vat_percent / 100)


@dataclass
class Invoice:
    number: str
    date: str
    due_date: str
    business: Business
    customer: Customer
    items: List[Item]
    total_eur: float
    vat_percent: float
    items: List["Item"]  # Use forward reference for Item

    def __post_init__(self):
        """Automatically calculate the total EUR after initialization."""
        self.calculate_total_eur()

    def calculate_total_eur(self):
        """Calculate the total amount in EUR for this invoice based on the items."""
        self.total_eur = sum(item.total for item in self.items)
        return self.total_eur
