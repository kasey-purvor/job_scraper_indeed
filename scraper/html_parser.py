"""
HTML parsing utilities for the Indeed Job Scraper
"""
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
from scraper.logging_utils import logger

def extract_description_from_html(html_content):
    """
    Extract job description from HTML content
    
    Args:
        html_content (str): HTML content of job page
        
    Returns:
        str: Job description text or None if extraction failed
    """
    try:
        # First check if the content is JSON (AI extraction result)
        try:
            json_data = json.loads(html_content)
            if isinstance(json_data, dict) and 'job_summary' in json_data:
                # Use the job summary as the description
                return json_data['job_summary']
        except json.JSONDecodeError:
            # Not JSON, so proceed with HTML parsing
            pass
            
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Save HTML for debugging
        debug_filename = f"debug_job_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        debug_path = os.path.join('logs', debug_filename)
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.debug(f"Saved job page HTML to {debug_path}")
        
        # Try different possible selectors for job description
        description_element = None
        
        # Option 1: Standard job description container
        description_element = soup.select_one('div#jobDescriptionText')
        
        # Option 2: Alternative selector
        if not description_element:
            description_element = soup.select_one('div.jobsearch-jobDescriptionText')
            
        # Option 3: Another alternative
        if not description_element:
            description_element = soup.select_one('div[data-testid="jobDescriptionText"]')
        
        if description_element:
            # Extract and clean the text
            description = description_element.get_text(separator='\n', strip=True)
            return description
        else:
            logger.warning("Could not find job description element")
            return None
            
    except Exception as e:
        logger.error(f"Error parsing job description HTML: {str(e)}")
        return None

def extract_job_details(job_card, base_url):
    """
    Extract details from a job card
    
    Args:
        job_card: BeautifulSoup element for a job card
        base_url: Base URL for Indeed
        
    Returns:
        dict: Job details or None if extraction failed
    """
    try:
        # Extract job title
        title_element = job_card.find('h2', class_='jobTitle')
        if not title_element:
            return None
            
        job_title = title_element.get_text(strip=True)
        
        # Extract company name
        company_element = job_card.find('span', {'data-testid': 'company-name'})
        if not company_element:
            company_element = job_card.find('span', class_=lambda x: x and 'company' in str(x).lower())
        company_name = company_element.get_text(strip=True) if company_element else "Not specified"
        
        # Extract location
        location_element = job_card.find('div', {'data-testid': 'text-location'})
        if not location_element:
            location_element = job_card.find('div', class_=lambda x: x and 'location' in str(x).lower())
        location = location_element.get_text(strip=True) if location_element else "Not specified"
        
        # Extract posting date
        date_element = job_card.find('span', class_='date')
        if not date_element:
            date_element = job_card.find('span', {'data-testid': 'myJobsStateDate'})
        posting_date = date_element.get_text(strip=True) if date_element else "Not specified"
        
        # Extract job URL
        url_element = job_card.find('a', class_=lambda x: x and 'JobTitle' in x)
        if not url_element and 'href' not in url_element.attrs:
            url_element = job_card.find('a', {'data-jk': True})
            
        job_url = base_url + url_element['href'] if url_element and 'href' in url_element.attrs else "Not available"
        
        return {
            'title': job_title,
            'company': company_name,
            'location': location,
            'date_posted': posting_date,
            'url': job_url
        }
        
    except Exception as e:
        logger.error(f"Error extracting job details: {str(e)}")
        return None

def extract_job_data(html_content, base_url, fetch_descriptions=True, use_ai_extraction=True, 
                    delay_between_jobs=1, max_jobs=None, fetch_job_description_func=None):
    """
    Extract job data from HTML content
    
    Args:
        html_content (str): HTML content from Indeed
        base_url (str): Base URL for Indeed
        fetch_descriptions (bool): Whether to fetch job descriptions
        use_ai_extraction (bool): Whether to use AI extraction
        delay_between_jobs (int): Delay in seconds between job description requests
        max_jobs (int): Maximum number of jobs to process
        fetch_job_description_func (function): Function to fetch job descriptions
        
    Returns:
        tuple: (jobs_list, next_page_url, total_job_count)
    """
    if not html_content:
        logger.error("No HTML content to parse")
        return [], None, "Unknown"
        
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Save HTML for debugging
    debug_filename = f"debug_indeed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    debug_path = os.path.join('logs', debug_filename)
    with open(debug_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    logger.debug(f"Saved HTML content to {debug_path}")
        
    # Extract total job count
    total_job_count = "Unknown"
    job_count_element = soup.select_one('div[class*="jobsearch-JobCountAndSortPane-jobCount"]')
    if job_count_element:
        job_count = job_count_element.get_text(strip=True)
        logger.info(f"Found job count: {job_count} [OK]")
        total_job_count = job_count
    else:
        logger.warning("Could not find job count element")
        
    # Find all job cards
    job_cards = soup.find_all('div', class_='job_seen_beacon')
    
    if not job_cards:
        logger.warning("No job cards found. The page structure might have changed.")
        # Try alternative selectors
        job_cards = soup.find_all('div', {'data-testid': 'jobListing'})
        if not job_cards:
            logger.error("Failed to find job cards with alternative selectors")
            return [], None, total_job_count
        else:
            logger.info(f"Found {len(job_cards)} job cards using alternative selector [OK]")
    else:
        logger.info(f"Found {len(job_cards)} job cards [OK]")
    
    jobs = []
    job_count = 0
    
    for job_card in job_cards:
        # Check if we've reached the maximum number of jobs to process
        if max_jobs is not None and job_count >= max_jobs:
            logger.info(f"Reached maximum job limit of {max_jobs} while processing page")
            break
            
        try:
            job_data = extract_job_details(job_card, base_url)
            
            if job_data:
                # Initialize description fields
                job_data['description'] = ""
                job_data['ai_data'] = {}
                
                # If enabled, immediately fetch the job description
                if (fetch_descriptions or use_ai_extraction) and job_data['url'] != "Not available" and fetch_job_description_func:
                    logger.info(f"Fetching description for: {job_data['title']} ({job_count+1}/{min(len(job_cards), max_jobs or len(job_cards))})")
                    
                    # Add a small delay to avoid overloading the API
                    import time
                    time.sleep(delay_between_jobs)
                    
                    # Fetch and add the description
                    description_data = fetch_job_description_func(job_data['url'], use_ai_extraction)
                    
                    # Add conventional description if requested
                    if fetch_descriptions:
                        job_data['description'] = description_data.get('conventional', "")
                    
                    # Add AI data if requested and available
                    if use_ai_extraction:
                        ai_data = description_data.get('ai', {})
                        if ai_data:
                            # Store the full AI data object only, don't duplicate as individual fields
                            job_data['ai_data'] = ai_data
                
                jobs.append(job_data)
                job_count += 1
                
        except Exception as e:
            logger.error(f"Error extracting job details: {str(e)}")
            continue
    
    # Extract next page URL with multiple fallback methods
    next_page_url = None
    
    # Save pagination section for debugging
    pagination_section = soup.find('nav', {'role': 'navigation'})
    if pagination_section:
        debug_pagination_filename = f"debug_pagination_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        debug_pagination_path = os.path.join('logs', debug_pagination_filename)
        with open(debug_pagination_path, "w", encoding="utf-8") as f:
            f.write(str(pagination_section))
        logger.debug(f"Saved pagination HTML to {debug_pagination_path}")
    else:
        logger.warning("Could not find pagination section for debugging")
    
    # Method 1: Try the original aria-label selector
    try:
        next_page_element = soup.find('a', {'aria-label': 'Next Page'})
        if next_page_element and 'href' in next_page_element.attrs:
            next_page_url = base_url + next_page_element['href']
            logger.info(f"Found next page URL (method 1 - aria-label): {next_page_url} [OK]")
    except Exception as e:
        logger.error(f"Error in pagination method 1: {str(e)}")
    
    # Method 2: Try data-testid attribute
    if not next_page_url:
        try:
            next_page_element = soup.find('a', {'data-testid': 'pagination-page-next'})
            if next_page_element and 'href' in next_page_element.attrs:
                next_page_url = base_url + next_page_element['href']
                logger.info(f"Found next page URL (method 2 - data-testid): {next_page_url} [OK]")
        except Exception as e:
            logger.error(f"Error in pagination method 2: {str(e)}")
    
    # Method 3: Look for any pagination link with "Next" text or containing a right arrow
    if not next_page_url:
        try:
            # Look for text containing "Next" or "next"
            next_links = soup.find_all('a', string=lambda s: s and ('next' in s.lower() or 'next' in s.lower()))
            
            # Also look for links containing arrow icons (common in pagination)
            arrow_links = soup.find_all('a', class_=lambda c: c and ('next' in c.lower() or 'arrow' in c.lower()))
            
            # Combine the results
            potential_next_links = next_links + arrow_links
            
            if potential_next_links and 'href' in potential_next_links[0].attrs:
                next_page_url = base_url + potential_next_links[0]['href']
                logger.info(f"Found next page URL (method 3 - text/class): {next_page_url} [OK]")
        except Exception as e:
            logger.error(f"Error in pagination method 3: {str(e)}")
    
    # Method 4: URL-based pagination fallback
    # If we found jobs but no next page link, try to construct the URL
    if not next_page_url and jobs:
        try:
            # Check if the current URL has a start parameter
            current_url = soup.find('link', {'rel': 'canonical'})
            if current_url and 'href' in current_url.attrs:
                current_url_str = current_url['href']
                
                # Parse the current URL to find pagination parameters
                import re
                start_match = re.search(r'start=(\d+)', current_url_str)
                
                if start_match:
                    # If there's a start parameter, increment it by the number of jobs per page (typically 10-15)
                    current_start = int(start_match.group(1))
                    next_start = current_start + len(jobs)
                    next_page_url = re.sub(r'start=\d+', f'start={next_start}', current_url_str)
                    logger.info(f"Constructed next page URL (method 4 - URL pattern): {next_page_url} [OK]")
                else:
                    # If there's no start parameter yet, add it
                    if '?' in current_url_str:
                        next_page_url = f"{current_url_str}&start={len(jobs)}"
                    else:
                        next_page_url = f"{current_url_str}?start={len(jobs)}"
                    logger.info(f"Constructed first pagination URL (method 4 - URL pattern): {next_page_url} [OK]")
        except Exception as e:
            logger.error(f"Error in pagination method 4: {str(e)}")
    
    # Final check - if we still don't have a next page URL
    if not next_page_url:
        logger.info("No next page URL found - this appears to be the last page")
            
    return jobs, next_page_url, total_job_count
