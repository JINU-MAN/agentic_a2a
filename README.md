# agentic_system_a2a

A2A(Agent-to-Agent) 프로토콜 기반 멀티 에이전트 시스템.
MainAgent가 사용자 요청을 분석하고 전문 에이전트(web search, paper, SNS)에게 위임합니다.

## 아키텍처

```
MainAgent (port 8000)
├── WebSearchAnalyst (port 8001)  — Tavily 웹 검색
├── PaperAnalyst     (port 8002)  — 로컬 PDF 검색 + arXiv/DOI 외부 조회
└── SnsAnalyst       (port 8003)  — 로컬 SNS JSON 데이터 검색
```

- 각 에이전트는 독립적인 uvicorn 서버로 기동되며 A2A 프로토콜로 통신합니다.
- 워커 에이전트들은 MCP(stdio) 방식으로 로컬 서버와 통신해 데이터를 수집합니다.
- 최종 응답은 `format_handoff_contract` 표준 포맷으로 반환됩니다.

## 설치

```bash
cd C:\agentic_system_a2a
pip install -r requirements.txt
```

## 환경변수 설정

`.env.example`을 `.env`로 복사 후 키를 입력합니다:

```bash
cp .env.example .env
```

| 변수 | 설명 |
|------|------|
| `GOOGLE_API_KEY` | Google Gemini API 키 |
| `TAVILY_API_KEY` | Tavily 웹 검색 API 키 |
| `MAIN_AGENT_MODEL` | MainAgent 모델 (기본값: `gemini-2.0-flash`) |
| `WORKER_AGENT_MODEL` | 워커 에이전트 모델 (기본값: `gemini-2.0-flash`) |

## 실행

각 에이전트를 별도 터미널에서 기동합니다:

```bash
# 터미널 1 — WebSearchAnalyst
cd C:\agentic_system_a2a
python -m agentic_system_a2a.web_search_agent.a2a_server

# 터미널 2 — PaperAnalyst
python -m agentic_system_a2a.paper_agent.a2a_server

# 터미널 3 — SnsAnalyst
python -m agentic_system_a2a.sns_agent.a2a_server

# 터미널 4 — MainAgent (워커들이 모두 기동된 후 실행)
python -m agentic_system_a2a.main_agent.a2a_server
```

또는 uvicorn 직접 실행:

```bash
uvicorn agentic_system_a2a.web_search_agent.a2a_server:app --host localhost --port 8001
uvicorn agentic_system_a2a.paper_agent.a2a_server:app --host localhost --port 8002
uvicorn agentic_system_a2a.sns_agent.a2a_server:app --host localhost --port 8003
uvicorn agentic_system_a2a.main_agent.a2a_server:app --host localhost --port 8000
```

## 로컬 데이터 (선택)

- **SNS 데이터**: `db/sns/*.json` — `data` 배열을 가진 Facebook/SNS 형식 JSON 파일
- **논문 PDF**: `db/paper/*.pdf` — 검색 가능한 PDF 파일들

데이터 없이도 시스템이 동작합니다 (빈 결과 반환).

## 포트 배정

| 에이전트 | 포트 |
|----------|------|
| MainAgent | 8000 |
| WebSearchAnalyst | 8001 |
| PaperAnalyst | 8002 |
| SnsAnalyst | 8003 |
