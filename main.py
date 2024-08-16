import os
import json
import logging
from dotenv import load_dotenv
from services.classroom import ClassroomDataManager
from services.notion import NotionDatabaseManager
from services.assignment_parser import AssignmentParser
from services.cache_manager import NotionCache
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(filename='classroom_to_notion.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def load_json_file(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read().strip()
            if content:
                return json.loads(content)
            else:
                logging.warning(f"File {file_path} is empty. Returning an empty list.")
                return []
    except FileNotFoundError:
        logging.info(f"File {file_path} not found. Returning an empty list.")
        return []
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from {file_path}. Returning an empty list.")
        return []

def query_database(database_id: str, statuses: List[str]) -> Dict[str, Any]:
    ndm = NotionDatabaseManager(database_id)
    cdm = ClassroomDataManager()
    results = ndm.get_tasks_by_status(statuses)
    print(json.dumps(results, indent=2))
    cdm.save_to_json(results, 'outputs/notion_results.json')
    return results

def load_activities():
    load_dotenv()
    ndm = NotionDatabaseManager(database_id=os.getenv("ACTIVITIES_DATABASE_ID"), token=os.getenv('NOTION_TOKEN'))
    cdm = ClassroomDataManager()
    response = query_database(database_id=os.getenv("ACTIVITIES_DATABASE_ID"), statuses=['In Progress'])

    with open('outputs/notion_results.json', 'w') as file:
        json.dump(response, file, indent=2)
    
    return response

def main():
    try:
        load_dotenv()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cdm = ClassroomDataManager()
        ndm = NotionDatabaseManager(database_id=os.environ.get('NOTION_DATABASE_ID'), token=os.environ.get('NOTION_TOKEN'))
        notion_cache = NotionCache()
        
        # Load activities
        activities = load_activities()
        
        # Initialize AssignmentParser with loaded activities
        ap = AssignmentParser(activities)
        
        filter_criteria = {
            'From': 'no-reply@classroom.google.com',
            'Subject': 'New assignment'
        }
        
        email_cache = load_json_file('outputs/classroom_data.json')
        
        if len(email_cache) == 0:
            logging.info("Cache is empty, running service")
            messages = cdm.run(max_results=20, filter_criteria=filter_criteria)
            cdm.save_to_json(messages, 'outputs/classroom_data.json')
        elif email_cache and email_cache[0]['id'] == cdm.run(max_results=2, filter_criteria=filter_criteria)[0]['id']:
            logging.info('No new messages. Using email_cache for data')
            messages = email_cache
        else:
            messages = cdm.run(max_results=20, filter_criteria=filter_criteria)    
            logging.info(f"Retrieved {len(messages)} new messages")
            cdm.save_to_json(messages, 'outputs/classroom_data.json')

        # Filter Messages
        filtered_messages = cdm.filter_messages(messages)
        cdm.save_to_json(filtered_messages, 'outputs/filtered_classroom_data.json')
        
        # Extract assignment info
        extracted_data = cdm.extract_assignment_info(filtered_messages)
        cdm.save_to_json(extracted_data, 'outputs/extracted_classroom_data.json')
        
        # Parse and filter 
        parsed_data = ap.parse_assignments(extracted_data)
        uncached_data = notion_cache.filter_with_cache(parsed_data)
        
        # Add new assignments to Notion
        if uncached_data is None:
            logging.info("No new assignments to process")
            print("No new assignments to process")
            print("-------------------------------------------------")
            return
        else:
            responses = ndm.post_data(uncached_data)
            logging.info(f"Processed {len(responses)} new assignments")
            logging.info("Saving new assignments to cache")
            cdm.save_to_json(responses, 'outputs/new_assignments.json')
            print("-------------------------------------------------")


    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
        print(e)

if __name__ == "__main__":
    main()