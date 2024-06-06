import os
from dotenv import load_dotenv
import gradio as gr
import requests
#from langchain.chat_models import AzureChatOpenAI
from langchain_community.chat_models import AzureChatOpenAI
from langchain.prompts import (
    PromptTemplate,
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

from azure.cosmosdb.table.tableservice import TableService
import pandas as pd
import langchain
from langchain.chains.question_answering import load_qa_chain
#from langchain.document_loaders import WebBaseLoader
from langchain_community.document_loaders import WebBaseLoader
from langchain.prompts import PromptTemplate
#from langchain.llms import AzureOpenAI
from langchain_community.llms import AzureOpenAI
from translate import Translator
from azure.cosmosdb.table.tableservice import TableService
import pandas as pd

from constants import states

langchain.debug = True
load_dotenv()

# Create instance to call GPT model
gpt = AzureChatOpenAI(
    #openai_api_base=
    azure_endpoint=os.environ.get("openai_endpoint"),
    openai_api_version="2023-03-15-preview",
    deployment_name=os.environ.get("gpt_deployment_name"),
    openai_api_key=os.environ.get("openai_api_key"),
    openai_api_type = os.environ.get("openai_api_type"),
)

def call_gpt_model(rag_from_bing, message):
    system_template="You are a professional, helpful assistant to provide resources to combat childhood hunger.  \n"
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

    user_prompt=PromptTemplate(
        template="## Context \n {rag_from_bing} \n" +
                "## Instructions \n Considering all information you have at your disposal, answer the question below, giving as much specific detail as possible.\n" +
                "## Question \n {message} \n",
        input_variables=["rag_from_bing", "message"],
    )
    human_message_prompt = HumanMessagePromptTemplate(prompt=user_prompt)
    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

    # Get formatted messages for the chat completion
    messages = chat_prompt.format_prompt(rag_from_bing={rag_from_bing}, message={message}).to_messages()

    # Call the model
    output = gpt(messages)
    return output.content

def call_langchain_model(rag_from_bing, docs, user_ask):
    qa_template = """
        # Reference documentation
        {context} 
        # Question 
        {question}
        # Answer
    """
    PROMPT = PromptTemplate(
        template=qa_template, input_variables=["context", "question"]
    )
    llm = AzureChatOpenAI(deployment_name=os.environ.get("gpt_deployment_name"), 
                        openai_api_version="2023-05-15",
                        temperature=0,
                        openai_api_key=os.environ.get("openai_api_key"),
                        openai_api_base=os.environ.get("openai_endpoint"))

    chain = load_qa_chain(llm, chain_type="stuff", prompt=PROMPT)
    result = chain({"input_documents": docs, "question": user_ask}, return_only_outputs=True)
    #print(result)
    return result["output_text"]

def scrape(urls):
    loader = WebBaseLoader(urls)
    docs = loader.load()
    return docs

    '''
    # Send a GET request to the URL
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Print the HTML content of the response
        #print(response.text)
        # TODO: consider stripping html tags or any extra tokens?  
        return response.text
    else:
        # Print an error message
        print(f"Request failed with status code {response.status_code}")

    '''

def chat(message, state):
    try:
        # # Get location
        # location = get_location()
        # print("Location")
        # print(location)

        # # Table storage logic here
        # state = location["region"]
        print("State")
        print(state)
    except KeyError:
        print("Error: 'region' key not found in the location dictionary.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        
    #fq = "PartitionKey eq 'State'"
    partition_key = 'State'
    fq =  "PartitionKey eq '{}' and RowKey eq '{}'".format(partition_key, state)

    ts = get_table_service()
    #df = get_dataframe_from_table_storage_table(table_service=ts, filter_query=fq)
    filteredList = get_dataframe_from_table_storage_table(table_service=ts, filter_query=fq)
    pd.set_option('display.max_colwidth', None)
    #filteredList = df[df["RowKey"] == state]
    #print("Filtered List:")
    #print(filteredList)

    eligibility_website = None
    snap_screener = None
    eligibility_pdf = None
    
    if 'EligibilityWebsite' in filteredList.columns:
        eligibility_website = (filteredList['EligibilityWebsite']).to_string(index=False)
    #print(eligibility_website)
    
    if 'SnapScreener' in filteredList.columns:
        snap_screener = (filteredList['SnapScreener']).to_string(index=False)
    #print(snap_screener)
    
    if 'OnlineApplication' in filteredList.columns:
        online_application =  (filteredList['OnlineApplication']).to_string(index=False)
    #print(online_application)
    
    if 'EligibilityPDF' in filteredList.columns:
        eligibility_pdf =  (filteredList['EligibilityPDF']).to_string(index=False)
    #print(eligibility_pdf)
    
    urls_list = [eligibility_website, snap_screener, online_application, eligibility_pdf]
    #print(urls_list)
    urls = [x for x in urls_list if x is not None and x != "NaN"]
        
    #Did some testing with this, not necessary nor helpful with helper program
    
    #bing_response = bingsearch.call_search_api(query, bing_endpoint, bing_api_key)
    #rag_from_bing = bing_response
    rag_from_bing = ""

    docs = scrape(urls)
    gov_docs_langchain_response = call_langchain_model(rag_from_bing, docs, message)
    
    # Call GPT model with context from Bing
    #model_response =call_gpt_model(rag_from_bing, message)
    #return model_response
    return gov_docs_langchain_response


# Gets the ip address of the request (user)
def get_ip():
    response = requests.get('https://api64.ipify.org?format=json').json()
    return response["ip"]

# Fetches the location of the user based on the ip address
def get_location():
    ip_address = get_ip()
    response = requests.get(f'https://ipapi.co/{ip_address}/json/').json()
    location_data = {
        "ip": ip_address,
        "city": response.get("city"),
        "region": response.get("region"),
        "country": response.get("country_name")
    }
    return location_data

# Azure Table Storage logic
def get_table_service():
# """ Set the Azure Table Storage service """
    return TableService(connection_string=os.environ.get("db_connection_string"))

def get_dataframe_from_table_storage_table(table_service, filter_query):
    # Create a dataframe from table storage data
    return pd.DataFrame(get_data_from_table_storage_table(table_service, filter_query))

def get_data_from_table_storage_table(table_service, filter_query):
    # Retrieve data from Table Storage
    for record in table_service.query_entities(os.environ.get("source_table"), filter=filter_query):
        yield record

def translate_to_spanish(input_text):
    try:
        translator= Translator(to_lang="es")
        spanish_text = translator.translate(input_text)
        return spanish_text
    except Exception as e:
        return str(e)

# UI components (using Gradio - https://gradio.app)
# This section no longer does anything
chatbot = gr.Chatbot(bubble_full_width = False)
with gr.Blocks() as sosChatBot:
    with gr.Row():
        statesArray = states
        statesDropdown = gr.Dropdown(
            statesArray, label="States", info="Choose your state"
        ),

    with gr.Row():
        chat_interface = gr.ChatInterface(fn=chat, chatbot=chatbot)
        
#sosChatBot.launch()
