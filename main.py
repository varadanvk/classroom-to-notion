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
    service.save_to_json(messages, 'outputs/classroom_data.json')

    #Filter Messages
    filtered_messages = service.filter_messages(messages)
    service.save_to_json(filtered_messages, 'outputs/filtered_classroom_data.json')
    
    #Extract assignment info
    extracted_data = service.extract_assignment_info(filtered_messages)
    service.save_to_json(extracted_data, 'outputs/extracted_classroom_data.json')
    
    
    #TODO: Use notion service to have user input for class names based on teacher that posts the assignment
    
    
main()