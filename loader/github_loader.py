from time import sleep
from typing import List, Dict
from pydantic import BaseModel

from loader.github_api import GitHubApi


from tools.logger import _logger

from loader.bm25 import rank_documents


logger = _logger('github_loader')


api = GitHubApi()


### Load Recent Issues from relevant repositories for keywords.
# - search or find github repositories by keywords.
# - load and filter github repositories by #issues and #stars.
# - extract issues across all filtered repositories.


class GithubLoader(BaseModel):
    """Model for loading things from github."""


    """Outputs"""
    repos: List[Dict] = []          # repositories. (Make documents w/ readme as page_content.)

    issues: List[Dict] = []         # issues, actually Document...

    accounts: List[Dict] = []       # contacts....

    contributors: List[Dict] = []   # contributors... filter accounts...


    def load_repos(self, search_terms: List[str], stars=10):
        """use github search to find repositories for keywords. query params?"""

        logger.info(f"Searching for repositories for {search_terms}")

        results = []
        for term in search_terms:
            response = api.search_repositories(term, top_n=30)
            logger.info(f"Found {len(response)} repositories for {term}")
            if response:
                results.extend(response)
        logger.info(f"{len(results)} total repositories.")


        # convert repos to documents by loading README using GH File loader...
        ## for each...
        
        # deduplicate
        results = list({repo['full_name']: repo for repo in results}.values())
        logger.info(f"{len(results)} unique repositories.")

        # filter for issues
        results = [repo for repo in results if repo.get('has_issues', False)]
        logger.info(f"{len(results)} repositories with issues.")

        # filter repos by 'open_issues_count' > 0
        results = [repo for repo in results if repo.get('open_issues_count', 0) > 0]
        logger.info(f"{len(results)} repositories with open issues.")

        # filter for stars
        results = [repo for repo in results if repo.get('stargazers_count', 0) >= stars]
        logger.info(f"{len(results)} repositories with {stars}+ stars.")
        
        # rank repositories... with bm25 module...
        # readme as document could be nice as repodocument (metadata is response...)
        results = rank_documents(results, ' '.join(search_terms), key=lambda o: str(o))

        # update repos self
        self.repos = results


    def load_contributors(self, repos=10):
        """load contributors for repositories."""

        for idx, repo in enumerate(self.repos):
            results = api.load_contributors(repo['full_name'])
            if results:
                self.contributors.extend(results)
                logger.info(f"Loaded {len(results)} contributors from {repo['full_name']}")
            
            if idx >= repos:
                logger.warning(f"Loaded contributors for {len(self.contributors)} repositories. Stopping.")
                break

    def load_issues(self, limit=100, repos=10):
        """load issues for a repository."""

        for idx, repo in enumerate(self.repos):
            results = api.load_issues(repo['full_name'])
            if results:
                self.issues.extend([issue.metadata for issue in results])
                logger.info(f"Loaded {len(results)} issues from {repo['full_name']}")
            
            if len(self.issues) >= limit:
                logger.warning(f"Loaded {len(self.issues)} issues. Stopping.")
                break
                
            if idx >= repos:
                logger.warning(f"Loaded issues for {len(self.issues)} repositories. Stopping.")
                break

    
    def load_accounts(self, limit=100):
        """load accounts from issues."""

        creators_list = [] 
        contributors_list = [c['login'] for c in self.contributors]

        for issue in self.issues:

            if len(self.accounts) >= limit:
                logger.warning(f"Loaded {len(self.accounts)} accounts. Stopping.")
                break

            creator = issue.get('creator', None)

            is_contributor = creator in contributors_list

            if creator and creator not in creators_list and creator not in contributors_list:

                response = api.load_account(issue['creator'])
                
                if response:

                    self.accounts.append(response)

                    creators_list.append(creator)

                    logger.info(f"Loaded account {response['login']}")
            
            else:
                if not is_contributor:
                    logger.warning(f"Skipping account {creator}")
                else:
                    logger.warning(f"Skipping account {creator} (contributor)")

            
            

    def load(self, search_terms: List[str], min_stars=10, max_issues=100, max_repos=10, max_accounts=100):
        """load repos and issues."""

        # load best matching repositories
        self.load_repos(search_terms, min_stars)    
        logger.info(f"Found {len(self.repos)} repositories for {search_terms}")


        # filter contributors
        self.load_contributors(max_repos)          
        logger.info(f"Found {len(self.contributors)} contributors for {search_terms}")


        # load issues for top repos
        self.load_issues(max_issues, max_repos)
        logger.info(f"Found {len(self.issues)} issues for {search_terms}")


        # load accounts from issues
        self.load_accounts(max_accounts)          # accounts...
        logger.info(f"Found {len(self.accounts)} accounts for {search_terms}")

        # valid accounts... eghhh... no none?



if __name__ == "__main__":

    search_terms = ['solana', 'game', 'gaming', 'nft']

    min_stars = 100
    
    max_issues = 100

    max_repos = 10

    max_accounts = 100


    loader = GithubLoader()

    loader.load(search_terms, min_stars, max_issues, max_repos, max_accounts)
    
    logger.warning(f'Ratelimit (search): {api.get_rate_limit(core=False)["search"]}')
    logger.warning(f'Ratelimit (core): {api.get_rate_limit(core=False)["core"]}')
