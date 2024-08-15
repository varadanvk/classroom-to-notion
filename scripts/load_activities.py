
from dotenv import load_dotenv
import os
import json
from typing import List, Dict, Any
from services.notion import NotionDatabaseManager


def save_to_json(data, filename):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=2)

def query_database(database_id: str, statuses: List[str]) -> Dict[str, Any]:
    ndm = NotionDatabaseManager(database_id)
    results = ndm.get_tasks_by_status(statuses)
    print(json.dumps(results, indent=2))
    save_to_json(results, 'outputs/notion_results.json') #Can be removed
    return results

def load_activities():
    load_dotenv()
    ndm = NotionDatabaseManager(database_id=os.getenv("ACTIVITIES_DATABASE_ID"), token=os.getenv('NOTION_TOKEN'))
    response =  query_database(database_id=os.getenv("ACTIVITIES_DATABASE_ID"), statuses=['In Progress'])
    with open('outputs/notion_results.json', 'w') as file:
        json.dump(response, file, indent=2)
    return response