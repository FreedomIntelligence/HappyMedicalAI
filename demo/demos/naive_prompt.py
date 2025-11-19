# prompt_engineering.py
import streamlit as st
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

def prompt_engineering_demo():
    """Prompt engineering demo layout."""
    st.header("探索不同的提示策略如何影响模型回答")
    st.header("Exploring different prompting strategies")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("提示策略设置")
        strategy = st.selectbox(
            "选择提示策略",
            ["基础模式 (basic)", "少样本示例 (few_shot)", "思维链推理 (cot)", "角色建模 (role_modelling)"],
            index=0
        )

        # 角色模板字典
        ROLE_PROFILE = {
            "资深老中医": {
                "view": "强调整体观、阴阳平衡、脏腑经络理论。常用“气血”、“湿热”、“瘀阻”、“脾肾”等中医术语解释病因病机。重视生活方式（饮食情志起居）的调养。治疗思路常包含中药内服、外治（如针灸、贴敷）、食疗建议。",
                "style": "语言可能带有一定文学性或古语色彩（但避免过度晦涩），善用比喻（如“不通则痛”）。诊断常提及“望闻问切”四诊合参。",
                "tone": "通常较为和缓、耐心、带有一定关怀和说教意味（如强调“养生之道”、“忌口”）。"
            },
            "资深内分泌科专家": {
                "view": "专注于激素调节、代谢紊乱相关疾病（如糖尿病、甲状腺疾病、肾上腺疾病等）。善于从内分泌轴、代谢通路角度分析病情，重视实验室检查数据（血糖、激素水平等）。",
                "style": "常使用专业术语（如胰岛素抵抗、糖化血红蛋白、TSH等），习惯结合数值指标进行分析，注重循证医学证据。",
                "tone": "专业严谨，逻辑性强，会详细解释疾病机制，强调长期管理和随访的重要性。"
            },
            "康复中心技师": {
                "view": "关注功能恢复、运动康复、日常生活能力提升。擅长评估运动功能、制定康复计划，注重循序渐进的训练原则。",
                "style": "语言通俗易懂，常使用动作描述和比喻，会给出具体可操作的训练方法，强调正确姿势和动作要领。",
                "tone": "鼓励性强，富有耐心，会提醒注意事项和可能出现的不适反应，强调坚持训练的重要性。"
            },
            "急诊护士": {
                "view": "擅长快速评估急危重症，关注生命体征、症状变化，注重急救处理和病情观察。熟悉急诊流程和常见急症处理原则。",
                "style": "语言简洁明了，指令性强，会分优先级列出处理步骤，常用医学缩写（如BP、HR、SPO2等）。",
                "tone": "果断干练，紧迫感强，既专业又富有同情心，能在紧急情况下给予清晰指导。"
            },
            "custom": {
                "view": "待添加",
                "style": "待添加",
                "tone": "待添加"
            }
        }

        # 统一模板构造器
        BASE_PROMPT = """请扮演以下指定的医学专家角色 `{role}`，**深度融入其专业视角、常用表达方式和典型沟通语气**来回答问题。用与问题相同的语言回答。
        **角色描述：{role}**：
        *   **专业视角**：{view}
        *   **表达方式**：{style}
        *   **沟通语气**：{tone}
        **问题：{question}**
        **回答：** (请务必以`{role}`的口吻和视角开始你的回答)"""

        # 生成 role_templates
        role_templates = {
            role_name: BASE_PROMPT.format(
                role=role_name,
                view=info["view"],
                style=info["style"],
                tone=info["tone"],
                question="{question}"
            )
            for role_name, info in ROLE_PROFILE.items()
        }

        # 预设提示模板
        preset_templates = {
            "基础模式 (basic)": "你是一个经验丰富的医生助手。请根据医学知识，简洁、直接、准确地回答以下问题。用与问题相同的语言回答：\n问题：{question}\n回答：",
            "少样本示例 (few_shot)": "你是一个经验丰富的医生助手。请严格参考以下示例的**回答风格和结构**来回答问题：\n示例1:\n  问：患者出现持续头痛和视力模糊，可能是什么原因？\n  答：头痛伴随视力模糊可能由多种原因引起：\n    1.  **偏头痛**：部分患者发作时可伴有视觉先兆或视力模糊。\n    2.  **青光眼**：眼压急剧升高可导致头痛、视力急剧下降、眼痛、恶心。\n    3.  **颅内压增高**：可由肿瘤、出血、感染等引起，表现为持续性头痛、呕吐、视乳头水肿导致视力模糊。\n    **建议**：此情况需紧急就医，进行详细眼科检查（测眼压、眼底镜）和神经系统评估（如头颅影像学检查），并监测血压。\n\n示例2:\n  问：儿童接种麻疹疫苗的最佳时间是什么时候？\n  答：我国免疫规划对麻疹疫苗接种有明确规定：\n    *   **第一剂**：在儿童 **8月龄** 时接种。\n    *   **第二剂**：在 **18-24月龄** 期间完成接种。\n    **强调**：务必按时接种两剂次，才能提供最佳保护效果，有效预防麻疹及其并发症。\n\n现在请回答以下问题，注意模仿示例的分点/结构化、原因列举和明确的建议/强调部分：\n问题：{question}\n回答：",
            "思维链推理 (cot)": "你是一个医生助手，请严格遵循**逐步推理**的原则回答以下医学问题。用与问题相同的语言回答。\n问题：{question}\n**请务必按以下步骤思考并清晰标注：**\n1.  **理解问题核心**：准确抓住问题的关键点和需要解决的具体方面。\n2.  **回顾相关知识**：回忆相关的医学概念、病理生理、诊断标准、治疗原则、指南推荐等。\n3.  **分析关键因素**：识别影响问题答案的关键变量（如患者年龄、症状、检查结果、合并症、风险因素等）。对于未明确的信息，指出其重要性。\n4.  **逻辑推演/权衡利弊**：基于知识，一步步推导出结论或对不同选项进行比较分析（如诊断可能性排序、治疗选择的优缺点）。\n5.  **形成结论/建议**：给出明确的答案或建议，并简要总结关键推理依据。\n**现在，请严格按照上述步骤（1-5）进行思考，每一步的思考内容请清晰标明（如‘步骤1：...’），然后在最后给出你的最终答案。**",
            "角色建模 (role_modelling)": role_templates["资深老中医"]
        }

        # 角色建模的特殊设置
        role = ""
        if "角色建模" in strategy:
            role_option = st.selectbox(
                "选择专家角色模板",
                ["资深老中医", "资深内分泌科专家", "康复中心技师", "急诊护士", "custom (自定义)"],
                index=0
            )

            # 根据选择的角色模板更新角色和模板
            if role_option != "custom (自定义)":
                role = role_option
                template = st.text_area(
                    "编辑角色提示词模板",
                    value=role_templates[role_option],
                    height=400
                )
            else:
                role = st.text_input("设定专家角色", value="例如：刚开始规培的住院医师")
                template = st.text_area(
                    "编辑角色提示词模板",
                    value=role_templates["custom"],
                    height=400
                )
        else:
            # 非角色建模策略使用预设模板
            template = st.text_area(
                "编辑提示词（使用 {question} 作为问题占位符）",
                value=preset_templates[strategy],
                height=500
            )

    with col2:
        st.subheader("问题输入")
        question = st.text_area("输入您的问题", key="pe_question", height=200)

        if st.button("获取回答", key="pe_submit"):
            if not question.strip():
                st.warning("请输入问题")
            else:
                # 替换模板中的占位符
                final_prompt = template.replace("{question}", question)
                if "{role}" in final_prompt and role:
                    final_prompt = final_prompt.replace("{role}", role)

                with st.spinner("思考中..."):
                    try:
                        # 直接使用模型生成回答
                        model = st.session_state["assistant"].model
                        prompt_template = ChatPromptTemplate.from_template("{input}")
                        chain = prompt_template | model | StrOutputParser()
                        response = chain.invoke({"input": final_prompt})

                        # 显示结果
                        st.subheader("模型回答")
                        st.write(response)

                        # 显示使用的提示词
                        with st.expander("查看完整提示词"):
                            st.code(final_prompt)

                        # 保存历史，包含策略和角色信息
                        if "pe_history" not in st.session_state:
                            st.session_state["pe_history"] = []
                        st.session_state["pe_history"].append((
                            question,
                            response,
                            final_prompt,
                            strategy,  # 保存使用的策略
                            role if "角色建模" in strategy else None  # 保存角色（如果是角色建模）
                        ))

                    except Exception as e:
                        st.error(f"发生错误: {str(e)}")

        # 显示历史记录
        if "pe_history" in st.session_state and st.session_state["pe_history"]:
            st.subheader("历史记录")
            for i, (q, r, p, s, role) in enumerate(st.session_state["pe_history"]):
                with st.expander(f"问题 {i+1}: {q[:50]}..."):
                    st.write(f"> **问题**: {q}")
                    st.write(f"> **提示策略**: {s}")
                    if role:
                        st.write(f"> **专家角色**: {role}")
                    st.write(f"**回答**: {r}")
                    with st.expander("查看完整提示词"):
                        st.code(p)

            if st.button("清除历史记录", key="clear_pe_history"):
                st.session_state["pe_history"] = []