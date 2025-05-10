import re
from webScraper import Webscraper
import os

class BuzzDataPoint:
    """
    Represents a single NHL Buzz news entry.
    Contains date information, team name, and article text.
    """
    def __init__(self, year, month, day):
        """
        Initialize data point with date information.
        
        Args:
            year: Year of the article
            month: Month of the article
            day: Day of the article
        """
        self.year = year
        self.month = month
        self.day = day
        self.text = None   
        self.team = None 

    def __str__(self):
        """String representation of the data point."""
        return f"Date: {self.month}-{self.day}-{self.year}\n{self.team}\n{self.text}\n"
    
# Dictionary of all NHL teams for identification in text
nhl_teams = {
    "Anaheim Ducks": 1,
    "Arizona Coyotes": 1,
    "Boston Bruins": 1,
    "Buffalo Sabres": 1,
    "Calgary Flames": 1,
    "Carolina Hurricanes": 1,
    "Chicago Blackhawks": 1,
    "Colorado Avalanche": 1,
    "Columbus Blue Jackets": 1,
    "Dallas Stars": 1,
    "Detroit Red Wings": 1,
    "Edmonton Oilers": 1,
    "Florida Panthers": 1,
    "Los Angeles Kings": 1,
    "Minnesota Wild": 1,
    "Montreal Canadiens": 1,
    "Nashville Predators": 1,
    "New Jersey Devils": 1,
    "New York Islanders": 1,
    "New York Rangers": 1,
    "Ottawa Senators": 1,
    "Philadelphia Flyers": 1,
    "Pittsburgh Penguins": 1,
    "San Jose Sharks": 1,
    "Seattle Kraken": 1,
    "St. Louis Blues": 1,
    "Tampa Bay Lightning": 1,
    "Toronto Maple Leafs": 1,
    "Vancouver Canucks": 1,
    "Vegas Golden Knights": 1,
    "Washington Capitals": 1,
    "Winnipeg Jets": 1
}

class DataCleaner:
    """
    Cleans and processes NHL Buzz data for training.
    Handles text cleaning, formatting, and data loading.
    """
    def run(self, clean=True, load=True):
        """
        Execute data cleaning and loading workflow.
        
        Args:
            clean: Whether to clean the data
            load: Whether to load the cleaned data
            
        Returns:
            List of BuzzDataPoint objects if load is True, None otherwise
        """
        data = None
        os.makedirs("/mnt/gcs/buzz/clean_data", exist_ok=True)
        if clean:
            self.proccess_nhl_buzz_data()
            self.remove_empty_dates()
        if clean and load:
            data = self.load_buzz_data()
        return data

    def clean_data_charaters(self, path, path_to_write):
        """
        Clean unwanted characters from a file and write to another file.
        
        Args:
            path: Input file path
            path_to_write: Output file path
        """
        with open(path, 'r') as ofile:
            with open(path_to_write, 'w') as wfile:
                for line in ofile:
                    text = self.clean_line(line)  # Clean each line
                    wfile.write(text + "\n")  # Write cleaned line to output file

    def clean_line(self, text):
        """
        Remove unwanted characters from a line of text.
        
        Args:
            text: Text to clean
            
        Returns:
            str: Cleaned text
        """
        text = re.sub(r"[^A-Za-z0-9'/\.,;\-\+=: \"\']", "", text)
        return text.strip()

    def proccess_nhl_buzz_data(self):
        """
        Clean NHL Buzz data and count tokens in the result.
        """
        path = "/mnt/gcs/buzz/nhl_buzz_data.txt"
        path_to_write = "/mnt/gcs/buzz/clean_data/clean_nhl_buzz_data.txt"
        self.clean_data_charaters(path, path_to_write)
        self.count_tokens(path_to_write)

    def count_tokens(self, path):
        """
        Count and print the total number of words in a file.
        
        Args:
            path: Path to the file
        """
        total = 0
        with open(path, 'r') as ofile:
            for line in ofile:
                tokens = line.split(" ")
                total += len(tokens)
        print(f"Total tokens found in {path}: {total}", flush=True)

    def remove_empty_dates(self, path="/mnt/gcs/buzz/clean_data/clean_nhl_buzz_data.txt", path_to_write="/mnt/gcs/buzz/clean_data/usable_buzz_data.txt"):
        """
        Remove entries with a date but no content.
        
        Args:
            path: Input file path
            path_to_write: Output file path
        """
        with open(path, 'r') as ofile:
            with open(path_to_write, 'w') as wfile:
                string_to_write = ""
                for line in ofile:
                    # If line is a date pattern
                    if re.match(r"^[A-Za-z]+-\d+-\d{4}:$", line):
                        if not string_to_write:
                            string_to_write += line
                    else:
                        string_to_write += line
                        wfile.write(string_to_write)
                        string_to_write = ""
    
    @staticmethod
    def load_buzz_data(path="/mnt/gcs/buzz/clean_data/usable_buzz_data.txt"):
        """
        Load and parse NHL Buzz data into structured objects.
        
        Args:
            path: Path to cleaned data file
            
        Returns:
            List of BuzzDataPoint objects
        """
        inputs = []
        data_point = None
        text = ""
        month = None
        day = None
        year = None
        
        with open(path, 'r') as ofile:
            for line in ofile:
                line = line.strip()
                # Check if line is a date pattern
                date = re.match(r"^([A-Za-z]+)-(\d+)-(\d{4}):$", line)
                
                if not line:
                    continue
                elif date:
                    # Extract date components
                    month = date.group(1)
                    day = date.group(2)
                    year = date.group(3)
                    
                    # Save previous data point if exists
                    if data_point:
                        data_point.text = text
                        inputs.append(data_point)
                        text = ""
                        
                elif line in nhl_teams:
                    # Save previous data point if exists
                    if text:
                        data_point.text = text
                        inputs.append(data_point)
                        text = ""
                        
                    # Create new data point for this team
                    data_point = BuzzDataPoint(year=year, month=month, day=day)
                    data_point.team = line
                    
                else:
                    # Accumulate text content
                    if text:
                        text += " " + line
                    else:
                        text += line
                        
            # Save the last data point
            if data_point:  # Added check if data_point exists
                data_point.text = text
                inputs.append(data_point)
                
        return inputs

if __name__ == "__main__":
    Webscraper().run()
    DataCleaner().run()