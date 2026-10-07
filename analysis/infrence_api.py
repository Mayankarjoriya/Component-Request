import os
import requests
from dotenv import load_dotenv

load_dotenv()
HF_TOKEN= os.getenv('HUGGINGFACE_API_KEY')
API_URL = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"

def get_embeddings(texts:str):
    headers = {'Authorization': f"Bearer {HF_TOKEN}"}
    response= requests.post(API_URL,
                            headers=headers,
                            json={'inputs':texts})

    if response.status_code == 200:
        return response.json()
    else:
        print("Error from Huggingface API:", response.text)
        return []
