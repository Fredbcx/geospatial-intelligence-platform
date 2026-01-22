"""
Background Scheduler - Runs periodic tasks
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
import atexit

from data_ingestion import fetch_and_store_aircraft_job

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None

def start_scheduler(interval_minutes: int = 5):
    """
    Start background scheduler
    interval_minutes: How often to fetch data (default: 5 minutes)
    """
    global scheduler
    
    if scheduler is not None:
        logger.warning("Scheduler already running")
        return scheduler
    
    logger.info("=" * 60)
    logger.info("🚀 Starting Background Scheduler")
    logger.info("=" * 60)
    
    scheduler = BackgroundScheduler()
    
    # Add aircraft fetching job
    scheduler.add_job(
        func=fetch_and_store_aircraft_job,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id='fetch_aircraft',
        name='Fetch Aircraft Data',
        replace_existing=True,
        max_instances=1  # Prevent overlapping runs
    )
    
    # Start scheduler
    scheduler.start()
    
    logger.info(f"✅ Scheduler started - fetching every {interval_minutes} minutes")
    logger.info(f"📅 Next run: {scheduler.get_jobs()[0].next_run_time}")
    logger.info("=" * 60)
    
    # Shutdown scheduler on exit
    atexit.register(lambda: stop_scheduler())
    
    return scheduler

def stop_scheduler():
    """Stop the scheduler"""
    global scheduler
    
    if scheduler is not None:
        logger.info("Stopping scheduler...")
        scheduler.shutdown()
        scheduler = None
        logger.info("✅ Scheduler stopped")

def get_scheduler_status():
    """Get current scheduler status"""
    if scheduler is None:
        return {
            "running": False,
            "jobs": []
        }
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None
        })
    
    return {
        "running": True,
        "jobs": jobs
    }

def trigger_job_now(job_id: str = 'fetch_aircraft'):
    """Manually trigger a job immediately"""
    if scheduler is None:
        logger.error("Scheduler not running")
        return False
    
    try:
        job = scheduler.get_job(job_id)
        if job:
            logger.info(f"⚡ Manually triggering job: {job_id}")
            job.modify(next_run_time=None)  # Run immediately
            return True
        else:
            logger.error(f"Job {job_id} not found")
            return False
    except Exception as e:
        logger.error(f"Error triggering job: {e}")
        return False