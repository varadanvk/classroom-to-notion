import json
import os
from datetime import datetime
from typing import List, Dict, Any

class AssignmentParser:
    def __init__(self, activities):
        self.activities = []
        self.load_or_create_activities()

    def set_activities(self, activities: List[Dict[str, Any]]) -> None:
        self.activities = activities


    def load_or_create_activities(self):
        activities_file = 'constants/activities_with_teachers.json'
        if os.path.exists(activities_file):
            with open(activities_file, 'r') as file:
                self.activities = json.load(file)
            print(f"Loaded existing activities with teachers from {activities_file}")
        else:
            self.activities = self.extract_activities()
            self.assign_teachers()
            self.save_activities(activities_file)

    def extract_activities(self) -> List[Dict[str, Any]]:
        # This method needs to be implemented or replaced with appropriate logic
        return []

    def assign_teachers(self):
        print("Assign teachers to activities:")
        for activity in self.activities:
            teacher = input(f"Enter teacher name for '{activity['title']}' (or press Enter to skip): ")
            activity['teacher'] = teacher.strip()

    def save_activities(self, filename: str = 'activities_with_teachers.json'):
        with open(filename, 'w') as file:
            json.dump(self.activities, file, indent=2)
        print(f"Activities with teachers saved to {filename}")

    def match_assignment_to_activity(self, assignment: Dict) -> str:
        posted_by = assignment.get('posted_by', '').lower()
        
        # First, try to find an exact match
        for activity in self.activities:
            if activity['teacher'].lower() == posted_by:
                return activity['id']
        
        # If no exact match, try partial match
        for activity in self.activities:
            if activity['teacher'].lower() in posted_by or posted_by in activity['teacher'].lower():
                return activity['id']
        
        # If still no match, try matching any word in the teacher's name
        teacher_words = posted_by.split()
        for activity in self.activities:
            activity_teacher_words = activity['teacher'].lower().split()
            if any(word in activity_teacher_words for word in teacher_words):
                return activity['id']
        
        # If no match found, return an empty string
        return ''

    def parse_assignments(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        
        pages = []
        
        # Parse the due date
        for assignment_data in data:
            due_date = None
            if assignment_data['due_date'] != "Not found":
                try:
                    due_date_obj = datetime.strptime(f"{assignment_data['due_date']} 2024", "%b %d %Y")
                    due_date = {
                        "start": due_date_obj.isoformat(),
                        "end": None
                    }
                except ValueError:
                    print(f"Unable to parse due date: {assignment_data['due_date']}")

            # Match the assignment to an activity
            activity_id = self.match_assignment_to_activity(assignment_data)

            # Create the Notion page structure
            notion_page = {
                "parent": {"database_id": os.environ.get('NOTION_DATABASE_ID')},
                "properties": {
                    "Status": {
                        "status": {
                            "name": "Not started"
                        }
                    },
                    "Type": {
                        "select": None
                    },
                    "Estimated Time": {
                        "rich_text": []
                    },
                    "Priority": {
                        "select": None
                    },
                    "Due date": {
                        "date": due_date
                    },
                    "Note": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": f"Assignment Link: {assignment_data['assignment_link']}\n"
                                            f"Class Link: {assignment_data['class_link']}\n"
                                            f"Class Name: {assignment_data['class_name']}\n"
                                            f"Posted Date: {assignment_data['posted_date']}\n"
                                            f"Posted By: {assignment_data['posted_by']}\n"
                                            f"Description: {assignment_data['assignment_description']}"
                                }
                            }
                        ]
                    },
                    "Name": {
                        "title": [
                            {
                                "text": {
                                    "content": assignment_data['assignment_name'],
                                    "link": {
                                        "url": assignment_data['assignment_link']
                                    }
                                }
                            }
                        ]
                    }
                }
            }

            # Add the Activity relation if a match was found
            if activity_id:
                notion_page["properties"]["Activity"] = {
                    "relation": [
                        {
                            "id": activity_id
                        }
                    ]
                }
            else:
                print(f"No matching activity found for assignment: {assignment_data['assignment_name']}")
            
            pages.append(notion_page)

        return pages