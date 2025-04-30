import re
from os import listdir
from os.path import isfile, join
import datetime
from tqdm import tqdm

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

class PodcastDataPoint:
    """
    Represents a single Podcast.
    Contains date information and episode transcription.
    """
    def __init__(self, year, month, day, episode):
        """
        Initialize data point with date information.
        
        Args:
            year: Year of the Podcast
            month: Month of the Podcast
            day: Day of the Podcast
        """
        self.year = year
        self.month = month
        self.day = day
        self.episode= episode
        self.text = None   

    def __str__(self):
        """String representation of the data point."""
        return f"Date: {self.month}-{self.day}-{self.year}\n{self.episode}\n{self.text}\n"

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
    
    @staticmethod
    def load_buzz_data(path="/bucket/clean_data/usable_buzz_data.txt"):
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

    @staticmethod
    def load_pod_data(path="/bucket/podcast_scraper/spittin-chiclets"):
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
        
        podcast_files = [f for f in listdir(path) if isfile(join(path, f))]
        
        for file in tqdm(podcast_files, desc="Loading Files into Dataset"):
            with open(join(path, file), 'r') as ofile:
                #get date from file-name
                episode= file.split("|")[0]
                date= file.split("|")[1][0:-4]
                
                date_dt= datetime.datetime.strptime(date, '%Y-%m-%d')
            
                # Extract date components
                month = date_dt.month
                day = date_dt.day
                year = date_dt.year
                
                data_point = PodcastDataPoint(year=year, month=month, day=day, episode=episode)
                for line in ofile:
                    line = line.strip()
                    # Accumulate text content
                    text+=line
                data_point.text=text
                inputs.append(data_point)
        return inputs   