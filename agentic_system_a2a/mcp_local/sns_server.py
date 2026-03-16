from pathlib import Path
from typing import Any, Dict, List
import json
import logging

from mcp.server.fastmcp import FastMCP


logger = logging.getLogger(__name__)
mcp = FastMCP("sns-mcp-server", json_response=True)

DB_ROOT = Path(__file__).parent.parent.parent / "db" / "sns"


@mcp.tool()
def search_sns_posts(keyword: str) -> List[Dict[str, Any]]:
    """
    db/sns 아래의 JSON 파일들에서 keyword와 관련된 게시글만 모아 반환합니다.

    JSON 예시 스키마:
    {
      "data": [
        {
          "id": "123456789_987654321",
          "message": "이번 주말에 열리는 AI 컨퍼런스 소식입니다! #AI #Tech",
          "created_time": "2026-02-12T10:30:00+0000",
          "full_picture": "https://...",
          "permalink_url": "https://...",
          "from": { "name": "Tech News Page", "id": "123456789" }
        },
        ...
      ],
      "paging": { ... }
    }
    """
    logger.debug("search_sns_posts called: keyword=%s db_root=%s", keyword, DB_ROOT)

    if not DB_ROOT.exists():
        logger.debug("search_sns_posts: db_root missing, returning []")
        return []

    try:
        keyword_lower = keyword.lower()
        collected: List[Dict[str, Any]] = []

        for path in DB_ROOT.rglob("*.json"):
            try:
                with path.open("r", encoding="utf-8") as f:
                    obj = json.load(f)
            except Exception:
                continue

            data_list = obj.get("data", [])
            if not isinstance(data_list, list):
                continue

            matched_posts: List[Dict[str, Any]] = []
            for item in data_list:
                message = str(item.get("message", ""))
                if keyword_lower in message.lower():
                    matched_posts.append(item)

            if matched_posts:
                collected.append(
                    {
                        "file": str(path),
                        "matched_posts": matched_posts,
                    }
                )

        logger.debug(
            "search_sns_posts completed: keyword=%s result_count=%d",
            keyword,
            len(collected),
        )
        return collected
    except Exception as e:
        logger.exception("search_sns_posts failed: keyword=%s", keyword)
        raise


if __name__ == "__main__":
    mcp.run(transport="stdio")
