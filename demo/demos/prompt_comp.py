import os
import yaml
import streamlit as st
from PIL import Image

def load_case_data(case_dir):
    """从指定目录加载 description.yaml 文件"""
    yaml_path = os.path.join(case_dir, "description.yaml")
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        st.error(f"错误：在 '{case_dir}' 目录下未找到 description.yaml 文件。")
        return None
    except Exception as e:
        st.error(f"加载或解析YAML文件时出错: {e}")
        return None

def prompt_comp_section():
    """渲染整个提示词对比分析界面"""
    st.header("不同提示案例对比分析")

    cases = {
        "案例一：骨科图片对比分析": "assets/prompt_comp/case1_knee_joint_fracture",
        "案例二：痛风病例对比分析": "assets/prompt_comp/case2_gout_ankle_pain"
    }

    selected_case_name = st.selectbox("选择案例", list(cases.keys()))
    case_dir = cases[selected_case_name]
    case_data = load_case_data(case_dir)

    if not case_data:
        return # 如果数据加载失败则停止渲染

    # --- 顶部区域：案例需求与附件图片 ---
    col1, col2 = st.columns([1, 3])
    with col1:
        st.subheader("案例需求")
        st.write(case_data.get("description", "未提供描述。"))

    with col2:
        # 需求2：改进图片显示逻辑
        images_data = case_data.get("images")
        if images_data and isinstance(images_data, list):
            # 过滤出真实存在的图片文件
            valid_images = [
                img for img in images_data
                if img.get("path") and os.path.exists(img["path"])
            ]

            if valid_images:
                # 为每张有效图片创建一个列，实现横向排列
                image_cols = st.columns(len(valid_images))
                for i, image_info in enumerate(valid_images):
                    with image_cols[i]:
                        # 需求1：使用 use_container_width 替代旧参数，并控制图片大小
                        # st.image(
                        #     image_info["path"],
                        #     caption=image_info.get("caption", ""),
                        #     # use_container_width=True
                        # )
                        image = Image.open(image_info["path"])

                        # 获取原图尺寸
                        original_width, original_height = image.size

                        # 设定目标高度
                        target_height = 300

                        # 计算等比例缩放后的宽度
                        # 避免原图高度为0导致除零错误
                        if original_height > 0:
                            ratio = target_height / original_height
                            target_width = int(original_width * ratio)

                            # 按新尺寸缩放图片
                            resized_image = image.resize((target_width, target_height))

                            # 显示处理后的图片
                            st.image(
                                resized_image,
                                caption=image_info.get("caption", ""),
                                )

            # 为YAML中配置但路径不正确的图片显示警告
            for img_info in images_data:
                path = img_info.get("path")
                if path and not os.path.exists(path):
                    st.warning(f"图片文件未找到，请检查路径：{path}")

    st.divider()

    # --- 左右对比区域 ---
    prompts = case_data.get("prompts", {})
    if not prompts:
        st.warning("当前案例未配置任何提示词。")
        return

    prompt_names = list(prompts.keys())

    # 确保至少有两个提示词可供选择，否则设置默认值
    index1 = 0
    index2 = 1 if len(prompt_names) > 1 else 0

    col1, col2 = st.columns(2)

    with col1:
        # 需求3：加粗 selectbox 标签，并移除背景色块
        prompt1_name = st.selectbox(
            "**选择第一个提示词模板**",
            prompt_names,
            index=index1,
            key="prompt1"
        )
        prompt1_data = prompts[prompt1_name]

        st.subheader("提示词内容")
        st.code(prompt1_data.get("prompt", ""), language="text")

        st.subheader("模型回答")
        st.write(prompt1_data.get("response", ""))

        # 需求4：将“评价”提升为同级标题
        st.subheader("评价")
        st.write(prompt1_data.get("evaluation", ""))

    with col2:
        # 需求3：加粗 selectbox 标签，并移除背景色块
        prompt2_name = st.selectbox(
            "**选择第二个提示词模板**",
            prompt_names,
            index=index2,
            key="prompt2"
        )
        prompt2_data = prompts[prompt2_name]

        st.subheader("提示词内容")
        st.code(prompt2_data.get("prompt", ""), language="text")

        st.subheader("模型回答")
        st.write(prompt2_data.get("response", ""))

        # 需求4：将“评价”提升为同级标题
        st.subheader("评价")
        st.write(prompt2_data.get("evaluation", ""))

# 如果要直接运行此文件进行测试，可以添加以下代码
if __name__ == "__main__":
    # 在运行前，请确保你的项目目录结构如下：
    # your_app.py
    # └── assets
    #     └── prompt_comp
    #         ├── case1_knee_joint_fracture
    #         │   ├── description.yaml
    #         │   └── your_image.png
    #         └── case2_gout_ankle_pain
    #             └── description.yaml
    prompt_comp_section()