import requests
import boto3
import json
import re

# Hasura Schema
schema_file_path = (
    "/Users/akshatsahu/Desktop/FuturePath/InternationalSos/hasura_schema.txt"
)

with open(schema_file_path, "r") as file:
    hasura_schema = file.read()

# Hasura GraphQL Query
hasura_endpoint = "https://trusted-lynx-38.hasura.app/v1/graphql"
hasura_admin_secret = "1F5fMJXlnIbL1ku10HSEw4d6HnX2g7kAz7H887cDAAjwVqKaZ3DKuCo0KLLF6npV"

# English Question
nlp_query = input("Enter your question: ")

system_prompt_start = """Assistant, your task is to help generate a precise and relevant GraphQL query.
You will be given a database schema and a natural language query from a user.
Your response must strictly adhere to the provided schema and be directly relevant to the user's query.
Remember, your goal is to interpret the user's requirements accurately and translate them into a valid GraphQL query
that can be used to fetch data from a database as per the user's intent.
Please ensure that your response is clear, concise, and technically accurate, reflecting a deep understanding
of both the GraphQL schema and the user's query.""".encode(
    "unicode-escape"
).decode(
    "utf-8"
)

system_prompt_end = """Generate a GraphQL query with correct syntax that fulfills the user's request based on the provided database schema.""".encode(
    "unicode-escape"
).decode(
    "utf-8"
)


final_prompt = f"{system_prompt_start}User Query is: {nlp_query}GraphQL Schema is: {hasura_schema}{system_prompt_end}"

prompt_format = "Human: " + final_prompt + "\n\nAssistant:"

# AWS Bedrock Claude
bedrock_runtime = boto3.client(service_name="bedrock-runtime", region_name="us-west-2")

input_claude_v2 = {
    "modelId": "anthropic.claude-v2",
    "contentType": "application/json",
    "accept": "*/*",
    "body": json.dumps(
        {
            "prompt": prompt_format,
            "max_tokens_to_sample": 2048,
            "temperature": 0.5,
            "top_k": 250,
            "top_p": 0.999,
            "stop_sequences": ["\n\nHuman:"],
            "anthropic_version": "bedrock-2023-05-31",
        }
    ),
}

response = bedrock_runtime.invoke_model(**input_claude_v2)

response_body = json.loads(response.get("body").read())
# print(response_body)

graphql_query = response_body.get("completion", "").strip()
print(graphql_query)


# GraphQL Query Extractor
def extract_graphql_query(text):
    # Regular expression to match GraphQL query
    query_regex = re.compile(r"```graphql([\s\S]*?)```", re.MULTILINE)

    # Search for the regex pattern in the input text
    match = query_regex.search(text)

    # Return the matched query or None if no match
    return match.group(1).strip() if match else None


# Extracted GraphQL query
extracted_query = extract_graphql_query(graphql_query)


# Hasura GraphQL API
def get_hasura_data(hasura_endpoint, hasura_admin_secret, graphql_query):
    headers = {
        "Content-Type": "application/json",
        "x-hasura-admin-secret": hasura_admin_secret,
    }
    data = {"query": graphql_query}
    response = requests.post(hasura_endpoint, json=data, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None


#  Get data from Hasura
hasura_data = get_hasura_data(hasura_endpoint, hasura_admin_secret, extracted_query)
if hasura_data:
    print("Hasura Data:", hasura_data)

# hasura_graphql_query = """
# query {
#   intsosdataset_tlc_yellow_trips_2012_aggregate(order_by: {tip_amount: desc}, limit: 1) {
#     aggregate {
#       max {
#         tip_amount
#       }
#     }
#   }
# }
# """