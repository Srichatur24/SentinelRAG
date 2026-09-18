import pytest
from src.models import Document, ClearanceLevel
from src.rag.vector_store import ChromaVectorStore


@pytest.fixture
def vector_store(tmp_path):
    chroma_dir = str(tmp_path / "chroma_test")
    return ChromaVectorStore(persist_dir=chroma_dir, collection_name="test_coll")


def test_chroma_add_and_search(vector_store):
    doc1 = Document(
        document_id="DOC-101",
        title="Q4 Revenue Forecast",
        classification="Internal",
        content="Q4 projected revenue is 120 crore."
    )
    doc2 = Document(
        document_id="DOC-102",
        title="Engineering Roadmap",
        classification="Internal",
        content="The next platform release is planned for October."
    )

    vector_store.add_documents([doc1, doc2])

    results = vector_store.search("revenue forecast", n_results=5)
    assert len(results) > 0
    # Top result should be DOC-101 due to semantic relevance
    assert results[0].document_id == "DOC-101"
