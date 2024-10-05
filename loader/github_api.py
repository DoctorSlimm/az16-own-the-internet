import os
import requests
from time import sleep
from langchain_community.document_loaders import GitHubIssuesLoader


from tools.logger import _logger

from loader.utils import clean_github_api_data as clean_fn


class GitHubApi:
    def __init__(self):
        self.logger = _logger('github_api')
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN')}",
            "Accept": "application/vnd.github+json"
        }

    def get_rate_limit(self, core=True):
        """Get the current rate limit status."""

        url = f"{self.base_url}/rate_limit"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            if core:
                return response.json().get('resources', {}).get('core', {})
            else:
                return response.json().get('resources', {})

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get rate limit: {e}")
            return None


    def make_request(self, url, cache=True, login=None, repo_name=None, headers=None):
        """Make a request to GitHub, handling rate limits and caching."""

        response = None
        try:
            self.logger.debug(f"Fetching data from {url}")

            if headers:
                headers = {**self.headers, **headers}
            else:
                headers = self.headers
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            cleaned_data = clean_fn(response.json())
            return cleaned_data
        
        except Exception as e:
            if response: self.logger.warning(f"Error {e.response.status_code}: {url} -> {response.text} {e}")
            else: self.logger.warning(f"Error {e}: {url}")
            return None

    
    def search(self, query: str, top_n=30):
        """search for repositories using github search.
        Args:
            query: search query

        Resources:
            * https://docs.github.com/en/rest/search/search?apiVersion=2022-11-28#search-repositories
            * https://docs.github.com/en/rest/search/search?apiVersion=2022-11-28#text-match-metadata
        """

        headers = {'Accept': 'application/vnd.github.text-match+json'}
        # q=tetris+language:assembly&sort=stars&order=desc
        # https://docs.github.com/en/rest/search/search?apiVersion=2022-11-28#constructing-a-search-query
        # https://api.github.com/search/repositories?q=Q
        url = f"{self.base_url}/search/repositories?q={query}+"
        results = self.make_request(url, headers=headers)
        if top_n < len(results['items']):
            results['items'] = results['items'][:top_n]
        return results


    def search_repositories(self, query: str, top_n=30):
        """Search for repositories using GitHub search.

        returns list:
        {
            'name': 'divvy',
            'full_name': 'LamApps/divvy',
            'private': False, 
            'owner': {'login': 'LamApps', 'url': 'https://api.github.com/users/LamApps', 'type': 'User', 'site_admin': False}, 
            'description': 'Divvy.bet NFT gaming on solana (Rust & Go & React)', 
            'fork': False, 
            'url': 'https://api.github.com/repos/LamApps/divvy', 
            'created_at': '2023-09-26T14:43:44Z',
            'updated_at': '2024-04-16T15:51:23Z',
            'pushed_at': '2023-09-26T14:46:37Z', 
            'size': 35706, 
            'stargazers_count': 0, 
            'watchers_count': 0, 
            'language': 'TypeScript', 
            'has_issues': True, 
            'has_projects': True, 
            'has_downloads': True, 
            'has_wiki': True, 
            'has_pages': False, 
            'has_discussions': False, 
            'forks_count': 2, 
            'archived': False, 
            'disabled': False, 
            'open_issues_count': 0, 
            'allow_forking': True, 
            'is_template': False, 
            'web_commit_signoff_required': False, 
            'topics': [], 
            'visibility': 'public', 
            'forks': 2, 'open_issues': 0, 
            'watchers': 0, 
            'default_branch': 'main', 
            'permissions': {'admin': False, 'maintain': False, 'push': False, 'triage': False, 'pull': True}, 
            'score': 1.0, 
            'text_matches': [{'object_type': 'Repository', 'property': 'description', 'fragment': 'Divvy.bet NFT gaming on solana (Rust & Go & React)', 'matches': [{'text': 'NFT gaming', 'indices': [10, 20]}, {'text': 'solana', 'indices': [24, 30]}]}]} 
        """

        response = self.search(query, top_n)
        if 'items' in response:
            results = response['items']
            if results:
                if len(results) > 0:
                    return results
        return []


    def load_issues(self, full_name: str, by_creator=False):
        """"

        Resources:
            * https://python.langchain.com/docs/integrations/document_loaders/github/ 
        
        Returns:
            List[Document]
                page_content: str
                metadata: {
                    'url': 'https://github.com/Azure/azure-search-vector-samples/issues/271',
                    'title': "cast(TokenCredential, self._credential).get_token(*scopes, **kwargs)  | AttributeError: 'str' object has no attribute 'get_token'",
                    'creator': 'avatar-lavventura',
                    'created_at': '2024-09-30T16:58:08Z',
                    'comments': 0,
                    'state': 'open',
                    'labels': [],
                    'assignee': None,
                    'milestone': None,
                    'locked': False,
                    'number': 271,
                    'is_pull_request': False
                }
        """

        l = GitHubIssuesLoader(
            repo=full_name,
            access_token=os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN'),
            include_prs=False, # contributors != sales
            per_page=1000
        )

        docs = l.load()

        if not by_creator:
            return docs
        
        # Group by creator
        creators = {}
        for doc in docs:
            creator = doc.metadata['creator']
            if creator not in creators:
                creators[creator] = []
            doc.metadata['content'] = doc.page_content
            creators[creator].append(doc)
        
        return creators


    def load_repository(self, full_name: str):
        """Load repository metadata from GitHub API."""

        url = f"{self.base_url}/repos/{full_name}"
        return self.make_request(url)
    

    def load_contributors(self, full_name: str):
        """Load contributors for a repository."""

        url = f"{self.base_url}/repos/{full_name}/contributors"
        return self.make_request(url)


    def load_account(self, login: str):
        """Load account metadata from GitHub API."""

        url = f"{self.base_url}/users/{login}"
        return self.make_request(url, login=login)
    

if __name__ == "__main__":
    g = GitHubApi()

    print(g.get_rate_limit())

    print('=== Search ===')
    for repo in g.search_repositories('solana game gaming nft', top_n=7):
        print('-- repo --')
        print(repo['full_name'])
        print(repo)
    sleep(2)


    print('=== Repository ===')
    print(g.load_repository('Azure/azure-search-vector-samples'))
    sleep(2)

    print('=== Issues ===')
    for issue in g.load_issues('Azure/azure-search-vector-samples'):
        print(issue.metadata['title'])
    sleep(2)

    print('=== Account ===')
    print(g.load_account('doctorslimm'))
    sleep(2)