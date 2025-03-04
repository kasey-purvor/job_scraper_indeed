import requests
import json
import logging
import os
import pandas as pd
import time
import sys
import colorama
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv

# Initialize colorama for cross-platform colored terminal output
# Force conversion for Windows terminals
colorama.init(strip=False, convert=True)

# Create necessary directories
os.makedirs('logs', exist_ok=True)
os.makedirs('data', exist_ok=True)

# ANSI color codes for colored output
class Colors:
    RESET = colorama.Style.RESET_ALL
    BOLD = colorama.Style.BRIGHT
    
    # Category colors
    NAVIGATION = colorama.Fore.BLUE
    LISTING = colorama.Fore.GREEN
    AI = colorama.Fore.MAGENTA
    DESCRIPTION = colorama.Fore.CYAN
    SAVING = colorama.Fore.YELLOW
    ERROR = colorama.Fore.RED
    SUCCESS = colorama.Fore.GREEN
    INFO = colorama.Fore.WHITE
    WARNING = colorama.Fore.YELLOW

# ASCII symbols for different categories (Windows-compatible)
class Emoji:
    NAVIGATION = "[NAV]"
    LISTING = "[LIST]"
    AI = "[AI]"
    DESCRIPTION = "[DESC]"
    SAVING = "[SAVE]"
    ERROR = "[ERR]"
    WARNING = "[WARN]"
    SUCCESS = "[OK]"
    INFO = "[INFO]"
    PROGRESS = "[PROG]"
    SEARCH = "[SRCH]"
    PAGE = "[PAGE]"

# Custom formatter for console output
class ColoredFormatter(logging.Formatter):
    def format(self, record):
        # Default formatting
        emoji = Emoji.INFO
        color = Colors.INFO
        
        # Categorize and color based on message content
        msg = record.getMessage()
        
        if "page" in msg.lower() or "url" in msg.lower() or "request" in msg.lower():
            emoji = Emoji.NAVIGATION
            color = Colors.NAVIGATION
            record.msg = f"{emoji} {Colors.BOLD}{Colors.NAVIGATION}PAGE NAVIGATION:{Colors.RESET} {record.msg}"
        elif "job card" in msg.lower() or "found job" in msg.lower() or "extract" in msg.lower() and "detail" in msg.lower():
            emoji = Emoji.LISTING
            color = Colors.LISTING
            record.msg = f"{emoji} {Colors.BOLD}{Colors.LISTING}JOB LISTINGS:{Colors.RESET} {record.msg}"
        elif "ai" in msg.lower() or "ai extraction" in msg.lower():
            emoji = Emoji.AI
            color = Colors.AI
            record.msg = f"{emoji} {Colors.BOLD}{Colors.AI}AI EXTRACTION:{Colors.RESET} {record.msg}"
        elif "description" in msg.lower() and not "ai" in msg.lower():
            emoji = Emoji.DESCRIPTION
            color = Colors.DESCRIPTION
            record.msg = f"{emoji} {Colors.BOLD}{Colors.DESCRIPTION}DESCRIPTION:{Colors.RESET} {record.msg}"
        elif "save" in msg.lower() or "saved" in msg.lower() or "saving" in msg.lower():
            emoji = Emoji.SAVING
            color = Colors.SAVING
            record.msg = f"{emoji} {Colors.BOLD}{Colors.SAVING}SAVING DATA:{Colors.RESET} {record.msg}"
        elif "error" in msg.lower() or "fail" in msg.lower() or "exception" in msg.lower():
            emoji = Emoji.ERROR
            color = Colors.ERROR
            record.msg = f"{emoji} {Colors.BOLD}{Colors.ERROR}ERROR:{Colors.RESET} {record.msg}"
        elif "warning" in msg.lower() or "could not" in msg.lower():
            emoji = Emoji.WARNING
            color = Colors.WARNING
            record.msg = f"{emoji} {Colors.BOLD}{Colors.WARNING}WARNING:{Colors.RESET} {record.msg}"
        elif "success" in msg.lower() or "complete" in msg.lower():
            emoji = Emoji.SUCCESS
            color = Colors.SUCCESS
            record.msg = f"{emoji} {Colors.BOLD}{Colors.SUCCESS}SUCCESS:{Colors.RESET} {record.msg}"
        elif "start" in msg.lower() or "beginning" in msg.lower() or "initializ" in msg.lower():
            emoji = Emoji.SEARCH
            color = Colors.INFO
            record.msg = f"{emoji} {Colors.BOLD}{Colors.INFO}STARTING:{Colors.RESET} {record.msg}"
        
        # Apply standard formatting
        return super().format(record)

# Create a base logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a formatter for console output
console_formatter = ColoredFormatter('%(message)s')

# Add a console handler with the colored formatter
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# The file handler will be set dynamically for each job search

# Load environment variables
load_dotenv()

# ScrapingBee API key
API_KEY = "SXE9F6ZZ8E8FGAFGE988REK5KABOUJJCZPSF7WHXMOK5ALSV2AJ9PXTVY23K6YMRZSOVJY3I0IFGEGDD"

# Indeed country URLs
INDEED_URLS = {
    'uk': 'https://uk.indeed.com',
    'us': 'https://www.indeed.com',
    # Add other countries as needed
}

# Helper function to print a box around text
def print_box(text, color=Colors.INFO, emoji=""):
    width = len(text) + 10
    box_top = f"{color}╔{'═' * width}╗{Colors.RESET}"
    box_bottom = f"{color}╚{'═' * width}╝{Colors.RESET}"
    box_content = f"{color}║{' ' * 4}{emoji} {text}{' ' * (width - len(text) - 5)}║{Colors.RESET}"
    
    print("\n" + box_top)
    print(box_content)
    print(box_bottom + "\n")

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
    
    def generate_filename(self, job_position, job_location, extension, include_timestamp=True):
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
    
    def configure_job_specific_logger(self, job_position, job_location):
        """
        Configure a job-specific logger
        
        Args:
            job_position (str): Job position used in the search
            job_location (str): Location used in the search
        """
        # Remove any existing file handlers
        for handler in logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                logger.removeHandler(handler)
        
        # Create a new log filename based on job position and location
        log_filename = f"{job_position.replace(' ', '_').lower()}_{job_location.replace(' ', '_').lower()}.log"
        log_path = os.path.join('logs', log_filename)
        
        # Create a new file handler with standard formatting (no colors or emojis)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        logger.info(f"Configured job-specific logger for '{job_position}' in '{job_location}'")
        logger.info(f"Log file: {log_path}")
    
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
                    logger.info(f"Successfully received response {Emoji.SUCCESS}")
                    
                    # Parse AI extraction data if it was requested
                    ai_data = None
                    if use_ai_extraction:
                        try:
                            # First check if AI extraction results are in the response headers
                            ai_extraction_header = response.headers.get('X-ScrapingBee-AI-Extraction')
                            if ai_extraction_header:
                                ai_data = json.loads(ai_extraction_header)
                                logger.info(f"Successfully extracted AI data from headers: {list(ai_data.keys())} {Emoji.SUCCESS}")
                            else:
                                # If not in headers, check if the response body is JSON
                                try:
                                    # Try to parse the response text as JSON
                                    json_data = json.loads(response.text)
                                    # Check if it has the expected AI extraction fields
                                    if isinstance(json_data, dict) and 'job_title' in json_data:
                                        ai_data = json_data
                                        logger.info(f"Successfully extracted AI data from response body: {list(ai_data.keys())} {Emoji.SUCCESS}")
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
                description = self._extract_description_from_html(html_content)
                if description:
                    logger.info(f"Successfully extracted job description ({len(description)} chars) {Emoji.SUCCESS}")
                    result['conventional'] = description
                    
                    # If AI extraction was requested and successful
                    if use_ai_extraction and ai_data:
                        result['ai'] = ai_data
                        logger.info(f"Successfully extracted AI data for job description {Emoji.SUCCESS}")
                    
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
    
    def _extract_description_from_html(self, html_content):
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
    
    def extract_job_data(self, html_content, fetch_descriptions=True, use_ai_extraction=True, delay_between_jobs=1, max_jobs=None):
        """
        Extract job data from HTML content
        
        Args:
            html_content (str): HTML content from Indeed
            fetch_descriptions (bool): Whether to fetch job descriptions
            use_ai_extraction (bool): Whether to use AI extraction
            delay_between_jobs (int): Delay in seconds between job description requests
            max_jobs (int): Maximum number of jobs to process
            
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
            logger.info(f"Found job count: {job_count} {Emoji.SUCCESS}")
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
                logger.info(f"Found {len(job_cards)} job cards using alternative selector {Emoji.SUCCESS}")
        else:
            logger.info(f"Found {len(job_cards)} job cards {Emoji.SUCCESS}")
        
        jobs = []
        job_count = 0
        
        for job_card in job_cards:
            # Check if we've reached the maximum number of jobs to process
            if max_jobs is not None and job_count >= max_jobs:
                logger.info(f"Reached maximum job limit of {max_jobs} while processing page")
                break
                
            try:
                job_data = self._extract_job_details(job_card)
                
                if job_data:
                    # Initialize description fields
                    job_data['description'] = ""
                    job_data['ai_data'] = {}
                    
                    # If enabled, immediately fetch the job description
                    if (fetch_descriptions or use_ai_extraction) and job_data['url'] != "Not available":
                        logger.info(f"Fetching description for: {job_data['title']} ({job_count+1}/{min(len(job_cards), max_jobs or len(job_cards))})")
                        
                        # Add a small delay to avoid overloading the API
                        time.sleep(delay_between_jobs)
                        
                        # Fetch and add the description
                        description_data = self.fetch_job_description(job_data['url'], use_ai_extraction)
                        
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
        
        # Extract next page URL
        next_page_url = None
        try:
            next_page_element = soup.find('a', {'aria-label': 'Next Page'})
            if next_page_element and 'href' in next_page_element.attrs:
                next_page_url = self.base_url + next_page_element['href']
                logger.info(f"Found next page URL: {next_page_url} {Emoji.SUCCESS}")
            else:
                logger.info("No next page URL found - this appears to be the last page")
        except Exception as e:
            logger.error(f"Error extracting next page URL: {str(e)}")
                
        return jobs, next_page_url, total_job_count
    
    def _extract_job_details(self, job_card):
        """
        Extract details from a job card
        
        Args:
            job_card: BeautifulSoup element for a job card
            
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
                
            job_url = self.base_url + url_element['href'] if url_element and 'href' in url_element.attrs else "Not available"
            
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
    
    def scrape_indeed_jobs(self, job_position, job_location, date_posted='', 
                          fetch_descriptions=True, use_ai_extraction=True,
                          max_jobs=None, max_pages=None, delay_between_pages=2, 
                          delay_between_jobs=1, save_progress=True):
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
        print_box(f"STARTING SEARCH: {job_position} in {job_location}", Colors.INFO, Emoji.SEARCH)
        
        # Configure job-specific logger
        self.configure_job_specific_logger(job_position, job_location)
        
        all_jobs = []
        indeed_url = self.construct_indeed_url(job_position, job_location, date_posted)
        current_page = 1
        next_page_url = None
        total_job_count = "Unknown"
        
        # Create filenames for progress saving - always include timestamp
        json_filename = self.generate_filename(job_position, job_location, 'json')
        json_path = os.path.join('data', json_filename)
        csv_filename = self.generate_filename(job_position, job_location, 'csv')
        csv_path = os.path.join('data', csv_filename)
        
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
                    jobs, next_page_url, page_total_job_count = self.extract_job_data(
                        html_content, 
                        fetch_descriptions=fetch_descriptions,
                        use_ai_extraction=use_ai_extraction,  # Pass the original value for job descriptions
                        delay_between_jobs=delay_between_jobs,
                        max_jobs=max_jobs - len(all_jobs) if max_jobs is not None else None
                    )
                    
                    # Update total job count if we got a valid count
                    if page_total_job_count != "Unknown":
                        total_job_count = page_total_job_count
                    
                    if jobs:
                        logger.info(f"Successfully scraped {len(jobs)} jobs on page {current_page} {Emoji.SUCCESS}")
                        all_jobs.extend(jobs)
                        
                        # Save progress after each page if enabled
                        if save_progress and all_jobs:
                            logger.info(f"Saving progress after page {current_page}...")
                            self.save_jobs_to_json(all_jobs, job_position, job_location, json_path)
                            self.save_jobs_to_csv(all_jobs, job_position, job_location, csv_path)
                            logger.info(f"Progress saved to {json_path} and {csv_path} {Emoji.SUCCESS}")
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

    def save_jobs_to_json(self, jobs, job_position=None, job_location=None, filename=None):
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
                filename = os.path.join('data', self.generate_filename(job_position, job_location, 'json'))
            else:
                filename = os.path.join('data', "indeed_jobs.json")  # Fallback to default
            
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Saved {len(jobs)} jobs to {filename} {Emoji.SUCCESS}")
    
    def save_jobs_to_csv(self, jobs, job_position=None, job_location=None, filename=None):
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
                filename = os.path.join('data', self.generate_filename(job_position, job_location, 'csv'))
            else:
                filename = os.path.join('data', "indeed_jobs.csv")  # Fallback to default
        
        df = pd.DataFrame(jobs)
        df.to_csv(filename, index=False)
        
        logger.info(f"Saved {len(jobs)} jobs to {filename} {Emoji.SUCCESS}")

def main():
    """Main function to run the scraper"""
    # Initialize the scraper
    scraper = ScrapingBeeIndeedScraper(country='uk')
    
    # Get user input
    job_position = input("Enter job title: ")
    job_location = input("Enter location: ")
    date_posted = input("Enter number of days (leave empty for any time): ")
    fetch_descriptions = input("Fetch job descriptions? (y/n): ").lower() == 'y'
    use_ai = input("Use AI extraction? (y/n): ").lower() == 'y'
    max_jobs = input("Maximum jobs to fetch for testing (leave empty for all): ")
    max_jobs = int(max_jobs) if max_jobs.strip() else None
    
    # Scrape jobs
    jobs = scraper.scrape_indeed_jobs(
        job_position=job_position,
        job_location=job_location,
        date_posted=date_posted,
        fetch_descriptions=fetch_descriptions,
        use_ai_extraction=use_ai,
        max_jobs=max_jobs
    )
    
    # Results are already saved in the scrape_indeed_jobs method
    if jobs:
        print(f"Successfully scraped {len(jobs)} jobs")
        print(f"Results saved to data folder with timestamp in filename")
    else:
        print("No jobs found. Check the logs for details.")


if __name__ == "__main__":
    main()