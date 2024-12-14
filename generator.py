from dataclasses import dataclass
from typing import List
from jinja2 import Environment, FileSystemLoader

from models import Invoice, Business, Customer, Item


def generate():
    # Create some example data
    invoice = Invoice(
        number="12345",  # Placeholder for invoice number
        date="2024-08-15",  # Placeholder for invoice date
        due_date="2024-09-15",  # Placeholder for due date
        business=Business(
            name="Example Business",  # Placeholder for business name
            tax_number="RO12345678",  # Placeholder for business tax number
            reg_number="J12/345/6789",  # Placeholder for business registration number
            address="123 Business St.",  # Placeholder for business address
            city_province_country="Business City, BC, Country",  # Placeholder for business city/province/country
            postal_code="123456",  # Placeholder for business postal code
            iban="RO49AAAA1B31007593840000",  # Placeholder for business IBAN
            swift="AAAAROBU",  # Placeholder for business SWIFT code
            email="contact@example.com",  # Placeholder for business email
        ),
        customer=Customer(
            name="Bloomreach Slovakia s.r.o.",
            tax_number="SK2023578965",
            reg_number="",  # Placeholder for customer reg number, as it's not provided
            address="Karadžičova 16",
            city_province_country="Bratislava, Bratislavský kraj, Slovakia",
            postal_code="821 08",
            phone="+421 2/321 543 21",
            email="info@bloomreach.com",
            currency="EUR",
        ),
        items=[
            Item(
                description="Main work item",
                unit="hour",
                amount=168,
                unit_price=25,
                vat_percent=0,
                value=168 * 222,  # Compute the value based on hours and rate
                total=168 * 222,  # With VAT
            ),
            Item(
                description="Less complex task",
                unit="hour",
                amount=22,
                unit_price=10,
                vat_percent=0,
                value=22 * 10,  # Compute the value based on hours and rate
                total=22 * 10,  # With VAT
            ),  # Use customer items here as well if needed separately in the invoice.
        ],
        total_eur=444444,
        vat_percent=0,
    )

    # Set up Jinja2 environment and load the template
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("invoice.html")

    # Render the template with the invoice data
    html_output = template.render(invoice=invoice)

    # Write the rendered HTML to a file
    with open("invoice_output.html", "w") as f:
        f.write(html_output)
