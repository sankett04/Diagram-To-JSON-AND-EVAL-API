from unittest.mock import AsyncMock, patch

import pytest
import json
import os
from Module.imgtojson import image_to_json
@pytest.mark.asyncio
async def test_image_to_json():
    sample_image_path ="tests/data/PassFail.png"
    expected_json = {
        "nodes": [
            {"id": "1", "label": "Start"},
            {"id": "2", "label": "Process"},
            {"id": "3", "label": "Decision"},
            {"id": "4", "label": "End"},
            {"id": "5", "label": "Fail"}
        ],
        "edges": [
            {"from": "1", "to": "2"},
            {"from": "2", "to": "3"},
            {"from": "3", "to": "4", "label": "Yes"},
            {"from": "3", "to": "5", "label": "No"}
        ]
    }
  
    # patch the specific client method used in our module and keep the context active for the call
    with patch("Module.imgtojson.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
        # simulate the API returning our expected JSON string
        mock_create.return_value.choices[0].message.content = json.dumps(expected_json)
        result = await image_to_json(sample_image_path)
        assert result == expected_json