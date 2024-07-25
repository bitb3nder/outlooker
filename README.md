# Outlooker

## Overview
Outlooker is a bad python script used to automate sending emails from a template with an attachment via https://graph.microsoft.com/v1.0/me/sendMail.

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Usage](#usage)
- [Working With Templates](#working-with-templates)
- [Building A Campaign](#building-a-campaign)
- [Launching A Campaign](#launching-a-campaign)
- [Authentication](#authentication)
- [Inbox Interactions](#inbox-interactions)
- [Other Modules](#other-modules)
- [To-Do's](#to-dos)
- [Quick Commands](#quick-commands)

## Installation
```
git clone git@github.com:bitb3nder/outlooker.git && cd outlooker
python3 -m venv outlooker-venv && source outlooker-venv/bin/activate
python3 -m pip install -r requirements.txt
python3 outlooker.py -h
```

## Usage 
```
usage: outlooker.py [-h] {send,read,search,sendinvites,list,devicecode} ...

Sending email campaigns through the Graph API

positional arguments:
  {send,read,search,sendinvites,list,devicecode}
                        Command to execute
    send                Launch an email campaign
    read                Read emails from the user's inbox (won't mark as read)
    search              Search for emails from the user's inbox by keyword
    sendinvites         Launch a calendar invite campaign
    list                List available templates
    addtemplate         Add script support for a custom HTML template
    devicecode          Authenticate using device code flow

optional arguments:
  -h, --help            show this help message and exit
```

## Working With Templates
List loaded templates with
```
python3 outlooker.py list
```

HTML Templates are located in the `/templates` directory. All currently implemented templates are indexed in the `/templates/templates_metadata.json` file with the following structure:
```
{
  "test": {
    "filename": "test.html",
    "fields": ["email", "firstname"],
    "description": "Simple HTML to test landing in the inbox",
    "category": "Spam"
  }
}
```
To create a new HTML template, simply generate the HTML for the template with placeholder fields and place the file in the `/templates` directory. Fields in templates are completely customizable and are denoted with the `{.field}` syntax in the html content. The `addtemplate` module can then be called to account for the new template:
```
usage: outlooker.py addtemplate [-h] -t TEMPLATE -n NAME -d DESCRIPTION -c CATEGORY

optional arguments:
  -h, --help            show this help message and exit
  -t TEMPLATE, --template TEMPLATE
                        Full filename of the .html file in the /templates directory
  -n NAME, --name NAME  Short name to reference the template by
  -d DESCRIPTION, --description DESCRIPTION
                        Brief description of what the template aims to do
  -c CATEGORY, --category CATEGORY
                        Category for the template (e.g., Payload, Malicious Links, Spam)
```

> [!NOTE]  
> The `email` field should automatically prepend to the list of fields, as this is required by every campaign.

## Building A Campaign
After determining a template, the fields array will serve as the structure for the .csv file that will determine the variables of the emails sent. In the above example for `test.html`, there are only two fields, email and firstname. The firstname field is dynamic content loaded into the html body of the email. The resulting .csv for a `test` campaign should look like:
```
ash.ketchum@example.com,Ash
misty.waters@example.com,Misty
samuel.oak@example.com,Sam
```

## Launching A Campaign
After creating a template and building the campaign csv, Outlookers `send` module will send the emails via the Graph API. The send module supports specification of a subject line and an attachment, as well as multiple forms of authentication (email/password, Graph Access Token).

> [!TIP] 
> To throttle the rate at which emails are sent, use the `--sleep` flag, and the `--delete-on-send` will prevent the email from staying in the Sent folder, which is useful for internal phishing campaigns.

```
usage: outlooker.py send [-h] -uL USER_LIST -s SUBJECT -t TEMPLATE [-a ATTACHMENT] [-e EMAIL] [-p PASSWORD] [-tid TENANT_ID] [-at ACCESS_TOKEN]
                         [--delete-on-send] [--sleep SLEEP]

send arguments:
  -h, --help            show this help message and exit
  -uL USER_LIST         user list file (CSV formatted per template guidance)
  -s SUBJECT            email subject line
  -t TEMPLATE           html template file
  -a ATTACHMENT         attachment file
  -e EMAIL              email used for authentication
  -p PASSWORD           auth emails password
  -at ACCESS_TOKEN      access token instead of username/password combination
  -tid TENANT_ID        manually specify a tenant_id (script will attempt to obtain)
  --delete-on-send      removes the sent mail from the user's sent box (stealth??)
  --sleep SLEEP         time between sending emails (in seconds)
```

> [!IMPORTANT]  
> If instead of sending the emails out all at once you'd rather save the campain to the drafts folder, use the `savedrafts` module with the same syntax to do so. Sending all the emails from the drafts folder is accomplished with the `senddrafts` module. 

## Authentication
This script supports multiple methods of authentication to allow for multiple use-cases for campaigns using controlled accounts or compromised ones. The `devicecode` module is the most robust, allowing for authentication through the device code authentication flow which accounts for multi-factor authentication. The resulting refresh token will be stored in a file called `.auth_token` and will be sourced first when attempting to authenticate to the graph API. 

Additionally, a simple email and password combination are supported, as well as supplying a Graph scoped `--refresh-token` or `--access-token` as command line arguments. This will be useful in scenarios where such a token is taken from a target and the password is not known.

## Inbox Interactions
While not as robust as some [other](https://github.com/dafthack/GraphRunner) post-exploitation Outlook toolkits, Outlooker does offer some functionality to assist with reading inboxes and searching inboxes of users, which is useful when authenticating with a stolen token. 
```
usage: outlooker.py read [-h] [-e EMAIL] [-p PASSWORD] [-tid TENANT_ID] [-at ACCESS_TOKEN] [-n NUMBER] [-id EMAIL_ID]
usage: outlooker.py search [-h] [-e EMAIL] [-p PASSWORD] [-tid TENANT_ID] [-at ACCESS_TOKEN] -k KEYWORD [-id EMAIL_ID]

optional arguments:
  -h, --help            show this help message and exit
  -e EMAIL, --email EMAIL
                        Email used for authentication
  -p PASSWORD, --password PASSWORD
                        Password for authentication
  -tid TENANT_ID, --tenant-id TENANT_ID
                        Azure Tenant ID
  -at ACCESS_TOKEN, --access-token ACCESS_TOKEN
                        Access Token for authentication
  -n NUMBER, --number NUMBER
                        Number of emails to retrieve
  -id EMAIL_ID, --email-id EMAIL_ID
                        ID of the email to read in detail
  -k KEYWORD, --keyword KEYWORD
                        Term to search the inbox for 
```
## Other Modules
Currently Outlooker supports the sending and prompt deletion of Outlook calender invites (which are often overlooked when promptly cancelled) for the purpose of recieving Out of Office automatic replies. 
```
usage: outlooker.py ooohunt [-h] -uL USER_LIST -s SUBJECT -t TEMPLATE -sd START_DATETIME -ed END_DATETIME [-e EMAIL] [-p PASSWORD] [-tid TENANT_ID] [-at ACCESS_TOKEN] [--delete-on-send] [--sleep SLEEP]
example: python3 outlooker.py ooohunt -uL ./campaigns/bypass_campaign_example.txt -s "Meeting" -t bypass -sd "2024-07-01T10:00:00" -ed "2024-07-01T11:00:00" -e user@example.com -p password --delete-on-send --sleep 2

optional arguments:
  -h, --help            show this help message and exit
  -uL USER_LIST, --user-list USER_LIST
                        User list file (CSV format: email,firstname,id,step)
  -s SUBJECT, --subject SUBJECT
                        Calendar invite subject line
  -t TEMPLATE, --template TEMPLATE
                        HTML template file (use shortname specified in template_metadata.json)
  -sd START_DATETIME, --start-datetime START_DATETIME
                        Start datetime of the event (format: YYYY-MM-DDTHH:MM:SS)
  -ed END_DATETIME, --end-datetime END_DATETIME
                        End datetime of the event (format: YYYY-MM-DDTHH:MM:SS)
  -e EMAIL, --email EMAIL
                        Email used for authentication
  -p PASSWORD, --password PASSWORD
                        Password for authentication
  -tid TENANT_ID, --tenant-id TENANT_ID
                        Azure Tenant ID
  -at ACCESS_TOKEN, --access-token ACCESS_TOKEN
                        Access Token for authentication
  --delete-on-send      Cancel event after sending
  --sleep SLEEP         Sleep time between actions (in seconds)
```
> [!CAUTION]
> The `--delete-on-send` flag is required to remove the calender invite upon sending. In the future, may switch to don't delete but for now just include it.

## To Do's
- add quick commands

## Quick Commands
- see todo's
