"""
File utilities for the Indeed Job Scraper
"""
import os
import json
import pandas as pd
from datetime import datetime
from scraper.logging_utils import logger

def generate_filename(job_position, job_location, extension, include_timestamp=True):
    """
    Generate a filename based on job position and location
    
    Args:
        job_position (str): Job position used in the search
        job_location (str): Location used in the search
        extension (str): File extension (e.g., 'json', 'csv')
        include_timestamp (bool): Whether to include a timestamp
        
    Returns:
        str: Generated filename
    """
    # Clean the job position and location for filename
    clean_job = job_position.replace(' ', '_').lower()
    clean_location = job_location.replace(' ', '_').lower()
    
    # Always include timestamp to avoid duplicate files
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{clean_job}_{clean_location}_{timestamp}.{extension}"

def save_jobs_to_json(jobs, job_position=None, job_location=None, filename=None):
    """
    Save jobs to a JSON file
    
    Args:
        jobs (list): List of job dictionaries
        job_position (str, optional): Job position used in the search
        job_location (str, optional): Location used in the search
        filename (str, optional): Output filename (overrides automatic naming)
    """
    if not jobs:
        logger.warning("No jobs to save")
        return
    
    # Use provided filename or generate one based on job position and location
    if not filename:
        if job_position and job_location:
            filename = os.path.join('data', generate_filename(job_position, job_location, 'json'))
        else:
            filename = os.path.join('data', "indeed_jobs.json")  # Fallback to default
        
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
        
    logger.info(f"Saved {len(jobs)} jobs to {filename} [OK]")

def save_jobs_to_csv(jobs, job_position=None, job_location=None, filename=None):
    """
    Save jobs to a CSV file
    
    Args:
        jobs (list): List of job dictionaries
        job_position (str, optional): Job position used in the search
        job_location (str, optional): Location used in the search
        filename (str, optional): Output filename (overrides automatic naming)
    """
    if not jobs:
        logger.warning("No jobs to save")
        return
    
    # Use provided filename or generate one based on job position and location
    if not filename:
        if job_position and job_location:
            filename = os.path.join('data', generate_filename(job_position, job_location, 'csv'))
        else:
            filename = os.path.join('data', "indeed_jobs.csv")  # Fallback to default
    
    df = pd.DataFrame(jobs)
    df.to_csv(filename, index=False)
    
    logger.info(f"Saved {len(jobs)} jobs to {filename} [OK]")
