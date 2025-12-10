from langchain_openai import ChatOpenAI
from config import settings
from pydantic import BaseModel
from typing import List, Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from converter import extract_text_from_pdf_bytes
from langchain_core.documents import Document
# from agent import Agent, Runner
# from agent import function_tool
# from agent import SQLiteSession

from braintrust import init_logger,traced
from braintrust_langchain import BraintrustCallbackHandler, set_global_handler

model = ChatOpenAI(
    api_key=settings.OPENAI_API_KEY,
    model="gpt-5.1",
    temperature=0,
)

init_logger(project="Prodapt", api_key=settings.BRAINTRUST_API_KEY)
handler = BraintrustCallbackHandler()
set_global_handler(handler)

class JDAnalysis(BaseModel):
    unclear_sections: List[str]
    jargon_terms: List[str]
    biased_language: List[str]
    missing_information: List[str]
    overall_summary: str

class RewrittenSection(BaseModel):
    category: Literal["clarity", "jargon", "bias", "missing_information"]
    original_text: str
    issue_explanation: str
    improved_text: str

class JDRewriteOutput(BaseModel):
    rewritten_sections: List[RewrittenSection]

class ReviewedApplication(BaseModel):
    revised_description: str
    overall_summary: str

class Skills(BaseModel):
    skills: list[str]

@traced(name="Review Job Description")
def review_application(job_description: str) -> ReviewedApplication:
    print("Reviewing the description")
    ANALYSIS_SYSTEM_PROMPT = """
    You are an expert HR job description analyst specializing in inclusive hiring practices.

    Analyze the provided job description for potential issues across these dimensions:

    1. CLARITY: Identify sections with vague responsibilities, unclear expectations, or ambiguous requirements.
    Flag phrases like "various duties," "other tasks as assigned," or undefined acronyms.

    2. JARGON: Flag unnecessarily technical language inappropriate for the role level.
    Consider whether terms would be understood by qualified candidates unfamiliar with internal terminology.

    3. BIAS: Identify language that may discourage diverse candidates:
    - Gender-coded words (e.g., "rockstar," "ninja," "aggressive," "nurturing")
    - Age bias (e.g., "digital native," "recent graduate")
    - Exclusionary phrases (e.g., "culture fit," "work hard/play hard")
    - Excessive requirements (unnecessarily requiring degrees or years of experience)

    4. MISSING INFORMATION: Note absent critical details:
    - Salary range or compensation structure
    - Work location/arrangement (remote/hybrid/onsite)
    - Reporting structure or team context
    - Clear distinction between required vs. preferred qualifications
    - Application process and timeline
    - Growth/development opportunities

    5. SUMMARY: Provide 2-3 sentences describing overall quality and primary concerns.

    For each issue you identify:
    - Quote the exact problematic text
    - Explain why it is problematic

    Your output MUST be valid JSON that conforms exactly to the provided schema.
    Do not include any text outside the JSON.

    If information is missing, return empty arrays.
    """

    ANALYSIS_USER_PROMPT = """
    Analyze the following job description:

    --- JOB DESCRIPTION ---
    {job_description}
    ----------------------

    Return only JSON.

    {format_instructions}
    """

    analysis_parser = PydanticOutputParser(pydantic_object=JDAnalysis)
    analysis_prompt = (
        ChatPromptTemplate.from_messages(
            [
                ("system", ANALYSIS_SYSTEM_PROMPT),
                ("human", ANALYSIS_USER_PROMPT),
            ]
        ).partial(format_instructions=analysis_parser.get_format_instructions())
    )

    analysis_chain = analysis_prompt | model | analysis_parser
    analysis: JDAnalysis = analysis_chain.invoke({"job_description": job_description})

    print(analysis)

    REWRITE_SYSTEM_PROMPT = """
    You are an expert HR editor specializing in rewriting job descriptions for clarity, inclusivity,
    and accessibility.

    You will receive:
    1. The original job description.
    2. A structured analysis of issues found in Step 1.

    Your task is to rewrite ONLY the problematic sections, not the entire job description.

    For each identified issue:
    - Include the original problematic text (quoted exactly)
    - Include the category (clarity, jargon, bias, or missing_information)
    - Provide an improved, inclusive alternative that preserves meaning
    - Maintain neutral, professional tone
    - Ensure suggestions follow inclusive hiring practices

    Return ONLY valid JSON matching the provided schema. Do not write any prose outside JSON.
    """

    REWRITE_USER_PROMPT = """
    Original Job Description:
    -------------------------
    {job_description}

    Analysis Findings:
    ------------------
    {analysis_json}

    Rewrite ONLY the problematic sections using the schema.
    Return only JSON.

    {format_instructions}
    """

    rewrite_parser = PydanticOutputParser(pydantic_object=JDRewriteOutput)
    rewrite_prompt = (
        ChatPromptTemplate.from_messages(
            [
                ("system", REWRITE_SYSTEM_PROMPT),
                ("human", REWRITE_USER_PROMPT),
            ]
        )
        .partial(format_instructions=rewrite_parser.get_format_instructions())
    )

    rewrite_chain = rewrite_prompt | model | rewrite_parser
    rewrite: JDRewriteOutput = rewrite_chain.invoke(
        {"job_description": job_description, "analysis_json": analysis.json()}
    )

    FINALISE_SYSTEM_PROMPT = """
    You are an expert HR writer specializing in creating clear, concise, and inclusive job descriptions.

    Your job is to produce the final polished version of the job description.

    You will receive:
    1. The original job description.
    2. A list of rewritten sections (from Step 2).

    Your tasks:
    - Incorporate all improved rewritten sections into the original job description.
    - Remove or replace the problematic text that was flagged in earlier steps.
    - Maintain the original intent, structure, and role scope.
    - Ensure clarity, inclusivity, and accessibility.
    - Make tone consistent: professional, warm, and concise.
    - Improve flow and readability where necessary.
    - Do NOT invent new responsibilities, requirements, or benefits.

    Return ONLY valid JSON that matches the provided schema.
    Do not include any text outside the JSON.
    """

    FINALISE_USER_PROMPT = """
    Original Job Description:
    -------------------------
    {job_description}

    Rewritten Sections:
    -------------------
    {rewritten_sections_json}

    Create the final polished job description by integrating the improvements.
    Return only JSON.

    {format_instructions}
    """

    final_parser = PydanticOutputParser(pydantic_object=ReviewedApplication)
    final_prompt = (
        ChatPromptTemplate.from_messages(
            [
                ("system", FINALISE_SYSTEM_PROMPT),
                ("human", FINALISE_USER_PROMPT),
            ]
        ).partial(format_instructions=final_parser.get_format_instructions())
    )

    final_chain = final_prompt | model | final_parser
    final_result: ReviewedApplication = final_chain.invoke(
        {
            "job_description": job_description,
            "rewritten_sections_json": rewrite.json(),
        }
    )

    overall_summary = analysis.overall_summary
    revised_description = final_result.revised_description

    return ReviewedApplication(
        revised_description=revised_description,
        overall_summary=overall_summary,
    )

def get_vector_store():
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large", api_key=settings.OPENAI_API_KEY)
    vector_store = QdrantVectorStore.from_existing_collection(embedding=embeddings, collection_name="resumes", path="qdrant_store")
    return vector_store

def inmemory_vector_store():
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large", api_key=settings.OPENAI_API_KEY)
    client = QdrantClient(":memory:")
    client.create_collection(collection_name="resumes", vectors_config=VectorParams(size=3072, distance=Distance.COSINE))
    vector_store = QdrantVectorStore(client=client, collection_name="resumes", embedding=embeddings)
    try:
        yield vector_store
    finally:
        client.close()

def ingest_resume(resume_text, resume_url, resume_id, vector_store):
    doc = Document(page_content=resume_text, metadata={"url": resume_url})
    vector_store.add_documents(documents=[doc], ids=[resume_id])
    print(f"{resume_url} added to vector db")

def ingest_resume_for_recommendataions(resume_content, resume_url, resume_id, vector_store):
   resume_raw_text = extract_text_from_pdf_bytes(resume_content)
   ingest_resume(resume_raw_text, resume_url, resume_id, vector_store)

def get_recommendation(job_description,vector_store):
    retriver = vector_store.as_retriever(search_kwargs = {"k":1})
    result = retriver.invoke(job_description)
    return result[0]

# def extract_skills(job_description) -> Skills:
#     query = """You are an expert HR analyst and your task is to extract **all relevant skills** from the provided job description.

# ## INSTRUCTIONS
# - Read the job description carefully.
# - Identify ALL skills mentioned, including:
#   - Technical skills
#   - Soft skills
#   - Tools & technologies
#   - Frameworks / libraries
#   - Programming languages
#   - Cloud platforms
#   - Domain-specific skills
#   - Certifications (if mentioned)
# - Deduplicate similar skills (e.g., “Python coding” = “Python”).
# - Do NOT invent skills that are not clearly implied.
# - Return skills ONLY in a structured JSON array."""

# def take_interview():
#     session = SQLiteSession("SQL Session ..!")