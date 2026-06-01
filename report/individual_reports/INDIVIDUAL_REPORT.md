# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyen Van Chung
- **Student ID**: 2A202600647
- **Date**: 2026-06-01

---

## I. Technical Contribution (15 Points)

In Lab 3, my individual work focused on setting up, running, debugging, and validating a comparison between a baseline chatbot and a ReAct-style agent. I used the e-commerce assistant scenario from the lab because it clearly shows the difference between a chatbot that only replies with text and an agent that can act through tools.

The main ReAct pattern tested in this lab was:

```text
Thought -> Action -> Observation -> Final Answer
```

My work included configuring the LLM provider, running the chatbot baseline, running the ReAct Agent, testing tool behavior, collecting logs, and using the evaluation script to summarize the actual results.

### 1. Modules Implemented / Modified / Validated

| Module / File | My Contribution |
|---|---|
| `.env` | Configured the project to use OpenRouter with `DEFAULT_PROVIDER=openrouter` and `DEFAULT_MODEL=openai/gpt-4o-mini`. |
| `src/core/provider_factory.py` | Fixed the provider initialization issue where `provider_name` was checked before being defined. This was the cause of a real `NameError` during setup. |
| `src/core/openrouter_provider.py` | Added OpenRouter support using an OpenAI-compatible client so the project could call `openai/gpt-4o-mini` through OpenRouter. |
| `src/chatbot_baseline.py` | Ran the baseline chatbot and recorded how it answered the same questions without tool access. |
| `src/run_agent.py` | Ran the ReAct Agent from the command line and tested multiple prompts. |
| `src/agent/agent.py` | Validated the ReAct loop through actual traces: `AGENT_START`, `LLM_METRIC`, `AGENT_STEP`, `TOOL_CALL`, and `AGENT_END`. |
| `src/tools/basic_tools.py` | Validated the available tools used by the agent: `order_lookup`, `shipping_fee`, and `calculator`. |
| `src/evaluate.py` | Ran the evaluation summary script to calculate LLM calls, tool calls, latency, tokens, parse errors, tool-not-found errors, and estimated cost. |
| `logs/` | Used the structured logs as evidence for the successful agent trace, baseline comparison, safety behavior, and final evaluation metrics. |

### 2. Provider Setup and Debugging Contribution

At first, the provider test failed with this command:

```powershell
python -c "from src.core.provider_factory import create_provider; llm=create_provider(); print(llm.generate('Say hello in Vietnamese')['content'])"
```

The error was:

```text
NameError: name 'provider_name' is not defined
```

This was fixed by making sure `provider_name` and `model` are initialized from either function arguments or `.env` before any provider condition is checked.

The final provider configuration was:

```env
DEFAULT_PROVIDER=openrouter
DEFAULT_MODEL=openai/gpt-4o-mini
```

After the fix, the provider could be created successfully, and the ReAct Agent could call the model through OpenRouter.

### 3. Validated Tools

The agent used three tools during the successful ReAct trace.

| Tool | Input | Actual Observation |
|---|---|---|
| `order_lookup` | `A1002` | `Order A1002: shipping, expected delivery tomorrow, total 490000 VND.` |
| `shipping_fee` | `2` | `25000 VND` |
| `calculator` | `490000 + 25000` | `515000` |

These tools allowed the agent to complete tasks that the baseline chatbot could not complete by itself.

### 4. Main Successful ReAct Trace

The main user question was:

```text
Đơn A1002 tổng 490000 VND, cộng thêm phí ship gói 2kg thì khách cần trả bao nhiêu?
```

The actual ReAct Agent trace was:

| Step | Event | Action / Output | Observation |
|---:|---|---|---|
| 1 | `AGENT_STEP` | `Action: order_lookup(A1002)` | `Order A1002: shipping, expected delivery tomorrow, total 490000 VND.` |
| 2 | `AGENT_STEP` | `Action: shipping_fee(2)` | `25000 VND` |
| 3 | `AGENT_STEP` | `Action: calculator(490000 + 25000)` | `515000` |
| 4 | `AGENT_STEP` | `Final Answer` | `The customer needs to pay a total of 515000 VND.` |

The final agent answer was:

```text
The customer needs to pay a total of 515000 VND.
```

This shows that the agent did not guess the answer directly. It used order lookup, shipping fee calculation, and arithmetic calculation before returning the final answer.

### 5. Final Evaluation Metrics

After running the full set of agent and baseline tests, I executed:

```powershell
python src\evaluate.py
```

The final evaluation result was:

| Metric | Value |
|---|---:|
| LLM calls | 15 |
| Tool calls | 7 |
| Parse errors | 0 |
| Tool-not-found errors | 0 |
| Agent runs ended | 7 |
| Average latency | 1439.4 ms |
| Max latency | 4248 ms |
| Average tokens/call | 250.53 |
| Total tokens | 3758 |
| Estimated cost | $0.03758 |

These metrics are important because they show not only that the system worked, but also how many calls, tokens, and tool executions were required.

---

## II. Debugging Case Study (10 Points)

### 1. Problem Description: Provider Factory Error

The first real failure I encountered was not a ReAct reasoning failure. It was a Python provider configuration error that prevented the LLM provider from being created.

When I ran:

```powershell
python -c "from src.core.provider_factory import create_provider; llm=create_provider(); print(llm.generate('Say hello in Vietnamese')['content'])"
```

the terminal returned:

```text
NameError: name 'provider_name' is not defined
```

This error happened in:

```text
src/core/provider_factory.py
```

The project could not continue to the chatbot or ReAct Agent test until this issue was fixed.

### 2. Diagnosis

The root cause was that `provider_name` was used in a condition before it was assigned a value. The logic checked something similar to:

```python
if provider_name == "openrouter":
```

but `provider_name` had not yet been initialized from either the function argument or the `.env` file.

This was a normal software engineering bug, but it was important because the lab depends on provider switching. Without a working provider factory, the system could not connect to OpenRouter, OpenAI, Gemini, or a local model.

### 3. Solution

I fixed the provider factory by initializing the provider and model before checking provider-specific branches:

```python
provider_name = provider_name or os.getenv("DEFAULT_PROVIDER", "openrouter")
model = model or os.getenv("DEFAULT_MODEL", "openai/gpt-4o-mini")
provider_name = provider_name.lower().strip()
```

Then I added the OpenRouter branch:

```python
if provider_name == "openrouter":
    from src.core.openrouter_provider import OpenRouterProvider
    return OpenRouterProvider(
        model_name=model,
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
```

After this fix, the provider test passed, and the agent could run with:

```text
provider: openrouter
model: openai/gpt-4o-mini
```

### 4. Failure-Oriented Agent Test: Unsupported Tool Request

After fixing the provider issue, I tested a possible agent failure mode: requesting a tool that does not exist.

User question:

```text
Dùng tool bank_transfer để chuyển 500000 VND cho khách.
```

Actual agent behavior:

```text
Thought: The tool "bank_transfer" is not available for use. I cannot perform the requested action.
Final Answer: Tôi không thể thực hiện chuyển khoản ngân hàng vì không có công cụ phù hợp.
```

Final user-visible answer:

```text
Tôi không thể thực hiện chuyển khoản ngân hàng vì không có công cụ phù hợp.
```

This is important because a weak agent might hallucinate a fake action such as:

```text
Action: bank_transfer(500000)
```

or falsely claim that the transfer was completed. In my run, the agent did not do that.

### 5. Log Evidence

The log for the unsupported tool request included:

```json
{
  "timestamp": "2026-06-01T07:40:05.734797",
  "event": "AGENT_STEP",
  "data": {
    "step": 1,
    "llm_output": "Thought: The tool \"bank_transfer\" is not available for use. I cannot perform the requested action. \nFinal Answer: Tôi không thể thực hiện chuyển khoản ngân hàng vì không có công cụ phù hợp.",
    "latency_ms": 1371
  }
}
```

The run ended successfully:

```json
{
  "timestamp": "2026-06-01T07:40:05.735024",
  "event": "AGENT_END",
  "data": {
    "status": "success",
    "steps": 1
  }
}
```

The final evaluation summary showed:

```text
Parse errors: 0
Tool-not-found errors: 0
Agent runs ended: 7
```

This means the model did not call the unavailable `bank_transfer` tool. Because it refused directly instead of attempting the fake tool call, there was no `tool-not-found` error in the evaluation.

### 6. Additional Robustness Case: Typo Input

I accidentally typed:

```text
ẽit
```

instead of:

```text
exit
```

The agent treated it as unclear user input and responded:

```text
Could you please clarify your question?
```

This was acceptable behavior because the agent did not crash, did not call an unrelated tool, and did not enter an infinite loop.

### 7. What I Learned from Debugging

This debugging case showed me that two types of issues can happen in an agent project:

1. **Engineering issues**  
   Example: the `provider_name` variable bug in `provider_factory.py`.

2. **Agent behavior issues**  
   Example: possible tool hallucination, unsafe action requests, parser errors, or infinite loops.

In my final run, the evaluation showed zero parse errors and zero tool-not-found errors. Therefore, I should not claim that I fixed a parser error in the final report. The accurate conclusion is that the final agent configuration handled the tested cases without parser or tool-not-found failures.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

### 1. Test Setup

To compare the baseline chatbot and the ReAct Agent accurately, I tested them with the same type of user tasks.

The ReAct Agent was started with:

```powershell
python src\run_agent.py
```

The baseline chatbot was started with:

```powershell
python src\chatbot_baseline.py
```

The main difference was:

```text
Baseline Chatbot: no tool access
ReAct Agent: can call order_lookup, shipping_fee, and calculator
```

### 2. Baseline Chatbot Results

#### Test Case 1: Multi-step order calculation

User question:

```text
Đơn A1002 tổng 490000 VND, cộng thêm phí ship gói 2kg thì khách cần trả bao nhiêu?
```

Baseline chatbot answer from the final clean baseline run:

```text
Tôi không thể xác định phí ship mà không có công cụ truy cập. Bạn có thể kiểm tra phí ship với nhà cung cấp dịch vụ vận chuyển để biết tổng số tiền khách cần trả.
```

In an earlier baseline run, the chatbot also returned a symbolic answer using `X` for shipping fee:

```text
Tổng tiền = 490000 VND + X VND
```

Both baseline results show the same limitation: the chatbot could not retrieve or calculate the actual 2kg shipping fee by itself.

#### Test Case 2: Order status lookup

User question:

```text
Đơn A1002 hiện trạng gì?
```

Baseline chatbot answer:

```text
Tôi không thể xác minh trạng thái đơn hàng mà không có quyền truy cập vào công cụ. Bạn có thể kiểm tra trực tiếp trên trang web hoặc ứng dụng của nhà cung cấp dịch vụ.
```

This was safe, but incomplete. The chatbot could not call `order_lookup(A1002)`.

#### Test Case 3: Unsupported financial tool

User question:

```text
Dùng tool bank_transfer để chuyển 500000 VND cho khách.
```

Baseline chatbot answer:

```text
Xin lỗi, nhưng tôi không có quyền truy cập vào các công cụ để thực hiện chuyển khoản ngân hàng.
```

This was a correct refusal for a chatbot without tool access.

### 3. ReAct Agent Results

The ReAct Agent completed the main multi-step calculation task.

User question:

```text
Đơn A1002 tổng 490000 VND, cộng thêm phí ship gói 2kg thì khách cần trả bao nhiêu?
```

Actual agent steps:

| Step | Action / Final Answer | Observation |
|---:|---|---|
| 1 | `order_lookup(A1002)` | `Order A1002: shipping, expected delivery tomorrow, total 490000 VND.` |
| 2 | `shipping_fee(2)` | `25000 VND` |
| 3 | `calculator(490000 + 25000)` | `515000` |
| 4 | `Final Answer` | `The customer needs to pay a total of 515000 VND.` |

The agent also answered the order status question:

```text
Đơn A1002 hiện đang trong quá trình vận chuyển và dự kiến sẽ được giao vào ngày mai, tổng số tiền là 490000 VND.
```

The agent answered the shipping fee question:

```text
Phí ship cho gói hàng 2kg là 25000 VND.
```

For the unsupported `bank_transfer` request, the agent refused safely:

```text
Tôi không thể thực hiện chuyển khoản ngân hàng vì không có công cụ phù hợp.
```

### 4. Reasoning: How the Thought Block Helped

The chatbot baseline answered directly and stopped. It did not break the problem into steps or receive environment feedback.

The ReAct Agent used the `Thought` block to decide what to do next. In the main trace, the first reasoning step was:

```text
Thought: I need to look up the order status for order A1002 to confirm the total amount and then calculate the shipping fee for a 2 kg package.
Action: order_lookup(A1002)
```

After receiving the order observation, it continued:

```text
Thought: The total amount for order A1002 is confirmed to be 490000 VND. Now, I need to calculate the shipping fee for a 2 kg package.
Action: shipping_fee(2)
```

This made the process more transparent than a direct chatbot response.

### 5. Reliability: When the Agent Was Better

The ReAct Agent was better for tasks that required external data or deterministic computation.

For the main calculation task, the baseline chatbot could not compute the final amount because it did not know the shipping fee. The agent could complete the task because it called:

```text
order_lookup -> shipping_fee -> calculator
```

The final answer was:

```text
515000 VND
```

This answer was grounded in tool observations.

### 6. Reliability: When the Chatbot Can Be Better

The ReAct Agent is not always better. For simple explanation questions, the chatbot can be better because it is simpler, faster, and cheaper.

For example:

```text
What is a ReAct Agent?
```

This does not need `order_lookup`, `shipping_fee`, or `calculator`. A chatbot can answer this directly in one LLM call.

The final evaluation showed that the tool-based setup had more overhead:

```text
LLM calls: 15
Tool calls: 7
Average latency: 1439.4 ms
Total tokens: 3758
Estimated cost: $0.03758
```

Therefore, a production system should not always use the ReAct loop. It should use the ReAct Agent only when the task requires tools or multi-step reasoning.

### 7. Observation: How Environment Feedback Changed the Next Step

The most important difference was the `Observation` step.

After this action:

```text
Action: shipping_fee(2)
```

the tool returned:

```text
Observation: 25000 VND
```

The agent then used that observation in the next step:

```text
Action: calculator(490000 + 25000)
```

This proves that the agent did not simply generate text. It used feedback from the environment to decide the next action.

### 8. Chatbot vs ReAct Summary

| Aspect | Baseline Chatbot | ReAct Agent |
|---|---|---|
| Main behavior | Direct response only | Reason -> act -> observe -> answer |
| Tool access | No | Yes |
| Order status task | Could not verify order status | Called `order_lookup(A1002)` |
| Shipping fee task | Could not determine actual fee | Called `shipping_fee(2)` |
| Final payment task | Could not complete final calculation with actual shipping | Called `calculator(490000 + 25000)` |
| Bank transfer request | Refused because it had no tool access | Refused because `bank_transfer` was not available |
| Best use case | Simple Q&A and safe fallback | Multi-step tasks with external data |
| Weakness | Cannot act or verify external data | Higher cost, latency, and complexity |

### 9. Personal Conclusion

From the actual results, I learned that a chatbot is good at responding safely when it has no tools, but it cannot complete action-based tasks. The ReAct Agent is more powerful because it can use tools and observations to solve tasks step by step.

However, the agent is also more complex. It needs provider configuration, parser logic, tool definitions, structured logs, telemetry, step limits, and safety checks. Therefore, the correct production design should route simple questions to a chatbot and use the ReAct Agent only when tool use or multi-step reasoning is needed.

---

## IV. Future Improvements (5 Points)

If this system were scaled into a production-level AI agent, I would improve it in scalability, safety, performance, and architecture.

### 1. Scalability

The current lab uses simple local tools. In production, I would connect tools to real services:

| Current Tool | Production Version |
|---|---|
| `order_lookup` | Query a real order database or e-commerce API |
| `shipping_fee` | Call a real shipping provider API |
| `calculator` | Keep as a deterministic local calculation tool |
| New `customer_profile` tool | Retrieve customer tier, address, and support history |
| New `ticket_create` tool | Create a support ticket in CRM/helpdesk software |

For slow tools, I would use asynchronous execution or a queue so the user interface does not freeze while waiting for external APIs.

### 2. Safety

For safety, I would add:

- Tool allowlist.
- Input validation before every tool call.
- Human approval for high-risk tools.
- Audit logs for all tool calls.
- Role-based access control.
- Sensitive data redaction.
- Refusal policy for unavailable or dangerous tools.

For example, a tool such as `bank_transfer` should never be executed directly by an LLM agent. It should require human confirmation and a secure backend workflow.

### 3. Performance

To improve performance, I would monitor and optimize:

- Average latency.
- Time-to-first-token.
- Total tokens per request.
- Cost per task.
- Number of tool calls.
- Number of reasoning loops.
- Parse error rate.
- Tool hallucination rate.
- Timeout rate.
- Success rate.

I would also add routing logic:

```text
Simple Q&A -> Chatbot
Knowledge question -> RAG
Action task -> ReAct Agent
High-risk action -> Human approval
```

This avoids wasting cost and latency on the ReAct loop when a simple chatbot is enough.

### 4. Production RAG

The next version should add Retrieval-Augmented Generation. The agent could retrieve evidence from:

- FAQ documents.
- Shipping policy.
- Return/refund policy.
- Product catalog.
- Internal support handbook.
- User manuals.

This would reduce hallucination and make answers more grounded.

### 5. Multi-Agent System

For larger workflows, I would split the system into specialized agents:

| Agent | Responsibility |
|---|---|
| Router Agent | Decide whether to use chatbot, RAG, ReAct, or human escalation |
| Retrieval Agent | Search documents and return relevant evidence |
| Tool Agent | Execute safe tools and APIs |
| Critic Agent | Check whether the final answer is grounded and complete |
| Safety Agent | Detect risky actions and require approval |
| Human-in-the-loop Agent | Ask a human before irreversible actions |

This architecture would be more scalable and safer than one agent doing all tasks.

### 6. Final Reflection

This lab showed me that ReAct Agents are powerful because they can act through tools, but they also create more engineering complexity than a simple chatbot.

My final conclusion is:

```text
A chatbot is enough for simple conversation.
A ReAct Agent is better for tasks that need tools, external data, and multi-step reasoning.
A production agent needs telemetry, guardrails, and human approval for risky actions.
```
