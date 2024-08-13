import os
from services.classroom import ClassroomDataManager

def main():
    service = ClassroomDataManager()
    filter_criteria = {
    'From': 'no-reply@classroom.google.com',
    'Subject': 'New assignment'
    }
    messages = service.run(max_results=10, filter_criteria=filter_criteria)    
    print(messages)
    service.save_to_json(messages, 'classroom_data.json')
    
    filtered_messages = []
    for message in messages:
        if "classroom.google.com" in message['payload']['headers']['From'] and "New assignment" in message['payload']['headers']['Subject']:
            filtered_messages.append(message)

    service.save_to_json(filtered_messages, 'filtered_classroom_data.json')
    
main()