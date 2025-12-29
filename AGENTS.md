# PydanticAI + OpenRouter Implementation Best Practices Checklist

## 📋 Phase 1: Project Setup & Dependencies

### ☐ 1.1 Install Core Dependencies

```bash
pip install 'pydantic-ai-slim[openai]'
```

- Use `pydantic-ai-slim[openai]` for OpenRouter compatibility (OpenRouter uses OpenAI-compatible API)
- Verify Python version ≥ 3.9

### ☐ 1.2 Environment Configuration

- Create `.env` file for API keys
- Add `OPENROUTER_API_KEY=sk-or-...` to environment
- Never hardcode API keys in source code
- Use `python-dotenv` or similar for loading environment variables

### ☐ 1.3 Project Structure Setup

```
project/
├── agents/           # Agent definitions
├── tools/            # Tool functions
├── models/           # Pydantic models for structured output
├── dependencies/     # Dependency injection classes
├── config/           # Configuration files
└── tests/            # Test files
```

---

## 📋 Phase 2: OpenRouter Model Configuration

### ☐ 2.1 Initialize OpenRouter Model

```python
from pydantic_ai.models.openai import OpenAIModel

model = OpenAIModel(
    "anthropic/claude-3.5-sonnet",  # Or any OpenRouter model
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
```

### ☐ 2.2 Implement Model Selection Strategy

- Research available models on [OpenRouter](https://openrouter.ai/models)
- Consider model capabilities vs. cost trade-offs
- Document why specific models were chosen for each agent
- Plan fallback models for redundancy

### ☐ 2.3 Configure Model Settings

```python
from pydantic_ai.settings import ModelSettings

model_settings = ModelSettings(
    temperature=0.7,          # Adjust for creativity vs. consistency
    max_tokens=4096,          # Set appropriate token limits
    timeout=30.0,             # Request timeout in seconds
)
```

---

## 📋 Phase 3: Type-Safe Agent Design

### ☐ 3.1 Define Dependency Types

```python
from dataclasses import dataclass

@dataclass
class MyDependencies:
    database: DatabaseConnection
    api_client: ExternalAPIClient
    user_context: dict[str, Any]
```

- Use dataclasses or Pydantic models for dependencies
- Make dependencies explicit and typed
- Inject all external services through deps (no global state)

### ☐ 3.2 Define Structured Output Models

```python
from pydantic import BaseModel, Field

class AgentOutput(BaseModel):
    result: str = Field(..., description="The main result")
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
```

- Use Pydantic models for all structured outputs
- Add field descriptions for better LLM understanding
- Include validators for complex business logic
- Keep output models focused and single-purpose

### ☐ 3.3 Create Type-Safe Agent

```python
from pydantic_ai import Agent

agent = Agent[MyDependencies, AgentOutput](
    model,
    deps_type=MyDependencies,
    output_type=AgentOutput,
    system_prompt="Clear, specific instructions for the agent",
)
```

- Explicitly declare generic types: `Agent[DepsType, OutputType]`
- Leverage IDE autocomplete and type checking
- System prompts should be clear, specific, and testable

---

## 📋 Phase 4: Tool Implementation

### ☐ 4.1 Define Tools with Proper Context

```python
from pydantic_ai import RunContext

@agent.tool
async def my_tool(
    ctx: RunContext[MyDependencies],
    param: str,
) -> str:
    """Clear docstring explaining what the tool does."""
    # Access dependencies through ctx.deps
    result = await ctx.deps.database.query(param)
    return result
```

- All tools must have clear docstrings (LLM reads them)
- Use `RunContext[DepsType]` for dependency access
- Make tools async when performing I/O operations
- Keep tool functions focused on single responsibilities

### ☐ 4.2 Implement Tool Error Handling

```python
from pydantic_ai import ModelRetry

@agent.tool
async def risky_tool(ctx: RunContext[MyDependencies]) -> str:
    try:
        result = await potentially_failing_operation()
        return result
    except TemporaryError as e:
        # Let the LLM retry with context
        raise ModelRetry(f"Temporary failure: {e}. Please try again.")
    except PermanentError as e:
        # Return error as string for LLM to handle
        return f"Operation failed: {e}"
```

- Use `ModelRetry` for recoverable errors
- Return error messages as strings for permanent failures
- Log errors for debugging

### ☐ 4.3 Configure Tool Retries

```python
@agent.tool(retries=3)
async def my_tool(ctx: RunContext[MyDependencies]) -> str:
    """Tool with automatic retry logic."""
    pass
```

- Set appropriate retry counts for unreliable operations
- Balance between reliability and latency

---

## 📋 Phase 5: Output Validation & Processing

### ☐ 5.1 Implement Output Validators

```python
@agent.output_validator
async def validate_output(
    ctx: RunContext[MyDependencies],
    output: AgentOutput,
) -> AgentOutput:
    """Validate and potentially modify output."""
    if output.confidence < 0.5:
        raise ModelRetry("Confidence too low, please reconsider.")
    return output
```

- Add business logic validators for outputs
- Use validators to ensure quality thresholds
- Raise `ModelRetry` to request better responses

### ☐ 5.2 Handle Structured vs. Text Output

```python
# For structured output
result = await agent.run("prompt", deps=my_deps)
typed_output: AgentOutput = result.output

# For text output (output_type=str or not specified)
result = await agent.run("prompt", deps=my_deps)
text_output: str = result.output
```

- Access validated output via `result.output`
- Type is guaranteed by PydanticAI validation
- Handle validation errors gracefully

---

## 📋 Phase 6: OpenRouter-Specific Error Handling

### ☐ 6.1 Implement Retry Logic with Exponential Backoff

```python
import asyncio
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

class RateLimitError(Exception):
    pass

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(RateLimitError),
)
async def run_agent_with_retry(prompt: str, deps: MyDependencies):
    try:
        result = await agent.run(prompt, deps=deps)
        return result
    except Exception as e:
        if "429" in str(e):  # Rate limit error
            raise RateLimitError(str(e))
        raise
```

### ☐ 6.2 Handle OpenRouter Error Codes

- **400**: Bad Request - Validate inputs before sending
- **401**: Invalid credentials - Check API key configuration
- **402**: Insufficient credits - Monitor credit balance
- **403**: Moderation flagged - Review content policies
- **408**: Timeout - Increase timeout or reduce complexity
- **429**: Rate limited - Implement backoff strategy
- **502**: Model unavailable - Use fallback models
- **503**: No provider available - Check routing requirements

### ☐ 6.3 Monitor API Credits

```python
import httpx

async def check_api_credits():
    """Check OpenRouter API key credits."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://openrouter.ai/api/v1/key",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        return response.json()
```

- Implement credit monitoring in production
- Set up alerts for low credits
- Log usage patterns for cost optimization

---

## 📋 Phase 7: Streaming & Performance

### ☐ 7.1 Implement Streaming for Long Responses

```python
async def stream_agent_response(prompt: str, deps: MyDependencies):
    async with agent.run_stream(prompt, deps=deps) as response:
        async for text in response.stream_text():
            print(text, end="", flush=True)
    
    # Access final validated output
    final_output = response.output
```

- Use `run_stream()` for real-time user feedback
- Stream text with `stream_text()` for unstructured output
- Stream structured output with `stream_output()` for Pydantic models

### ☐ 7.2 Implement Event Stream Handlers

```python
from pydantic_ai import AgentStreamEvent

async def handle_events(
    ctx: RunContext,
    event_stream: AsyncIterable[AgentStreamEvent],
):
    async for event in event_stream:
        # Log tool calls, think events, etc.
        if isinstance(event, FunctionToolCallEvent):
            logger.info(f"Tool called: {event.part.tool_name}")
```

- Monitor agent execution in real-time
- Log important events for debugging
- Track tool usage patterns

### ☐ 7.3 Configure Usage Limits

```python
from pydantic_ai import UsageLimits

result = await agent.run(
    prompt,
    deps=deps,
    usage_limits=UsageLimits(
        request_limit=10,           # Max requests in this run
        response_tokens_limit=8000,  # Max output tokens
    ),
)
```

- Prevent infinite loops with request limits
- Control costs with token limits
- Catch `UsageLimitExceeded` exceptions

---

## 📋 Phase 8: Production Best Practices

### ☐ 8.1 Implement Comprehensive Logging

```python
import structlog

logger = structlog.get_logger()

@agent.tool
async def logged_tool(ctx: RunContext[MyDependencies]) -> str:
    logger.info("tool_called", tool_name="logged_tool")
    try:
        result = await operation()
        logger.info("tool_success", result_length=len(result))
        return result
    except Exception as e:
        logger.error("tool_error", error=str(e))
        raise
```

- Log all agent runs with unique IDs
- Track token usage and costs
- Monitor tool execution times
- Log errors with full context

### ☐ 8.2 Use Dependency Injection Properly

```python
# ❌ Bad: Global state
database = Database()

@agent.tool
async def bad_tool() -> str:
    return database.query()  # Hard to test, not type-safe

# ✅ Good: Injected dependencies
@agent.tool
async def good_tool(ctx: RunContext[MyDependencies]) -> str:
    return await ctx.deps.database.query()  # Testable, type-safe
```

- Never use global variables in tools
- All external services through dependencies
- Makes testing and mocking trivial

### ☐ 8.3 Implement Proper Message History Management

```python
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter

# Store conversation history
messages: list[ModelMessage] = []

# First run
result = await agent.run("Hello", deps=deps)
messages.extend(result.new_messages())

# Continue conversation
result = await agent.run(
    "Follow-up question",
    deps=deps,
    message_history=messages,
)
messages.extend(result.new_messages())
```

- Maintain conversation context across runs
- Serialize messages for persistence
- Implement message pruning for long conversations

### ☐ 8.4 Handle Long Conversations

```python
def summarize_old_messages(messages: list[ModelMessage]) -> list[ModelMessage]:
    """Keep recent messages, summarize old ones."""
    if len(messages) <= 10:
        return messages
    
    # Keep last 10, summarize older ones
    recent = messages[-10:]
    old = messages[:-10]
    
    # Create summary message
    summary = create_summary(old)
    return [summary] + recent
```

- Monitor token usage in message history
- Implement automatic summarization
- Balance context retention vs. token costs

---

## 📋 Phase 9: Testing & Validation

### ☐ 9.1 Write Unit Tests for Tools

```python
import pytest
from unittest.mock import Mock

@pytest.mark.asyncio
async def test_my_tool():
    # Mock dependencies
    mock_deps = Mock(spec=MyDependencies)
    mock_deps.database.query.return_value = "test result"
    
    # Create mock context
    ctx = Mock(spec=RunContext)
    ctx.deps = mock_deps
    
    # Test tool
    result = await my_tool(ctx, "test param")
    assert result == "test result"
```

- Test tools independently of agents
- Mock dependencies for isolation
- Test error cases thoroughly

### ☐ 9.2 Test Agent Outputs

```python
@pytest.mark.asyncio
async def test_agent_output():
    # Use a cheap/fast model for testing
    test_model = OpenAIModel(
        "openrouter/auto",  # Cheapest available
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    
    test_agent = Agent[MyDependencies, AgentOutput](
        test_model,
        deps_type=MyDependencies,
        output_type=AgentOutput,
    )
    
    result = await test_agent.run("test prompt", deps=test_deps)
    
    # Validate output structure
    assert isinstance(result.output, AgentOutput)
    assert result.output.confidence >= 0.0
```

- Create test-specific agents with cheap models
- Validate output types and structure
- Test edge cases and error handling

### ☐ 9.3 Implement Integration Tests

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_agent_workflow():
    """Test complete agent workflow with real dependencies."""
    result = await agent.run(
        "Real user prompt",
        deps=real_dependencies,
        usage_limits=UsageLimits(request_limit=5),
    )
    
    assert result.output is not None
    assert result.usage().total_tokens > 0
```

- Test with real OpenRouter API (separate test key)
- Monitor actual costs and latency
- Test multi-turn conversations

---

## 📋 Phase 10: Monitoring & Optimization

### ☐ 10.1 Track Usage Metrics

```python
from pydantic_ai import RunUsage

result = await agent.run(prompt, deps=deps)
usage: RunUsage = result.usage()

# Log metrics
logger.info(
    "agent_run_completed",
    input_tokens=usage.input_tokens,
    output_tokens=usage.output_tokens,
    total_tokens=usage.total_tokens,
    requests=usage.requests,
)
```

- Track token usage per run
- Monitor request counts
- Calculate cost per agent run
- Aggregate metrics for analysis

### ☐ 10.2 Implement Cost Optimization

```python
# Use cheaper models for simple tasks
simple_model = OpenAIModel("openrouter/auto", ...)
complex_model = OpenAIModel("anthropic/claude-3.5-sonnet", ...)

# Route based on complexity
def get_model_for_task(task_complexity: str):
    if task_complexity == "simple":
        return simple_model
    return complex_model
```

- Route requests to appropriate model tiers
- Cache common responses when possible
- Batch requests where applicable

### ☐ 10.3 Set Up Alerting

```python
async def run_with_monitoring(prompt: str, deps: MyDependencies):
    result = await agent.run(prompt, deps=deps)
    usage = result.usage()
    
    # Alert on high costs
    if usage.total_tokens > 10000:
        await send_alert(f"High token usage: {usage.total_tokens}")
    
    # Alert on errors
    if result.output.confidence < 0.3:
        await send_alert("Low confidence output detected")
    
    return result
```

- Monitor for unusual token usage
- Alert on repeated failures
- Track degraded performance

---

## 📋 Phase 11: Security & Compliance

### ☐ 11.1 Secure API Key Management

- Store keys in environment variables or secret managers
- Rotate API keys regularly
- Use separate keys for dev/staging/production
- Never log API keys

### ☐ 11.2 Implement Input Validation

```python
def validate_user_input(user_input: str) -> str:
    """Validate and sanitize user input."""
    if len(user_input) > 10000:
        raise ValueError("Input too long")
    
    # Remove/escape potentially dangerous content
    sanitized = sanitize_input(user_input)
    return sanitized
```

- Validate input length and format
- Sanitize user-provided content
- Implement rate limiting per user

### ☐ 11.3 Handle Sensitive Data

```python
@dataclass
class SecureDependencies:
    database: DatabaseConnection
    
    def get_user_data(self, user_id: str) -> dict:
        """Fetch user data with PII redaction."""
        data = self.database.get_user(user_id)
        return redact_pii(data)
```

- Redact PII before sending to LLM
- Log without sensitive information
- Comply with data protection regulations

### ☐ 11.4 Configure OpenRouter Privacy

```python
# Use OpenRouter headers for privacy
model = OpenAIModel(
    "anthropic/claude-3.5-sonnet",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    http_client=httpx.AsyncClient(
        headers={
            "HTTP-Referer": "https://your-app.com",
            "X-Title": "Your App Name",
        }
    ),
)
```

- Set HTTP-Referer for request attribution
- Use X-Title for app identification
- Review OpenRouter's data usage policies

---

## 📋 Phase 12: Documentation & Maintenance

### ☐ 12.1 Document Agent Purpose

```python
"""
Customer Support Agent

Purpose: Handle customer inquiries about orders and products
Models: Claude 3.5 Sonnet (primary), GPT-4 (fallback)
Cost: ~$0.02 per average interaction
Latency: 2-5 seconds typical response time

Dependencies:
- OrderDatabase: Query order information
- ProductCatalog: Fetch product details
- EmailService: Send follow-up emails
"""
```

### ☐ 12.2 Document Tool Functions

```python
@agent.tool
async def fetch_order(ctx: RunContext[MyDependencies], order_id: str) -> str:
    """
    Fetch order details for a customer.
    
    Args:
        order_id: The unique order identifier (format: ORD-XXXXX)
        
    Returns:
        JSON string with order details including status, items, and tracking
        
    Raises:
        ModelRetry: If order service is temporarily unavailable
        
    Example:
        > fetch_order("ORD-12345")
        '{"status": "shipped", "tracking": "TRK123", ...}'
    """
```

### ☐ 12.3 Maintain Configuration Documentation

```yaml
# config/agents.yaml
customer_support_agent:
  model: anthropic/claude-3.5-sonnet
  temperature: 0.7
  max_tokens: 4096
  tools:
    - fetch_order
    - search_products
    - send_email
  rate_limits:
    requests_per_minute: 60
    max_concurrent: 10
```

### ☐ 12.4 Create Runbooks

```markdown
# Agent Troubleshooting Runbook

## High Token Usage
1. Check message history length
2. Verify summarization is working
3. Review tool output sizes

## Low Confidence Outputs
1. Check output validators
2. Review recent prompt changes
3. Test with multiple models

## Rate Limit Errors
1. Check OpenRouter credits
2. Verify backoff implementation
3. Review request patterns
```

---

## ✅ Final Checklist Review

Before deploying to production:

- [ ] All dependencies properly typed and injected
- [ ] Structured outputs defined with Pydantic models
- [ ] Error handling with retries and fallbacks
- [ ] Comprehensive logging implemented
- [ ] Usage limits configured appropriately
- [ ] Tests cover tools, outputs, and workflows
- [ ] Monitoring and alerting set up
- [ ] Security review completed
- [ ] Documentation is complete and current
- [ ] Cost projections reviewed
- [ ] Rate limiting strategy tested
- [ ] Message history management working
- [ ] Fallback models configured
- [ ] API keys secured properly
- [ ] Performance benchmarks established

---

## 📚 Key Resources

- [PydanticAI Documentation](https://ai.pydantic.dev)
- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [PydanticAI GitHub](https://github.com/pydantic/pydantic-ai)
- [OpenRouter API Reference](https://openrouter.ai/docs/api/reference)
- [PydanticAI Examples](https://ai.pydantic.dev/examples/)

---

This checklist provides a comprehensive, chronological approach to implementing production-grade PydanticAI agents with OpenRouter. Follow each phase sequentially, and check off items as you implement them to ensure nothing is missed.
