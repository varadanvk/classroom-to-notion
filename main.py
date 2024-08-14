import os
import json
from dotenv import load_dotenv
from services.classroom import ClassroomDataManager
from services.notion import NotionDatabaseManager

def main():
    load_dotenv()
    cdm = ClassroomDataManager()
    ndm = NotionDatabaseManager(database_id=os.environ.get('NOTION_DATABASE_ID'), token=os.environ.get('NOTION_TOKEN'))
    filter_criteria = {
    'From': 'no-reply@classroom.google.com',
    'Subject': 'New assignment'
    }
    
    try: 
        with open('outputs/classroom_data.json', 'r') as file:
            cache = json.load(file)
    except FileNotFoundError:
        cache = []
    
    if len(cache) == 0:
        messages = cdm.run(max_results=20, filter_criteria=filter_criteria)
    elif cache[0]['id'] == cdm.run(max_results=2, filter_criteria=filter_criteria)[0]['id']:
        print('No new messages. Using cache for data')
        messages = cache
    else:
        messages = cdm.run(max_results=20, filter_criteria=filter_criteria)    
        print(messages)
        cdm.save_to_json(messages, 'outputs/classroom_data.json')

    #Filter Messages
    filtered_messages = cdm.filter_messages(messages)
    cdm.save_to_json(filtered_messages, 'outputs/filtered_classroom_data.json')
    
    #Extract assignment info
    extracted_data = cdm.extract_assignment_info(filtered_messages)
    cdm.save_to_json(extracted_data, 'outputs/extracted_classroom_data.json')
    
    
    #TODO: Use notion service to have user input for class names based on teacher that posts the assignment
    #assignments = [ndm.parse_assignments(assignment) for assignment in extracted_data]
    for assignment_data in extracted_data:
        parsed_data = ndm.parse_assignments(assignment_data=assignment_data)
        response = ndm.post_data(parsed_data)
        print(response)  # Optional: print the response to verify success
    
    
    
main()