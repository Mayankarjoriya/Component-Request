from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings 
from infrence_api import get_embeddings

app = FastAPI()

class HFembeddingFunction(EmbeddingFunction):
    def __call__(self,input:Documents) -> Embeddings:
        return get_embeddings(input)

hf_ef = HFembeddingFunction()


# 1. initializing ChromaDB in memory client
chroma_client = chromadb.Client()

# creating collection
# Chroma defaults to the all-MiniLM-L6-v2 embedding model if no 'embedding_function' is provided.

try:
    collection = chroma_client.create_collection(
        name='parts_catalog',
        embedding_function=hf_ef)
except Exception:
    collection = chroma_client.get_collection(
        name='parts_catalog',
        embedding_function=hf_ef)
        

# 2. Load Mock catalog Data (seed)
# In a real node.js might push this,or read it from shared JSON
# Here we just mock 3 items for simplicity for testing

mock_parts = [
    {
        "id": "RES-0805-10K-1%",
        "text": "10kΩ Surface Mount Resistor 0805 1% tolerance. Category: Resistors. Package: 0805 SMD. Price: $0.05",
        "metadata": {"part_number": "RES-0805-10K-1%", "category": "Resistors", "price": 0.05}
    },
    {
        "id": "REG-BUCK-5V-SOIC8",
        "text": "5V buck converter IC, small package. Category: Power Management. Package: SOIC-8. Price: $1.20",
        "metadata": {"part_number": "REG-BUCK-5V-SOIC8", "category": "Power Management", "price": 1.20}
    },
    {
        "id": "MCU-STM32F103",
        "text": "STM32 microcontroller 64-pin LQFP 72MHz. Category: Microcontrollers. Package: LQFP-64. Price: $3.50",
        "metadata": {"part_number": "MCU-STM32F103", "category": "Microcontrollers", "price": 3.50}
    }
]

# Add to chromaDB (embdeds the text automatically)
if collection.count() ==0:
    collection.add(
        documents=[p['text'] for p in mock_parts],
        metadatas=[p['metadata'] for p in mock_parts],
        ids=[p['id'] for p in mock_parts]
    )

# 3. Define The Request schema
class AnalyzeRequest(BaseModel):
    text:str


# 4. The Analyze Endpoint
@app.post('/analyze')
async def analyze_request(req: AnalyzeRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400,details='Request text cannot be empty.')

    # Query ChromaDB for top 3 matched
    results = collection.query(
        query_texts=[req.text],
        n_result=3
    )

    # ChromaDB returns lists of lists for queries
    distance = results['distances'][0] if results['distances'] else []
    metadatas = results['metadata'][0] if results['metadata'] else []

    # build matched items with similarity

    # refusal logic: check if the top results distance is too high(meaning low similarity)
    # chroma uses L2 distance by default 
    # lower is better, A threshhold of 1.2 is a decent starting point

    threshold = 1.2
    
    if not distance or distance[0] > threshold:
        # Nothing in the catalog matches this request
        return {
            "matched_parts": [],
            "draft_reply": "I could not find any perfectly matching parts in our current catalog. I have flagged this request for a specialist to review.",
            "flagged_for_human": True
        }
    # if we have good matches draft a reply
    too_part = metadata[0]
    draft_reply = f"Based On your request I recomend {too_part['part_number']} at ${too_part['price']} each"

    return {
        'matched_parts':metadatas,
        'draft_reply':draft_reply,
        'flagged_for_human':False
    }

@app.get('/health')
def health_check():
    return {'status':'ok',
    'parts_indexed':collection.count(),
    }
    