"""
Utility functions for the Indeed job scraper
"""
import os
import logging
import pandas as pd
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

def get_user_desktop_path():
    """Get the path to the user's desktop"""
    home_dir = os.path.expanduser("~")
    desktop_path = os.path.join(home_dir, "Desktop")
    return desktop_path

def save_to_desktop(df, job_position, job_location):
    """
    Save a DataFrame to the user's desktop
    
    Args:
        df (DataFrame): DataFrame to save
        job_position (str): Job position used in the search
        job_location (str): Location used in the search
        
    Returns:
        str: Path to the saved file
    """
    try:
        # Create a clean filename
        clean_job = job_position.replace(' ', '_')
        clean_location = job_location.replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        filename = f"{clean_job}_{clean_location}_{timestamp}.csv"
        file_path = os.path.join(get_user_desktop_path(), filename)
        
        # Save the file
        df.to_csv(file_path, index=False)
        logger.info(f"Saved results to desktop: {file_path}")
        
        return file_path
    except Exception as e:
        logger.error(f"Error saving to desktop: {str(e)}")
        return None

def format_job_count(count_text):
    """
    Format the job count text from Indeed
    
    Args:
        count_text (str): Job count text from Indeed
        
    Returns:
        int or str: Formatted job count
    """
    try:
        # Remove non-numeric characters
        count_text = ''.join(c for c in count_text if c.isdigit())
        return int(count_text) if count_text else "Unknown"
    except Exception as e:
        logger.error(f"Error formatting job count: {str(e)}")
        return "Unknown"

def clean_job_data(jobs_list):
    """
    Clean and standardize job data
    
    Args:
        jobs_list (list): List of job dictionaries
        
    Returns:
        list: Cleaned list of job dictionaries
    """
    cleaned_jobs = []
    
    for job in jobs_list:
        if not job:
            continue
            
        # Standardize date posted format
        if 'date_posted' in job and job['date_posted']:
            job['date_posted'] = job['date_posted'].replace('EmployerActive', '').strip()
            
        # Ensure all expected fields exist
        for field in ['title', 'company', 'location', 'date_posted', 'url']:
            if field not in job or not job[field]:
                job[field] = "Not specified"
                
        cleaned_jobs.append(job)
        
    return cleaned_jobs
