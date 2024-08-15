from dotenv import load_dotenv
import os
import json
from typing import List, Dict, Any
from services.notion import NotionDatabaseManager

def load_activities() -> List[Dict[str, Any]]:
    load_dotenv()
    ndm = NotionDatabaseManager(database_id=os.getenv("ACTIVITIES_DATABASE_ID"), token=os.getenv('NOTION_TOKEN'))

    response = ndm.get_tasks_by_status(['In Progress'])

    # Save the full response for debugging
    with open('outputs/notion_results.json', 'w') as file:
        json.dump(response, file, indent=2)

    # Extract the actual activity data from the 'results' key
    activities = []
    if isinstance(response, dict) and 'results' in response:
        for item in response['results']:
            activity = {
                'id': item.get('id', ''),
                'title': item.get('properties', {}).get('Name', {}).get('title', [{}])[0].get('plain_text', ''),
                'teacher': ''  # Initialize teacher as empty string
            }
            activities.append(activity)
    
    # Save the extracted activities for verification
    with open('outputs/extracted_activities.json', 'w') as file:
        json.dump(activities, file, indent=2)

    return activities