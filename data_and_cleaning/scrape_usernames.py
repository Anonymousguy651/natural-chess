import requests
from bs4 import BeautifulSoup
import re

def scrape_usernames(url, output_file):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch the webpage: {response.status_code}")
        return

    soup = BeautifulSoup(response.content, "html.parser")
    
    # Find the h2 containing the text "Standard"
    standard_section = None
    for h2 in soup.find_all('h2'):
        if h2.get_text(strip=True) == 'Standard':
            standard_section = h2
            break
    
    if not standard_section:
        print("Standard section not found.")
        return

    # Collect usernames
    usernames = set()  # Using a set to avoid duplicates
    current_element = standard_section.find_next_sibling()
    current_section = None
    
    while current_element:
        # If we hit another h2, we've left the Standard section
        if current_element.name == "h2":
            break
            
        # If it's an h3, check if it's a section we want to skip
        if current_element.name == "h3":
            current_section = current_element.get_text(strip=True).lower()
            current_element = current_element.find_next_sibling()
            continue
            
        # Skip unwanted sections
        if current_section in ["chess960", "ultrabullet", "other"]:
            current_element = current_element.find_next_sibling()
            continue
        
        # Look for links that point to user profiles
        for a_tag in current_element.find_all('a', href=True):
            href = a_tag['href']
            # Match Lichess user profile URLs
            match = re.match(r'https://lichess\.org/@/([^/]+)', href)
            if match:
                username = match.group(1).strip()
                if username:  # Only add non-empty usernames
                    usernames.add(username)
        
        current_element = current_element.find_next_sibling()

    # Write the usernames to the output file
    with open(output_file, "w") as file:
        for username in sorted(usernames):  # Sort them alphabetically
            file.write(username + "\n")

    print(f"Saved {len(usernames)} unique usernames to {output_file}.")

if __name__ == "__main__":
    BLOG_URL = "https://lichess.org/@/CyberShredder/blog/cool-lichess-studies-list/UOPFWocV"
    OUTPUT_FILE = "study_authors.txt"

    scrape_usernames(BLOG_URL, OUTPUT_FILE)