# Azure resources
- Use "ExportedTemplate-RFPSummaryPOC-Azure_resource" to recreate resource group. Read below before doing so.
- If the azure subscriptions OpenAI token quota is maxed ou then the template resource creation will failed with a token quota error
- - IF this is the case then there are two options
- - - Delete or reduce the quota for other deployed OpenAI models for gpt-4o or 01-mini and redeploy template
- - - Or the template.json will need to be modified and anything with OpenAI needs to be removed and the resouces will be created manually 
- The App service puts the pricing teir high than what is probably needed. GO into the app service resource and change the pricing teir.

# Local development
## Setup
- Create venv `python3 -m venv venv`
- Activate venv `source venv/bin/activate`
- pip install requirements `pip3 install -r requirements.txt`

## .env 
- Update all the env variables with the newly created resources 

## Run
- streamlit run Home.py

# Deployment
- Use AZ CLI or the VScode "Azure App Service" plugin
