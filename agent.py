"""
LangChain Agent - Yahoo Finance 工具调用
基于 LangGraph (LangChain 1.x)
"""
import logging
from typing import AsyncIterator

from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from config import get_settings
from tools import (
    get_stock_info,
    get_historical_data,
    get_stock_actions,
    get_shares_count,
    get_financials,
    get_holders_info,
    get_recommendations,
    get_options_expiration_dates,
    get_option_chain,
    get_stock_news,
    get_stock_analysis,
    get_sec_filing,
)

logger = logging.getLogger(__name__)

# 所有可用的 Yahoo Finance 工具
FINANCE_TOOLS = [
    get_stock_info,
    get_historical_data,
    get_stock_actions,
    get_shares_count,
    get_financials,
    get_holders_info,
    get_recommendations,
    get_options_expiration_dates,
    get_option_chain,
    get_stock_news,
    get_stock_analysis,  # 综合分析：估值、盈利能力、财务健康
    get_sec_filing,      # SEC 10-K 文档：风险因素、业务描述
]

# 开启详细日志
import langchain
langchain.verbose = True

SYSTEM_PROMPT = """You are a professional financial analyst assistant powered by Yahoo Finance data and SEC filings.

Your capabilities:
- Fetch real-time stock prices and company information
- Retrieve historical price data and market trends
- Access financial statements (income, balance sheet, cash flow)
- Get analyst recommendations and ratings
- Show stock holder information (institutional, mutual funds)
- Provide options data and expiration dates
- Fetch latest news for any stock
- Access SEC 10-K filings for risk factors, business description, and MD&A

Guidelines:
- Always use tools to fetch real-time data when asked about specific stocks
- Present numerical data clearly with proper formatting
- Use tables or bullet points for better readability
- Be concise but thorough in your analysis
- If a tool returns an error, explain it clearly to the user
- For stock tickers, use standard symbols (e.g., AAPL for Apple, MSFT for Microsoft)

For Risk Analysis (important):
When analyzing risks, provide DETAILED and STRUCTURED analysis:
1. Categorize risks (Competition, Supply Chain, Regulatory, Financial, etc.)
2. For each risk category, explain:
   - What the specific risk is
   - Why it matters to investors
   - Potential impact on the business
   - Any recent developments related to this risk
3. Prioritize risks by severity (High/Medium/Low)
4. Connect risks to current market conditions when relevant

Example risk format:
### 🔴 High Priority Risks
**1. Supply Chain Concentration**
- Risk: 80% of components sourced from Asia
- Impact: Production delays, increased costs
- Recent: Ongoing chip shortage affecting lead times

### 🟡 Medium Priority Risks  
**2. Regulatory Pressure**
- Risk: Antitrust investigations in EU and US
- Impact: Potential fines, forced business changes
"""


class FinanceAgent:
    """Yahoo Finance LangGraph Agent"""
    
    def __init__(self, model: str | None = None):
        settings = get_settings()
        self.model_name = model or settings.openai_model
        self.tools = FINANCE_TOOLS
        self.chat_history: list[BaseMessage] = []
        self.agent = self._create_agent()
    
    def _create_agent(self):
        """创建 LangGraph React Agent"""
        settings = get_settings()
        llm = ChatOpenAI(
            model=self.model_name,
            temperature=0,
            streaming=True,
            api_key=settings.openai_api_key,
        )
        
        # 使用 LangGraph 的 create_react_agent
        return create_react_agent(
            llm,
            self.tools,
            prompt=SYSTEM_PROMPT
        )
    
    def load_history(self, messages: list[dict]):
        """从数据库加载历史消息"""
        self.chat_history = []
        for msg in messages:
            if msg["role"] == "user":
                self.chat_history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                self.chat_history.append(AIMessage(content=msg["content"]))
    
    def chat(self, message: str) -> str:
        """同步聊天"""
        try:
            # 构建输入
            messages = self.chat_history + [HumanMessage(content=message)]
            
            # 调用 agent
            result = self.agent.invoke({"messages": messages})
            
            # 提取最后的 AI 消息
            ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage)]
            if ai_messages:
                response = ai_messages[-1].content
                # 更新历史
                self.chat_history.append(HumanMessage(content=message))
                self.chat_history.append(AIMessage(content=response))
                return response
            return "No response generated."
            
        except Exception as e:
            logger.exception(f"Agent error: {e}")
            return f"Error: {str(e)}"
    
    async def achat(self, message: str) -> str:
        """异步聊天"""
        try:
            messages = self.chat_history + [HumanMessage(content=message)]
            result = await self.agent.ainvoke({"messages": messages})
            
            ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage)]
            if ai_messages:
                response = ai_messages[-1].content
                self.chat_history.append(HumanMessage(content=message))
                self.chat_history.append(AIMessage(content=response))
                return response
            return "No response generated."
            
        except Exception as e:
            logger.exception(f"Agent error: {e}")
            return f"Error: {str(e)}"
    
    async def astream(self, message: str) -> AsyncIterator[str]:
        """异步流式输出"""
        try:
            messages = self.chat_history + [HumanMessage(content=message)]
            full_response = ""
            
            async for event in self.agent.astream_events({"messages": messages}, version="v2"):
                kind = event["event"]
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, "content") and chunk.content:
                        full_response += chunk.content
                        yield chunk.content
            
            # 更新历史
            if full_response:
                self.chat_history.append(HumanMessage(content=message))
                self.chat_history.append(AIMessage(content=full_response))
                        
        except Exception as e:
            logger.exception(f"Stream error: {e}")
            yield f"Error: {str(e)}"
    
    def clear_memory(self):
        """清除对话历史"""
        self.chat_history = []


# Agent 实例缓存 (按 conversation_id)
_agent_cache: dict[str, FinanceAgent] = {}


def get_agent(conversation_id: str, model: str | None = None) -> FinanceAgent:
    """获取或创建 Agent 实例"""
    if conversation_id not in _agent_cache:
        _agent_cache[conversation_id] = FinanceAgent(model=model)
    return _agent_cache[conversation_id]


def remove_agent(conversation_id: str):
    """移除 Agent 实例"""
    if conversation_id in _agent_cache:
        del _agent_cache[conversation_id]
