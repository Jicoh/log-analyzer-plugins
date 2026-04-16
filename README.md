# Log Analyzer Plugins

日志分析器插件系统，提供可扩展的日志分析能力。

## 安装

### 作为 Git Submodule 使用

```bash
git submodule add <repo_url> plugins
git submodule update --init --recursive
```

## 插件开发指南

### 目录结构

```
my_plugin/
├── plugin.py        # 必需：插件实现
└── plugin.json      # 必需：插件元数据
```

### plugin.json 元数据

```json
{
    "id": "my_plugin",
    "name": "My Plugin",
    "version": "1.0.0",
    "description": "插件中文描述",
    "plugin_type": "CloudBMC"
}
```

字段说明：
- `id`: 插件唯一标识
- `name`: 插件显示名称
- `version`: 版本号
- `description`: 中文描述
- `plugin_type`: 插件类型（CloudBMC、iBMC、LxBMC）

### plugin.py 实现

```python
from plugins.base import BasePlugin, AnalysisResult, ResultMeta, StatsItem

class MyPlugin(BasePlugin):
    def analyze(self, log_path: str) -> AnalysisResult:
        import os
        from datetime import datetime

        # 判断是文件还是目录
        if os.path.isfile(log_path):
            log_files = [log_path]
        else:
            # 目录：查找所有日志文件
            log_files = []
            for root, dirs, files in os.walk(log_path):
                for f in files:
                    if f.endswith('.log') or f.endswith('.txt'):
                        log_files.append(os.path.join(root, f))

        # 分析所有日志文件
        all_lines = []
        for log_file in log_files:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines.extend(f.readlines())

        meta = ResultMeta(
            plugin_id=self.id,
            plugin_name=self.name,
            version=self.get_version(),
            analysis_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            log_files=[os.path.basename(f) for f in log_files],
            plugin_type=self.get_plugin_type()
        )

        result = AnalysisResult(meta=meta)

        result.add_stats("分析概览", [
            StatsItem(label="总行数", value=len(all_lines), severity="info", icon="file-text"),
            StatsItem(label="错误数", value=5, severity="error", icon="x-circle"),
        ])

        result.add_table("错误详情",
            columns=[
                {"key": "line", "label": "行号", "type": "number"},
                {"key": "message", "label": "消息", "type": "text"}
            ],
            rows=[{"line": 123, "message": "Error occurred"}],
            severity="error"
        )

        return result

plugin_class = MyPlugin
```

## API 文档

### PluginManager

```python
from plugins import get_plugin_manager

manager = get_plugin_manager()
plugins = manager.get_all_plugins()
categories = manager.get_plugins_categories()
result = manager.run_analysis(["log_parser"], "/path/to/logfile")
```

### AnalysisResult 格式

插件分析结果保存为 `plugin_result.json`，格式如下：

```json
{
  "log_parser": {
    "meta": {
      "plugin_id": "log_parser",
      "plugin_name": "Log Parser",
      "version": "2.0",
      "analysis_time": "2026-04-13 16:44:19",
      "log_files": ["server.log"],
      "plugin_type": "CloudBMC",
      "description": "日志解析插件，提取错误和警告信息"
    },
    "sections": [
      {
        "type": "stats",
        "title": "分析概览",
        "icon": "chart-bar",
        "items": [
          {"label": "总行数", "value": 1523, "unit": "行", "severity": "info", "icon": "file-text"},
          {"label": "错误数", "value": 15, "unit": "个", "severity": "error", "icon": "x-circle"},
          {"label": "警告数", "value": 23, "unit": "个", "severity": "warning", "icon": "alert-triangle"}
        ]
      },
      {
        "type": "table",
        "title": "错误详情",
        "severity": "error",
        "icon": "table",
        "columns": [
          {"key": "line", "label": "行号", "type": "number"},
          {"key": "time", "label": "时间", "type": "text"},
          {"key": "message", "label": "消息", "type": "text", "truncate": 50}
        ],
        "rows": [
          {"line": 123, "time": "10:23:45", "message": "Connection timeout"},
          {"line": 456, "time": "10:25:12", "message": "Sensor reading failed"}
        ]
      },
      {
        "type": "timeline",
        "title": "事件时间线",
        "icon": "clock",
        "events": [
          {"timestamp": "2026-04-10 10:23:45", "title": "系统启动", "description": "", "severity": "info", "icon": "", "detail": ""},
          {"timestamp": "2026-04-10 10:25:12", "title": "传感器错误", "description": "温度传感器异常", "severity": "error", "icon": "x-circle", "detail": "Sensor ID: TEMP_01"}
        ]
      },
      {
        "type": "cards",
        "title": "问题卡片",
        "icon": "layers",
        "cards": [
          {"title": "内存泄漏", "severity": "error", "icon": "alert-triangle", "content": {"summary": "内存持续增长", "metrics": {"影响": "高", "进程": "java"}}}
        ]
      },
      {
        "type": "chart",
        "title": "错误分布",
        "icon": "chart-bar",
        "chart_type": "bar",
        "data": {"labels": ["ERROR", "WARNING", "INFO"], "values": [15, 23, 100]},
        "options": {}
      },
      {
        "type": "search_box",
        "title": "日志搜索",
        "icon": "search",
        "placeholder": "输入关键词搜索日志",
        "data": [{"line": 123, "content": "Error occurred at startup"}],
        "search_fields": ["line", "content"]
      },
      {
        "type": "raw",
        "title": "原始数据",
        "data": {"custom_key": "custom_value", "debug_info": {"count": 42}}
      }
    ]
  }
}
```

#### meta 元数据字段

| 字段 | 类型 | 说明 |
|------|------|------|
| plugin_id | string | 插件唯一标识 |
| plugin_name | string | 插件显示名称 |
| version | string | 版本号 |
| analysis_time | string | 分析时间（YYYY-MM-DD HH:MM:SS） |
| log_files | array | 分析的日志文件路径列表(如果有则必填) |
| plugin_type | string | 插件类型（CloudBMC、iBMC、LxBMC） |
| description | string | 插件描述 |

#### sections 区块数组

每个插件返回一个 sections 数组，包含多个展示区块。区块类型由 `type` 字段决定。

**stats - 统计概览**

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 固定值 "stats" |
| title | string | 区块标题 |
| icon | string | 图标名称 |
| items | array | 统计项数组 |

items 数组中每个 StatsItem：

| 字段 | 类型 | 说明 |
|------|------|------|
| label | string | 统计项标签 |
| value | number/string | 统计值 |
| unit | string | 单位（可选） |
| severity | string | 严重程度：info/warning/error/success |
| icon | string | 图标名称（可选） |

**table - 表格**

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 固定值 "table" |
| title | string | 区块标题 |
| severity | string | 区块严重程度 |
| icon | string | 图标名称 |
| columns | array | 列定义数组 |
| rows | array | 数据行数组 |

columns 数组中每个列定义：

| 字段 | 类型 | 说明 |
|------|------|------|
| key | string | 列键名（对应 rows 中的字段） |
| label | string | 列显示名称 |
| type | string | 列类型：text/number |
| width | string | 列宽度（可选） |
| truncate | number | 截断长度（可选，超过则显示...） |

**timeline - 时间线**

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 固定值 "timeline" |
| title | string | 区块标题 |
| icon | string | 图标名称 |
| events | array | 事件数组 |

events 数组中每个 TimelineEvent：

| 字段 | 类型 | 说明 |
|------|------|------|
| timestamp | string | 时间戳 |
| title | string | 事件标题 |
| description | string | 事件描述（可选） |
| severity | string | 严重程度 |
| icon | string | 图标名称（可选） |
| detail | string | 详细信息（可选） |

**cards - 卡片组**

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 固定值 "cards" |
| title | string | 区块标题 |
| icon | string | 图标名称 |
| cards | array | 卡片数组 |

cards 数组中每个 CardItem：

| 字段 | 类型 | 说明 |
|------|------|------|
| title | string | 卡片标题 |
| severity | string | 严重程度 |
| icon | string | 图标名称（可选） |
| content | object | 卡片内容（自定义结构） |

**chart - 图表**

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 固定值 "chart" |
| title | string | 区块标题 |
| icon | string | 图标名称 |
| chart_type | string | 图表类型：bar/pie/line |
| data | object | 图表数据 |
| options | object | 图表选项（可选） |

data 对象结构：

| 字段 | 类型 | 说明 |
|------|------|------|
| labels | array | 标签数组 |
| values | array | 值数组 |

**search_box - 搜索框**

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 固定值 "search_box" |
| title | string | 区块标题 |
| icon | string | 图标名称 |
| placeholder | string | 搜索框提示文字 |
| data | array | 可搜索数据数组 |
| search_fields | array | 可搜索字段列表 |

**raw - 原始数据**

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 固定值 "raw" |
| title | string | 区块标题 |
| data | object | 自定义数据结构 |

## 数据流程说明

### 统计流程（历史记录）

历史记录 API（`src/web/routes/history_api.py`）从 `plugin_result.json` 中提取统计数据：

1. 遍历所有插件的 sections 数组
2. 筛选 `type == 'stats'` 的区块
3. 遍历 items 数组，检查 `severity` 字段
4. 累计 `severity == 'error'` 的统计项的 value 为总错误数
5. 累计 `severity == 'warning'` 的统计项的 value 为总警告数
6. 显示在历史记录列表页面

**关键代码逻辑：**
```python
for section in sections:
    if section.get('type') == 'stats' and section.get('items'):
        for item in section.get('items', []):
            severity = item.get('severity', '')
            value = item.get('value', 0)
            if severity == 'error':
                total_errors += int(value)
            elif severity == 'warning':
                total_warnings += int(value)
```

### 渲染流程（HTML 输出）

HTML 渲染器（`plugins/renderer/html_renderer.py`）将 JSON 转换为静态 HTML：

1. 按 plugin_id 分组展示，每个插件一个区块
2. 使用 Jinja2 模板渲染各 section 类型
3. severity 映射为 Bootstrap 颜色：
   - info → secondary（灰色）
   - warning → warning（黄色）
   - error → danger（红色）
   - success → success（绿色）
4. 图标使用 Feather Icons

**输出文件：**
- JSON: `data/plugin_output/{timestamp}_log/plugin_result.json`
- HTML: `data/plugin_output/{timestamp}_log/plugin_result.html`

### Section 类型

#### stats - 统计概览

```python
result.add_stats("分析概览", [
    StatsItem(label="错误数", value=15, unit="个", severity="error", icon="x-circle"),
    StatsItem(label="警告数", value=23, unit="个", severity="warning", icon="alert-triangle")
])
```

#### table - 表格

```python
result.add_table("错误详情",
    columns=[
        {"key": "line", "label": "行号", "type": "number"},
        {"key": "message", "label": "消息", "type": "text", "truncate": 50}
    ],
    rows=[{"line": 123, "message": "Error occurred"}],
    severity="error",
    icon="x-circle"
)
```

#### chart - 图表

支持 `bar`、`pie`、`line` 三种类型。

```python
from plugins.base import ChartData

result.add_chart("错误分布", chart_type="bar",
    data=ChartData(labels=["ERROR", "WARNING"], values=[15, 23])
)
```

#### timeline - 时间线

```python
from plugins.base import TimelineEvent

result.add_timeline("事件时间线", [
    TimelineEvent(timestamp="2026-04-10 10:23:45", title="系统启动", severity="info"),
    TimelineEvent(timestamp="2026-04-10 10:25:12", title="传感器错误", severity="error")
])
```

#### cards - 卡片组

```python
from plugins.base import CardItem

result.add_cards("问题卡片", [
    CardItem(title="内存泄漏", severity="error", icon="alert-triangle",
             content={"summary": "发现内存持续增长", "metrics": {"影响": "高"}}),
])
```

#### search_box - 搜索框

```python
result.add_search_box("日志搜索",
    data=[{"line": 123, "content": "error msg"}],
    search_fields=["line", "content"],
    placeholder="输入关键词搜索"
)
```

#### raw - 原始数据

```python
result.add_raw("自定义数据", {"key": "value"})
```

### Severity 严重程度

| 值 | 说明 |
|----|------|
| info | 普通信息 |
| warning | 警告 |
| error | 错误 |
| success | 成功 |

### Icon 图标

| 名称 | 说明 |
|------|------|
| x-circle | 错误 |
| alert-triangle | 警告 |
| info-circle | 信息 |
| check-circle | 成功 |
| clock | 时间 |
| chart-bar | 图表 |
| file-text | 文件 |
| table | 表格 |
| layers | 卡片 |
| search | 搜索 |

## HTML渲染器

将插件分析结果JSON转换为静态HTML文件，按插件分类展示。

### 使用方法

```python
from plugins.renderer import render_html

# 从JSON文件生成HTML（保存在JSON同目录）
html_path = render_html('data/plugin_output/xxx/plugin_result.json')
print(f'HTML文件: {html_path}')

# 或使用HtmlRenderer类
from plugins.renderer import HtmlRenderer

renderer = HtmlRenderer()
html_content = renderer.render(data_dict)
html_path = renderer.render_to_file('path/to/plugin_result.json')
```

### 输出文件

- JSON: `data/plugin_output/xxx/plugin_result.json`
- HTML: `data/plugin_output/xxx/plugin_result.html`

### HTML特性

- 独立静态HTML，无需JavaScript
- 内嵌Bootstrap CSS和图标
- 支持所有Section类型渲染
- 按插件分组展示

## 内置插件

### log_parser

解析日志文件，提取错误和警告信息。

### log_statistics

分析日志统计信息，包括时间分布和日志级别分布。