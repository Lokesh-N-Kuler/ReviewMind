from unittest.mock import MagicMock
from app.services.memory_service import MemoryService
from hindsight_client import RecallResponse, RecallResult

def test_hindsight_project_isolation():
    service = MemoryService()
    bank_1 = service.get_bank_id_for_project(1)
    bank_2 = service.get_bank_id_for_project(2)
    assert bank_1 != bank_2
    assert bank_1 == "reviewmind-project-1"
    assert bank_2 == "reviewmind-project-2"

def test_hindsight_mocked_recall_and_retain():
    service = MemoryService()
    # Mock client with official Hindsight signatures
    mock_client = MagicMock()
    
    # Mock retain response
    mock_retain_res = MagicMock()
    mock_retain_res.operation_id = "op_test_123"
    mock_client.retain.return_value = mock_retain_res

    # Mock recall response
    mock_res_item = MagicMock()
    mock_res_item.id = "mem-001"
    mock_res_item.text = "Rule: Always use parameterized queries for user_id filters"
    mock_res_item.context = "coding_standards"
    mock_res_item.tags = ["sql", "security"]
    mock_res_item.scores = MagicMock()
    mock_res_item.scores.total = 0.95

    mock_recall_resp = MagicMock()
    mock_recall_resp.results = [mock_res_item]
    mock_client.recall.return_value = mock_recall_resp

    service._client = mock_client

    # Test retain
    mem_id = service.retain_memory(
        project_id=1,
        content="Rule: Always use parameterized queries for user_id filters",
        category="coding_standards",
        tags=["sql"]
    )
    assert mem_id == "op_test_123"
    mock_client.retain.assert_called_once_with(
        bank_id="reviewmind-project-1",
        content="Rule: Always use parameterized queries for user_id filters",
        context="ReviewMind project 1 - coding_standards",
        metadata={"project_id": "1", "category": "coding_standards"},
        tags=["coding_standards", "sql"]
    )

    # Test recall
    results = service.recall_memories(
        project_id=1,
        query="SELECT query with user_id parameter"
    )
    assert len(results) == 1
    assert "parameterized queries" in results[0].text
    assert results[0].score == 0.95
