from typing import List, Dict
from pydantic import BaseModel


### Load Recent Issues from relevant repositories for keywords.
# - 
# - search or find github repositories by keywords.
# - load and filter github repositories by #issues and #stars.
# - extract issues across all filtered repositories.


class GithubLoader(BaseModel):
    """Model for loading things from github."""


    """Inputs"""
    num_proc: int = 2

    """Outputs"""
    repos: List[Dict] = []

    issues: List[Dict] = []

    accounts: List[Dict] = []


    def filter(self):
        pass

    def merge(self):
        pass

    def load_repos(self, keywords):
        """use github search to find repositories for keywords."""
        pass

    def load_issues(self, ):
        pass


    def load():
