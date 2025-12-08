"""
FastMCP server exposing FAQ tools for an IT/helpdesk-style chatbot.

Run locally with:
    fastmcp run faq_mcp_server.py

(or, if you don't use the CLI: `python faq_mcp_server.py`)
"""

from pathlib import Path
from typing import List, Dict, Any

from fastmcp import FastMCP  # pip install fastmcp

# Optional: use your existing stack here
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader

from dotenv import load_dotenv

load_dotenv() 

mcp = FastMCP("FAQ Server")



# ---------- Simple FAQ index loader (replace with your notebook logic) ----------

_FAQ_INDEX = None
_FAQ_DOCS = None


def _load_faq_index() -> None:
    """
    Lazy-load the vector index from a text file or folder.
    Replace this with the logic you already have in the notebook.
    """
    global _FAQ_INDEX, _FAQ_DOCS
    if _FAQ_INDEX is not None:
        return

    # Example: load a single text file called "faqs.txt" in the same folder.
    base_dir = Path(__file__).parent
    faq_path = base_dir / "policy_docs.txt"

    if not faq_path.exists():
        # You can instead load from multiple files or a CSV → Documents, etc.
        raise FileNotFoundError(
            f"FAQ file not found at {faq_path}. "
            f"Create it or change _load_faq_index()."
        )

    loader = TextLoader(str(faq_path), encoding="utf-8")
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=50,
    )
    split_docs = splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings()  # uses OPENAI_API_KEY env var
    index = FAISS.from_documents(split_docs, embeddings)

    _FAQ_INDEX = index
    _FAQ_DOCS = split_docs

_load_faq_index()

def _search_faq_internal(query: str, k: int = 3) -> List[Dict[str, Any]]:
    """Internal helper using LangChain/FAISS."""
    
    results = _FAQ_INDEX.similarity_search(query, search_type="similarity_score_threshold", search_kwargs={"k": k, "score_threshold": 0.5})

    formatted = []
    for i, doc in enumerate(results):
        formatted.append(
            {
                "rank": i + 1,
                "content": doc.page_content,
                "metadata": doc.metadata,
            }
        )
    return formatted


# ---------- Tools exposed via MCP ----------

@mcp.tool
def faq_search(query: str, top_k: int = 3) -> Dict[str, Any]:
    """
    Search the FAQ knowledge base and return the most relevant chunks.

    Parameters
    ----------
    query : str
        User's question or issue description.
    top_k : int
        Number of retrieved FAQ chunks to return.

    Returns
    -------
    dict:
        {
          "query": "...",
          "results": [
             {"rank": 1, "content": "...", "metadata": {...}},
             ...
          ]
        }
    """
    results = _search_faq_internal(query, k=top_k)
    return {"query": query, "results": results}


@mcp.tool
def create_ticket(
    summary: str,
    description: str,
    severity: str = "medium",
    contact_email: str | None = None,
) -> Dict[str, Any]:
    """
    Create an IT/helpdesk ticket for the given problem.

    NOTE: This is a stub. Replace with your real ticketing integration
    (DB insert, REST API call, etc.)
    """
    ticket_id = f"TKT-{hash((summary, description)) & 0xFFFF:04X}"

    # TODO: persist to your system instead of just returning a dict
    return {
        "ticket_id": ticket_id,
        "summary": summary,
        "description": description,
        "severity": severity,
        "contact_email": contact_email,
        "status": "OPEN",
        "message": "Ticket created in demo MCP server (replace with real backend).",
    }


if __name__ == "__main__":
    # FastMCP will default to stdio transport when run via `fastmcp run`
    mcp.run(transport="sse")
