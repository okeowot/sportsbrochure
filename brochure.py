from urllib.parse import urljoin
import os
import requests
import json
from typing import List
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from IPython.display import Markdown, display, update_display
from openai import OpenAI


load_dotenv(override=True)
MODEL = 'gpt-4o-mini'
openai = OpenAI()
# A class to represent a Webpage

# Some websites need you to use proper headers when fetching them:
headers = {
 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

class Website:
    """
    A utility class to represent a Website that we have scraped, now with links
    """

    def __init__(self, url):
        self.url = url
        response = requests.get(url, headers=headers)
        self.body = response.content
        soup = BeautifulSoup(self.body, 'html.parser')
        self.title = soup.title.string if soup.title else "No title found"
        if soup.body:
            for irrelevant in soup.body(["script", "style", "img", "input"]):
                irrelevant.decompose()
            self.text = soup.body.get_text(separator="\n", strip=True)
        else:
            self.text = ""
        links = [link.get('href') for link in soup.find_all('a')]
        self.links = [link for link in links if link]

    def get_contents(self):
        return f"Webpage Title:\n{self.title}\nWebpage Contents:\n{self.text}\n\n"
    
system_prompt_link = "You are provided with a list of links from a wikipedia webpage that contains stats in a season of a sporting event. \
You are able to decide what links would be relevant for the sporting event and it's equivalent season.\n"

system_prompt_link += "You should respond in JSON as in this example:"
system_prompt_link += """
{
    "links":[
        {"type":"Revelant link title", "url":"https://relevant.full.url/"},
        
    ]

}
"""

system_prompt_sports_season = "You are an exciting eagles sports analyst provided with a wikipedia webpage that contains stats in a season of a sporting events and the contents of several relevant webpages. \
You are able to decide what sporting event is being talked about in the webpage and what season. respond in markdown\n"
system_prompt_sports_season += "You should be able to analyze the webpages and provide a fully detailed humorous, entertaining, jokey brochure of the whole season,\
providing information about the players, the teams, the records of the teams, the rivalries, the divisions and conferences, the coaches, \
the winner of the season, list the players of the week and players of the month that had repeats in frequent months\
any news during that season awards and any other thing you feel is important as a sports analyst would\n" 
system_prompt_sports_season += "You should respond with the Sports: sports name and the Season: season name\n"

def get_links_user_prompt_sports(website):
    user_prompt = f"Here is the list of links on the website of {website.url} - "
    user_prompt += "please decide which of these are relevant web links for stats in a season of a sporting event. \
    You are able to decide what links would be relevant for the sporting event and it's equivalent season..\n"
    user_prompt += "Links (some might be relative links):\n"
    user_prompt += "\n".join(website.links)
    return user_prompt

def get_links_sports(url):
    website = Website(url)
    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt_link},
            {"role": "user", "content": get_links_user_prompt_sports(website)}
      ],
        response_format={"type": "json_object"}
    )
    result = response.choices[0].message.content
    return json.loads(result)

def get_sports_brochure_user_prompt(url):
    user_prompt = f"Here are the contents of its landing page and other relevant pages; use this information to build a a fully detailed humorous, entertaining, jokey brochure of the whole season.\n"
    user_prompt += get_all_dets_sports(url)
    user_prompt = user_prompt[:50_000] # Truncate if more than 5,000 characters
    return user_prompt

def get_all_dets_sports(url):
    result = "Landing page:\n"
    result += Website(url).get_contents()
    links = get_links_sports(url)

    base_url = "https://en.wikipedia.org"

    for link in links["links"]:
        full_url = urljoin(base_url, link["url"])  # Ensures absolute URL
        result += f"\n\n{link['type']}:\n"
        result += Website(full_url).get_contents()
    
    return result


def get_season_summary_with_links(url):
    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt_sports_season},
            {"role": "user", "content": get_sports_brochure_user_prompt(url)}
      ],
    )
    result = response.choices[0].message.content
    print(result)
    return result


get_season_summary_with_links('https://en.wikipedia.org/wiki/2024_NFL_season')