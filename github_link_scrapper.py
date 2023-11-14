import requests
from bs4 import BeautifulSoup
import re
from fetch_dependencies import get_dependencies
from github_links import github_links as all_github_links


def get_substring_before_fifth_slash(url):
    # Split the URL by slashes
    components = url.split('/')

    # Join the first five components back together
    substring = '/'.join(components[:5])

    return substring

def filter_urls(urls):
    version_controlling_domains = [
        'github.com',
        'gitlab.com',
        'opendev.org',
        'bitbucket.org',
        'logilab.fr'
    ]
    filtered_urls = []

    for url in urls:
        # Count the number of forward slashes in the URL
        num_slashes = url.count('/')
        
        # Check if the URL contains a maximum of 5 forward slashes and belongs to an allowed domain
        if num_slashes <= 5 and any(domain in url for domain in version_controlling_domains):
            if num_slashes is 5:
                filtered_urls.append(get_substring_before_fifth_slash(url))
            else:
                filtered_urls.append(url)

    return filtered_urls

def write_to_file(file_path, data):
    with open(file_path, 'w') as output_file:
        output_file.write("# GitHub links for PyPI packages\n")
        output_file.write("github_links = [\n")
        for package, github_url in data.items():
            output_file.write(f'    {{"dependency": "{package}", "github_url": "{github_url}"}},\n')
        output_file.write("]\n")

github_links = {}
webpage_failed = []
no_project_links = []
csv_path = 'dashboard_main.csv'
column_name = 'dependencies.pypi_all.list'
# dep_not_have_github_links = [dependency for dependency in all_github_links if dependency['github_url'] == 'No Github Link']
for dependency_name in get_dependencies(
        csv_path,
        column_name
    ):
    # URL of the webpage
    url = f"https://pypi.org/project/{dependency_name}/"

    # Send a GET request to the URL
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the section with the title "Project links"
        project_links_section = soup.find('h3', {'class': 'sidebar-section__title'}, text='Project links')

        # Check if the section is found
        if project_links_section:
            # Navigate up to the parent <div> tag
            parent_div = project_links_section.find_parent('div', {'class': 'sidebar-section'})

            # Find all <a> tags within the <ul> tag
            link_elements = parent_div.find('ul', {'class': 'vertical-tabs__list'}).find_all('a')

            # Extract and print links that match the GitHub pattern
            links = filter_urls(list(set([link['href'] for link in link_elements])))

            github_links[dependency_name] = links[0] if len(links) > 0 else "No Github Link"
            
            # Write the current GitHub link to the file
            write_to_file("github_links.py", github_links)
        else:
            github_links[dependency_name] = "No Project Links Tab"
            write_to_file("github_links.py", github_links)
            no_project_links.append(url)
            print("Project links section not found on the webpage.")
    else:
        webpage_failed.append(url)
        print(f"Failed to retrieve the webpage for {url}. Status code:", response.status_code)
        github_links[dependency_name] = f"Failed to retrieve the webpage for {url}"
        write_to_file("github_links.py", github_links)


print(f"webpage_failed: {len(webpage_failed)}")
print(f"no_project_links: {len(no_project_links)}")
