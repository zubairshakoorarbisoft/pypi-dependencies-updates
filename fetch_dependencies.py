import pandas as pd
import re
import os
import certifi

# Set SSL_CERT_FILE for this script
os.environ['SSL_CERT_FILE'] = certifi.where()

import pandas as pd
import re
import requests
from requests.auth import HTTPBasicAuth
import shutil
from constants import GITHUB_ACCESS_TOKEN

# GitHub raw URL for the file
GITHUB_RAW_URL = "https://raw.githubusercontent.com/edx/repo-health-data/master/dashboards/dashboard_main.csv"



def download_file(url, local_filename, token):
    headers = {'Authorization': f'token {token}'}
    with requests.get(url, headers=headers, stream=True) as response:
        with open(local_filename, 'wb') as file:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, file)

def get_dependencies(csv_path, column_name):
    download_file(
        GITHUB_RAW_URL,
        csv_path,
        GITHUB_ACCESS_TOKEN
    )
    df = pd.read_csv(csv_path)

    # Extract and combine dependency names
    all_dependencies = set()

    for dependencies_list in df[column_name]:
        if isinstance(dependencies_list, str):
            dependencies = eval(dependencies_list)
            dependency_names = [re.sub(r'\[.*\]', '', dependency.split('==')[0]) for dependency in dependencies]
            all_dependencies.update(dependency for dependency in dependency_names if dependency != 'django')

    # Write unique dependency names to a new Python file
    # with open('org_dependencies.py', 'w') as file:
    #     file.write("# List of unique dependency names\n")
    #     file.write("dependencies = {}\n".format(list(all_dependencies)))

    return list(all_dependencies)

