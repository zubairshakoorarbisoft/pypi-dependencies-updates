import os
import requests
from bs4 import BeautifulSoup
from fetch_dependencies import get_dependencies


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
        'logilab.fr',
        'heptapod.net'
    ]
    filtered_urls = []

    for url in urls:
        num_slashes = url.count('/')

        if num_slashes <= 5 and any(domain in url for domain in version_controlling_domains):
            filtered_urls.append(get_substring_before_fifth_slash(url) if num_slashes == 5 else url)
        elif num_slashes > 5 and 'sourceforge.net' in url and url.endswith(("tree/", "tree")):
            filtered_urls.append(url)
        elif num_slashes > 5 and 'sdk/storage/azure-storage-blob' in url:  # only for azure-sdk-for-python
            filtered_urls.append(url)

    return filtered_urls


def write_to_file(file_path, data):
    with open(file_path, 'w') as output_file:
        output_file.write("# GitHub links for PyPI packages\n")
        output_file.write("github_links = [\n")
        for package, github_url in data.items():
            output_file.write(f'    {{"dependency": "{package}", "source": "{github_url}"}},\n')
        output_file.write("]\n")


def is_git_supported(url):
    git_domains = [
        "github.com",
        "gitlab.com",
        "bitbucket.org",
        "gitea.io",
        "gitkraken.com",
        "sourcetreeapp.com",
        "dev.azure.com",
        "sourceforge.net"
    ]

    # Extract domain from the URL
    domain = url.split('//')[-1].split('/')[0].lower()

    # Check if the domain is in the list of git domains
    return any(git_domain in domain for git_domain in git_domains)


def scrape_source_code_url(dependency_name):
    url = f"https://pypi.org/project/{dependency_name}/"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Step 1: Check for Project Links Tab
        project_links_section = soup.find('h3', {'class': 'sidebar-section__title'}, text='Project links')
        
        if project_links_section:
            parent_div = project_links_section.find_parent('div', {'class': 'sidebar-section'})
            link_elements = parent_div.find('ul', {'class': 'vertical-tabs__list'}).find_all('a')
            links = list(set(filter_urls([link['href'] for link in link_elements])))
            return links[0] if links else "No Github Link"
        
        # Step 2: If Project Links Tab is not found, try to get releases history
        history_url = f"https://pypi.org/project/{dependency_name}#history"
        history_response = requests.get(history_url)
        history_response.raise_for_status()
        history_soup = BeautifulSoup(history_response.text, 'html.parser')
        
        # Step 3: Find up to 10 latest versions from release history
        release_versions = [
            p.text.split('\n')[0].strip() if '\n' in p.text else p.text.strip() for p in history_soup.find_all('p', {'class': 'release__version'})
        ][:10]
        
        # Step 4: Iterate through versions to find Project Links
        for version in release_versions:
            url_with_version = f"https://pypi.org/project/{dependency_name}/{version}"
            version_response = requests.get(url_with_version)
            version_response.raise_for_status()
            version_soup = BeautifulSoup(version_response.text, 'html.parser')
            
            project_links_section = version_soup.find('h3', {'class': 'sidebar-section__title'}, text='Project links')
            
            if project_links_section:
                parent_div = project_links_section.find_parent('div', {'class': 'sidebar-section'})
                link_elements = parent_div.find('ul', {'class': 'vertical-tabs__list'}).find_all('a')
                links = list(set(filter_urls([link['href'] for link in link_elements])))
                return links[0] if links else "No Github Link"
        
        # If Project Links are not found in any version, return the appropriate message
        return "No Github Link in Release History"
    
    except requests.RequestException as e:
        print(f"Failed to retrieve the webpage for {url}. Exception: {e}")
        return f"Failed to retrieve the webpage for {url}"


def clear_file(file_path):
    with open(file_path, 'w') as output_file:
        output_file.truncate(0)

def scrape_links():
    csv_path = 'dashboard_main.csv'
    column_name = 'dependencies.pypi_all.list'
    github_links_file = 'github_links.py'
    # Clear the contents of the github_links.py file
    clear_file(github_links_file)

    github_links = {}
    to_return_links = []

    for dependency_name in get_dependencies(csv_path, column_name):
        source_code_link = scrape_source_code_url(dependency_name)
        github_links[dependency_name] = source_code_link
        to_return_links.append(
            {
                "dependency": dependency_name,
                "source": source_code_link,
                "is_git_supported": is_git_supported(source_code_link)
            }
        )
        # write_to_file(github_links_file, github_links)
    
    return to_return_links


if __name__ == "__main__":
    scrape_links()
