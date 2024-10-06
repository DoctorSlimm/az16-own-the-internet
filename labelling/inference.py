import yaml
from typing import List
from datasets import Dataset

from tools.logger import _logger

from tools.llm import gpt4, gpt3

from tools.extractor import extract_model_from_content



logger = _logger('labelling.inference')


### Templates.

label_options = [

    ## poor questions (0)
    {"label": "basic_setup_onboarding", "description": "Initial product exploration, focused on setup, free trials, and basic integrations."},
    {"label": "comparing_competitors", "description": "Price-sensitive customers comparing your product against competitors based on features and pricing."},

    ## good questions (+1)
    {"label": "integration_and_customizations", "description": "Integration with existing tech stacks, API compatibility, and customization needs."},
    {"label": "security_and_compliance", "description": "Focus on data security, regulatory compliance, and security protocols."},
    {"label": "scalability", "description": "Concern with the product’s ability to scale as the business grows."},
    {"label": "analytics_and_advanced_monitoring", "description": "Focus on real-time performance tracking, metrics, and custom monitoring."},
    {"label": "on_premise_private_cloud", "description": "Requests for on-premise or private cloud deployments, often for enterprise customers."},
    {"label": "long_term_support", "description": "Customers seeking long-term product stability and support, often tied to multi-year contracts."},
    {"label": "platform_dependency", "description": "Customers trying multiple options to avoid switching platforms, with concerns about vendor lock-in."},

    ## neutral questions (0) 
    {"label": "other", "description": "Other concerns not covered by the existing labels."}
]
label_definitions = yaml.dump(label_options, default_flow_style=False)


template = """You are an expert open source github repository maintainer. \
Please categorize the github issue based on the title.\
Respond in the format:
comma separated list of top 3 labels from the options in order of relevance to the github issue provided (most relevant first.) eg: foo, bar, zoo


===Label Options:
{label_definitions}


===Github Issue:
{github_issue_content}


===Labels:"""


def generate_labels_for_github_issue(content: str, llm=gpt3) -> List[str]:

    try:
        prompt = template.format(

            label_definitions=label_definitions,

            github_issue_content=content

        )

        completion = llm.invoke(prompt).content

        labels = completion.strip().split(',')
        labels = [label.strip() for label in labels]
        labels = [label.lower() for label in labels if label]
        return labels
    
    except Exception as e:
        logger.error(f"Error generating labels: {e}")
        return None # compatible with datasets...?
    

def generate_labels_for_github_issue_gpt3(content: str) -> List[str]:
    return generate_labels_for_github_issue(content, llm=gpt3)


def generate_labels_for_github_issue_gpt4(content: str) -> List[str]:
    return generate_labels_for_github_issue(content, llm=gpt4)


def agenerate_labels_for_github_issue_list(github_issue_content_list, num_proc=16, model_name='gpt3') -> List[List[str]]:
    """generate labels for alist and return a list of lists of labels."""


    # set model outside of ssl context.

    if model_name == 'gpt3':
        fn = lambda x: {"labels": generate_labels_for_github_issue_gpt3(x['content'])}
    elif model_name == 'gpt4':
        fn = lambda x: {"labels": generate_labels_for_github_issue_gpt4(x['content'])}
    else:
        raise ValueError(f"Model name {model_name} not supported.")


    # run in parallel

    inp = Dataset.from_dict({"content": github_issue_content_list})
    out = inp.map(fn, num_proc=num_proc, desc=f"labelling ({model_name})")


    # extract labels from output and unpack

    list_of_labels = out['labels']

    list_of_labels = [labels if labels else [] for labels in list_of_labels]

    return list_of_labels


def compute_label_intent_score(predicted_labels: List[str]) -> float:
    """copmute intent score from labels, average intent from rank of labels."""


    # label score intentions

    positive_labels = ["integration_and_customizations", "security_and_compliance", "scalability", "analytics_and_advanced_monitoring", "on_premise_private_cloud", "long_term_support", "platform_dependency"]

    negative_labels = ["other", "basic_setup_onboarding", "comparing_competitors"]



    # compute total and divide by maximum

    cumulative_score = 0 

    total_label_max_score = len(predicted_labels)

    # exit no div by zero.
    if total_label_max_score == 0:
        return 0


    for predicted in predicted_labels:

        if predicted in positive_labels:

            cumulative_score += 1
    

    return round(cumulative_score / total_label_max_score, 2)
    


def standardize_list_of_numbers(ls: List[float]) -> List[float]:
    """standardize a list of numbers"""

    _max = max(ls)
    _min = min(ls)
    return [round((x - _min) / (_max - _min), 2) for x in ls]    


def normalize_list_of_numbers(ls: List[float]) -> List[float]:
    """normalize a list of numbers"""

    _max = max(ls)
    return [round(x / _max, 2) for x in ls]



