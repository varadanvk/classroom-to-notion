import json
import os
from typing import List, Dict, Any

class NotionAssignmentMatcher:
    def __init__(self, notion_results_path: str, output_path: str):
        self.notion_results_path = notion_results_path
        self.output_path = output_path
        self.activities = []

    def load_notion_results(self) -> Any:
        try:
            with open(self.notion_results_path, 'r') as file:
                data = json.load(file)
                if isinstance(data, str):
                    # If the content is a JSON string, parse it again
                    return json.loads(data)
                return data
        except json.JSONDecodeError:
            print(f"Error: The file {self.notion_results_path} is not a valid JSON.")
            return None
        except FileNotFoundError:
            print(f"Error: The file {self.notion_results_path} was not found.")
            return None

    def extract_activities(self, notion_results: Any) -> List[Dict]:
        activities = []
        if isinstance(notion_results, dict) and 'results' in notion_results:
            items = notion_results['results']
        elif isinstance(notion_results, list):
            items = notion_results
        else:
            print("Error: Unexpected data structure in notion_results.")
            return activities

        for item in items:
            if not isinstance(item, dict):
                continue
            properties = item.get('properties', {})
            title = properties.get('Name', {}).get('title', [{}])[0].get('plain_text', '')
            activity_id = item.get('id', '')
            if title and activity_id:
                activities.append({
                    'title': title,
                    'id': activity_id,
                    'teacher': ''
                })
        return activities

    def assign_teachers(self) -> None:
        print("Assign teachers to activities:")
        for activity in self.activities:
            teacher = input(f"Enter teacher name for '{activity['title']}' (or press Enter to skip): ")
            activity['teacher'] = teacher.strip()

    def save_activities(self) -> None:
        with open(self.output_path, 'w') as file:
            json.dump(self.activities, file, indent=2)
        print(f"Activities with teachers saved to {self.output_path}")

    def match_assignment_to_activity(self, assignment: Dict) -> str:
        posted_by = assignment.get('posted_by', '').lower()
        for activity in self.activities:
            if activity['teacher'].lower() in posted_by:
                return activity['id']
        return ''

    def run(self):
        notion_results = self.load_notion_results()
        if notion_results is None:
            return

        self.activities = self.extract_activities(notion_results)
        if not self.activities:
            print("No activities found in the Notion results.")
            return

        self.assign_teachers()
        self.save_activities()

        print("\nMatching system ready. You can now use this to match assignments to activities.")

        # Example usage:
        sample_assignment = {
            'assignment_name': 'Sample Assignment',
            'posted_by': 'John Doe'
        }
        
        matched_activity_id = self.match_assignment_to_activity(sample_assignment)
        if matched_activity_id:
            print(f"Assignment '{sample_assignment['assignment_name']}' matches activity with ID: {matched_activity_id}")
        else:
            print(f"No matching activity found for assignment '{sample_assignment['assignment_name']}'")

def matcher():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    notion_results_path = os.path.join(script_dir, 'outputs', 'notion_results.json')
    output_path = os.path.join(script_dir, 'constant', 'activities_with_teachers.json')

    matcher = NotionAssignmentMatcher(notion_results_path, output_path)
    matcher.run()

if __name__ == "__main__":
    main()