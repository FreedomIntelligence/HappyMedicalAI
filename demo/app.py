# app.py
import os

import requests
import streamlit as st

from core.models import ModelManager
from core.kba import KnowledgeBaseAssistant
from demos.todo import todo_page_ideas
from demos.naive_rag import rag_demo
from demos.naive_prompt import prompt_engineering_demo
from demos.smed_interaction import smed_interaction_demo
from demos.weight_management import weight_management_demo

st.set_page_config(page_title="happy-medical-llm demo", layout="wide")

def fetch_ollama_models():
    """从本地Ollama服务获取可用模型列表"""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = [model["name"] for model in response.json().get("models", [])]
            return sorted(models)
        return []
    except Exception as e:
        st.error(f"无法连接Ollama服务: {str(e)}")
        return []

def model_selection_page():
    """模型选择页面"""
    st.title("🐍 happy-medical-llm demo")
    col1, col2 = st.columns(2)
    # 根据当前sub_page状态动态设置按钮样式
    current_sub_page = st.session_state.get("sub_page")
    with col1:
        if st.button(
            "医疗大模型可视化",
            use_container_width=True,
            # 当当前是可视化页时高亮
            type="primary" if current_sub_page == "smed_interaction" else "secondary"
        ):
            st.session_state["sub_page"] = "smed_interaction"
            st.rerun()
    with col2:
        if st.button(
            "选择模型体验不同应用",
            use_container_width=True,
            # 当当前是模型选择页时高亮
            type="primary" if current_sub_page == "model_selection" else "secondary"
        ):
            st.session_state["sub_page"] = "model_selection"
            st.rerun()

    # 如果选择了模型选择子页面，显示原有内容
    if st.session_state.get("sub_page") == "model_selection":
        st.subheader("第一步：选择语言模型和嵌入模型")

        with st.expander("配置说明", expanded=True):
            st.markdown("""
            - **LLM模型**：用于生成回答的核心语言模型
            - **嵌入模型**：用于文档内容向量化的专用模型
            - 请确保已在config.yaml中配置好相关API密钥（Ollama除外）
            """)

        try:
            # 初始化模型管理器
            model_manager = ModelManager()
        except Exception as e:
            st.error(f"加载模型配置失败: {str(e)}")
            st.stop()

        # 选择模型提供商
        st.subheader("选择模型提供商")
        available_providers = [p for p in model_manager.available_providers if model_manager.available_providers[p]["available"]]
        unavailable_providers = [p for p in model_manager.available_providers if not model_manager.available_providers[p]["available"]]

        # 显示可用提供商
        col1, col2 = st.columns(2)
        with col1:
            llm_provider = st.selectbox(
                "LLM模型提供商",
                available_providers,
                index=available_providers.index("ollama") if "ollama" in available_providers else 0,
                help="选择用于生成回答的语言模型提供商"
            )

        with col2:
            embedding_provider = st.selectbox(
                "嵌入模型提供商",
                available_providers,
                index=available_providers.index("ollama") if "ollama" in available_providers else 0,
                help="选择用于文档向量化的嵌入模型提供商"
            )

        # 显示不可用提供商及其原因
        if unavailable_providers:
            with st.expander(f"不可用的提供商 ({len(unavailable_providers)})", expanded=False):
                for provider in unavailable_providers:
                    st.markdown(f"- {provider}: 请在config.yaml中配置API密钥")

        # 选择具体模型
        st.subheader("选择具体模型")
        col1, col2 = st.columns(2)

        with col1:
            # 获取所选提供商的可用聊天模型
            chat_models = [m["name"] for m in model_manager.available_providers[llm_provider]["chat_models"]]
            default_chat_model = model_manager.get_default_chat_model(llm_provider)
            llm_model = st.selectbox(
                f"{llm_provider} - 选择LLM模型",
                chat_models,
                index=chat_models.index(default_chat_model) if default_chat_model in chat_models else 0,
                help="选择用于生成回答的语言模型"
            )

        with col2:
            # 获取所选提供商的可用嵌入模型
            embedding_models = [m["name"] for m in model_manager.available_providers[embedding_provider]["embedding_models"]]
            default_embedding_model = model_manager.get_default_embedding_model(embedding_provider)
            embedding_model = st.selectbox(
                f"{embedding_provider} - 选择嵌入模型",
                embedding_models,
                index=embedding_models.index(default_embedding_model) if default_embedding_model in embedding_models else 0,
                help="选择用于文档向量化的嵌入模型"
            )

        # 保存模型选择
        if st.button("确认选择并进入交互演示", type="primary"):
            st.session_state["model_manager"] = model_manager
            st.session_state["llm_provider"] = llm_provider
            st.session_state["llm_model"] = llm_model
            st.session_state["embedding_provider"] = embedding_provider
            st.session_state["embedding_model"] = embedding_model
            st.session_state["page"] = "main"
            st.rerun()

        # 模型信息展示
        st.divider()
        st.subheader("当前配置信息")
        st.json(model_manager.available_providers, expanded=False)

    # 如果选择了医疗大模型可视化子页面，显示相应内容
    elif st.session_state.get("sub_page") == "smed_interaction":
        smed_interaction_demo()

def main_page():
    """Main app page layout."""
    # 如果模型参数不存在，返回选择页面
    required_states = ["model_manager", "llm_provider", "llm_model", "embedding_provider", "embedding_model"]
    if not all(state in st.session_state for state in required_states):
        st.session_state["page"] = "model_selection"
        st.rerun()

    # 固定位置显示模型信息和按钮
    st.write("---")

    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 20px; font-family: sans-serif; flex-wrap: wrap;">
            <form action="#" method="get" style="margin: 0;">
                <button type="submit" name="rechoose_model_top" style="
                    background: none;
                    border: none;
                    color: lightgray;
                    cursor: pointer;
                    font-size: 20px;
                    font-weight: bold;
                    font-family: inherit;
                    padding: 0;
                ">重新选择模型</button>
            </form>
            <span><strong>LLM模型</strong>: <code>{st.session_state['llm_provider']}/{st.session_state['llm_model']}</code></span>
            <span><strong>嵌入模型</strong>: <code>{st.session_state['embedding_provider']}/{st.session_state['embedding_model']}</code></span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 处理模型重新选择事件（防重入）
    if "reset_triggered" not in st.session_state:
        if st.query_params.get("rechoose_model_top") is not None:
            # 安全清除所有相关状态
            keys_to_remove = ["assistant", "llm_provider", "llm_model", "embedding_provider", "embedding_model", "model_manager", "messages", "file_uploader_key"]
            for key in keys_to_remove:
                st.session_state.pop(key, None)

            # 设置页面跳转 + 防重入标记
            st.session_state["page"] = "model_selection"
            st.session_state["reset_triggered"] = True

            # 立即清除查询参数
            st.query_params.clear()
            st.rerun()

    st.write("---")

    # 初始化助手
    if "assistant" not in st.session_state:
        st.session_state["assistant"] = KnowledgeBaseAssistant(
            model_manager=st.session_state["model_manager"],
            llm_provider=st.session_state["llm_provider"],
            llm_model=st.session_state["llm_model"],
            embedding_provider=st.session_state["embedding_provider"],
            embedding_model=st.session_state["embedding_model"]
        )

    if "rag_messages" not in st.session_state:
        st.session_state["rag_messages"] = []

    tab1, tab2, tab3, tab4 = st.tabs([
        "不同提示案例对比分析 (Different Prompt Comparision)",
        "体重管理饮食建议 (Weight Management Suggestions)",
        "提示词交互实践 (Interactive Prompt Practice)",
        "RAG增强问答 (RAG-enhanced QA)",
        # "更多想法 (TODO Ideas)"
    ])

    with tab1:
        from demos.prompt_comp import prompt_comp_section
        prompt_comp_section()

    with tab2:
        weight_management_demo()

    with tab3:
        from demos.naive_rag import rag_demo
        rag_demo()

    with tab4:
        from demos.naive_prompt import prompt_engineering_demo
        prompt_engineering_demo()

    # with tab5:
    #     todo_page_ideas()

if __name__ == "__main__":
    if "sub_page" not in st.session_state:
        st.session_state["sub_page"] = "smed_interaction"

    if "page" not in st.session_state:
        st.session_state["page"] = "model_selection"

    if st.session_state["page"] == "model_selection":
        model_selection_page()
    elif st.session_state["page"] == "main":
        main_page()
