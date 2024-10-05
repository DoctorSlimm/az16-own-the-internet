import tiktoken
from typing import List, Any
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever


def tiktokenize(text, model="gpt-4") -> List[str]:
    """tokenize text using tiktoken -> ["123", "721", ...]"""
    text = text.lower()
    enc = tiktoken.encoding_for_model(model)
    return [str(token) for token in enc.encode(text)]



def create_retriever(documents: List[Document], top_n=10):
    """create a bm25 retriever for sparse retrieval."""
    sparse_retriever = BM25Retriever.from_documents(documents, preprocess_func=tiktokenize)
    sparse_retriever.k = top_n
    return sparse_retriever


def rank_documents(documents: List[Any], query: str, key=lambda o: o.page_content):
    """Note: documents can be any list of objects actually."""

    ## handle non-document types
    key2document = {key(doc): doc for doc in documents}
    lc_documents = [Document(key(doc), metadata={}) for doc in documents]

    ## invert
    retriever = create_retriever(lc_documents, top_n=len(documents))
    results = retriever.invoke(query) # lc

    ## revert
    ranked_documents = [key2document[lc.page_content] for lc in results]
    return ranked_documents