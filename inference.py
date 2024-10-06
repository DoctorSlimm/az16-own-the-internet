import yaml
from copy import deepcopy
from typing import List, Dict
from pydantic import BaseModel
from collections import Counter

from tools.logger import _logger

from search.inference import StackRequirements, identify_requirements

from loader.inference import AccountData, load_account_data_list

from labelling.inference import (
    agenerate_labels_for_github_issue_list,
    compute_label_intent_score,
    normalize_list_of_numbers
)


class Contact(BaseModel):

    url: str = None                    # html url of github account.
    title: str = None                  # name or username (display name)
    labels: List[str] = None           # merged labels (duplicated... or top by count?)
    caption: str = None                # bio / concerns / activity / why is he a good sale.
    confidence: float = 0.0            # confidence score (from labels... cap)

    timeline: List[Dict] = []

    # links_and_icons: List[Dict] = [] # links / icons! company / email / social / blog / company / socials / other 



logger = _logger('inference')


def annotate_account_data_with_labels(account_data_list: List[AccountData]) -> List[AccountData]:
    """
    >> Adds labels to account_data.documents.metadata
    >> labels to account_data.account.metadata
    """

    # deep copy account_data_list
    account_data_list = deepcopy(account_data_list)


    # unpack issues (merge back on username / login (creator))
    github_issues_list = []
    for account_data in account_data_list: github_issues_list.extend(account_data.documents)

    # unpack contents and generate labels
    contents = [issue.metadata['title'] for issue in github_issues_list] # first 300...?
    github_issue_labels_list = agenerate_labels_for_github_issue_list(contents)

    # merge back into github_issues_list
    for i, issue in enumerate(github_issues_list): issue.metadata['labels'] = github_issue_labels_list[i]

    # update documents in github accounts again
    for account in account_data_list:

        # technical update issue only.
        login = account.account.metadata['login']
        issues = [issue for issue in github_issues_list if issue.metadata['creator'] == login]
        account.documents = issues

        # update global merged labels (count?...score...?)
        labels = [label for issue in issues for label in issue.metadata['labels']]
        account.account.metadata['labels'] = labels
        account.account.page_content = yaml.dump(account.account.metadata, default_flow_style=False)

    return account_data_list



def contact_from_account_data(account_data: AccountData) -> Contact:
    """Parse contact for display from AccountData for UI display."""

    account = account_data.account          # issues
    documents = account_data.documents      # issues... to timeline?

    ## github profile url
    url = f"https://github.com/{account.metadata['login']}"

    ## company links_and_socials (twitter_username, ) and other links??? all in one??? with icon??!!


    ## main display title
    title = account.metadata['login']
    if account.metadata.get('name', None):
        title = f"{title} | {account.metadata['name']}"
    

    ## main display caption (or llm generate if none?)
    caption = account.metadata.get('bio', 'Developer') # location...
    if account.metadata.get('company', None):
        caption = f"{account.metadata['company']} | {caption}"
    if account.metadata.get('location', None):
        caption = f"{caption} | {account.metadata['location']}"

    ## get company name or url (email / bio / company / blog)

    ## labels (top 3 max)
    labels = account.metadata.get('labels', [])
    labels = [l for l in labels if 'other' not in l]
    top_k_labels = [l for l, _ in Counter(labels).most_common(3)]


    ### confidence score
    confidence = compute_label_intent_score(labels)


    contact = Contact(
        url=url,

        title=title,

        caption=caption,

        labels=top_k_labels,

        confidence=confidence,

        timeline=[doc.metadata for doc in documents]

    )

    return contact


def output_fn(account_data_list: List[AccountData]) -> List[Contact]: # metrics.
    """Return contacts from account data."""

    # format contacts.
    contacts = [contact_from_account_data(account_data) for account_data in account_data_list]

    # normalize scores...
    normalized_confidence_scores = normalize_list_of_numbers([c.confidence for c in contacts])
    for c, score in zip(contacts, normalized_confidence_scores):
        c.confidence = min(0.95, score) # cap score at 0.95 + some std??? egh

    # return sorted.
    return sorted(contacts, key=lambda c: c.confidence, reverse=True) # should never be 1


def inference_fn(query: str, verbose=False) -> Dict: # make custom model...
    """Return contacts and metrics for a given query. for display."""

    # Step 1: Identify the requirements.
    stack_requirements: StackRequirements = identify_requirements(query, verbose)
    framework_list = stack_requirements.frameworks

    # Step 2: Load the account data and issues.
    account_data_list: List[AccountData] = load_account_data_list(framework_list, verbose)

    # Step 3: Annotate Label the account data based on the issues.
    account_data_list = annotate_account_data_with_labels(account_data_list)

    # Step 4: Output the contacts from the account data.
    contacts = output_fn(account_data_list)

    # Step 5: Compute Metrics
    metrics = {}

    return dict(
        data=contacts,          # return documents timeline by id better?
        metrics=metrics
    )



if __name__ == "__main__":
    import pandas as pd

    query = "A security auditing service for organizations utilizing smart contracts."

    result = inference_fn(query, verbose=True)

    data_list = [c.model_dump() for c in result['data']]
    for c in data_list:
        c['_timeline'] = len(c['timeline'])
        del c['timeline']
    
    sample_df = pd.DataFrame(data_list).head(3).to_markdown(index=False)

    logger.info(f'Total contacts: {len(data_list)}\n\n{sample_df}')

