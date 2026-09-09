"""Model Context Protocol (MCP) Server and Tool Registration.

Exposes MedQuAD retrieval, Clinical DB, and Citation Verifier tools via
standardized Model Context Protocol JSON-RPC 2.0 schemas and handlers.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import BaseModel, Field

from backend.tools.citation_verifier import verify_response_citations
from backend.tools.clinical_db_tool import clinical_db_lookup_tool
from backend.tools.search_tool import SearchTool

logger = logging.getLogger(__name__)


class MCPToolParameter(BaseModel):
    name: str
    type: str
    description: str
    required: bool = True


class MCPToolDefinition(BaseModel):
    name: str
    description: str
    parameters: list[MCPToolParameter] = Field(default_factory=list)


# Authoritative Tool Manifest
MCP_TOOL_MANIFEST: list[MCPToolDefinition] = [
    MCPToolDefinition(
        name="medquad_search",
        description="Searches authoritative NIH MedQuAD clinical database for guidelines, symptoms, and trial markers.",
        parameters=[
            MCPToolParameter(
                name="query", type="string", description="Clinical search query", required=True
            ),
            MCPToolParameter(
                name="category", type="string", description="Medical sub-specialty", required=False
            ),
            MCPToolParameter(
                name="top_k",
                type="integer",
                description="Number of results to return (1-5)",
                required=False,
            ),
        ],
    ),
    MCPToolDefinition(
        name="clinical_db_lookup",
        description="Queries clinical reference databases for lab normal ranges, trial protocols, and drug interactions.",
        parameters=[
            MCPToolParameter(
                name="query_type",
                type="string",
                description="One of 'lab_reference', 'trial_protocol', 'drug_interaction'",
                required=True,
            ),
            MCPToolParameter(
                name="lookup_key",
                type="string",
                description="Test name, protocol ID, or drug name",
                required=True,
            ),
        ],
    ),
    MCPToolDefinition(
        name="verify_citations",
        description="Verifies that inline citations [1], [2] in text map 1:1 to retrieved MedQuAD grounding passages.",
        parameters=[
            MCPToolParameter(
                name="text",
                type="string",
                description="Generated response text to verify",
                required=True,
            ),
            MCPToolParameter(
                name="chunks_json",
                type="string",
                description="JSON string of retrieved GroundedSearchResult objects",
                required=True,
            ),
        ],
    ),
]


class MCPServer:
    """Standardized MCP Tool Server handling schema discovery and execution."""

    def __init__(self, search_tool: SearchTool | None = None) -> None:
        self.search_tool = search_tool or SearchTool()

    def list_tools(self) -> list[dict[str, Any]]:
        """Returns MCP tool manifest for discovery."""
        return [tool.model_dump() for tool in MCP_TOOL_MANIFEST]

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Executes tool invocation via MCP dispatch."""
        logger.info("MCP invoking tool '%s' with arguments: %s", tool_name, arguments)

        if tool_name == "medquad_search":
            query = arguments.get("query", "")
            category = arguments.get("category", "General Medicine")
            top_k = int(arguments.get("top_k", 3))
            results = await self.search_tool.search(query=query, category=category, top_k=top_k)
            return {
                "status": "success",
                "results": [r.model_dump() for r in results],
            }

        elif tool_name == "clinical_db_lookup":
            q_type = arguments.get("query_type", "lab_reference")
            key = arguments.get("lookup_key", "")
            raw = clinical_db_lookup_tool(query_type=q_type, lookup_key=key)
            return {
                "status": "success",
                "data": json.loads(raw),
            }

        elif tool_name == "verify_citations":
            text = arguments.get("text", "")
            chunks_raw = arguments.get("chunks_json", "[]")
            chunks_data = json.loads(chunks_raw) if isinstance(chunks_raw, str) else chunks_raw
            from backend.models.schemas import GroundedSearchResult

            chunks = [GroundedSearchResult(**c) for c in chunks_data]
            res = verify_response_citations(text, chunks)
            return {
                "status": "success",
                "is_valid": res.is_valid,
                "citations": [c.model_dump() for c in res.citations],
                "hallucinated": res.hallucinated_indices,
            }

        return {
            "status": "error",
            "message": f"Tool '{tool_name}' not found in MCP registry.",
        }


# Global singleton
_mcp_server_instance: MCPServer | None = None


def get_mcp_server() -> MCPServer:
    global _mcp_server_instance
    if _mcp_server_instance is None:
        _mcp_server_instance = MCPServer()
    return _mcp_server_instance
