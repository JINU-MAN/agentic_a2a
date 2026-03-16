# agentic_system_a2a

A2A(Agent-to-Agent) 프로토콜 기반 멀티 에이전트 시스템.
MainAgent가 사용자 요청을 받아 전문 에이전트(웹 검색, 논문, SNS)에게 위임하고 결과를 종합합니다.

## 아키텍처

```
사용자 (cli.py)
    │
    ▼
MainAgent (port 8000)          ← 오케스트레이터
├── WebSearchAnalyst (port 8001)  — Tavily 웹 검색
├── PaperAnalyst     (port 8002)  — 로컬 PDF + arXiv/DOI 조회
└── SnsAnalyst       (port 8003)  — 로컬 SNS JSON 검색
```

각 에이전트는 독립 uvicorn 서버로 기동되며 A2A 프로토콜(HTTP JSON-RPC)로 통신합니다.

---

## 1. Python 설치

**Python 3.11 이상** 이 필요합니다.

1. https://www.python.org/downloads/ 에서 최신 Python 다운로드
2. 설치 시 **"Add Python to PATH"** 체크 필수
3. 설치 확인:

```
python --version
```

---

## 2. 프로젝트 클론

```
git clone https://github.com/JINU-MAN/agentic_a2a.git
cd agentic_a2a
```

---

## 3. 패키지 설치

```
pip install -r requirements.txt
```

---

## 4. 환경변수 설정

`.env.example`을 복사해 `.env` 파일을 만들고 API 키를 입력합니다.

**Windows:**
```
copy .env.example .env
```

**macOS / Linux:**
```
cp .env.example .env
```

`.env` 파일을 열어 아래 값을 채웁니다:

```
GOOGLE_API_KEY=발급받은_구글_API_키
TAVILY_API_KEY=발급받은_Tavily_API_키
```

| 변수 | 설명 | 발급 경로 |
|---|---|---|
| `GOOGLE_API_KEY` | Gemini 모델 호출에 사용 | https://aistudio.google.com/app/apikey |
| `TAVILY_API_KEY` | 웹 검색 기능에 사용 | https://app.tavily.com |
| `SLACK_BOT_TOKEN` | Slack 메시지 전송 (선택) | Slack App 관리 페이지 |
| `MAIN_AGENT_MODEL` | MainAgent 모델명 (기본값: `gemini-2.5-flash-lite`) | — |
| `WORKER_AGENT_MODEL` | 워커 에이전트 모델명 (기본값: `gemini-2.5-flash-lite`) | — |

---

## 5. 서버 실행

`start.bat`을 더블클릭하거나 터미널에서 실행합니다:

```
start.bat
```

4개의 PowerShell 창이 열리며 각 에이전트가 순차적으로 기동됩니다.
모든 창에 `Application startup complete` 메시지가 뜨면 준비 완료입니다.

> 재실행 시 `start.bat`을 다시 실행하면 세션 로그(`logs/session.log`)가 자동 초기화됩니다.

---

## 6. 대화 시작

새 터미널에서 CLI 클라이언트를 실행합니다:

```
python cli.py
```

```
MainAgent CLI — connected to http://localhost:8000
Session ID: a3f9c2...

You: AI 트렌드 2025 검색해줘
Agent: ...

You: exit
```

- `exit` 또는 `quit` 입력, 혹은 `Ctrl+C`로 종료
- 같은 세션 내에서는 대화 내용이 유지됩니다

---

## 로컬 데이터 추가 (선택)

에이전트에 로컬 데이터를 제공하려면 아래 경로에 파일을 넣습니다.
데이터 없이도 시스템은 정상 동작합니다(빈 결과 반환).

| 경로 | 형식 | 사용 에이전트 |
|---|---|---|
| `db/paper/*.pdf` | PDF 파일 | PaperAnalyst |
| `db/sns/*.json` | `{"data": [...]}` 형식 JSON | SnsAnalyst |

---

## 로그

| 파일 | 설명 |
|---|---|
| `logs/session.log` | 현재 세션 전체 로그 (start.bat 실행 시 초기화) |
| `logs/mainagent.log` | MainAgent 전용 로그 (10MB 롤링) |
| `logs/websearchanalyst.log` | WebSearchAnalyst 전용 로그 |
| `logs/paperanalyst.log` | PaperAnalyst 전용 로그 |
| `logs/snsanalyst.log` | SnsAnalyst 전용 로그 |

---

## 포트 정보

| 에이전트 | 포트 |
|---|---|
| MainAgent | 8000 |
| WebSearchAnalyst | 8001 |
| PaperAnalyst | 8002 |
| SnsAnalyst | 8003 |
