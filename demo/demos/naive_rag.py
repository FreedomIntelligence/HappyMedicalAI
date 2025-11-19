# naive_rag.py
import os
import tempfile
import time
import streamlit as st
from streamlit_chat import message
from core.kba import KnowledgeBaseAssistant

def display_rag_messages():
    """Display the RAG chat history."""
    st.subheader("Chat History")
    for i, (msg, is_user) in enumerate(st.session_state["rag_messages"]):
        message(msg, is_user=is_user, key=f"rag_{i}")
    st.session_state["rag_thinking"] = st.empty()

def process_rag_input():
    """Process RAG user input and generate response."""
    user_input = st.session_state["rag_user_input"]
    if user_input and user_input.strip():
        user_text = user_input.strip()
        with st.session_state["rag_thinking"], st.spinner("思考中..."):
            try:
                agent_text = st.session_state["assistant"].ask(
                    user_text,
                    k=st.session_state["retrieval_k"],
                    score_threshold=st.session_state["retrieval_threshold"],
                )
            except Exception as e:
                agent_text = f"Error: {str(e)}"
                st.error(f"An error occurred: {str(e)}")

        st.session_state["rag_messages"].append((user_text, True))
        st.session_state["rag_messages"].append((agent_text, False))
        st.session_state["rag_user_input"] = ""

def handle_file_upload(uploaded_files):
    """Handle file upload and ingestion."""
    if not uploaded_files:
        return

    st.session_state["rag_messages"] = []

    for file in uploaded_files:
        file_ext = os.path.splitext(file.name)[1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tf:
            tf.write(file.getbuffer())
            file_path = tf.name

        with st.session_state["ingestion_spinner"], st.spinner(f"Ingesting {file.name}..."):
            try:
                t0 = time.time()
                st.session_state["assistant"].ingest(file_path)
                t1 = time.time()
                st.session_state["rag_messages"].append(
                    (f"Ingested {file.name} in {t1 - t0:.2f} seconds", False)
                )
            except Exception as e:
                st.error(f"Failed to ingest {file.name}: {str(e)}")
                st.session_state["rag_messages"].append(
                    (f"Failed to ingest {file.name}", False)
                )
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)

def rag_demo():
    """RAG demo layout."""
    st.header("基于指南的简单医疗问答")
    st.header("Naive Guide-Based Medical QA")

    # 文件上传区域
    st.subheader("上传文档")
    uploaded_files = st.file_uploader(
        "指南、书籍、文件上传 (支持PDF/MD/TXT)",
        type=["pdf", "md", "txt"],
        key="file_uploader",
        label_visibility="collapsed",
        accept_multiple_files=True,
    )

    # 处理文件上传
    if uploaded_files and (
        "last_uploaded_files" not in st.session_state or
        st.session_state["last_uploaded_files"] != uploaded_files
    ):
        handle_file_upload(uploaded_files)
        st.session_state["last_uploaded_files"] = uploaded_files

    st.session_state["ingestion_spinner"] = st.empty()

    # 检索设置
    st.subheader("检索设置")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state["retrieval_k"] = st.slider(
            "检索结果数量 (k)", min_value=1, max_value=10, value=5
        )
    with col2:
        st.session_state["retrieval_threshold"] = st.slider(
            "相似度阈值", min_value=0.0, max_value=1.0, value=0.2, step=0.05
        )

    # 聊天区域
    display_rag_messages()
    st.text_input("输入消息...", key="rag_user_input", on_change=process_rag_input)

    # 操作按钮
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("清除聊天记录", key="clear_chat"):
            st.session_state["rag_messages"] = []
    with col2:
        if st.button("清除文档", key="clear_docs"):
            st.session_state["assistant"].clear()
            st.session_state["rag_messages"] = []
            if "last_uploaded_files" in st.session_state:
                del st.session_state["last_uploaded_files"]
            st.success("文档和聊天记录已清除")
    with col3:
        if st.button("重置所有", key="reset_all"):
            # 修改助手初始化参数，适配多提供商
            st.session_state["assistant"] = KnowledgeBaseAssistant(
                model_manager=st.session_state["model_manager"],
                llm_provider=st.session_state["llm_provider"],
                llm_model=st.session_state["llm_model"],
                embedding_provider=st.session_state["embedding_provider"],
                embedding_model=st.session_state["embedding_model"]
            )
            st.session_state["rag_messages"] = []
            if "last_uploaded_files" in st.session_state:
                del st.session_state["last_uploaded_files"]
            st.success("系统已重置")