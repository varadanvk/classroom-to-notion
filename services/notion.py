import requests
import json
import os
from datetime import datetime
from typing import List, Dict, Any

class NotionDatabaseManager:
    def __init__(self, database_id: str, token: str = None):
        self.database_id = database_id
        self.token = token or os.environ.get('NOTION_TOKEN')
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        self.activities = []
        self.load_or_create_activities()

    def query_database(self, filter_conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
        url = f"{self.base_url}/databases/{self.database_id}/query"
        data = {
            "filter": {
                "or": filter_conditions
            }
        }
        response = requests.post(url, json=data, headers=self.headers)
        return response.json()

    def get_tasks_by_status(self, statuses: List[str]) -> Dict[str, Any]:
        filter_conditions = [
            {
                "property": "Status",
                "status": {
                    "equals": status
                }
            } for status in statuses
        ]
        return self.query_database(filter_conditions)
    
    def get_database_properties(self) -> Dict[str, Any]:
        url = f"{self.base_url}/databases/{self.database_id}"
        response = requests.get(url, headers=self.headers)
        return response.json()

    def save_results_to_file(self, data: Dict[str, Any], filename: str = 'notion_results.json'):
        with open(filename, 'w') as file:
            json.dump(data, file, indent=2)

    def parse_notion_response(self, response: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Parse the Notion API response and extract important properties for multiple tasks.
        
        :param response: The full Notion API response
        :return: A list of dictionaries, each containing the simplified data for a task
        """
        parsed_tasks = []
        
        if not response.get('results'):
            return parsed_tasks
        
        for task in response['results']:
            properties = task['properties']
            
            parsed_task = {
                "Name": properties['Name']['title'][0]['text']['content'] if properties['Name']['title'] else "",
                "Status": properties['Status']['status']['name'] if properties['Status']['status'] else "",
                "Priority": properties['Priority']['select']['name'] if properties['Priority']['select'] else "",
                "Estimated Time": properties['Estimated Time']['rich_text'][0]['text']['content'] if properties['Estimated Time']['rich_text'] else "",
                "Due date": properties['Due date']['date']['start'] if properties['Due date']['date'] else "",
                "Activity": properties['Rollup']['rollup']['array'][0]['title'][0]['text']['content'] if properties['Rollup']['rollup']['array'] else "",
                "url": task['url'],
            }
            
            parsed_tasks.append(parsed_task)
        
        return parsed_tasks
       
    
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
        schema = self.get_database_schema()
        properties = schema.get("properties", {})
        
        activities = []
        for prop_name, prop_data in properties.items():
            if prop_data.get("type") == "rollup":
                activity_info = {
                    "title": prop_name,
                    "id": prop_data.get("id"),
                    "teacher": ""
                }
                activities.append(activity_info)
        
        return activities

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

    def parse_assignments(self, assignment_data):
        # Parse the due date
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
            "parent": {"database_id": self.database_id},
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

        return notion_page
    
    def get_database_schema(self) -> Dict[str, Any]:
        url = f"{self.base_url}/databases/{self.database_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_rollups(self) -> List[Dict[str, Any]]:
        schema = self.get_database_schema()
        properties = schema.get("properties", {})
        
        rollups = []
        for prop_name, prop_data in properties.items():
            if prop_data.get("type") == "rollup":
                rollup_info = {
                    "name": prop_name,
                    "id": prop_data.get("id"),
                    "rollup": prop_data.get("rollup", {})
                }
                rollups.append(rollup_info)
        
        return rollups
    
    def post_data(self, data: Dict[str, Any]):
        url = f"https://api.notion.com/v1/pages/"
        response = requests.post(url, json=data, headers=self.headers)
        return response.json()