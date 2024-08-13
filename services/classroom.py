import os
import json
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class ClassroomDataManager:
    SCOPES = ["https://mail.google.com/"]

    def __init__(self, credentials_file="credentials.json", token_file="token.json"):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.creds = None
        self.service = None

    def save_to_json(self, data, filename):
        #if the data type is a list, we need to convert it to a dictionary
        print(f"Saving data to {filename}...")
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Data saved to {filename}")

    def authenticate(self):
        print("Starting authentication process...")
        if os.path.exists(self.token_file):
            print(f"Token file found: {self.token_file}")
            self.creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                print("Refreshing expired credentials...")
                self.creds.refresh(Request())
            else:
                print(f"Running OAuth flow with {self.credentials_file}...")
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.SCOPES)
                self.creds = flow.run_local_server(port=0)
            print("Saving new token...")
            with open(self.token_file, "w") as token:
                token.write(self.creds.to_json())

        print("Building Gmail API service...")
        self.service = build("gmail", "v1", credentials=self.creds)
        print("Authentication completed.")
        
        # Save authentication status
        auth_status = {"authenticated": self.creds is not None}

    def get_messages(self, max_results=100):
        print(f"Fetching up to {max_results} messages...")
        try:
            results = self.service.users().messages().list(userId="me", maxResults=max_results).execute()
            messages = results.get("messages", [])
            print(f"Fetched {len(messages)} messages.")
            
            # Save fetched messages
            
            return messages
        except HttpError as error:
            print(f"An error occurred while fetching messages: {error}")
            return []

    def get_message_details(self, message_id, max_retries=3, retry_delay=5):
        print(f"Fetching details for message ID: {message_id}")
        for attempt in range(max_retries):
            try:
                message = self.service.users().messages().get(userId="me", id=message_id).execute()
                print(f"Successfully fetched details for message ID: {message_id}")
                return message
            except TimeoutError as e:
                if attempt < max_retries - 1:
                    print(f"Timeout error occurred. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"Failed to fetch details for message ID: {message_id} after {max_retries} attempts.")
                    return None
            except HttpError as error:
                print(f"An error occurred while fetching message details: {error}")
                return None

    def decode_body(self, body):
        return base64.urlsafe_b64decode(body).decode("utf-8")
    
    def process_payload(self, payload):
        headers = {header['name']: header['value'] for header in payload.get('headers', [])}
        body = self.decode_body(payload.get('body', {}).get('data', ''))
        
        processed_payload = {
            'headers': headers,
            'body': body,
            'mimeType': payload.get('mimeType', ''),
            'filename': payload.get('filename', ''),
            'parts': [self.process_payload(part) for part in payload.get('parts', [])]
        }
        return processed_payload


    def process_messages(self, max_results=100, filter_criteria=None):
        messages = self.get_messages(max_results)
        print(f"Total messages fetched: {len(messages)}")

        processed_messages = []
        for message in messages:
            details = self.get_message_details(message['id'])
            if details:
                message = {
                    'id': details['id'],
                    'threadId': details['threadId'],
                    'labelIds': details.get('labelIds', []),
                    'snippet': details.get('snippet', ''),
                    'payload': self.process_payload(details.get('payload', {}))
                }
            else:
                print(f"Could not fetch details for message ID: {message['id']}")

        print(f"Total processed messages: {len(processed_messages)}")
        
        
        print(f"Total filtered messages: {len(filtered_messages)}")
        return messages
    
    
    def filter_message(self, message, criteria):
        """
        Filter a message based on the given criteria.
        
        :param message: The message to filter
        :param criteria: A dictionary of criteria to filter by
        :return: True if the message meets all criteria, False otherwise
        """
        for key, value in criteria.items():
            if key == 'from':
                from_header = next((header['value'] for header in message['payload']['headers'] if header['name'].lower() == 'from'), '')
                if value.lower() not in from_header.lower():
                    return False
            elif key == 'subject':
                subject_header = next((header['value'] for header in message['payload']['headers'] if header['name'].lower() == 'subject'), '')
                if value.lower() not in subject_header.lower():
                    return False
            elif key == 'label':
                if value not in message.get('labelIds', []):
                    return False
            # Add more criteria as needed
        return True
    
    def filter_messages(self, messages):
        """
        Filter a list of messages based on the given criteria.
        
        :param messages: The list of messages to filter
        :param criteria: A dictionary where keys are header names and values are desired header values
        :return: A list of messages that meet all criteria
        """
        filtered_messages = []
        
        for message in messages:
            if "classroom.google.com" in message['payload']['headers']['From'] and "New assignment" in message['payload']['headers']['Subject']:
                filtered_messages.append(message)
            
        return filtered_messages

    def process_messages(self, max_results=100, filter_criteria=None):
        messages = self.get_messages(max_results)
        print(f"Total messages fetched: {len(messages)}")

        processed_messages = []
        for message in messages:
            details = self.get_message_details(message['id'])
            if details:
                message = {
                    'id': details['id'],
                    'threadId': details['threadId'],
                    'labelIds': details.get('labelIds', []),
                    'snippet': details.get('snippet', ''),
                    'payload': self.process_payload(details.get('payload', {}))
                }
                processed_messages.append(message)
            else:
                print(f"Could not fetch details for message ID: {message['id']}")

        print(f"Total processed messages: {len(processed_messages)}")
        
        return processed_messages
    
    def parse_message_content(self, messages):
        content = []
        for message in messages:
            return None
    
    def run(self, max_results=100, output_file="classroom_data.json", filter_criteria=None):
        print("Starting ClassroomDataManager...")
        self.authenticate()
        processed_messages = self.process_messages(max_results, filter_criteria)
        print(processed_messages)
        if processed_messages:
            #self.save_to_json(processed_messages, output_file)
            print(f"Processed {len(processed_messages)} messages.")
            return processed_messages
        else:
            print("No messages were processed. Check the logs for errors.")
            return None

