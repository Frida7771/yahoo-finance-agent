"""
RAG 文档问答 - 基于 SEC 文件
LangChain 1.x 版本
"""
import logging
from pathlib import Path

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from config import get_settings

logger = logging.getLogger(__name__)


class RAGService:
    """SEC 文档 RAG 问答服务"""
    
    def __init__(self):
        self.settings = get_settings()
        self.embeddings = OpenAIEmbeddings(
            model=self.settings.embedding_model,
            api_key=self.settings.openai_api_key
        )
        self.vector_store: FAISS | None = None
        self.chat_history: list[BaseMessage] = []
    
    def _get_documents_path(self) -> Path:
        """获取文档路径"""
        return self.settings.documents_dir / "sec_filing_combined.txt"
    
    def _get_vector_store_path(self) -> Path:
        """获取向量存储路径"""
        return self.settings.vector_store_dir
    
    async def initialize(self):
        """初始化向量存储"""
        vector_store_path = self._get_vector_store_path()
        
        # 尝试加载已有的向量存储
        if vector_store_path.exists():
            try:
                logger.info(f"Loading existing vector store from {vector_store_path}")
                self.vector_store = FAISS.load_local(
                    str(vector_store_path), 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info("Vector store loaded successfully")
                return
            except Exception as e:
                logger.warning(f"Failed to load vector store: {e}, rebuilding...")
        
        # 构建新的向量存储
        await self._build_vector_store()
    
    async def _build_vector_store(self):
        """构建向量存储"""
        documents_path = self._get_documents_path()
        
        if not documents_path.exists():
            raise FileNotFoundError(f"Documents not found: {documents_path}")
        
        logger.info(f"Loading documents from {documents_path}")
        
        # 加载文档
        loader = TextLoader(str(documents_path), encoding="utf-8")
        documents = loader.load()
        
        # 分割文档
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        splits = text_splitter.split_documents(documents)
        logger.info(f"Split into {len(splits)} chunks")
        
        # 创建向量存储
        logger.info("Creating vector store (this may take a while)...")
        self.vector_store = FAISS.from_documents(splits, self.embeddings)
        
        # 保存向量存储
        vector_store_path = self._get_vector_store_path()
        vector_store_path.parent.mkdir(parents=True, exist_ok=True)
        self.vector_store.save_local(str(vector_store_path))
        logger.info(f"Vector store saved to {vector_store_path}")
    
    def _format_docs(self, docs) -> str:
        """格式化检索到的文档"""
        return "\n\n".join(doc.page_content for doc in docs)
    
    def _format_history(self) -> str:
        """格式化对话历史"""
        if not self.chat_history:
            return ""
        history_str = ""
        for msg in self.chat_history[-6:]:  # 只保留最近 3 轮对话
            if isinstance(msg, HumanMessage):
                history_str += f"Human: {msg.content}\n"
            elif isinstance(msg, AIMessage):
                history_str += f"Assistant: {msg.content}\n"
        return history_str
    
    def load_history(self, messages: list[dict]):
        """从数据库加载历史消息"""
        self.chat_history = []
        for msg in messages:
            if msg["role"] == "user":
                self.chat_history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                self.chat_history.append(AIMessage(content=msg["content"]))
    
    async def ask(self, question: str) -> tuple[str, list[str]]:
        """
        问答
        Returns: (answer, sources)
        """
        try:
            if self.vector_store is None:
                raise RuntimeError("Vector store not initialized. Call initialize() first.")
            
            retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 4}
            )
            
            llm = ChatOpenAI(
                model=self.settings.openai_model,
                temperature=0,
                api_key=self.settings.openai_api_key
            )
            
            # RAG prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a helpful assistant that answers questions based on the provided context from SEC filings.

Context:
{context}

Previous conversation:
{history}

Answer the question based on the context. If the answer is not in the context, say so."""),
                ("user", "{question}")
            ])
            
            # 检索文档
            docs = retriever.invoke(question)
            context = self._format_docs(docs)
            history = self._format_history()
            
            # 构建 chain
            chain = prompt | llm | StrOutputParser()
            
            # 执行
            answer = await chain.ainvoke({
                "context": context,
                "history": history,
                "question": question
            })
            
            # 更新历史
            self.chat_history.append(HumanMessage(content=question))
            self.chat_history.append(AIMessage(content=answer))
            
            # 提取来源
            sources = []
            for doc in docs:
                snippet = doc.page_content[:200].replace("\n", " ")
                if snippet not in sources:
                    sources.append(snippet + "...")
            
            return answer, sources[:3]
            
        except Exception as e:
            logger.exception(f"RAG error: {e}")
            return f"Error: {str(e)}", []
    
    def clear_memory(self):
        """清除对话历史"""
        self.chat_history = []
    
    async def rebuild_index(self):
        """重建向量索引"""
        # 删除旧的向量存储
        vector_store_path = self._get_vector_store_path()
        if vector_store_path.exists():
            import shutil
            shutil.rmtree(vector_store_path)
        
        # 重建
        await self._build_vector_store()


# 全局 RAG 服务实例缓存
_rag_cache: dict[str, RAGService] = {}


async def get_rag_service(conversation_id: str) -> RAGService:
    """获取或创建 RAG 服务实例"""
    if conversation_id not in _rag_cache:
        service = RAGService()
        await service.initialize()
        _rag_cache[conversation_id] = service
    return _rag_cache[conversation_id]


def remove_rag_service(conversation_id: str):
    """移除 RAG 服务实例"""
    if conversation_id in _rag_cache:
        del _rag_cache[conversation_id]
