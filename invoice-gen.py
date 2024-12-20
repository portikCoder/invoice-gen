#!/usr/bin/python
import pdfkit
import yaml
import subprocess
import argparse
import os.path
import datetime
import string
import random
import sys

import generator

now = datetime.datetime.now()

CONFIG_PATH = "config.yaml"
INVOICE_NUMBER_UID_LENGTH = 5
DEFAULT_CONFIG = {
    "name": "[BUSINESS_NAME]",
    "address": "[BUSINESS_ADDRESS]",
    "city_province_country": "[BUSINESS_CITY_PROVINCE_COUNTRY]",
    "postal_code": "[BUSINESS_POSTAL_CODE]",
    "phone": "[BUSINESS_PHONE]",
    "email": "[BUSINESS_EMAIL]",
    "abrv": "[ABRV]",
    "customers": [
        {
            "id": 1,
            "name": "[CUSTOMER_NAME]",
            "address": "[CUSTOMER_ADDRESS]",
            "city_province_country": "[CUSTOMER_CITY_PROVINCE_COUNTRY]",
            "postal_code": "[CUSTOMER_POSTAL_CODE]",
            "phone": "[CUSTOMER_PHONE]",
        }
    ],
}
DEFAULT_DATA = {
    "customer_id": 0,
    "invoice_type": "invoice",
    "invoice_date": "",
    "invoice_number": "",
    "currency": "CAD",
    "items": [
        {
            "desc": "[DESCRIPTION]",
            "hours": 0,
            "rate": 35,
        }
    ],
}

generator.generate()
with open("invoice_output.html") as f:
    DEFAULT_TEMPLATE = f.read()


DEFAULT_FOLLOWUP_INVOICE = """
    <div class="col-sm-10 mt-2">
      <p class="text-center text-small">
        Please process all payments within <span class="bold">15 days</span> of receiving this invoice.
      </p>
      <ul>
        <li class="thin">Make all cheques payable to <span class="bold">[BUSINESS_OWNER]</span></li>
      </ul>
    </div>
    <div class="col-sm-4">
      <div class="sep"></div>
    </div>
"""
# TODO: Make etransfers optional
# <li class="thin">eTransfers and Paypal payments are also accepted, please send to  <span class="bold">[BUSINESS_EMAIL]</span></li>

parser = argparse.ArgumentParser(description="Generate invoices.")
parser.add_argument(
    "customer_id", help="enter customer id to initialize invoice", nargs="?", const=0
)
parser.add_argument(
    "-l", "--list-customers", help="list all customers", action="store_true"
)
parser.add_argument(
    "-b",
    "--build",
    help="build a new pdf using the specified yaml file",
    metavar="YAML_FILE",
    nargs=1,
)
args = parser.parse_args()


def main():
    config = {}
    if os.path.isfile(CONFIG_PATH):
        with open(CONFIG_PATH) as raw_config:
            config = yaml.safe_load(raw_config)
    else:
        create_yaml_file(CONFIG_PATH, DEFAULT_CONFIG)
        print("Missing config, please fill it in and try again.")
        open_file(CONFIG_PATH)
        exit()
    if args.list_customers:
        list_customers(config)
    elif args.build:
        data = {}
        if os.path.isfile(args.build[0]):
            with open(args.build[0]) as raw_data:
                data = yaml.safe_load(raw_data)
                build_pdf(config, data, args.build[0].replace(".yaml", ".pdf"))
        else:
            print("Invoice data file '%s' does not exist." % args.build[0])
    elif args.customer_id:
        if not args.customer_id.isdigit():
            print(
                "Invalid customer_id value '%s', please enter a number or use -l to list active customers."
                % args.customer_id
            )
        elif (
            len(
                [
                    customer
                    for customer in config["customers"]
                    if customer["id"] == int(args.customer_id)
                ]
            )
            > 0
        ):
            init_new_invoice_data(
                config, get_customer_by_id(config["customers"], args.customer_id)
            )
        else:
            print(
                "Customer with id '%s' does not exist, please use -l to list active customers."
                % args.customer_id
            )
    else:
        parser.print_help(sys.stderr)


def list_customers(config):
    for customer in config["customers"]:
        print("%s - %s" % (customer["id"], customer["name"]))


def build_pdf(config, data, export_path):
    print("Generating...")
    processed_data = process_invoice_data(data)
    customer = get_customer_by_id(config["customers"], data["customer_id"])
    template = (
        DEFAULT_TEMPLATE.replace("[BUSINESS_NAME]", config["name"])
        .replace("[BUSINESS_ADDRESS]", config["address"])
        .replace("[BUSINESS_CITY_PROVINCE_COUNTRY]", config["city_province_country"])
        .replace("[BUSINESS_POSTAL_CODE]", config["postal_code"])
        .replace("[BUSINESS_PHONE]", config["phone"])
        .replace("[BUSINESS_OWNER]", config["owner"])
        .replace("[BUSINESS_EMAIL]", config["email"])
        .replace("[BUSINESS_TAX_NUMBER]", config["tax_number"])
        .replace("[CUSTOMER_NAME]", customer["name"])
        .replace("[CUSTOMER_ID]", str(customer["id"]))
        .replace("[CUSTOMER_ADDRESS]", customer["address"])
        .replace("[CUSTOMER_CITY_PROVINCE_COUNTRY]", customer["city_province_country"])
        .replace("[CUSTOMER_POSTAL_CODE]", customer["postal_code"])
        .replace("[INVOICE_DATE]", data["invoice_date"])
        .replace("[INVOICE_NUMBER]", data["invoice_number"])
        .replace("[INVOICE_TYPE]", data["invoice_type"])
        .replace("[INVOICE_ITEMS]", get_invoice_items(processed_data))
        .replace("[INVOICE_SUBTOTAL]", str(get_invoice_subtotal(processed_data)))
        .replace("[INVOICE_SALES_TAX_DESC]", str(get_sales_tax_desc(data, config)))
        .replace(
            "[INVOICE_SALES_TAX]", str(get_invoice_sales_tax(processed_data, config))
        )
        .replace("[INVOICE_TOTAL]", str(get_invoice_total(processed_data, config)))
        .replace("[FOLLOWUP_INFO]", get_followup_info(data["invoice_type"], config))
        .replace("[CURRENCY]", data["currency"])
    )
    final_export_path = export_path.replace(
        "Invoice", data["invoice_type"].capitalize()
    )
    pdfkit.from_string(template, final_export_path)
    subprocess.check_call(["open", "-a", "Preview.app", final_export_path])
    print("Complete.")


def open_file(path):
    subprocess.check_call(["open", "-a", "Sublime Text.app", path])


def init_new_invoice_data(config, customer):
    data = DEFAULT_DATA
    data["customer_id"] = customer["id"]
    data["invoice_date"] = get_invoice_date(now)
    data["invoice_number"] = get_invoice_number(config["abrv"], now)
    data["currency"] = customer["currency"]
    data["items"] = customer["items"]
    file_name = "%s_-_%s_Invoice_-_%s.yaml" % (
        config["name"].replace(" ", "_"),
        customer["name"].replace(" ", "_"),
        data["invoice_number"],
    )
    create_yaml_file(file_name, data)
    # open_file(file_name)


def create_yaml_file(path, data):
    with open(path, "w") as file:
        yaml.dump(data, file, default_flow_style=False)


def get_customer_by_id(customers, customer_id):
    for customer in customers:
        if customer["id"] == int(customer_id):
            return customer
    return None


def get_invoice_number(abbreviation, now):
    return "%s%s%s" % (
        abbreviation,
        str(now.strftime("%d%m%Y")),
        "".join(
            random.choices(
                string.ascii_uppercase + string.digits, k=INVOICE_NUMBER_UID_LENGTH
            )
        ),
    )


def get_invoice_date(now):
    return now.strftime("%b %d, %Y")


def get_invoice_items(data):
    out = ""
    for item in data["items"]:
        out += "<tr>"
        out += "<td class='item-cell'>%s</td>" % process_item_desc(item["desc"])
        if "units" in item:
            out += "<td class='text-center item-cell'>%s %s(s)</td>" % (
                item["units"],
                item["by"],
            )
            out += (
                "<td class='text-right item-cell'><span class='currency'>$</span>%s / %s</td>"
                % (item["rate"], item["by"])
            )
        else:
            out += "<td class='text-center item-cell'>-</td>"
            out += (
                "<td class='text-right item-cell'><span class='currency'>$</span>%s</td>"
                % (item["rate"])
            )
        out += (
            "<td class='text-right item-cell'><span class='currency'>$</span>%s</td>"
            % item["total"]
        )
        out += "</tr>"
    return out


def process_item_desc(desc):
    if isinstance(desc, list):
        out = ""
        for item in desc:
            if item[0].isupper():
                out += "%s</br>" % item
            else:
                out += "- %s</br>" % item
        return out
    return desc


def get_invoice_total(data, config):
    if "taxable" in data and data["taxable"]:
        return "{:.2f}".format(
            sum([float(item["total"]) for item in data["items"]])
            + (
                sum([float(item["total"]) for item in data["items"]])
                * config["tax_rate"]
            )
        )
    else:
        return "{:.2f}".format(sum([float(item["total"]) for item in data["items"]]))


def get_invoice_sales_tax(data, config):
    if "taxable" in data and data["taxable"]:
        return "{:.2f}".format(
            sum([float(item["total"]) for item in data["items"]]) * config["tax_rate"]
        )
    else:
        return "-"


def get_sales_tax_desc(data, config):
    if "taxable" in data and data["taxable"]:
        return "(" + config["tax_desc"] + ")"
    else:
        return ""


def get_invoice_subtotal(data):
    return "{:.2f}".format(sum([float(item["total"]) for item in data["items"]]))


def process_invoice_data(data):
    for item in data["items"]:
        if "units" in item:
            item["total"] = "{:.2f}".format(item["units"] * item["rate"])
        else:
            item["total"] = "{:.2f}".format(item["rate"])
    return data


def get_followup_info(invoice_type, config):
    if invoice_type == "invoice":
        return DEFAULT_FOLLOWUP_INVOICE.replace(
            "[BUSINESS_OWNER]", config["owner"]
        ).replace("[BUSINESS_EMAIL]", config["email"])
    return ""


if __name__ == "__main__":
    main()
