# def stage1(product_description: str = 'A gaming-specific SDK for the solana blockchain.'):

#     stack_requirements: StackRequirements = identify_requirements(
#         product_description
#     )

#     framework_list = stack_requirements.frameworks

#     search_terms = ', '.join(framework_list)

#     return search_terms


# # Stage 2: Find accounts for search terms by github repository activity.

# def stage2(
#         ## sources would be nice...
#         # https://solana.com/developers/guides/games/game-sdks
#         search_terms: str = 'solana unity magicblock sdk, \
# godot engine, solana gameshift, turbo rust game engine, \
# honeycomb protocol, unreal sdk, bitfrost unreal sdk, \
# thugz unreal sdk, star atlas foundation kit, \
# solana anchor framework, phaser'
#     ):

#     logger.info(f"search_terms: {search_terms}")

#     # Find accounts for search terms
#     # by github repository activity and load from issues
#     # - excluding contributers
#     # - excluding invalid repositories (stars / open_issues / rank bm25)

#     search_terms = search_terms.split(', ')

#     account_data_list: List[AccountData] = load_account_data_list(

#         search_terms,

#         verbose=True
#     )


#     # list of accounts metadatas (minify / model...)

#     # { login url type site_admin name hireable public_repos public_gists followers following created_at updated_at location email twitter_username bio company blog}

#     accounts = [

#         data.account.metadata           # {Search Results

#         for data in account_data_list

#     ]

#     # list of list of documents for each account. (to label...)

#     account_documents = [

#         data.documents 
        
#         for data in account_data_list
#     ]

    

#     return pd.DataFrame(accounts)






# ### Gradio interface for each stage

# with gr.Blocks() as demo:

#     # Query input for product description
#     query_input = gr.Textbox(
#         # value=""

#         "A gaming-specific SDK for the solana blockchain.",

#         label="Product description:"
#     )

#     # Stage 1: Search terms output
#     search_terms_output = gr.Textbox(

#         "solana unity magicblock sdk, \
# godot engine, solana gameshift, turbo rust game engine, \
# honeycomb protocol, unreal sdk, bitfrost unreal sdk, \
# thugz unreal sdk, star atlas foundation kit, \
# solana anchor framework, phaser",

#         label="Identified alternative frameworks:",

#         #interactive=False

#         interactive=True

#     )
    
#     # Stage 2: Search results table
#     search_results_output = gr.Dataframe(

#         pd.DataFrame(
#             columns=['login', 'confidence']
#         ),
        
#         label="Search Results",

#         interactive=True
#     )

#     # Stage 3: Annotate and Re-Rank accounts...
#     # - by issue similarity to Product description.
#     # - by labelling score intent.
#     # - by wether has a company in description.
    

#     ### Set up the logic between the stages


#     query_input.submit(
#         stage1,
#         inputs=query_input,
#         outputs=search_terms_output
#     )

#     search_terms_output.submit(
#         stage2,
#         inputs=search_terms_output,
#         outputs=search_results_output,
#         # trigger_mode='once'
#     )

#     # ...score and stuff.


### gradio frontend / fastapi
# just return a json...
# Stage 1: Input query and process to extract search terms




### Reload mode
# https://www.gradio.app/guides/developing-faster-with-reload-mode
### >> cli: poetry run gradio main.py -demo-name=my_demo
###############
# Tip: the `gradio` command does not detect the parameters 
# passed to the `launch()` methods because the `launch()`
# method is never called in reload mode.
# For example, setting `auth`, or `show_error` in `launch()` 
# will not be reflected in the app.



### Run Demo

# if __name__ == "__main__":
#     # https://www.gradio.app/docs/gradio/mount_gradio_app
#     demo.launch()
