def valid_key(k):
    if k.startswith('id'): return False
    if k.endswith('_url'): return False
    if k.startswith('node_id'): return False
    return True

def valid_value(v):

    if v is None: return False
    if isinstance(v, str): return len(v.strip()) > 0
    return True
    
def clean_github_api_data(data):
    """Removes keys that end with '_url'."""
    if isinstance(data, dict):
        return {k: clean_github_api_data(v) for k, v in data.items() if valid_key(k) and valid_value(v)}
    elif isinstance(data, list):
        return [clean_github_api_data(i) for i in data]
    return data


