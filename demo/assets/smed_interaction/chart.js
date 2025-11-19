async function drawOrganChart() {
    try {
        // 1. 加载数据
        const dataset = await d3.json("./organ_model.json");
        if (!dataset || !dataset.organs) {
            throw new Error("Invalid data format: Missing organs data");
        }
        const organs = dataset.organs;

        // 2. 设置图表尺寸（根据人体图大小调整）
        const dimensions = {
            width: 800,
            height: 1000,
            margin: {
                top: 0,
                right: 0,
                bottom: 0,
                left: 0,
            },
        };

        dimensions.boundedWidth = dimensions.width
            - dimensions.margin.left
            - dimensions.margin.right;
        dimensions.boundedHeight = dimensions.height
            - dimensions.margin.top
            - dimensions.margin.bottom;

        // 3. 创建画布
        const wrapper = d3.select("#wrapper")
            .append("svg")
                .attr("width", dimensions.width)
                .attr("height", dimensions.height);

        const bounds = wrapper.append("g")
            .style("transform", `translate(${
                dimensions.margin.left
            }px, ${
                dimensions.margin.top
            }px)`);

        // 4. 绘制人体图作为底图
        bounds.append("image")
            .attr("class", "human-body")
            .attr("href", "bodymap.png")
            .attr("width", dimensions.boundedWidth)
            .attr("height", dimensions.boundedHeight);

        // 5. 绘制器官点（使用莫兰迪色系）
        const organPoints = bounds.selectAll(".organ-point")
            .data(organs)
            .join("circle")
                .attr("class", d => `organ-point category-${(d.category || Math.floor(Math.random() * 6) + 1)}`)
                .attr("cx", d => d.x)
                .attr("cy", d => d.y)
                .attr("r", 5) // 缩小点的大小
                .attr("tabindex", "0");

        // 6. 创建 Voronoi 图以优化交互体验
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

        // 7. 初始化 tooltip
        const tooltip = d3.select("#tooltip");

        // 辅助函数：获取模型的优先链接
        function getPriorityLink(model) {
            if (typeof model === 'string' || !model.links) return null;

            // 优先级: demo > github > paper
            if (model.links.demo && model.links.demo.trim() !== "") return model.links.demo;
            if (model.links.github && model.links.github.trim() !== "") return model.links.github;
            if (model.links.paper && model.links.paper.trim() !== "") return model.links.paper;

            return null;
        }

        // 辅助函数：渲染嵌套的模型列表
        function renderModels(models) {
            if (!Array.isArray(models) || models.length === 0) {
                return '<p>No models available</p>';
            }

            let html = '<ul class="models-list">';
            models.forEach(item => {
                if (!item) return;

                // 渲染主类别（类型 + 名称）
                html += `<li class="model-category"><strong>${item.type || 'Unknown'}：${item.name || 'Unnamed'}</strong>`;

                // 处理直接包含的模型
                if (item.models && Array.isArray(item.models)) {
                    html += '<ul class="model-items">';
                    item.models.forEach(model => {
                        if (typeof model === 'string') {
                            html += `<li>${model}</li>`;
                        } else if (model) {
                            const link = getPriorityLink(model);
                            const modelName = model.name || 'Unnamed Model';

                            if (link) {
                                html += `<li><a href="${link}" target="_blank" style="color: blue; text-decoration: underline;">${modelName}</a></li>`;
                            } else {
                                html += `<li>${modelName}</li>`;
                            }
                        }
                    });
                    html += '</ul>';
                }

                // 处理子类别
                else if (item.subcategories && Array.isArray(item.subcategories)) {
                    html += '<ul class="subcategories">';
                    item.subcategories.forEach(sub => {
                        if (!sub) return;
                        html += `<li class="subcategory"><em>${sub.name || 'Unnamed'}</em>`;
                        html += '<ul class="subcategory-models">';

                        if (Array.isArray(sub.models)) {
                            sub.models.forEach(model => {
                                if (typeof model === 'string') {
                                    html += `<li>${model}</li>`;
                                } else if (model) {
                                    const link = getPriorityLink(model);
                                    const modelName = model.name || 'Unnamed Model';

                                    if (link) {
                                        html += `<li><a href="${link}" target="_blank" style="color: blue; text-decoration: underline;">${modelName}</a></li>`;
                                    } else {
                                        html += `<li>${modelName}</li>`;
                                    }
                                }
                            });
                        }
                        html += '</ul></li>';
                    });
                    html += '</ul>';
                }

                html += '</li>';
            });
            html += '</ul>';
            return html;
        }

        // 8. 鼠标交互函数
        let tooltipHideTimer = null;

        function onMouseEnter(event, d) {
            // 清除可能的隐藏计时器
            clearTimeout(tooltipHideTimer);

            // 渲染内容
            tooltip.select("#models-list").html(renderModels(d.models || []));

            const halfWidth = dimensions.boundedWidth / 2;
            const tooltipX = d.x + dimensions.margin.left;
            const tooltipY = d.y + dimensions.margin.top;

            // 获取 tooltip 的尺寸（必须先设置 opacity 为 1 才能获取）
            tooltip.style("opacity", 1);
            const tooltipBox = tooltip.node().getBoundingClientRect();
            const tooltipHeight = tooltipBox.height;

            // 计算 tooltip 箭头相对位置（限制在 20% ~ 80%）
            const ratio = Math.min(0.8, Math.max(0.2, d.y / dimensions.boundedHeight));
            const arrowTopPercent = ratio * 100;

            // 设置 tooltip 位置
            if (d.x > halfWidth) {
                tooltip.classed("right", true).classed("left", false)
                    .style("transform", `translate(calc(${tooltipX + 20}px), calc(${tooltipY}px - ${tooltipHeight * ratio}px))`)
                    .style("--tooltip-arrow-top", `${arrowTopPercent}%`);
            } else {
                tooltip.classed("left", true).classed("right", false)
                    .style("transform", `translate(calc(${tooltipX - 20}px - 100%), calc(${tooltipY}px - ${tooltipHeight * ratio}px))`)
                    .style("--tooltip-arrow-top", `${arrowTopPercent}%`);
            }

            // 添加高亮点
            bounds.append("circle")
                .attr("class", "highlight-dot")
                .attr("cx", d.x)
                .attr("cy", d.y)
                .attr("r", 8);
        }

        function onMouseLeave(event, d) {
            // 设置延时器，如果鼠标没有进入 tooltip，就隐藏
            tooltipHideTimer = setTimeout(() => {
                tooltip.style("opacity", 0);
                d3.selectAll(".highlight-dot").remove();
            }, 100); // 100ms 内如果进入 tooltip，就取消隐藏
        }

        // 给 tooltip 绑定事件
        tooltip
            .on("mouseenter", () => {
                clearTimeout(tooltipHideTimer);
            })
            .on("mouseleave", () => {
                tooltip.style("opacity", 0);
                d3.selectAll(".highlight-dot").remove();
            });
    } catch (error) {
        console.error("Error drawing organ chart:", error);
        d3.select("#wrapper").append("div")
            .text("Error loading chart: " + error.message)
            .style("color", "red")
            .style("padding", "20px");
    }
}

// 页面加载完成后执行
window.addEventListener('DOMContentLoaded', drawOrganChart);