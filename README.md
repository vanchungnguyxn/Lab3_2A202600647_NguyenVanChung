\# Lab 3 - Chatbot vs ReAct Agent



\## Student Information



\* \*\*Name\*\*: Nguyen Van Chung

\* \*\*Student ID\*\*: 2A202600647

\* \*\*Lab\*\*: Day 3 - Chatbot vs ReAct Agent



\---



\## Submission Reports



This repository includes both the \*\*Group Report\*\* and the \*\*Individual Report\*\* required for Lab 3.



\### 1. Group Report



The group report is located at:



```text

report/group\_report/GROUP\_REPORT\_ReAct\_Ecommerce\_Assistant\_Team.md

```



This report includes:



\* Chatbot baseline comparison

\* ReAct Agent v1 implementation

\* ReAct Agent v2 improvement

\* Tool design evolution

\* Successful and failed/edge traces

\* Telemetry and performance evaluation

\* Provider switching experiment

\* Production readiness review



\### 2. Individual Report



The individual report is located at:



```text

report/individual\_reports/REPORT\_NguyenVanChung.md

```



This report includes:



\* My technical contribution

\* Debugging case study

\* Personal insights on Chatbot vs ReAct Agent

\* Future improvements for production RAG / multi-agent systems



\---



\## Main Source Files



```text

src/chatbot.py                 # Baseline chatbot, no tools

src/agent/agent.py             # ReAct Agent v1

src/agent/agent\_v2.py          # Improved ReAct Agent v2

src/tools/basic\_tools.py       # Tool definitions

src/run\_agent.py               # Run Agent v1

src/run\_agent\_v2.py            # Run Agent v2

src/compare\_v1\_v2.py           # Compare Agent v1 and Agent v2

src/evaluate.py                # Evaluation summary from logs

```



\---



\## Tools Implemented



The ReAct Agent uses the following tools:



| Tool           | Purpose                                      |

| -------------- | -------------------------------------------- |

| `order\_lookup` | Look up order status and total amount        |

| `shipping\_fee` | Calculate shipping fee by package weight     |

| `calculator`   | Perform deterministic arithmetic calculation |



\---



\## How to Run



\### 1. Install dependencies



```powershell

pip install -r requirements.txt

```



\### 2. Configure environment



Create a `.env` file from `.env.example` and set the provider/model:



```env

DEFAULT\_PROVIDER=openrouter

DEFAULT\_MODEL=openai/gpt-4o-mini

```



For provider switching experiment:



```env

DEFAULT\_PROVIDER=openrouter

DEFAULT\_MODEL=google/gemini-2.5-flash

```



\### 3. Run baseline chatbot



```powershell

python src\\chatbot.py

```



\### 4. Run ReAct Agent v1



```powershell

python src\\run\_agent.py

```



\### 5. Run ReAct Agent v2



```powershell

python src\\run\_agent\_v2.py

```



\### 6. Compare Agent v1 and Agent v2



```powershell

python src\\compare\_v1\_v2.py

```



\### 7. Run evaluation



```powershell

python src\\evaluate.py

```



\---



\## Notes



The `.env` file is not included in the submission because it contains API keys.

Use `.env.example` as the template for environment configuration.



The `logs/` directory may be generated during local testing and is used for telemetry analysis.



