# kba.py
"""
KnowledgeBaseAssistant
基于检索增强生成（RAG）技术的多文档问答处理器，支持PDF/MD/TXT等格式，
通过加载文档、生成嵌入、构建向量库，结合大语言模型实现精准问答
"""
import os
import logging

from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredMarkdownLoader,
    TextLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.runnables.passthrough import RunnablePassthrough
# from langchain_core.runnables import RunnableLambda
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from .models import ModelManager

# 配置日志，记录关键操作
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeBaseAssistant:
    """
    基于RAG技术的PDF文档问答处理器。
    功能：加载PDF文档并生成向量库，接收用户问题后通过检索向量库获取相关上下文，
          结合大语言模型生成基于文档内容的精准回答。
    """

    # 修改初始化方法，接收模型管理器和提供商信息
    def __init__(self,
                 model_manager: ModelManager,
                 llm_provider: str,
                 llm_model: str,
                 embedding_provider: str,
                 embedding_model: str):
        """
        初始化KnowledgeBaseAssistant实例，配置大语言模型（LLM）和嵌入模型。

        参数:
            model_manager: 模型管理器实例
            llm_provider: 大语言模型提供商
            llm_model: 用于生成回答的大语言模型名称
            embedding_provider: 嵌入模型提供商
            embedding_model: 用于生成文本嵌入的模型名称
        """
        self.model_manager = model_manager
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.embedding_provider = embedding_provider
        self.embedding_model = embedding_model

        self.vector_store = None  # 向量库实例
        self.retriever = None  # 检索器实例
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=100)

        try:
            # 通过模型管理器获取LLM客户端
            self.model = self.model_manager.get_chat_model(
                provider_name=llm_provider,
                model_name=llm_model
            )

            # 通过模型管理器获取嵌入模型客户端
            self.embeddings = self.model_manager.get_embedding_model(
                provider_name=embedding_provider,
                model_name=embedding_model
            )
        except Exception as e:
            logger.error(f"Failed to initialize models: {str(e)}")
            raise

        # 构建带上下文的提示模板（保持不变）
        self.prompt = ChatPromptTemplate.from_template(
            """
            You are an experienced doctor's assistant answering questions based on uploaded medical guidelines.
            Respond in the same language as the question.
            Context:
            {context}

            Question:
            {question}

            Answer concisely and accurately. If unsure, say 'I don't know' or '不清楚'.
            """
        )

    def ingest(self, file_path: str):
        """处理文档（PDF/MD/TXT）：加载、分割、生成嵌入并存储至向量库。

            参数:
                file_path: 文档本地路径
        """
        try:
            logger.info(f"Processing document: {file_path}")
            file_ext = os.path.splitext(file_path)[1].lower()

            if file_ext == ".pdf":
                loader = PyPDFLoader(file_path=file_path)
            elif file_ext == ".md":
                loader = UnstructuredMarkdownLoader(file_path=file_path)
            elif file_ext == ".txt":
                loader = TextLoader(file_path=file_path, encoding="utf-8")
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")

            docs = loader.load()
            chunks = self.text_splitter.split_documents(docs)
            chunks = filter_complex_metadata(chunks)

            if self.vector_store is None:
                # 创建新的向量库
                self.vector_store = Chroma.from_documents(
                    documents=chunks,
                    embedding=self.embeddings,
                    persist_directory="chroma_db",
                )
                logger.info(f"Created new vector store with {len(chunks)} chunks")
            else:
                # 增量添加文档
                self.vector_store.add_documents(chunks)
                logger.info(f"Added {len(chunks)} chunks to existing vector store")

            # 重置检索器
            self.retriever = None

        except Exception as e:
            logger.error(f"Document processing failed: {str(e)}")
            raise ValueError(f"文档处理失败: {str(e)}") from e

    def ask(self, query: str, k: int = 5, score_threshold: float = 0.2):
        """
        处理用户问题：若已加载文档则通过RAG流程回答，否则直接使用模型自身知识。

        参数:
            query: 用户的问题文本
            k: 检索相关文本的最大数量（默认5条）
            score_threshold: 检索的相似度阈值（低于此值的结果将被过滤，默认0.2）

        返回:
            模型生成的回答文本
        """
        try:
            # 分支1：已加载文档（存在向量库），使用RAG流程
            if self.vector_store:
                # 初始化检索器（若未初始化）
                if not self.retriever:
                    self.retriever = self.vector_store.as_retriever(
                        search_type="similarity_score_threshold",
                        search_kwargs={"k": k, "score_threshold": score_threshold},
                    )
                    logger.info(f"Initialized retriever with k={k}, threshold={score_threshold}")

                logger.info(f"Retrieving context for query: {query}")
                retrieved_docs = self.retriever.invoke(query)

                # 构建上下文
                if not retrieved_docs:
                    context = "No relevant context found in documents."
                else:
                    context = "\n\n".join(doc.page_content for doc in retrieved_docs)
                    logger.info(f"Retrieved {len(retrieved_docs)} relevant documents")

                formatted_input = {"context": context, "question": query}
                current_prompt = self.prompt

            # 分支2：未加载文档（无向量库），直接使用模型自身知识
            else:
                logger.info("No documents loaded, using model knowledge only")
                formatted_input = {"question": query}
                current_prompt = ChatPromptTemplate.from_template(
                    "You are an experienced doctor's assistant. Answer concisely in the same language as the question.\nQuestion: {question}"
                )

            # 构建处理链
            chain = (
                RunnablePassthrough()
                | current_prompt
                | self.model
                | StrOutputParser()
            )

            logger.info(f"Generating response using model: {self.llm_model}")
            return chain.invoke(formatted_input)

        except Exception as e:
            logger.error(f"Query processing failed: {str(e)}")
            return f"Error: {str(e)}"

    def clear(self):
        """重置向量库和检索器（用于清除当前加载的文档）"""
        logger.info("Clearing vector store and retriever")
        self.vector_store = None
        self.retriever = None