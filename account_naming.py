import boto3
import argparse
import logging
import sys
import re

logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s %(levelname)s %(message)s',
    handlers = [
        logging.FileHandler('name_change.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# This Python function lists all enrolled accounts on an AWS Organization
def list_accounts():
    client = boto3.client('organizations')
    paginator = client.get_paginator('list_accounts')
    accounts = []
    try:
        for page in paginator.paginate():
            for account in page['Accounts']:
                accounts.append(account)
        return accounts
    except Exception as e:
        print(e)

def rename_account(org_client, account_id, new_name):
    try:
        response = org_client.update_account_name(
            AccountId=account_id,
            AccountName=new_name
        )
        return response
    except Exception as e:
        logger.Error(f'Error renaming account {account_id}')
        return None

def generate_new_name(current_name, prefix = "AWS-", suffix = "-Dev"):
    # Validate the presence of the prefix and suffix
    if current_name.startswith(prefix) and current_name.endswith(suffix):
        return current_name

    # Remove any existing prefixes that might be similar
    name_parts = current_name.split("-", 1)
    if len(name_parts) > 1:
        # Check if the first part looks like a company prefix
        if re.match(r"^[A-Za-z]+$", name_parts[0]):
            current_name = name_parts[1]

    if current_name == "escenario A":
         new_name="870570205" + current_name


    return f"{prefix}{current_name}"

def main():
    parser = argparse.ArgumentParser(
        description="Rename AWS accounts in an Organization"
    )
    parser.add_argument(
        "--prefix",
        default="ACompany-",
        help="Prefix to use for account names (default: ACompany-)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without making changes",
    )
    parser.add_argument("--profile", help="AWS profile to use")
    parser.add_argument(
        "--region", default="us-east-1", help="AWS region (default: us-east-1)"
    )
    args = parser.parse_args()

    # Create boto3 session and client
    session_kwargs = {}
    if args.profile:
        session_kwargs["profile_name"] = args.profile

    session = boto3.Session(**session_kwargs, region_name=args.region)
    org_client = session.client("organizations")
    aws_config_client = session.client("config")

    try:
        # List all accounts
        accounts = list_accounts(org_client)
        logger.info(f"Found {len(accounts)} accounts in the organization")

        # Process each account
        for account in accounts:
            account_id = account["Id"]
            current_name = account["Name"]
            new_name = generate_new_name(current_name, args.prefix)

            if current_name == new_name:
                logger.info(
                    f"Account {account_id} ({current_name}) already follows naming convention"
                )
                continue

            logger.info(
                f"Account {account_id}: Renaming from '{current_name}' to '{new_name}'"
            )

            if not args.dry_run:
                response = rename_account(org_client, account_id, new_name)
                if response:
                    logger.info(f"Successfully renamed account {account_id}")
                else:
                    logger.error(f"Failed to rename account {account_id}")
            else:
                logger.info(f"[DRY RUN] Would rename account {account_id}")

        if args.dry_run:
            logger.info("Dry run completed. No changes were made.")
        else:
            logger.info("Account renaming completed.")

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
