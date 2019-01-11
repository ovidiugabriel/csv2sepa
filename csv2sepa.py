
# Script used to convert TransferWise CSV format file into SEPA XML 
# (pain.001.001.03) format (iso:20022)
#
# https://developers.paysera.com/en/file-formats-documentation/current#xml-format
#
# http://effbot.org/zone/element-index.htm

import csv
import xml.etree.cElementTree as ET
import xml.dom.minidom
import sys

config = {
    "account": {
        "iban": "",
        "currency": "EUR",
        "owner_name": "",
        "company_id": ""
    },

    "bank": {
        "name":         "Inst name",
        "company_id":   "",
        "bic":          "BIC code",
        "streetno":     "",
        "town":         "",
        "zipcode":      ""
    }
}

# This is a row of TransferWise account statement
class StatementRow:
    transferwise_id       = None
    date                  = None
    amount                = None
    currency              = None
    description           = None
    payment_reference     = None
    running_balance       = None
    exchange_from         = None
    exchange_to           = None
    exchange_rate         = None
    payer_name            = None
    payee_name            = None
    payee_account_number  = None
    merchant              = None
    total_fees            = None

# Parses a row in the CSV file and returns a Transfer
def parse_row(row):
    i = 0;
    tr = StatementRow()
    for field in csv_header:
        setattr(tr, field, row[i])
        i = i + 1
    return tr


# Sanitize CSV field name to match 'Transfer' class member names
def sanitize_field_name(name):
    return name.replace(' ', '_').lower()

def add_property(parent, key, value):
    prop = ET.SubElement(parent, key)
    prop.text = value
    return prop

def other_set_coid(parent, coid_value):
    other = ET.SubElement(parent, "Othr")
    add_property(other, "Id", coid_value)
    add_property(ET.SubElement(other, "SchmeNm"), "Cd", "COID")


def set_balance(bal, cd_type, date, currency, amount):
    add_property(ET.SubElement(ET.SubElement(bal, "Tp"), "CdOrPrty"), "Cd", "OPBD")

    amt = add_property(bal, "Amt", amount)
    amt.set('Ccy', currency)

    add_property(bal, "CdtDbtInd", cd_type)
    add_property(ET.SubElement(bal, "Dt"), "Dt", date)

def account_set_owner(account, name, reg_no):
    owner = ET.SubElement(account, "Ownr")
    add_property(owner, "Nm", name)
    org_id = ET.SubElement(ET.SubElement(owner, "Id"), "OrgId")
    other_set_coid(org_id, reg_no)

def set_enties(parent, entries_count, total_amount):
    add_property(parent, "NbOfNtries", entries_count)
    add_property(parent, "Sum", total_amount)


if len(sys.argv) < 3:
    print("Usage: {cmd_name} <csv-input> <xml-output>".format(cmd_name=sys.argv[0]))
    exit(1)


document = ET.Element("Document")
document.set("xmlns", "urn:iso:std:iso:20022:tech:xsd:camt.053.001.02")
document.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
document.set("xsi:schemaLocation", "urn:iso:std:iso:20022:tech:xsd:camt.053.001.02 camt.053.001.02.xsd")

# Bank to customer statement

statement    = ET.SubElement(document, "BkToCstmrStmt")

# writing statement header

stmt_header = ET.SubElement(statement, "GrpHdr")
add_property(stmt_header, "MsgId", "{msg_id}")
add_property(stmt_header, "CreDtTm", "{created_date_time}")

# writing statement body

stmt_body = ET.SubElement(statement, "Stmt")
add_property(stmt_body, "Id", "{Id}")
add_property(stmt_body, "CreDtTm", "{created_date_time}")

# from date to date
from_to_date = ET.SubElement(stmt_body, "FrToDt")
add_property(from_to_date, "FrDtTm", "{from}")
add_property(from_to_date, "ToDtTm", "{to}")

# account
account = ET.SubElement(stmt_body, "Acct")
add_property(ET.SubElement(account, "Id"), "IBAN", config["account"]["iban"])
add_property(account, "Ccy", config["account"]["currency"])

account_set_owner(account, config["account"]["owner_name"], config["account"]["company_id"])


# financial institution data
fin_inst = ET.SubElement(ET.SubElement(account, "Svcr"), "FinInstnId")
add_property(fin_inst, "BIC", config["bank"]["bic"])
add_property(fin_inst, "Nm", config["bank"]["name"])

postal_address = ET.SubElement(fin_inst, "PstlAdr")
add_property(postal_address, "StrtNm", config["bank"]["streetno"])
add_property(postal_address, "PstCd", config["bank"]["zipcode"])
add_property(postal_address, "TwnNm", config["bank"]["zipcode"])

other_set_coid(fin_inst, config["bank"]["company_id"])

start_bal = ET.SubElement(stmt_body, "Bal")
set_balance(start_bal, "CRDT", "date", config["account"]["currency"], 0.00)

end_bal = ET.SubElement(stmt_body, "Bal")
set_balance(end_bal, "CRDT", "date", config["account"]["currency"], 0.00)

summary = ET.SubElement(stmt_body, "TxsSummry")

add_property(ET.SubElement(summary, "TtlNtries"), "NbOfNtries", "nb of entries")
credit_entries = ET.SubElement(summary, "TtlCdtNtries")
debit_entries = ET.SubElement(summary, "TtlDbtNtries")

set_enties(credit_entries, "number of entries", 0.00)
set_enties(debit_entries, "number of entries", 0.00)

entry = ET.SubElement(stmt_body, "Ntry")
amount = add_property(entry, "Amt", "0.00")
amount.set("Ccy", config["account"]["currency"])

add_property(entry, "CdtDbtInd", "CRDT")

add_property(entry, "Sts", "BOOK")
add_property(ET.SubElement(entry, "BookgDt"), "DtTm", "datetime")
add_property(ET.SubElement(entry, "ValDt"), "DtTm", "datetime")

domn = ET.SubElement(ET.SubElement(entry, "BkTxCd"), "Domn")
add_property(domn, "Cd", "PMNT")
fmly = ET.SubElement(domn, "Fmly")

add_property(fmly, "Cd", "RCDT")
add_property(fmly, "SubFmlyCd", "OTHR")

tx_details = ET.SubElement(ET.SubElement(entry, "NtryDtls"), "TxDtls")
refs = ET.SubElement(tx_details, "Refs")

add_property(refs, "AcctSvcrRef", "{ref}")
add_property(refs, "TxId", "{txid}")

ET.SubElement(tx_details, "RltdPties")
ET.SubElement(tx_details, "RltdAgts")
ET.SubElement(tx_details, "RmtInf")



# Dump the output to a file
xmlstr = xml.dom.minidom.parseString(ET.tostring(document)).toprettyxml(indent="   ")
with open(sys.argv[2], "w") as f:
    f.write(xmlstr)


# Start CSV parsing

is_header = True
csv_header    = None
with open(sys.argv[1], 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for row in reader:
        if is_header:
            csv_header = map(sanitize_field_name, row)
            is_header = False
        else:
            print(row)
            tr = parse_row(row)
            print(tr.__dict__)
            print('')
            print('')

