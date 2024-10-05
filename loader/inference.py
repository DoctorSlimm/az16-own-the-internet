from typing import Dict, List
from pydantic import BaseModel
from langchain_core.documents import Document


from tools.logger import _logger

from loader.github_loader import GithubLoader


min_stars = 100
    
max_issues = 100

max_repos = 10

max_accounts = 100


class AccountData(BaseModel):
    account: Document = None                    # todo -> gh Account model / computed fields / active / inactive / organization / repos (forked) -> / organization
    documents: List[Document] = []          # issues...


logger = _logger('loader.inference')


def load_account_data_list(search_terms: List[str], verbose=True) -> List[AccountData]:
    """Load and format account data from github repositories and issues."""


    # load
    loader = GithubLoader(verbose=verbose)

    loader.load(

        ## keywords searched individually.
        search_terms,


        ## filter repos by min number of stars (+ open issues > 0)
        min_stars=min_stars,


        ## load limit cutoffs
        max_issues=max_issues,
        max_repos=max_repos,
        max_accounts=max_accounts,

    )

    if verbose: logger.info(f"Loaded {len(loader.issues)} issues and {len(loader.accounts)} accounts.")


    # format and group documents / issues by account.

    accounts_data_list = []

    loaded_issues_list = loader.issues

    loaded_accounts_list = loader.accounts


    for account in loaded_accounts_list:

        issues_created_by_account = [issue for issue in loaded_issues_list if issue.metadata['creator'] == account.metadata['login']]

        account_data = AccountData(
            account = account,
            documents = issues_created_by_account
        )

        accounts_data_list.append(account_data)


    # sort by number of documents / issues. 

    accounts_data_list = sorted(

        accounts_data_list,

        key=lambda x: len(x.documents),

        reverse=True
    )

    if verbose:
        import pandas as pd
        logins = [data.account.metadata['login'] for data in accounts_data_list]
        counts = [len(data.documents) for data in accounts_data_list]
        metrics_df = pd.DataFrame({'login': logins, 'count': counts}).to_markdown(index=False)
        logger.info(f'=== Account Data: \n{metrics_df}')
    
    return accounts_data_list