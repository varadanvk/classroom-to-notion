import schedule
import time
from main import main

main()

def job():
    print("Running Classroom to Notion sync...")
    main()

schedule.every(20).seconds.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)