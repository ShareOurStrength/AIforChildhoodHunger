import requests
import os
from dotenv import load_dotenv

api_key = os.environ.get("bing_api_key")
headers = {'Ocp-Apim-Subscription-Key': api_key}
endpoint = 'https://api.bing.microsoft.com/v7.0/search'

# List of all 50 U.S. states
states = ["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
          "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
          "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
          "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
          "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
          "New Hampshire", "New Jersey", "New Mexico", "New York",
          "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
          "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
          "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
          "West Virginia", "Wisconsin", "Wyoming"]

# Queries to be formatted with each state name
queries = ["{} SNAP eligibility website", "{} SNAP eligibility pdf",
           "{} SNAP office locations", "{} WIC program information"]

# List to hold all results, TODO: short script to put this in Azure DataTable
results = []

def fetch_most_relevant_link(query):
    """Fetch the most relevant link for a given query using the Bing Search API."""
    params = {'q': query, 'count': 1}  # Fetch only the most relevant result for each section of our table
    response = requests.get(endpoint, headers=headers, params=params)
    response.raise_for_status() 
    data = response.json()
    try:
        # Attempt to extract the URL of the first search result
        return data['webPages']['value'][0]['url']
    except (KeyError, IndexError):
        # Return None if no results are found or if any keys are missing, TODO: Handle this differently as we cannot have blank spaces
        return None

for state in states:
    for query_template in queries:
        query = query_template.format(state)
        link = fetch_most_relevant_link(query)
        results.append((query, link))

# Note that in this current state `results` contains tuples of (query, link) for all queries
