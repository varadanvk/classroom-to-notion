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
logging.basicConfig(
    filename="classroom_to_notion.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def load_json_file(file_path):
    try:
        with open(file_path, "r") as file:
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
    # print(json.dumps(results, indent=2))
    cdm.save_to_json(results, "outputs/notion_results.json")
    return results


def load_activities():
    load_dotenv()
    ndm = NotionDatabaseManager(
        database_id=os.getenv("ACTIVITIES_DATABASE_ID"), token=os.getenv("NOTION_TOKEN")
    )
    cdm = ClassroomDataManager()
    response = query_database(
        database_id=os.getenv("ACTIVITIES_DATABASE_ID"), statuses=["In Progress"]
    )

    with open("outputs/notion_results.json", "w") as file:
        json.dump(response, file, indent=2)

    return response


def main():
    try:
        load_dotenv()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cdm = ClassroomDataManager()
        ndm = NotionDatabaseManager(
            database_id=os.environ.get("NOTION_DATABASE_ID"),
            token=os.environ.get("NOTION_TOKEN"),
        )
        notion_cache = NotionCache()

        # Load activities
        activities = load_activities()

        # Initialize AssignmentParser with loaded activities
        ap = AssignmentParser(activities)

        # Use lowercase keys for filter criteria
        filter_criteria = {
            "from": "no-reply@classroom.google.com",
            "subject": "New assignment",
        }

        email_cache = load_json_file("outputs/classroom_data.json")

        # Improved caching logic
        if len(email_cache) == 0:
            logging.info("Cache is empty, running service")
            messages = cdm.run(max_results=20, filter_criteria=filter_criteria)
        else:
            # Check last 5 messages instead of just 1 to avoid missing any
            latest_messages = cdm.run(max_results=5, filter_criteria=filter_criteria)
            if latest_messages:
                # Check if any of the new messages are not in our cache
                cached_ids = {msg["id"] for msg in email_cache}
                new_message_exists = any(
                    msg["id"] not in cached_ids for msg in latest_messages
                )

                if not new_message_exists:
                    logging.info("No new messages. Using email_cache for data")
                    messages = email_cache
                else:
                    messages = cdm.run(max_results=20, filter_criteria=filter_criteria)
                    logging.info(f"Retrieved {len(messages)} new messages")
            else:
                messages = email_cache  # Fallback to cache if API call fails

        # Save the messages to cache
        if messages:
            cdm.save_to_json(messages, "outputs/classroom_data.json")

            filtered_messages = cdm.filter_messages(messages)
            cdm.save_to_json(filtered_messages, "outputs/filtered_classroom_data.json")

            # Extract assignment info (messages are already filtered)
            print("filtering messages")
            extracted_data = cdm.extract_assignment_info(filtered_messages)
            if extracted_data:
                cdm.save_to_json(
                    extracted_data, "outputs/extracted_classroom_data.json"
                )

                # Parse and filter
                parsed_data = ap.parse_assignments(extracted_data)
                uncached_data = notion_cache.filter_with_cache(parsed_data)

                # Add new assignments to Notion
                if not uncached_data:
                    logging.info("No new assignments to process")
                    print("No new assignments to process")
                    print("-------------------------------------------------")
                    return {"message": "No new assignments to process"}
                else:
                    responses = ndm.post_data(uncached_data)
                    logging.info(f"Processed {len(responses)} new assignments")
                    logging.info("Saving new assignments to cache")
                    cdm.save_to_json(responses, "outputs/new_assignments.json")
                    print("-------------------------------------------------")
                    return {"message": f"Processed {len(responses)} new assignments"}
            else:
                logging.warning("No assignments extracted from messages")
                return {"message": "No assignments extracted from messages"}
        else:
            logging.warning("No messages retrieved")
            return {"message": "No messages retrieved"}

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
        print(e)
        return {"message": f"Error: {str(e)}"}


if __name__ == "__main__":
    main()
