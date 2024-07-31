import requests
import json
import os
import base64
import re
import time
import csv

def send_email(access_token, email_data, save_to_sent_items=True):
    send_mail_url = "https://graph.microsoft.com/v1.0/me/sendMail"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    payload = {
        "message": email_data,
        "saveToSentItems": save_to_sent_items
    }

    response = requests.post(send_mail_url, headers=headers, json=payload)
    current_time = os.popen('date "+%m/%d/%Y %I:%M %p"').read().strip()

    if response.status_code == 202:
        message_id = response.headers.get("message-id")
        print(f'[+] {current_time}: Sent email to {email_data["toRecipients"][0]["emailAddress"]["address"]}')
        return message_id
    elif response.status_code == 403:
        print('403 Forbidden: Access denied. Check API permissions and ensure necessary consent has been granted.')
        return None
    else:
        print(f'Failed to send email to {email_data["toRecipients"][0]["emailAddress"]["address"]}')
        print("Response code:", response.status_code)
        print("Response message:", response.text)
        return None

def save_draft(access_token, email_data):
    save_draft_url = "https://graph.microsoft.com/v1.0/me/messages"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    response = requests.post(save_draft_url, headers=headers, data=json.dumps(email_data))
    current_time = os.popen('date "+%m/%d/%Y %I:%M %p"').read().strip()

    if response.status_code == 201:
        print(f'[+] {current_time}: Email saved as draft for {email_data["toRecipients"][0]["emailAddress"]["address"]}')
    elif response.status_code == 403:
        print('403 Forbidden: Access denied. Check API permissions and ensure necessary consent has been granted.')
    else:
        print(f'Failed to save email as draft for {email_data["toRecipients"][0]["emailAddress"]["address"]}')
        print("Response code:", response.status_code)
        print("Response message:", response.text)

def send_all_drafts(access_token, args):
    drafts_url = "https://graph.microsoft.com/v1.0/me/mailFolders('Drafts')/messages?$filter=isDraft eq true"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    response = requests.get(drafts_url, headers=headers)

    if response.status_code == 200:
        drafts_data = response.json()
        drafts = drafts_data.get("value", [])

        if not drafts:
            print("No drafts found in the Drafts folder.")
            return

        for draft in drafts:
            draft_id = draft.get("id")
            send_draft_url = f"https://graph.microsoft.com/v1.0/me/messages/{draft_id}/send"

            send_response = requests.post(send_draft_url, headers=headers)
            current_time = os.popen('date "+%m/%d/%Y %I:%M %p"').read().strip()

            if send_response.status_code == 202:
                print(f'[+] {current_time}: Draft {draft_id} sent successfully')
            else:
                print(f'Failed to send draft {draft_id}')
                print("Response code:", send_response.status_code)
                print("Response message:", send_response.text)
    else:
        print("Failed to retrieve drafts.")
        print("Response code:", response.status_code)
        print("Response message:", response.text)

def read_inbox(access_token, args):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    inbox_url = f"https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages?$top={args.number}"
    response = requests.get(inbox_url, headers=headers)

    if response.status_code == 200:
        emails = response.json().get('value', [])
        for i, email in enumerate(emails):
            print(f"ID: {email['id']}")
            print(f"From: {email['from']['emailAddress']['name']} <{email['from']['emailAddress']['address']}>")
            print(f"Subject: {email['subject']}")
            print(f"Preview: {email['bodyPreview']}")
            print("-" * 40)
    else:
        print("Failed to retrieve emails.")
        print("Response code:", response.status_code)
        print("Response message:", response.text)

def read_email(access_token, args):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    email_id = args.email_id
    email_url = f"https://graph.microsoft.com/v1.0/me/messages/{email_id}"
    response = requests.get(email_url, headers=headers)

    if response.status_code == 200:
        email = response.json()
        print(f"ID: {email['id']}")
        print(f"From: {email['from']['emailAddress']['name']} <{email['from']['emailAddress']['address']}>")
        print(f"Subject: {email['subject']}")
        print(f"Body: {email['body']['content']}")
    else:
        print("Failed to retrieve the email.")
        print("Response code:", response.status_code)
        print("Response message:", response.text)

def search_inbox(access_token, args):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    search_url = f"https://graph.microsoft.com/v1.0/me/messages?$search=\"{args.keyword}\""
    response = requests.get(search_url, headers=headers)

    if response.status_code == 200:
        emails = response.json().get('value', [])
        for i, email in enumerate(emails):
            print(f"ID: {email['id']}")
            print(f"From: {email['from']['emailAddress']['name']} <{email['from']['emailAddress']['address']}>")
            print(f"Subject: {email['subject']}")
            print(f"Preview: {email['bodyPreview']}")
            print("-" * 40)
    else:
        print("Failed to retrieve emails.")
        print("Response code:", response.status_code)
        print("Response message:", response.text)

def create_event(access_token, subject, body, start_datetime, end_datetime, attendees):
    create_event_url = "https://graph.microsoft.com/v1.0/me/events"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    event_data = {
        "subject": subject,
        "body": {
            "contentType": "HTML",
            "content": body  #body is a plain HTML string
        },
        "start": {
            "dateTime": start_datetime,
            "timeZone": "UTC"
        },
        "end": {
            "dateTime": end_datetime,
            "timeZone": "UTC"
        },
        "attendees": [{"emailAddress": {"address": email}, "type": "required"} for email in attendees],
        "location": {
            "displayName": "Online"
        }
    }
    response = requests.post(create_event_url, headers=headers, json=event_data)
    current_time = os.popen('date "+%m/%d/%Y %I:%M %p"').read().strip()

    if response.status_code == 201:
        event_id = response.json().get("id")
        print(f'[+] {current_time}: Created event with ID: {event_id}')
        return event_id
    else:
        print(f'Failed to create event. Status code: {response.status_code}')
        print(f'Response: {response.text}')
        return None

def cancel_event(access_token, event_id):
    delete_event_url = f"https://graph.microsoft.com/v1.0/me/events/{event_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    response = requests.delete(delete_event_url, headers=headers)
    current_time = os.popen('date "+%m/%d/%Y %I:%M %p"').read().strip()

    if response.status_code == 204:
        print(f'[+] {current_time}: Cancelled event with ID: {event_id}')
    else:
        print(f'Failed to cancel event. Status code: {response.status_code}')
        print(f'Response: {response.text}')