"""
Core functionality for the Indeed Job Scraper
"""
import requests
import json
import time
from scraper.constants import API_KEY, INDEED_URLS
from scraper.logging_utils import logger, print_box, configure_job_specific_logger
from scraper.file_utils import generate_filename, save_jobs_to_json, save_jobs_to_csv
from scraper.html_parser import extract_description_from_html, extract_job_data

class ScrapingBeeIndeedScraper:
    def __init__(self, api_key=API_KEY, country='uk'):
        """
        Initialize the scraper with API key and country
        
        Args:
            api_key (str): ScrapingBee API key
            country (str): Country code for Indeed (default: 'uk')
        """
        self.api_key = api_key
        self.country = country
        self.base_url = INDEED_URLS.get(country, INDEED_URLS['uk'])
        
        logger.info(f"Initialized scraper for {self.base_url}")
        
    def construct_indeed_url(self, job_position, job_location, date_posted=''):
        """
        Construct the Indeed search URL
        
        Args:
            job_position (str): Job title to search for
            job_location (str): Location to search in
            date_posted (str): Filter for jobs posted within X days
            
        Returns:
            str: Full Indeed URL
        """
        formatted_job = '+'.join(job_position.split())
        formatted_location = job_location.replace(' ', '+')
        
        full_url = f'{self.base_url}/jobs?q={formatted_job}&l={formatted_location}'
        
        if date_posted:
            full_url += f'&fromage={date_posted}'
            
        logger.info(f"Constructed URL: {full_url}")
        return full_url
    
    def get_scrapingbee_params(self):
        """
        Get ScrapingBee parameters for Indeed scraping
        
        Returns:
            dict: ScrapingBee parameters
        """
        logger.info("Using robust scraping parameters")
        return {
            'render_js': 'true',
            'premium_proxy': 'true',
            'country_code': 'gb',
            'stealth_proxy': 'true',
            'wait': '5000',  # Wait 5 seconds for JS to load
            'block_resources': 'false',  # Don't block any resources
            'return_page_source': 'true'
        }
    
    def scrape_page(self, url, use_ai_extraction=False, max_retries=1):
        """
        Scrape a page using ScrapingBee API
        
        Args:
            url (str): URL to scrape
            use_ai_extraction (bool): Whether to use AI extraction
            max_retries (int): Maximum number of retries for timeout errors
            
        Returns:
            tuple: (success, response_text, ai_data)
        """
        params = self.get_scrapingbee_params()
        params['url'] = url
        
        # Add AI extraction rules if requested
        if use_ai_extraction:
            logger.info("Using AI extraction for this request")
            # Create AI extraction rules as a JSON object
            ai_rules = {
                "job_title": "the job title",
                "company": "the company name",
                "location": "the job location",
                "salary": "the salary range if available",
                "required_skills": "list of required skills mentioned in the job description",
                "experience_level": "years of experience required",
                "education": "education requirements",
                "job_summary": "summarize the job description in 2-3 sentences"
            }
            # Add the stringified JSON to the parameters
            params['ai_extract_rules'] = json.dumps(ai_rules)
        
        api_url = f"https://app.scrapingbee.com/api/v1/"
        
        retries = 0
        while retries <= max_retries:
            try:
                logger.info(f"Sending request to ScrapingBee")
                response = requests.get(
                    api_url,
                    params={
                        'api_key': self.api_key,
                        **params
                    },
                    timeout=90  # Increased timeout from 60 to 90 seconds
                )
            
                if response.status_code == 200:
                    logger.info(f"Successfully received response [OK]")
                    
                    # Parse AI extraction data if it was requested
                    ai_data = None
                    if use_ai_extraction:
                        try:
                            # First check if AI extraction results are in the response headers
                            ai_extraction_header = response.headers.get('X-ScrapingBee-AI-Extraction')
                            if ai_extraction_header:
                                ai_data = json.loads(ai_extraction_header)
                                logger.info(f"Successfully extracted AI data from headers: {list(ai_data.keys())} [OK]")
                            else:
                                # If not in headers, check if the response body is JSON
                                try:
                                    # Try to parse the response text as JSON
                                    json_data = json.loads(response.text)
                                    # Check if it has the expected AI extraction fields
                                    if isinstance(json_data, dict) and 'job_title' in json_data:
                                        ai_data = json_data
                                        logger.info(f"Successfully extracted AI data from response body: {list(ai_data.keys())} [OK]")
                                    else:
                                        logger.warning("AI extraction was requested but no results were found in response")
                                except json.JSONDecodeError:
                                    # Not JSON, so it's probably HTML
                                    logger.warning("AI extraction was requested but response is not JSON")
                        except Exception as e:
                            logger.error(f"Error parsing AI extraction data: {str(e)}")
                    
                    return True, response.text, ai_data
                else:
                    logger.error(f"Error from ScrapingBee API: Status {response.status_code}, {response.text}")
                    return False, None, None
                    
            except requests.exceptions.Timeout:
                retries += 1
                if retries <= max_retries:
                    logger.warning(f"Request timed out. Retrying ({retries}/{max_retries})...")
                    time.sleep(2)  # Wait 2 seconds before retrying
                else:
                    logger.error("Request timed out and max retries reached")
                    return False, None, None
            except Exception as e:
                logger.error(f"Exception during scraping: {str(e)}")
                return False, None, None
    
    def fetch_job_description(self, job_url, use_ai_extraction=False):
        """
        Fetch and extract the job description from a job listing page
        
        Args:
            job_url (str): URL of the job listing
            use_ai_extraction (bool): Whether to use AI extraction
            
        Returns:
            dict: {
                'conventional': conventional_description,
                'ai': ai_extracted_data  # Only if use_ai_extraction is True
            }
        """
        result = {}
        
        try:
            logger.info(f"Attempting to fetch job description")
            success, html_content, ai_data = self.scrape_page(job_url, use_ai_extraction, max_retries=1)
            
            if success and html_content:
                # Extract description using conventional method
                description = extract_description_from_html(html_content)
                if description:
                    logger.info(f"Successfully extracted job description ({len(description)} chars) [OK]")
                    result['conventional'] = description
                    
                    # If AI extraction was requested and successful
                    if use_ai_extraction and ai_data:
                        result['ai'] = ai_data
                        logger.info(f"Successfully extracted AI data for job description [OK]")
                    
                    return result
                else:
                    logger.warning(f"Returned HTML but no description was extracted")
            else:
                logger.warning(f"Failed to retrieve job page content")
                
        except Exception as e:
            logger.error(f"Error fetching job description: {str(e)}")
        
        logger.error(f"Failed to extract job description from {job_url}")
        result['conventional'] = None
        return result
    
    def scrape_indeed_jobs(self, job_position, job_location, date_posted='', 
                          fetch_descriptions=True, use_ai_extraction=True,
                          max_jobs=None, max_pages=None, delay_between_pages=2, 
                          delay_between_jobs=1, save_progress=True, pagination_test=False):
        """
        Scrape Indeed jobs
        
        Args:
            job_position (str): Job title to search for
            job_location (str): Location to search in
            date_posted (str): Filter for jobs posted within X days
            fetch_descriptions (bool): Whether to fetch job descriptions
            use_ai_extraction (bool): Whether to use AI extraction (default: True)
            max_jobs (int): Maximum number of jobs to process (default: None = no limit)
            max_pages (int): Maximum number of pages to scrape (default: None = no limit)
            delay_between_pages (int): Delay in seconds between page requests
            delay_between_jobs (int): Delay in seconds between job description requests
            save_progress (bool): Whether to save progress after each page
            
        Returns:
            list: List of job dictionaries
        """
        # Print a nice box with search info
        print_box(f"STARTING SEARCH: {job_position} in {job_location}", "INFO", "[SRCH]")
        
        # Configure job-specific logger
        configure_job_specific_logger(job_position, job_location)
        
        all_jobs = []
        indeed_url = self.construct_indeed_url(job_position, job_location, date_posted)
        current_page = 1
        next_page_url = None
        total_job_count = "Unknown"
        
        # Create filenames for progress saving - always include timestamp
        json_filename = generate_filename(job_position, job_location, 'json')
        json_path = f'data/{json_filename}'
        csv_filename = generate_filename(job_position, job_location, 'csv')
        csv_path = f'data/{csv_filename}'
        
        logger.info(f"Starting job scraping for '{job_position}' in '{job_location}'")
        
        while True:
            # Check if we've reached the maximum page limit
            if max_pages is not None and current_page > max_pages:
                logger.info(f"Reached maximum page limit of {max_pages}")
                break
                
            logger.info(f"Scraping page {current_page}")
            
            try:
                # Don't use AI extraction for the search results page, only for job descriptions
                success, html_content, _ = self.scrape_page(indeed_url, use_ai_extraction=False, max_retries=1)
                
                if success and html_content:
                    # If pagination_test is enabled, override fetch_descriptions and max_jobs
                    # to speed up the process and focus on pagination
                    if pagination_test:
                        logger.info("Pagination test mode enabled - skipping job descriptions")
                        effective_fetch_descriptions = False
                        effective_use_ai_extraction = False
                        # Process just 1 job per page to quickly move to pagination
                        effective_max_jobs = 1 if max_jobs is None else min(max_jobs - len(all_jobs), 1)
                    else:
                        effective_fetch_descriptions = fetch_descriptions
                        effective_use_ai_extraction = use_ai_extraction
                        effective_max_jobs = max_jobs - len(all_jobs) if max_jobs is not None else None
                    
                    jobs, next_page_url, page_total_job_count = extract_job_data(
                        html_content, 
                        self.base_url,
                        fetch_descriptions=effective_fetch_descriptions,
                        use_ai_extraction=effective_use_ai_extraction,
                        delay_between_jobs=delay_between_jobs,
                        max_jobs=effective_max_jobs,
                        fetch_job_description_func=self.fetch_job_description
                    )
                    
                    # Update total job count if we got a valid count
                    if page_total_job_count != "Unknown":
                        total_job_count = page_total_job_count
                    
                    if jobs:
                        logger.info(f"Successfully scraped {len(jobs)} jobs on page {current_page} [OK]")
                        all_jobs.extend(jobs)
                        
                        # Save progress after each page if enabled
                        if save_progress and all_jobs:
                            logger.info(f"Saving progress after page {current_page}...")
                            save_jobs_to_json(all_jobs, job_position, job_location, json_path)
                            save_jobs_to_csv(all_jobs, job_position, job_location, csv_path)
                            logger.info(f"Progress saved to {json_path} and {csv_path} [OK]")
                    else:
                        logger.warning(f"Returned HTML but no jobs were extracted")
                else:
                    logger.error(f"Failed to retrieve content for page {current_page}")
                    break
            except Exception as e:
                logger.error(f"Exception during scraping page {current_page}: {str(e)}")
                break
            
            # Check if we've reached the job limit
            if max_jobs is not None and len(all_jobs) >= max_jobs:
                logger.info(f"Reached job limit of {max_jobs} jobs")
                break
            
            # Move to next page if available
            if next_page_url:
                indeed_url = next_page_url
                current_page += 1
                logger.info(f"Moving to page {current_page}: {indeed_url}")
                
                # Add delay between page requests to avoid overloading the API
                logger.info(f"Waiting {delay_between_pages} seconds before next request...")
                time.sleep(delay_between_pages)
            else:
                # No more pages
                logger.info("No more pages available - pagination complete")
                break
        
        logger.info(f"Scraping complete. Total jobs found: {len(all_jobs)} out of approximately {total_job_count}")
        return all_jobs
