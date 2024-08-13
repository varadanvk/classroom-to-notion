import os
from services.classroom import ClassroomDataManager

def main():
    service = ClassroomDataManager()
    filter_criteria = {
    'From': 'no-reply@classroom.google.com',
    'Subject': 'New assignment'
    }
    messages = service.run(max_results=30, filter_criteria=filter_criteria)    
    print(messages)
    service.save_to_json(messages, 'classroom_data.json')
    
    filtered_messages = service.filter_messages(messages)
    service.save_to_json(filtered_messages, 'filtered_classroom_data.json')
    
main()