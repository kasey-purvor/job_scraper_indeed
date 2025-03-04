"""
Logging utilities for the Indeed Job Scraper
"""
import logging
import os
import sys
import colorama
from datetime import datetime

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
logger = logging.getLogger('scraper')
logger.setLevel(logging.INFO)

# Create a formatter for console output
console_formatter = ColoredFormatter('%(message)s')

# Add a console handler with the colored formatter
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# Helper function to print a box around text
def print_box(text, color=Colors.INFO, emoji=""):
    width = len(text) + 10
    box_top = f"{color}╔{'═' * width}╗{Colors.RESET}"
    box_bottom = f"{color}╚{'═' * width}╝{Colors.RESET}"
    box_content = f"{color}║{' ' * 4}{emoji} {text}{' ' * (width - len(text) - 5)}║{Colors.RESET}"
    
    print("\n" + box_top)
    print(box_content)
    print(box_bottom + "\n")

def configure_job_specific_logger(job_position, job_location):
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
