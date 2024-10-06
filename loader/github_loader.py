import yaml
from time import sleep
from typing import List, Dict
from pydantic import BaseModel
from langchain_core.documents import Document


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
    verbose: bool = False


    """Outputs"""
    repos: List[Document] = []          # repositories. (Make documents w/ readme as page_content.)

    issues: List[Document] = []         # issues, actually Document...

    accounts: List[Document] = []       # contacts....

    contributors: List[Document] = []   # contributors... filter accounts...


    def load_repos(self, search_terms: List[str], stars=10):
        """use github search to find repositories for keywords. query params?"""

        if self.verbose: logger.info(f"Searching for repositories for {search_terms}")

        results = []
        for term in search_terms:
            response = api.search_repositories(term, top_n=30)
            if self.verbose: logger.info(f"Found {len(response)} repositories for {term}")
            if response:
                for res in response:
                    results.append(
                        Document(
                            yaml.dump(res, default_flow_style=False),
                            metadata=res
                        )
                    )


        if self.verbose: logger.info(f"{len(results)} total repositories.")


        # convert repos to documents by loading README using GH File loader...
        ## for each...
        
        # deduplicate
        results = list({repo.metadata['full_name']: repo for repo in results}.values())
        if self.verbose: logger.info(f"{len(results)} unique repositories.")

        # filter for issues
        results = [repo for repo in results if repo.metadata.get('has_issues', False)]
        if self.verbose: logger.info(f"{len(results)} repositories with issues.")

        # filter repos by 'open_issues_count' > 0
        results = [repo for repo in results if repo.metadata.get('open_issues_count', 0) > 0]
        if self.verbose: logger.info(f"{len(results)} repositories with open issues.")

        # filter for stars
        results = [repo for repo in results if repo.metadata.get('stargazers_count', 0) >= stars]
        if self.verbose: logger.info(f"{len(results)} repositories with {stars}+ stars.")
        
        # rank repositories... with bm25 module...
        results = rank_documents(

            results,

            query=' '.join(search_terms),

            key=lambda o: o.page_content
        )

        # update repos self
        self.repos = results


    def load_contributors(self, repos=10):
        """load contributors for repositories."""

        for idx, repo in enumerate(self.repos):

            results = api.load_contributors(repo.metadata['full_name'])

            if results:

                for res in results:

                    self.contributors.append(
                        Document(
                            yaml.dump(res, default_flow_style=False),
                            metadata=res
                        )
                    )

                if self.verbose: logger.info(f"Loaded {len(results)} contributors from {repo.metadata['full_name']}")
            
            if idx >= repos:
                if self.verbose: logger.warning(f"(max repos) Loaded {len(self.contributors)} contributors for {repos} repositories. Stopping.")
                break


    def load_issues(self, limit=100, repos=10):
        """load issues for a repository."""

        for idx, repo in enumerate(self.repos):

            results = api.load_issues(repo.metadata['full_name'])

            if results:

                self.issues.extend(results) # documents alreadyy?...

                if self.verbose: logger.info(f"Loaded {len(results)} issues from {repo.metadata['full_name']}")
            
            if len(self.issues) >= limit:
                if self.verbose: logger.warning(f"(max_issues) Loaded {len(self.issues)} issues. Stopping.")
                break
                
            if idx >= repos:
                if self.verbose: logger.warning(f"(max_repos) Loaded {len(self.issues)} issues for {repos} repositories. Stopping.")
                break

    
    def load_accounts(self, limit=100):
        """load accounts from issues."""

        creators_list = [] 
        contributors_list = [c.metadata['login'] for c in self.contributors]

        # map multiprocessuniqeu accounts prefilter here...?... ermmm

        for issue in self.issues:

            if len(self.accounts) >= limit:
                if self.verbose: logger.warning(f"Loaded {len(self.accounts)} accounts. Stopping.")
                break

            creator = issue.metadata.get('creator', None)

            if '[bot]' in creator:
                if self.verbose: logger.warning(f"Skipping bot {creator}")
                continue

            is_contributor = creator in contributors_list


            # if not loaded already or created by contributer, load account.

            if creator and creator not in creators_list and creator not in contributors_list:

                response = api.load_account(creator)
                
                if response:

                    ## Load Readme or something. Ideally.....

                    self.accounts.append(

                        Document(
                            yaml.dump(response, default_flow_style=False),
                            metadata=response                        
                        )

                    )

                    creators_list.append(creator)

                    if self.verbose: logger.info(f"Loaded account {response['login']}")
            
            else:
                if not is_contributor:
                    if self.verbose: logger.warning(f"Skipping account {creator}")
                else:
                    if self.verbose: logger.warning(f"Skipping account {creator} (contributor)")


    def load(self, search_terms: List[str], min_stars=10, max_issues=100, max_repos=10, max_accounts=100):
        """load repos and issues."""

        # load best matching repositories
        self.load_repos(search_terms, min_stars)    
        if self.verbose: logger.info(f"Found {len(self.repos)} repositories for {search_terms}")


        # filter contributors
        self.load_contributors(max_repos)          
        if self.verbose: logger.info(f"Found {len(self.contributors)} contributors for {search_terms}")


        # load issues for top repos
        self.load_issues(max_issues, max_repos)
        if self.verbose: logger.info(f"Found {len(self.issues)} issues for {search_terms}")


        # load accounts from issues
        self.load_accounts(max_accounts)
        if self.verbose: logger.info(f"Found {len(self.accounts)} accounts for {search_terms}")


        # valid accounts... eghhh... no none? missing etc...?

        if self.verbose:
            logger.warning(f'Ratelimit (core): {api.get_rate_limit(core=False)["core"]}')
            logger.warning(f'Ratelimit (search): {api.get_rate_limit(core=False)["search"]}')





if __name__ == "__main__":

    search_terms = ['solana', 'game', 'gaming', 'nft']

    min_stars = 100
    
    max_issues = 100

    max_repos = 10

    max_accounts = 100


    loader = GithubLoader(verbose=True)

    loader.load(search_terms, min_stars, max_issues, max_repos, max_accounts)
    
    logger.warning(f'Ratelimit (search): {api.get_rate_limit(core=False)["search"]}')
    logger.warning(f'Ratelimit (core): {api.get_rate_limit(core=False)["core"]}')
