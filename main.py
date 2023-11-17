import json
import os
import tempfile
import subprocess
import toml

from github_links import github_links


def check_version_in_toml(version_type, repo_dir, version):
    """
    version_type: Django or Python
    repo_dir: repository path
    version: version to look for
    """
    # Read the pyproject.toml file
    pyproject_toml_file_path = repo_dir + "/pyproject.toml"
    try:
        with open(pyproject_toml_file_path, 'r', encoding='utf-8') as toml_file:
            data = toml.load(toml_file)
    except FileNotFoundError:
        return False  # File not found
    except toml.TomlDecodeError:
        return False  # Invalid TOML format

    if version_type == "python":
        classifiers = data.get('project', {}).get('classifiers', [])
        return any(f"Programming Language :: Python :: {version}" in classifier for classifier in classifiers)
    elif version_type == "django":
        classifiers = data.get('project', {}).get('dependencies', [])
        return any(f"Django=={version}" in classifier for classifier in classifiers)


def clone_repository(repo_url):
    temp_dir = tempfile.mkdtemp()
    # temp_dir = f"/Users/zubairshkoor/Documents/edx/test_poc/{dependency}" # only for testing
    # if os.path.exists(temp_dir):
    #     print(f"Repository already exists at: {temp_dir}")
    # else:
    #     os.makedirs(temp_dir, exist_ok=True)
    #     subprocess.run(['git', 'clone', repo_url, temp_dir])
    #     print(f"Repository cloned to: {temp_dir}")

    try:
        subprocess.run(['git', 'clone', repo_url, temp_dir], check=True)
        print(f"Repository cloned to: {temp_dir}")
    except subprocess.CalledProcessError as e:
        print(f"Error cloning repository: {e}")
        # Optionally, you can clean up the temporary directory if the cloning fails
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)
        return None

    return temp_dir

def get_release_tags(repo_dir):
    try:
        subprocess.run(['git', 'fetch', '--tags'], cwd=repo_dir)
        git_tags = subprocess.check_output(['git', 'tag', '--sort=version:refname'], cwd=repo_dir, text=True)
        all_tags_list = git_tags.strip().split('\n')
        latest_tag = get_latest_release_tag(repo_dir)
        if not latest_tag and len(all_tags_list):
            return all_tags_list
        elif latest_tag and len(all_tags_list):
            return all_tags_list[:all_tags_list.index(latest_tag)+1]
        else:
            None
    except Exception as ex:
        print(str(ex))
        return None


def get_latest_release_tag(repo_dir):
    try:
        # Run the Git command to get the latest tag on the specified branch
        return subprocess.check_output(["git", "describe", "--tags", "--abbrev=0", get_default_branch(repo_dir)], cwd=repo_dir, text=True).strip()
    
    except subprocess.CalledProcessError as e:
        # Handle errors, e.g., when there are no tags on the specified branch
        print(f"Error: {e}")
        return None


def get_default_branch(repo_dir):
    # Get the symbolic reference for the remote's HEAD
    try:
        default_branch_ref = subprocess.check_output(
            ['git', 'symbolic-ref', 'refs/remotes/origin/HEAD'],
            cwd=repo_dir, text=True
        ).strip()
        # Extract the branch name
        default_branch = default_branch_ref.split('/')[-1]
        return default_branch
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return "No Default Branch"

def find_django_version_in_setup_py_classifier(repo_dir, tag, version):
    subprocess.run(['git', 'checkout', tag], cwd=repo_dir)
    setup_py_path = os.path.join(repo_dir, 'setup.py')
    setup_cfg_path = os.path.join(repo_dir, 'setup.cfg')

    if not os.path.exists(setup_py_path):
        setup_py_path = None
    if not os.path.exists(setup_cfg_path):
        setup_cfg_path = None

    if setup_py_path:
        with open(setup_py_path, 'r') as setup_py_file:
            if f"Framework :: Django :: {version}" in setup_py_file.read():
                return True
    if setup_cfg_path:
        with open(setup_cfg_path, 'r') as setup_cfg_file:
            if f"Framework :: Django :: {version}" in setup_cfg_file.read():
                return True
    if check_version_in_toml("django", repo_dir, version):
        return True
    return False


def find_python_version_in_config_files(repo_dir, tag, version):
    subprocess.run(['git', 'checkout', tag], cwd=repo_dir)
    setup_py_path = os.path.join(repo_dir, 'setup.py')
    setup_cfg_path = os.path.join(repo_dir, 'setup.cfg')

    if not os.path.exists(setup_py_path):
        setup_py_path = None
    if not os.path.exists(setup_cfg_path):
        setup_cfg_path = None

    if setup_py_path:
        with open(setup_py_path, 'r') as setup_py_file:
            if f"Programming Language :: Python :: {version}" in setup_py_file.read():
                return True
    if setup_cfg_path:
        with open(setup_cfg_path, 'r') as setup_cfg_file:
            if f"Programming Language :: Python :: {version}" in setup_cfg_file.read():
                return True
    if check_version_in_toml("python", repo_dir, version):
        return True
    return False


# def get_local_repo_info(repo_dir):
#     subprocess.run(['git', 'checkout', "master"], cwd=repo_dir)
#     subprocess.run(['git', 'pull', 'origin', 'master'], cwd=repo_dir)
#     # Get the total number of open pull requests
#     pull_requests_cmd = ['git', 'ls-remote', '--tags', '--refs', 'origin', 'refs/pull/*/head']
#     pull_requests_output = subprocess.check_output(pull_requests_cmd, cwd=repo_dir, text=True)
#     total_pull_requests = len(pull_requests_output.split('\n')) - 1

#     # Get the SHA and datetime of the last commit
#     last_commit_info_cmd = ['git', 'log', '-1', '--format=%H,%cI']
#     last_commit_info_output = subprocess.check_output(last_commit_info_cmd, cwd=repo_dir, text=True).strip()
#     last_commit_sha, last_commit_datetime = last_commit_info_output.split(',')

#     return total_pull_requests, last_commit_sha, last_commit_datetime

# existing_script.py


def save_update(results):
    with open("updates.json", "a") as file:
        json.dump(results, file)
        file.write("\n")

def is_django_package(repo_dir):
    setup_files = ['setup.py', 'setup.cfg']

    for setup_file in setup_files:
        file_path = os.path.join(repo_dir, setup_file)
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                content = file.read()
                if "'Framework :: Django" in content:
                    return True

    return False

def read_updates_file(file_path):
    with open(file_path, 'r') as file:
        updates_list = [json.loads(line.strip()) for line in file]

    return updates_list


if __name__ == '__main__':
    filtered_github_links = [dependency for dependency in github_links if dependency['github_url'] != 'No Github Link']
    empty_filtered_github_links = [dependency for dependency in github_links if dependency['github_url'] == 'No Github Link']
    # retry_deps = [dep for dep in filtered_github_links if dep["dependency"] not in [list(existing.keys())[0] for existing in read_updates_file("updates.json")]]

    for dependency in filtered_github_links:
        results = {}
        # repo_url = 'https://github.com/encode/django-rest-framework.git'  # Repository URL
        repo_url = dependency['github_url']
        dependency_name = dependency['dependency']

        repo_dir = clone_repository(repo_url)
        if not repo_dir:
            results[dependency_name] = {
                "repo_url": repo_url,
                "skipped": True,
                "reason": "no_access"
            }
            print(f"No access on: {repo_url}")
            save_update(results)
            continue
        release_tags = get_release_tags(repo_dir)
        if not release_tags:
            results[dependency_name] = {
                "repo_url": repo_url,
                "skipped": True,
                "reason": "no_tag_found"
            }
            print(f"There is not tag found for {dependency_name}: {repo_url}")
            save_update(results)
            continue
        latest_tag_having_django_support = None
        latest_tag_having_python_support = None
        django_versions = ['4.0', '4.1', '4.2']
        python_versions = ['3.11', '3.10', '3.9']
        results[dependency_name] = {}
        results[dependency_name]["django"] = {}
        results[dependency_name]["python"] = {}
        desc_tags_list = list(reversed(release_tags))
        if is_django_package(repo_dir):
            results[dependency_name]['is_django'] = True
            for version in django_versions:
                for tag in desc_tags_list:
                    if not find_django_version_in_setup_py_classifier(repo_dir, tag, version):
                        if tag == desc_tags_list[0]: # if the tag is latest the try with default latest/default branch as well
                            default_branch = get_default_branch(repo_dir)
                            if find_django_version_in_setup_py_classifier(repo_dir, default_branch, version):
                                print(f"Django {version} support in {repo_url.split('/')[-1].split('.')[0]} was first added in default branch: {default_branch}")
                                results[dependency_name]['django'][version] = default_branch
                            else:
                                results[dependency_name]['django'][version] = None
                            break
                        print(f"Django {version} support in {repo_url.split('/')[-1].split('.')[0]} was first added in release: {latest_tag_having_django_support}")
                        results[dependency_name]['django'][version] = latest_tag_having_django_support
                        break
                    else:
                        latest_tag_having_django_support = tag
        else:
            results[dependency_name]['is_django'] = False

        for version in python_versions:
            for tag in desc_tags_list:
                if not find_python_version_in_config_files(repo_dir, tag, version):
                    if tag == desc_tags_list[0]: # if the tag is latest the try with default latest/default branch as well
                        default_branch = get_default_branch(repo_dir)
                        if find_python_version_in_config_files(repo_dir, default_branch, version):
                            print(f"Python {version} support in {repo_url.split('/')[-1].split('.')[0]} was first added in default branch: {default_branch}")
                            results[dependency_name]['python'][version] = default_branch
                        else:
                            results[dependency_name]['python'][version] = None
                        break

                    print(f"Python {version} support in {repo_url.split('/')[-1].split('.')[0]} was first added in release: {latest_tag_having_python_support}")
                    results[dependency_name]['python'][version] = latest_tag_having_python_support
                    break
                else:
                    latest_tag_having_python_support = tag
        # total_pull_requests, last_commit_sha, last_commit_datetime = get_local_repo_info(repo_dir)
        # results[dependency_name]["total_pull_requests"] = total_pull_requests
        # results[dependency_name]["last_commit_sha"] = last_commit_sha
        # results[dependency_name]["last_commit_datetime"] = last_commit_datetime

        # Save the results to the file using file handling methods
        save_update(results)

        print(results)
