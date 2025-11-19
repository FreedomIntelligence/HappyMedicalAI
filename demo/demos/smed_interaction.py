# smed_interaction_demo.py
import streamlit as st
import os
import json
import base64

def get_base64_encoded_image(image_path):
    """将图片转换为base64编码，以便嵌入HTML"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except Exception as e:
        st.error(f"图片编码错误: {str(e)}")
        return ""

def get_file_content(file_path):
    """读取文件内容"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        st.error(f"读取文件错误 {file_path}: {str(e)}")
        return ""

def smed_interaction_demo():
    """医疗专业大模型交互展示页面"""
    st.title("医疗专业大模型可视化展示")
    st.write("交互式人体器官模型，展示各部位相关的专业医疗大模型")

    # 获取资源文件路径
    assets_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),  # 当前文件在demos/下
        "..", "assets", "smed_interaction"          # 上一级目录的assets/smed_interaction
    )

    # 验证资源目录是否存在
    if not os.path.exists(assets_dir):
        st.error(f"资源目录不存在: {assets_dir}")
        return

    # 读取各资源文件内容
    html_content = get_file_content(os.path.join(assets_dir, "index.html"))
    js_content = get_file_content(os.path.join(assets_dir, "chart.js"))
    css_content = get_file_content(os.path.join(assets_dir, "styles.css"))

    # 读取JSON数据并转换为JavaScript兼容格式
    json_path = os.path.join(assets_dir, "organ_model.json")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            organ_model_data = json.load(f)
            # 转换为JSON字符串，确保JavaScript兼容性
            json_content = json.dumps(organ_model_data)
    except Exception as e:
        st.error(f"读取JSON文件错误 {json_path}: {str(e)}")
        return

    # 转换图片为base64
    bodymap_path = os.path.join(assets_dir, "bodymap.png")
    if not os.path.exists(bodymap_path):
        st.error(f"人体图不存在: {bodymap_path}")
        return
    bodymap_base64 = get_base64_encoded_image(bodymap_path)

    # 构建完整的HTML内容
    full_html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <style>
            {css_content}
            /* 确保容器占满空间 */
            #wrapper {{
                width: 100% !important;
                height: 100% !important;
            }}
        </style>
        <!-- 引入D3.js -->
        <script src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"></script>
    </head>
    <body>
        <div id="wrapper" class="wrapper">
            <div id="tooltip" class="tooltip">
                <div class="tooltip-models">
                    <ul id="models-list"></ul>
                </div>
            </div>
        </div>

        <script>
            // 注入数据（使用JSON.stringify确保格式正确）
            const organModelData = {json_content};

            // 重写D3图表绘制函数，移除module类型避免MIME错误
            async function drawOrganChart() {{
                try {{
                    // 使用注入的数据
                    const dataset = organModelData;
                    if (!dataset || !dataset.organs) {{
                        throw new Error("无效数据格式: 缺少器官数据");
                    }}
                    const organs = dataset.organs;

                    // 设置图表尺寸
                    const dimensions = {{
                        width: 800,
                        height: 1000,
                        margin: {{ top: 0, right: 0, bottom: 0, left: 0 }}
                    }};

                    dimensions.boundedWidth = dimensions.width - dimensions.margin.left - dimensions.margin.right;
                    dimensions.boundedHeight = dimensions.height - dimensions.margin.top - dimensions.margin.bottom;

                    // 创建画布
                    const wrapper = d3.select("#wrapper")
                        .append("svg")
                            .attr("width", dimensions.width)
                            .attr("height", dimensions.height);

                    const bounds = wrapper.append("g")
                        .style("transform", `translate(${{dimensions.margin.left}}px, ${{dimensions.margin.top}}px)`);

                    // 绘制人体图（使用base64编码的图片）
                    bounds.append("image")
                        .attr("class", "human-body")
                        .attr("xlink:href", "data:image/png;base64,{bodymap_base64}")
                        .attr("width", dimensions.boundedWidth)
                        .attr("height", dimensions.boundedHeight);

                    // 绘制器官点
                    const organPoints = bounds.selectAll(".organ-point")
                        .data(organs)
                        .join("circle")
                            .attr("class", d => `organ-point category-$((d.category || Math.floor(Math.random() * 6) + 1))`)
                            .attr("cx", d => d.x)
                            .attr("cy", d => d.y)
                            .attr("r", 5)
                            .attr("tabindex", "0");

                    // 创建Voronoi图优化交互
                    const delaunay = d3.Delaunay.from(
                        organs,
                        d => d.x,
                        d => d.y
                    );

                    const voronoi = delaunay.voronoi();
                    voronoi.xMax = dimensions.boundedWidth;
                    voronoi.yMax = dimensions.boundedHeight;

                    bounds.selectAll(".voronoi")
                        .data(organs)
                        .join("path")
                        .attr("class", "voronoi")
                        .attr("d", (d, i) => voronoi.renderCell(i))
                        .on("mouseenter", onMouseEnter)
                        .on("mouseleave", onMouseLeave);

                    // 初始化tooltip
                    const tooltip = d3.select("#tooltip");

                    // 辅助函数：获取模型链接
                    function getPriorityLink(model) {{
                        if (typeof model === 'string' || !model.links) return null;
                        if (model.links.demo && model.links.demo.trim() !== "") return model.links.demo;
                        if (model.links.github && model.links.github.trim() !== "") return model.links.github;
                        if (model.links.paper && model.links.paper.trim() !== "") return model.links.paper;
                        return null;
                    }}

                    // 辅助函数：渲染模型列表
                    function renderModels(models) {{
                        if (!Array.isArray(models) || models.length === 0) {{
                            return '<p>无可用模型</p>';
                        }}

                        let html = '<ul class="models-list">';
                        models.forEach(item => {{
                            if (!item) return;
                            html += `<li class="model-category"><strong>${{item.type || 'Unknown'}}：${{item.name || 'Unnamed'}}</strong>`;

                            // 处理直接包含的模型
                            if (item.models && Array.isArray(item.models)) {{
                                html += '<ul class="model-items">';
                                item.models.forEach(model => {{
                                    if (typeof model === 'string') {{
                                        html += `<li>${{model}}</li>`;
                                    }} else if (model) {{
                                        const link = getPriorityLink(model);
                                        const modelName = model.name || 'Unnamed Model';
                                        if (link) {{
                                            html += `<li><a href="${{link}}" target="_blank" style="color: blue; text-decoration: underline;">${{modelName}}</a></li>`;
                                        }} else {{
                                            html += `<li>${{modelName}}</li>`;
                                        }}
                                    }}
                                }});
                                html += '</ul>';
                            }}

                            // 处理子类别
                            else if (item.subcategories && Array.isArray(item.subcategories)) {{
                                html += '<ul class="subcategories">';
                                item.subcategories.forEach(sub => {{
                                    if (!sub) return;
                                    html += `<li class="subcategory"><em>${{sub.name || 'Unnamed'}}</em>`;
                                    html += '<ul class="subcategory-models">';
                                    if (Array.isArray(sub.models)) {{
                                        sub.models.forEach(model => {{
                                            if (typeof model === 'string') {{
                                                html += `<li>${{model}}</li>`;
                                            }} else if (model) {{
                                                const link = getPriorityLink(model);
                                                const modelName = model.name || 'Unnamed Model';
                                                if (link) {{
                                                    html += `<li><a href="${{link}}" target="_blank" style="color: blue; text-decoration: underline;">${{modelName}}</a></li>`;
                                                }} else {{
                                                    html += `<li>${{modelName}}</li>`;
                                                }}
                                            }}
                                        }});
                                    }}
                                    html += '</ul></li>';
                                }});
                                html += '</ul>';
                            }}
                            html += '</li>';
                        }});
                        html += '</ul>';
                        return html;
                    }}

                    // 鼠标交互函数
                    let tooltipHideTimer = null;

                    function onMouseEnter(event, d) {{
                        clearTimeout(tooltipHideTimer);
                        tooltip.select("#models-list").html(renderModels(d.models || []));

                        const halfWidth = dimensions.boundedWidth / 2;
                        const tooltipX = d.x + dimensions.margin.left;
                        const tooltipY = d.y + dimensions.margin.top;

                        tooltip.style("opacity", 1);
                        const tooltipBox = tooltip.node().getBoundingClientRect();
                        const tooltipHeight = tooltipBox.height;

                        const ratio = Math.min(0.8, Math.max(0.2, d.y / dimensions.boundedHeight));
                        const arrowTopPercent = ratio * 100;

                        if (d.x > halfWidth) {{
                            tooltip.classed("right", true).classed("left", false)
                                .style("transform", `translate(calc(${{tooltipX + 20}}px), calc(${{tooltipY}}px - ${{tooltipHeight * ratio}}px))`)
                                .style("--tooltip-arrow-top", `${{arrowTopPercent}}%`);
                        }} else {{
                            tooltip.classed("left", true).classed("right", false)
                                .style("transform", `translate(calc(${{tooltipX - 20}}px - 100%), calc(${{tooltipY}}px - ${{tooltipHeight * ratio}}px))`)
                                .style("--tooltip-arrow-top", `${{arrowTopPercent}}%`);
                        }}

                        // 添加高亮点
                        bounds.append("circle")
                            .attr("class", "highlight-dot")
                            .attr("cx", d.x)
                            .attr("cy", d.y)
                            .attr("r", 8);
                    }}

                    function onMouseLeave(event, d) {{
                        tooltipHideTimer = setTimeout(() => {{
                            tooltip.style("opacity", 0);
                            d3.selectAll(".highlight-dot").remove();
                        }}, 100);
                    }}

                    // 绑定tooltip事件
                    tooltip
                        .on("mouseenter", () => clearTimeout(tooltipHideTimer))
                        .on("mouseleave", () => {{
                            tooltip.style("opacity", 0);
                            d3.selectAll(".highlight-dot").remove();
                        }});

                }} catch (error) {{
                    console.error("绘制图表错误:", error);
                    d3.select("#wrapper").append("div")
                        .text("加载图表错误: " + error.message)
                        .style("color", "red")
                        .style("padding", "20px");
                }}
            }}

            // 页面加载完成后执行
            window.addEventListener('DOMContentLoaded', drawOrganChart);
        </script>
    </body>
    </html>
    """

    # 显示HTML内容，增加高度确保完整显示
    st.components.v1.html(full_html, height=1200, width=850, scrolling=True)