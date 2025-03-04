# Indeed Job Scraper

A powerful and flexible web scraper for extracting job listings from Indeed.com using the ScrapingBee API.

## Overview

This program allows you to search for job listings on Indeed.com based on job titles, locations, and other criteria. It uses the ScrapingBee API to handle the web scraping, which helps avoid IP blocking and CAPTCHAs. The scraper can extract job titles, companies, locations, posting dates, and full job descriptions. It also supports AI-powered extraction for structured data from job descriptions.

## Features

- **Multi-country Support**: Search for jobs in different countries (UK, US, etc.)
- **Customizable Search**: Filter by job title, location, and date posted
- **Job Description Extraction**: Automatically fetch and parse full job descriptions
- **AI-powered Data Extraction**: Use ScrapingBee's AI to extract structured data from job descriptions
- **Pagination Handling**: Automatically navigate through multiple pages of search results
- **Data Export**: Save results in both JSON and CSV formats
- **Colorful Logging**: Detailed, categorized, and color-coded logging for better visibility
- **Progress Saving**: Save progress after each page to prevent data loss
- **Configurable Limits**: Set maximum jobs and pages to scrape
- **Robust Error Handling**: Multiple fallback methods for HTML parsing

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd job_scraper_indeed
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root directory with your ScrapingBee API key:
   ```
   SCRAPINGBEE_API_KEY=your_api_key_here
   ```

## Usage

### Command Line Interface

Run the scraper using the command line interface:

```
python main.py [options]
```

### Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--job` | Single job title to search for | None |
| `--jobs` | Multiple job titles to search for (space separated) | None |
| `--location` | Location to search in | "london" |
| `--days` | Filter for jobs posted within X days | "" (any time) |
| `--country` | Country code for Indeed | "uk" |
| `--delay-pages` | Delay in seconds between page requests | 2 |
| `--delay-jobs` | Delay in seconds between job description requests | 1 |
| `--descriptions` | Fetch job descriptions | True |
| `--no-descriptions` | Do not fetch job descriptions | - |
| `--ai` | Use ScrapingBee AI extraction for structured data | True |
| `--no-ai` | Disable ScrapingBee AI extraction | - |
| `--pagination-test` | Test pagination only (skips job descriptions) | False |
| `--max-jobs` | Maximum number of jobs to process | None (no limit) |
| `--max-pages` | Maximum number of pages to scrape | None (no limit) |
| `--debug` | Enable debug logging | False |
| `--use-default-jobs` | Use the default list of job titles | False |
| `--junior-only` | Only search for junior positions from the default list | False |
| `--graduate-only` | Only search for graduate positions from the default list | False |

### Examples

Search for a single job title:
```
python main.py --job "data scientist" --location "london" --days 7
```

Search for multiple job titles:
```
python main.py --jobs "data scientist" "machine learning engineer" --location "london"
```

Use default job titles (defined in main.py):
```
python main.py --use-default-jobs --location "london"
```

Limit the number of jobs and pages:
```
python main.py --job "data engineer" --location "london" --max-jobs 50 --max-pages 5
```

Test pagination without fetching job descriptions:
```
python main.py --job "data analyst" --location "london" --pagination-test
```

## Output

The scraper saves the results in two formats:

1. **JSON**: Complete job data including descriptions and AI-extracted information
2. **CSV**: Tabular format suitable for spreadsheet applications

Files are saved in the `data` directory with filenames based on the job title, location, and timestamp.

## Project Structure

```
job_scraper_indeed/
├── main.py                  # Main entry point with CLI
├── job_scraper_utils.py     # General utility functions
├── scraping_bee_scraper.py  # Legacy scraper implementation
├── requirements.txt         # Project dependencies
├── .gitignore               # Git ignore file
├── scraper/                 # Core scraper module
│   ├── __init__.py          # Package initialization
│   ├── constants.py         # API keys and URLs
│   ├── core.py              # Core scraper implementation
│   ├── file_utils.py        # File operations
│   ├── html_parser.py       # HTML parsing functions
│   └── logging_utils.py     # Logging configuration
├── data/                    # Output directory for scraped data
└── logs/                    # Log files directory
```

## Dependencies

- **requests**: HTTP requests
- **beautifulsoup4**: HTML parsing
- **pandas**: Data manipulation and CSV export
- **colorama**: Colored terminal output
- **python-dotenv**: Environment variable management
- **lxml**: XML/HTML processing (used by BeautifulSoup)

## Notes

- The scraper respects Indeed's terms of service by using reasonable delays between requests.
- ScrapingBee API usage is subject to their pricing and rate limits.
- Debug HTML files are saved in the `logs` directory for troubleshooting.
