import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import pytest
from ai import ingest_resume,ingest_resume_for_recommendataions,get_recommendation
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from config import settings

def test_dummy():
    pass

@pytest.fixture
def vector_store():
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large", api_key=settings.OPENAI_API_KEY)
    client = QdrantClient(":memory:")
    client.create_collection(collection_name="resumes", vectors_config=VectorParams(size=3072, distance=Distance.COSINE))
    vector_store = QdrantVectorStore(client=client, collection_name="resumes", embedding=embeddings)
    try:
        yield vector_store
    finally:
        client.close()
    
def test_should_embed_text_and_add_to_vector_db(vector_store):
    ingest_resume("Siddharta\nSiddharta is an AI trainer", "siddharta.pdf", 1, vector_store)
    retriever = vector_store.as_retriever(search_kwargs={"k": 1})
    result = retriever.invoke("I am looking for an AI trainer")
    assert len(result) == 1
    assert "Siddharta" in result[0].page_content
    assert result[0].metadata['_id'] == 1

def test_background_task(vector_store):
    filename = "test/resumes/ProfileAndrewNg.pdf"
    with open(filename, "rb") as f:
        content = f.read()
    ingest_resume_for_recommendataions(content, filename, resume_id=1, vector_store=vector_store)
    retriever = vector_store.as_retriever(search_kwargs={"k": 1})
    result = retriever.invoke("I am looking for an AI trainer")
    assert "Andrew" in result[0].page_content

def test_retrieval(vector_store):
    for id, filename in enumerate(os.listdir("test/resumes")):
        with open(f"test/resumes/{filename}", "rb") as f:
            content = f.read()
        ingest_resume_for_recommendataions(content, filename, resume_id=id, vector_store=vector_store)
    result = get_recommendation("I am looking for an expert in AI", vector_store)
    assert "Andrew" in result.page_content

