from apscheduler.schedulers.background import BackgroundScheduler
from collectors.resource_collector import collect_resources
from metric.metric import extract_metrics
import subprocess
import os

def renew_token():
    script_path = '/app/renew_token.sh'
    if os.path.exists(script_path):
        subprocess.call(['/bin/bash', script_path])
    else:
        print(f"Warning: renew_token.sh not found at {script_path}")

def start_scheduler():
    """
    Initializes and starts the background scheduler for periodic tasks.
    The resource collection interval is configurable via an environment variable.
    """
    scheduler = BackgroundScheduler()

    scheduler.add_job(renew_token, 'interval', hours=24)

    try:
        interval_hours = int(os.getenv("SCHEDULER_INTERVAL_HOURS", "48"))
        if interval_hours <= 0:
            raise ValueError("Interval must be a positive integer.")
    except (ValueError, TypeError):
        print("Invalid or missing SCHEDULER_INTERVAL_HOURS. Defaulting to 48 hour.")
        interval_hours = 1

    scheduler.add_job(collect_resources, 'interval', hours=interval_hours, id='resource_collector_job')

    # Schedule metric extraction more frequently (e.g. every 5 minutes)
    # This could be configurable, but hardcoding for now as per requirement for "service has a /metrics endpoint"
    scheduler.add_job(extract_metrics, 'interval', minutes=60, id='metric_extraction_job')

    scheduler.start()
    print(f"Scheduler started. Resource collection will run every {interval_hours} hour(s).")