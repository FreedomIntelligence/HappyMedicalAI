# demos/weight_management.py
import os
import streamlit as st
from PIL import Image
from core.kba import KnowledgeBaseAssistant

def load_diet_guidelines():
    """加载膳食指南文档"""
    docs_dir = "doc"
    guideline_files = [
        "成人高尿酸血症与痛风食养指南（2024）.pdf",
        "中国居民膳食指南.pdf"
    ]

    # 检查文档是否存在
    missing_files = []
    for file in guideline_files:
        file_path = os.path.join(docs_dir, file)
        if not os.path.exists(file_path):
            missing_files.append(file)

    if missing_files:
        st.warning(f"以下膳食指南文件未找到：\n{', '.join(missing_files)}")
        return False

    # 加载文档到知识库
    with st.spinner("正在加载膳食指南..."):
        for file in guideline_files:
            file_path = os.path.join(docs_dir, file)
            try:
                st.session_state["weight_assistant"].ingest(file_path)
                st.success(f"已加载：{file}")
            except Exception as e:
                st.error(f"加载{file}失败：{str(e)}")
                return False
    return True

def display_body_composition_report():
    """展示身体成分分析报告"""
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("身体成分分析报告")
        try:
            # 尝试加载图片
            image = Image.open("../assets/weight_rag/BodyCompositionAnalysisReport.jpg")
            st.image(image, use_column_width=True)
        except FileNotFoundError:
            st.warning("未找到报告图片：BodyCompositionAnalysisReport.jpg")
        except Exception as e:
            st.error(f"加载报告图片失败：{str(e)}")

    with col2:
        st.subheader("报告信息提取")
        report_info = """
- **体重**：87.2kg，相比 1 日前下降 0.7kg，评价 “过高”
- **身体得分**：81 分，建议 “控制饮食，减少摄入高油高热量食物，同时循序渐进地增加运动量”
- **BMI**：28.2（过高），相比之前下降 0.2
- **体脂率**：25.5%（偏高），相比之前下降 0.3
- **人体成分组成**：
    - 体水分量：49.3kg
    - 脂肪量：22.2kg
    - 骨盐量：3.6kg
    - 蛋白质量：11.4kg
- **肌肉相关**：
    - 肌肉量：61.4kg（优），下降 0.3
    - 肌肉率：70.4%（优），上升 0.2
- **身体水分与蛋白质**：
    - 身体水分：56.5%（优），上升 2.2
    - 蛋白质率：13.1%（标准），下降 2
- **骨盐与骨骼肌**：
    - 骨盐率：4.1%（正常），上升 0.1
    - 骨骼肌量：36.2kg（标准），上升 1.6
- **其他指标**：
    - 内脏脂肪等级：9（警戒），下降 2
    - 基础代谢率：1774kcal（正常），下降 4
    - 推测腰臀比：0.8（标准），下降 0.1
        """
        st.markdown(report_info)

        # TODO: 预留API输入图片接口
        # with st.expander("上传图片提取报告（预留功能）"):
        #     uploaded_image = st.file_uploader("选择图片", type=["jpg", "jpeg", "png"])
        #     if uploaded_image:
        #         st.image(uploaded_image, caption="上传的报告图片", use_column_width=True)
        #         st.info("图片分析功能待实现")

def generate_diet_recommendation():
    """生成饮食建议"""
    st.subheader("饮食建议生成")

    # 构建提示词
    report_info = """
体重：87.2kg，相比 1 日前下降 0.7kg，评价 “过高”
身体得分：81 分
BMI：28.2（过高）
体脂率：25.5%（偏高）
内脏脂肪等级：9（警戒）
其他指标见详细报告
    """

    prompt = f"""
基于以下身体成分分析报告和提供的膳食指南，为用户提供个性化的体重管理饮食建议：

身体成分分析报告：
{report_info}

请结合膳食指南，提供：
1. 每日饮食的总体原则
2. 推荐的食物种类和摄入量
3. 应避免或限制的食物
4. 其他有助于体重管理的饮食建议

回答应简洁明了，基于提供的指南，不要编造信息。如果指南中没有相关信息，请说明。
    """

    # 显示提示词
    with st.expander("查看生成提示词"):
        st.text(prompt)

    # 生成建议
    if st.button("生成饮食建议", type="primary"):
        with st.spinner("正在生成饮食建议..."):
            try:
                if "weight_assistant" not in st.session_state:
                    # 初始化助手
                    st.session_state["weight_assistant"] = KnowledgeBaseAssistant(
                        model_manager=st.session_state["model_manager"],
                        llm_provider=st.session_state["llm_provider"],
                        llm_model=st.session_state["llm_model"],
                        embedding_provider=st.session_state["embedding_provider"],
                        embedding_model=st.session_state["embedding_model"]
                    )
                    # 加载膳食指南
                    load_diet_guidelines()

                # 使用RAG生成建议
                response = st.session_state["weight_assistant"].ask(prompt)
                st.subheader("饮食建议")
                st.write(response)

                # 预留向量数据库切换选项
                with st.expander("向量数据库设置（预留）"):
                    st.selectbox("选择向量数据库", ["Chroma (默认)", "FAISS", "Milvus"], disabled=True)
                    st.info("目前使用默认的Chroma向量数据库，其他选项待实现")

            except Exception as e:
                st.error(f"生成建议失败：{str(e)}")

def weight_tracking_section():
    """体重跟踪部分（TODO）"""
    st.subheader("体重跟踪")
    st.info("体重跟踪功能待实现，未来将支持记录和可视化体重变化趋势")

    # 简单的TODO列表
    with st.expander("开发计划"):
        st.markdown("""
- 实现体重数据可视化功能
- 生成体重变化趋势图表
- 结合饮食记录分析体重变化原因
        """)

def weight_management_demo():
    """体重管理饮食建议demo主函数"""
    st.header("基于RAG的体重管理饮食建议")

    # 初始化助手
    if "weight_assistant" not in st.session_state:
        st.session_state["weight_assistant"] = KnowledgeBaseAssistant(
            model_manager=st.session_state["model_manager"],
            llm_provider=st.session_state["llm_provider"],
            llm_model=st.session_state["llm_model"],
            embedding_provider=st.session_state["embedding_provider"],
            embedding_model=st.session_state["embedding_model"]
        )
        # 自动加载膳食指南
        load_diet_guidelines()

    # 展示身体成分报告
    display_body_composition_report()

    st.divider()

    # 体重跟踪部分
    # weight_tracking_section()

    st.divider()

    # 生成饮食建议
    generate_diet_recommendation()

    # 清除数据按钮
    if st.button("清除体重管理数据", key="clear_weight_data"):
        if "weight_assistant" in st.session_state:
            st.session_state["weight_assistant"].clear()
            del st.session_state["weight_assistant"]
        st.success("体重管理数据已清除")