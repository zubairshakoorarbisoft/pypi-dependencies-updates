import requests
from bs4 import BeautifulSoup
import re
from read_dependency_packages import get_dependencies


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

            # Define a regex pattern for GitHub and GitLab repository links
            github_pattern = re.compile(r'https://(www\.)?(github\.com|gitlab\.com)/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?$')

            # Extract and print links that match the GitHub pattern
            links = list(set([link['href'] for link in link_elements if 'github.com' in link['href'] and github_pattern.match(link['href'])]))

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
