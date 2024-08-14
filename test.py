import json
import re

def extract_assignment_info(json_file_path):
    # Read the JSON file
    with open(json_file_path, 'r') as file:
        data = json.load(file)

    # Extract the HTML content
    html_content = data['payload']['parts'][1]['body']

    # Extract assignment name
    assignment_name_match = re.search(r'<div>(.*?)</div>', html_content)
    assignment_name = assignment_name_match.group(1) if assignment_name_match else "Not found"

    # Extract class link
    
    link_pattern = "https://accounts\.google\.com/AccountChooser\?continue="
    link_match = re.search(r'href=(https://accounts\.google\.com/AccountChooser\?continue=https://classroom\.google\.com/c/[^&]+)', html_content)
    class_link = link_match.group(1) if link_match else "Not found"
    class_link = re.sub(link_pattern, "", class_link)
    
    assignment_match=re.search(r'href=(https://accounts\.google\.com/AccountChooser\?continue=https://classroom\.google\.com/c/[^&]+/a/[^&]+)', html_content)
    assignment_link = assignment_match.group(1) if assignment_match else "Not found"
    assignment_link = re.sub(link_pattern, "", assignment_link)

    # Extract assignment description
    description_match = re.search(r'<ul>(.*?)</ul>', html_content, re.DOTALL)
    if description_match:
        description_items = re.findall(r'<li>(.*?)</li>', description_match.group(1))
        assignment_description = "\n".join(description_items)
    else:
        assignment_description = "Not found"

    # Extract class name
    class_match = re.search(r'>([^<]+)</td></tr></table></a></td>', html_content)
    class_name = class_match.group(1) if class_match else "Not found"

    # Extract due date
    due_date_match = re.search(r'Due ([^<]+)', html_content)
    due_date = due_date_match.group(1) if due_date_match else "Not found"

    # Extract posted date and author
    posted_info_match = re.search(r'Posted on ([^<]+) by ([^<]+)', html_content)
    if posted_info_match:
        posted_date = posted_info_match.group(1)
        posted_by = posted_info_match.group(2)
    else:
        posted_date = "Not found"
        posted_by = "Not found"

    return {
        "assignment_name": assignment_name,
        "assignment_link": assignment_link,
        "assignment_description": assignment_description,
        "class_name": class_name,
        "due_date": due_date,
        "posted_date": posted_date,
        "posted_by": posted_by,
        "class_link": class_link,
    }

# Usage
json_file_path = 'test.json'
result = extract_assignment_info(json_file_path)

print("Assignment Name:", result["assignment_name"])
print("Assignment Link:", result["assignment_link"])
print("Assignment Description:", result["assignment_description"])
print("Class:", result["class_name"])
print("Due Date:", result["due_date"])
print("Posted on:", result["posted_date"])
print("Posted by:", result["posted_by"])
print("Class Link:", result["class_link"])