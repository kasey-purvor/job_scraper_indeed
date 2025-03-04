from dotenv import load_dotenv
from scraper import ScrapingBeeIndeedScraper
import argparse
import logging

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Country codes for reference
COUNTRIES = {
    'uk': 'United Kingdom',
    # 'us': 'United States',
    # 'ca': 'Canada',
    # 'au': 'Australia',
    # 'de': 'Germany',
    # 'fr': 'France',
    # 'in': 'India',
    # 'sg': 'Singapore',
    # 'ie': 'Ireland',
    # Add more as needed
}

# Default job titles to search for
DEFAULT_JOB_TITLES = [
    "junior ai engineer"
    # Junior positions
    # "junior data engineer",
    # "junior data scientist",
    # "junior data analyst",
    # "junior machine learning engineer",
    # Graduate positions
    # "graduate data engineer",
    # "graduate data scientist",
    # "graduate data analyst",
    # "graduate machine learning engineer"
]

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Indeed Job Scraper using ScrapingBee')
    parser.add_argument('--job', type=str, default=None,
                        help='Single job title to search for')
    parser.add_argument('--jobs', type=str, nargs='+', default=None,
                        help='Multiple job titles to search for (space separated)')
    parser.add_argument('--location', type=str, default='london',
                        help='Location to search in')
    parser.add_argument('--days', type=str, default='',
                        help='Filter for jobs posted within X days')
    parser.add_argument('--country', type=str, default='uk',
                        help=f'Country code for Indeed (available: {", ".join(COUNTRIES.keys())})')
    parser.add_argument('--delay-pages', type=int, default=2,
                        help='Delay in seconds between page requests (default: 2)')
    parser.add_argument('--delay-jobs', type=int, default=1,
                        help='Delay in seconds between job description requests (default: 1)')
    parser.add_argument('--descriptions', action='store_true', default=True,
                        help='Fetch job descriptions (default: True)')
    parser.add_argument('--no-descriptions', action='store_false', dest='descriptions',
                        help='Do not fetch job descriptions')
    parser.add_argument('--ai', action='store_true', default=True,
                        help='Use ScrapingBee AI extraction for structured data (default: True)')
    parser.add_argument('--no-ai', action='store_false', dest='ai',
                        help='Disable ScrapingBee AI extraction')
    parser.add_argument('--pagination-test', action='store_true',
                        help='Test pagination only - skips job description fetching and processes minimal jobs per page')
    parser.add_argument('--max-jobs', type=int, default=None,
                        help='Maximum number of jobs to process (default: no limit)')
    parser.add_argument('--max-pages', type=int, default=None,
                        help='Maximum number of pages to scrape (default: no limit)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')
    parser.add_argument('--use-default-jobs', action='store_true',
                        help='Use the default list of job titles')
    parser.add_argument('--junior-only', action='store_true',
                        help='Only search for junior positions from the default list')
    parser.add_argument('--graduate-only', action='store_true',
                        help='Only search for graduate positions from the default list')
    
    return parser.parse_args()

def main():
    """Main function to run the ScrapingBee scraper"""
    args = parse_arguments()
    
    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("Debug logging enabled")
    
    # Determine which job titles to search for
    job_titles = []
    
    if args.job:
        # Single job title specified
        print(f"Using single specified job title: '{args.job}'")
        job_titles = [args.job]
    elif args.jobs:
        print(f"Using multiple specified job titles: {', '.join(args.jobs)}")
        # Multiple job titles specified
        job_titles = args.jobs
    elif args.use_default_jobs:
        # Use default job titles
        print("Using default job titles", DEFAULT_JOB_TITLES)
        job_titles = DEFAULT_JOB_TITLES
        
        # Filter for junior or graduate positions if requested
        if args.junior_only:
            job_titles = [title for title in DEFAULT_JOB_TITLES if title.startswith("junior")]
        elif args.graduate_only:
            job_titles = [title for title in DEFAULT_JOB_TITLES if title.startswith("graduate")]
    else:
        # No job titles specified, use the first default job title
        job_titles = [DEFAULT_JOB_TITLES[0]]
        print(f"No job titles specified. Using default: '{job_titles[0]}'")
        print(f"To use all default job titles, use the --use-default-jobs flag")
    
    # Initialize the scraper
    scraper = ScrapingBeeIndeedScraper(country=args.country)
    
    # Print general information
    print(f"Starting Indeed job scraper for {len(job_titles)} job title(s) in '{args.location}' ({COUNTRIES.get(args.country, args.country)})")
    print(f"Job description fetching: {'Enabled' if args.descriptions else 'Disabled'}")
    print(f"AI extraction: {'Enabled' if args.ai else 'Disabled'}")
    if args.max_jobs:
        print(f"Testing mode: Limited to {args.max_jobs} jobs per search")
    
    # Run the scraper for each job title
    total_jobs = 0
    for job_title in job_titles:
        print(f"\n{'='*80}")
        print(f"Searching for: '{job_title}'")
        
        # Scrape jobs
        jobs = scraper.scrape_indeed_jobs(
            job_position=job_title,
            job_location=args.location,
            date_posted=args.days,
            fetch_descriptions=args.descriptions,
            use_ai_extraction=args.ai,
            max_jobs=args.max_jobs,
            max_pages=args.max_pages,
            delay_between_pages=args.delay_pages,
            delay_between_jobs=args.delay_jobs,
            save_progress=True,  # Enable saving progress after each page
            pagination_test=args.pagination_test  # Pass the pagination test flag
        )
        
        # Save results
        if jobs:
            # Files are saved within the scrape_indeed_jobs method with job-specific filenames
            filename_base = job_title.replace(' ', '_').lower() + '_' + args.location.replace(' ', '_').lower()
            print(f"Successfully scraped {len(jobs)} jobs")
            print(f"Results saved to {filename_base}.json and {filename_base}.csv")
            total_jobs += len(jobs)
        else:
            print(f"No jobs found for '{job_title}'. Check the logs for details.")
    
    print(f"\n{'='*80}")
    print(f"Scraping complete. Total jobs found across all searches: {total_jobs}")


if __name__ == "__main__":
    main()
