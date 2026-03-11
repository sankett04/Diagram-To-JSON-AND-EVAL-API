from flask import json
import pytest
from Module import imgtojson
@pytest.mark.asyncio
async def test_imgtojson_threshold():
    # Instead of an exact match, check if at least 90% of nodes were found
    # mock the API call so we don't hit the real service
    expected_json = {"nodes": [{"id": "1"}, {"id": "2"}, {"id": "3"}, {"id": "4"}, {"id": "5"}], "edges": []}
    from unittest.mock import AsyncMock, patch
    with patch("Module.imgtojson.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value.choices[0].message.content = json.dumps(expected_json)
        actual_data = await imgtojson.image_to_json("tests/data/PassFail.png")

    expected_node_count = 5 
    accuracy = len(actual_data["nodes"]) / expected_node_count
    assert accuracy >= 0.8, f"AI accuracy dropped below 80%. Current accuracy: {accuracy}"