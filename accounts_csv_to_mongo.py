"""
> python ./accounts_csv_to_mongo.py -f ./data.accounts.csv -t writers

required header .csv format:
login:password:proxy_ip:proxy_port:proxy_login:proxy_pass
"""
import argparse
import csv

from db.model import AccountModel
from db.mongo import MongoConnector

CSV_ROW = ['login', 'password', 'proxy_ip', 'proxy_port', 'proxy_login', 'proxy_pass']

parser = argparse.ArgumentParser()
parser.add_argument(
    "-f",
    '--file',
    required=True,
    help="path to the account csv file",
)

parser.add_argument(
    "-t",
    '--account_type',
    required=True,
    choices=['searchers', 'writers'],
    help="type of downloading accounts",
)

args = parser.parse_args()
db = MongoConnector.get_instance()

if __name__ == '__main__':
    csv_path = args.file
    account_type = args.account_type

    with open(csv_path, 'r') as csv_file:
        reader = csv.DictReader(csv_file, delimiter=':')
        reader.fieldnames = CSV_ROW
        for row in reader:
            row['messages_written'] = 0
            account = AccountModel(**row)
            db.account_connector.insert_account(
                account=account,
                account_type=account_type
            )
            print(account)
