# backend/openai_api.py
import os
import requests
import logging

logger = logging.getLogger(__name__)

def read_prompt_template(file_path):
    """
    Read the prompt template from a file.
    
    Parameters:
    - file_path: The path to the prompt template file.
    
    Returns:
    - template: The content of the prompt template file.
    """
    with open(file_path, 'r') as file:
        template = file.read()
    return template

def generate_resume_retool_prompt(resume_text, rfp_summary, template_path):
    """
    Generate the prompt for retooling the resume based on the RFP summary.
    
    Parameters:
    - resume_text: The text content of the resume.
    - rfp_summary: Summary of the RFP document.
    - template_path: The path to the prompt template file.
    
    Returns:
    - prompt: The generated prompt for retooling the resume.
    """
    template = read_prompt_template(template_path)
    prompt = template.format(resume_document=resume_text, rfp_summary=rfp_summary)
    return prompt

def call_openai(prompt, step_name="Retool Resume"):
    """
    Make an OpenAI API call with the provided prompt.
    
    Parameters:
    - prompt: The prompt to send to the OpenAI API.
    - step_name: The name of the step for logging purposes.
    
    Returns:
    - response_text: The response text from the OpenAI API.
    """
    api_key = os.getenv('API_KEY')
    endpoint = 'https://aiagentservice.openai.azure.com/openai/deployments/gpt-4-AIAgent-deploy/chat/completions?api-version=2024-02-15-preview'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
    }

    data = {
        "messages": [
            {"role": "system", "content": "You are an AI assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1000  # Adjust as needed
    }

    try:
        response = requests.post(endpoint, headers=headers, json=data, verify=False)  # SSL verification disabled here
        response.raise_for_status()
        result = response.json()
        response_text = result['choices'][0]['message']['content'].strip()
        logger.info(f"{step_name} completed successfully.")
        return response_text
    except requests.exceptions.RequestException as e:
        logger.error(f"Request exception occurred: {e}")
        return f"An error occurred: {e}"
    except KeyError:
        logger.error("Unexpected response format.")
        return "Unexpected response format."
