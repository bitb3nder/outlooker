import argparse
import os
import json
import csv
import time
from auth import graph_auth, device_code_auth
from inbox_operations import *

def list_templates():
    templates_path = os.path.join(os.path.dirname(__file__), 'templates', 'templates_metadata.json')
    with open(templates_path, 'r') as f:
        templates = json.load(f)
    
    for shortname, details in templates.items():
        print(f"\n--Template: {shortname}")
        print(f"    Filename: {details['filename']}")
        print(f"    Fields: {', '.join(details['fields'])}")
        print(f"    Description: {details['description']}")
        print(f"    Category: {details['category']}\n")

def load_templates_metadata():
    templates_path = os.path.join(os.path.dirname(__file__), 'templates', 'templates_metadata.json')
    with open(templates_path, 'r') as f:
        templates_metadata = json.load(f)
    return templates_metadata

def read_template_file(template_filename):
    template_path = os.path.join(os.path.dirname(__file__), 'templates', template_filename)
    with open(template_path, 'r') as template_file:
        template_content = template_file.read()
    return template_content

def add_template(args):
    template_filename = args.template
    template_path = os.path.join(os.path.dirname(__file__), 'templates', template_filename)
    
    if not os.path.exists(template_path):
        print(f"Error: Template file {template_filename} not found.")
        return
    
    with open(template_path, 'r') as template_file:
        template_content = template_file.read()
    
    placeholders = re.findall(r'{\.(\w+)}', template_content)
    fields = ["email"] + list(set(placeholders))  
    
    new_template_metadata = {
        args.name: {
            "filename": template_filename,
            "fields": fields,
            "description": args.description,
            "category": args.category
        }
    }
    
    templates_metadata_path = os.path.join(os.path.dirname(__file__), 'templates', 'templates_metadata.json')
    with open(templates_metadata_path, 'r+') as f:
        templates_metadata = json.load(f)
        templates_metadata.update(new_template_metadata)
        f.seek(0)
        json.dump(templates_metadata, f, indent=4)
    
    print(f"[+] Template {args.name} added successfully.")

def build_email(template_name, user_data, template_content, subject, attachment=None):
    for key, value in user_data.items():
        template_content = template_content.replace(f"{{.{key}}}", value)

    email_data = {
        "subject": subject,
        "body": {
            "contentType": "HTML",
            "content": template_content
        },
        "toRecipients": [
            {
                "emailAddress": {
                    "address": user_data['email']
                }
            }
        ]
    }

    if attachment:
        email_data['attachments'] = [attachment]

    return email_data

def send_emails(access_token, args):
    user_list_path = args.user_list
    templates_metadata = load_templates_metadata()

    with open(user_list_path, "r") as user_list_file:
        reader = csv.reader(user_list_file)
        rows = list(reader)

        for row in rows:
            template_name = args.template
            if template_name not in templates_metadata:
                print(f"Template {template_name} not found in templates metadata.")
                continue

            template_details = templates_metadata[template_name]
            required_fields = template_details.get('fields', [])

            if len(required_fields) > len(row):
                print(f"Error: Insufficient data in row for template {template_name}.")
                continue

            user_data = {field: value for field, value in zip(required_fields, row)}

            try:
                template_content = read_template_file(template_details['filename'])

                email_data = build_email(template_name, user_data, template_content, args.subject, args.attachment)

                save_to_sent_items = not args.delete_on_send
                message_id = send_email(access_token, email_data, save_to_sent_items=save_to_sent_items)

            except FileNotFoundError:
                print(f"Error: Template file {template_details['filename']} not found.")
            except ValueError as e:
                print(f"Error: {e}")

            time.sleep(args.sleep)

def save_drafts(access_token, args):
    user_list_path = args.user_list
    templates_metadata = load_templates_metadata()

    with open(user_list_path, "r") as user_list_file:
        reader = csv.reader(user_list_file)
        rows = list(reader)

        for row in rows:
            template_name = args.template
            if template_name not in templates_metadata:
                print(f"Template {template_name} not found in templates metadata.")
                continue

            template_details = templates_metadata[template_name]
            required_fields = template_details.get('fields', [])

            if len(required_fields) > len(row):
                print(f"Error: Insufficient data in row for template {template_name}.")
                continue

            user_data = {field: value for field, value in zip(required_fields, row)}

            try:
                template_content = read_template_file(template_details['filename'])

                email_data = build_email(template_name, user_data, template_content, args.subject, args.attachment)

                save_draft(access_token, email_data)

            except FileNotFoundError:
                print(f"Error: Template file {template_details['filename']} not found.")
            except ValueError as e:
                print(f"Error: {e}")

def send_invites(access_token, args):
    user_list_path = args.user_list
    templates_metadata = load_templates_metadata()
    try:
        with open(user_list_path, "r") as user_list_file:
            reader = csv.reader(user_list_file)
            rows = list(reader)

            for row in rows:
                template_name = args.template
                if template_name not in templates_metadata:
                    print(f"Template {template_name} not found in templates metadata.")
                    continue

                template_details = templates_metadata[template_name]
                required_fields = template_details.get('fields', [])

                if len(required_fields) > len(row):
                    print(f"Error: Insufficient data in row for template {template_name}.")
                    continue

                user_data = {field: value for field, value in zip(required_fields, row)}

                try:
                    template_content = read_template_file(template_details['filename'])

                    start_datetime = args.start_datetime
                    end_datetime = args.end_datetime

                    event_id = create_event(access_token, args.subject, template_content, start_datetime, end_datetime, [user_data['email']])

                    if event_id and args.delete_on_send:
                        # Cancel event if --delete-on-send flag is provided
                        cancel_event(access_token, event_id)

                    time.sleep(args.sleep)

                except FileNotFoundError:
                    print(f"Error: Template file {template_details['filename']} not found.")
                except ValueError as e:
                    print(f"Error: {e}")
                except Exception as ex:
                    print(f"Failed to create event: {str(ex)}")

    except IOError as ioe:
        print(f"Error opening user list file: {str(ioe)}")
    except Exception as ex:
        print(f"Unhandled exception: {str(ex)}")

def main():
    parser = argparse.ArgumentParser(description="Sending email campaigns through the Graph API")
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    send_parser = subparsers.add_parser('send', help='Launch an email campaign')
    send_parser.add_argument("-uL", "--user-list", help="Campaign target list file (CSV format: email,firstname,id,step)", required=True)
    send_parser.add_argument("-s", "--subject", help="Email subject line", required=True)
    send_parser.add_argument("-t", "--template", help="HTML template file (use shortname specified in template_metadata.json)", required=True)
    send_parser.add_argument("-a", "--attachment", help="Attachment file", required=False, default="")
    send_parser.add_argument("-e", "--email", help="Email used for authentication", required=False)
    send_parser.add_argument("-p", "--password", help="Password for authentication", required=False)
    send_parser.add_argument("-tid", "--tenant-id", help="Azure Tenant ID", required=False)
    send_parser.add_argument("-at", "--access-token", help="Access Token for authentication", required=False)
    send_parser.add_argument("-rt", "--refresh-token", help="Refresh Token for authentication", required=False)
    send_parser.add_argument("--delete-on-send", action="store_true", help="Delete email from Sent Items after sending")
    send_parser.add_argument("--sleep", type=int, help="Sleep time between actions (in seconds)", required=False, default=0)

    '''
    save_draft_parser = subparsers.add_parser('savedrafts', help='Save campaign to the drafts folder')
    save_draft_parser.add_argument("-uL", "--user-list", help="User list file (CSV format: email,firstname,id,step)", required=True)
    save_draft_parser.add_argument("-s", "--subject", help="Email subject line", required=True)
    save_draft_parser.add_argument("-t", "--template", help="HTML template file (use shortname specified in template_metadata.json)", required=True)
    save_draft_parser.add_argument("-a", "--attachment", help="Attachment file", required=False, default="")
    save_draft_parser.add_argument("-e", "--email", help="Email used for authentication", required=False)
    save_draft_parser.add_argument("-p", "--password", help="Password for authentication", required=False)
    save_draft_parser.add_argument("-tid", "--tenant-id", help="Azure Tenant ID", required=False)
    save_draft_parser.add_argument("-at", "--access-token", help="Access Token for authentication", required=False)
    save_draft_parser.add_argument("-rt", "--refresh-token", help="Refresh Token for authentication", required=False)

    send_draft_parser = subparsers.add_parser('senddrafts', help='Send all drafted emails')
    send_draft_parser.add_argument("-e", "--email", help="Email used for authentication", required=False)
    send_draft_parser.add_argument("-p", "--password", help="Password for authentication", required=False)
    send_draft_parser.add_argument("-tid", "--tenant-id", help="Azure Tenant ID", required=False)
    send_draft_parser.add_argument("-at", "--access-token", help="Access Token for authentication", required=False)
    send_draft_parser.add_argument("-rt", "--refresh-token", help="Refresh Token for authentication", required=False)
    '''

    read_parser = subparsers.add_parser('read', help='Read emails from the user\'s inbox (won\'t mark as read)')
    read_parser.add_argument("-e", "--email", help="Email used for authentication", required=False)
    read_parser.add_argument("-p", "--password", help="Password for authentication", required=False)
    read_parser.add_argument("-tid", "--tenant-id", help="Azure Tenant ID", required=False)
    read_parser.add_argument("-at", "--access-token", help="Access Token for authentication", required=False)
    read_parser.add_argument("-n", "--number", type=int, help="Number of emails to retrieve", required=False, default=10)
    read_parser.add_argument("-id", "--email-id", help="ID of the email to read in detail", required=False)

    search_parser = subparsers.add_parser('search', help='Search for emails from the user\'s inbox by keyword')
    search_parser.add_argument("-e", "--email", help="Email used for authentication", required=False)
    search_parser.add_argument("-p", "--password", help="Password for authentication", required=False)
    search_parser.add_argument("-tid", "--tenant-id", help="Azure Tenant ID", required=False)
    search_parser.add_argument("-at", "--access-token", help="Access Token for authentication", required=False)
    search_parser.add_argument("-k", "--keyword", help="Keyword to search for", required=True)
    search_parser.add_argument("-id", "--email-id", help="ID of the email to read in detail", required=False)
    
    invite_parser = subparsers.add_parser('sendinvites', help='Send calendar invites')
    invite_parser.add_argument("-uL", "--user-list", help="User list file (CSV format: email,firstname,id,step)", required=True)
    invite_parser.add_argument("-s", "--subject", help="Event subject", required=True)
    invite_parser.add_argument("-t", "--template", help="HTML template file (use shortname specified in template_metadata.json)", required=True)
    invite_parser.add_argument("-a", "--attachment", help="Attachment file", required=False, default="")
    invite_parser.add_argument("-e", "--email", help="Email used for authentication", required=False)
    invite_parser.add_argument("-p", "--password", help="Password for authentication", required=False)
    invite_parser.add_argument("-tid", "--tenant-id", help="Azure Tenant ID", required=False)
    invite_parser.add_argument("-at", "--access-token", help="Access Token for authentication", required=False)
    invite_parser.add_argument("-rt", "--refresh-token", help="Refresh Token for authentication", required=False)
    invite_parser.add_argument("--start-datetime", help="Start date and time for the event (ISO 8601 format)", required=True)
    invite_parser.add_argument("--end-datetime", help="End date and time for the event (ISO 8601 format)", required=True)
    invite_parser.add_argument("--delete-on-send", action="store_true", help="Delete the event after sending")
    invite_parser.add_argument("--sleep", type=int, help="Sleep time between actions (in seconds)", required=False, default=0)

    list_parser = subparsers.add_parser('list', help='List templates')

    add_template_parser = subparsers.add_parser('addtemplate', help='Add script support for a custom HTML template')
    add_template_parser.add_argument("-t", "--template", help="Full filename of the .html file in the /templates directory", required=True)
    add_template_parser.add_argument("-n", "--name", help="Short name to reference the template by", required=True)
    add_template_parser.add_argument("-d", "--description", help="Brief description of what the template aims to do", required=True)
    add_template_parser.add_argument("-c", "--category", help="Category for the template (e.g., Payload, Malicious Links, Spam)", required=True)


    auth_parser = subparsers.add_parser('devicecode', help='Authenticate using device code flow')

    args = parser.parse_args()

    if args.command == 'send':
        access_token = args.access_token or graph_auth(args)
        send_emails(access_token, args)
    elif args.command == 'list':
        list_templates()
    elif args.command == 'devicecode':
        device_code_auth()
    elif args.command == 'read':
        if args.email_id:
            access_token = graph_auth(args)
            read_email(access_token, args)
        else:
            access_token = graph_auth(args)
            read_inbox(access_token, args)
    elif args.command == 'search':
        if args.email_id:
            access_token = graph_auth(args)
            read_email(access_token, args)
        else:
            access_token = graph_auth(args)
            search_inbox(access_token, args)
    elif args.command == 'sendinvites':
        access_token = args.access_token or graph_auth(args)
        send_invites(access_token, args)
    elif args.command == 'addtemplate':
        add_template(args)

if __name__ == "__main__":
    main()
