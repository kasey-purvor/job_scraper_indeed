"""
Constants for the Indeed Job Scraper
"""
import os
from dotenv import load_dotenv

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
