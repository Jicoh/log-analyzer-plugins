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
- `id`: 插件唯一标识，格式为插件类型_编号
- `name`: 插件显示名称
- `version`: 版本号
- `description`: 中文描述
- `plugin_type`: 插件类型（CloudBMC、iBMC、LxBMC）

### plugin.py 实现

```python
from typing import Dict, List, Union
from plugins.base import BasePlugin, AnalysisResult, ResultMeta, StatsItem, CliResult

class MyPlugin(BasePlugin):
    def analyze(self, log_content: Dict[str, List[str]],
                task_name: str = "", bmc_ip: str = "", date: str = "",
                source: str = "system") -> Union[AnalysisResult, CliResult]:
        from datetime import datetime

        # log_content 是 {"相对路径": ["行1", "行2"]} 字典
        # 例如: {"system.log": ["日志行1", "日志行2"], "sub/error.log": ["错误行1"]}
        log_files = list(log_content.keys())

        # 执行分析逻辑...

        # 构建 system 格式返回值
        meta = ResultMeta(
            plugin_id=self.id,
            plugin_name=self.name,
            version=self.get_version(),
            analysis_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            log_files=log_files,
            plugin_type=self.get_plugin_type()
        )

        result = AnalysisResult(meta=meta)
        result.add_stats("分析概览", [
            StatsItem(label="文件数", value=len(log_files), severity="info"),
        ])

        # 同时构建 cli 格式返回值, task_name, bmc_ip, date不需要修改，直接使用入参赋值
        cli_result = CliResult(
            task_name=task_name,
            bmc_ip=bmc_ip,
            status='OK',
            description='正常',
            log_detail={},
            date=date
        )

        # 根据 source 按需返回
        if source == 'cli':
            return cli_result
        return result

plugin_class = MyPlugin
```

**`analyze()` 接口说明：**

```python
def analyze(self, log_content: Dict[str, List[str]],
            task_name: str = "", bmc_ip: str = "", date: str = "",
            source: str = "system") -> Union[AnalysisResult, CliResult]:
    """
    分析日志内容，同时生成两套返回值，根据 source 按需返回。

    Args:
        log_content: {"日志名/相对路径": ["行1", "行2"]} 字典，值为行列表。
            - 单文件时: {"system.log": ["行1", "行2"]}
            - 目录时: {"system.log": [...], "sub/error.log": [...]}，键为相对路径
        task_name: 任务名称（cli模式使用，默认空）
        bmc_ip: BMC IP地址（cli模式使用，默认空）
        date: 日期（cli模式使用，默认空）
        source: 调用来源，'cli' 或 'system'（默认 'system'）

    Returns:
        source='system' 时返回 AnalysisResult
        source='cli' 时返回 CliResult
    """
```

> **重要**：插件必须在 `analyze()` 内部**同时生成两套返回值**（`AnalysisResult` 和 `CliResult`），
> 然后根据 `source` 参数决定返回哪一套。每个插件自行控制 `CliResult` 中 `description` 和 `log_detail`
> 的内容，不要依赖外层统一转换。

## API 文档

### PluginManager

```python
from plugins import get_plugin_manager
from src.utils.file_utils import read_log_files_to_content

manager = get_plugin_manager()
plugins = manager.get_all_plugins()
categories = manager.get_plugins_categories()

# 读取日志内容
log_content = read_log_files_to_content("/path/to/logfile_or_dir")
# log_content 格式: {"system.log": ["行1", "行2"], "sub/error.log": ["错误行1"]}

# system模式：Web/主程序使用，返回 {plugin_id: {'meta': ..., 'sections': ...}}
result = manager.run_analysis('system', ["CloudBMC_00001"], log_content)

# cli模式：CLI外部调用，返回 [task_name, bmc_ip, status, description, log_detail, date]
result = manager.run_analysis('cli', ["CloudBMC_00001"], log_content,
                              task_name="任务1", bmc_ip="192.168.1.1", date="2026-05-09")
```

#### `run_analysis()` 方法签名

```python
def run_analysis(self, source: str, plugin_ids: List[str],
                 log_content: Dict[str, List[str]],
                 task_name: str = "", bmc_ip: str = "", date: str = "",
                 log_callback: Optional[callable] = None) -> Any:
```

| 参数 | 类型 | 说明 |
|------|------|------|
| source | str | 调用来源：`'system'`（Web/主程序）或 `'cli'`（命令行） |
| plugin_ids | List[str] | 要运行的插件 ID 列表 |
| log_content | Dict[str, List[str]] | `{"日志名/相对路径": ["行1", "行2"]}` 字典，值为行列表 |
| task_name | str | 任务名称（cli模式使用，默认空） |
| bmc_ip | str | BMC IP地址（cli模式使用，默认空） |
| date | str | 日期（cli模式使用，默认空） |
| log_callback | callable | 日志回调函数（可选） |

**返回值：**
- `source='system'` 时：`{plugin_id: {'meta': ..., 'sections': ...}}`
- `source='cli'` 时：`[task_name, bmc_ip, status, description, log_detail, date]`
  - `status`: `'ERROR'`（有错误）或 `'OK'`
  - `description`: 错误/警告摘要文本（最长1000字符）
  - `log_detail`: 详细信息字典（序列化后最长3000字符）

### CliResult 数据类

插件在 `analyze()` 内部构建 `CliResult` 对象，`to_list()` 方法将其转为列表格式：

```python
from plugins.base import CliResult

cli_result = CliResult(
    task_name="巡检任务",      # 透传输入参数
    bmc_ip="192.168.1.1",     # 透传输入参数
    status='ERROR',            # 'OK' 或 'ERROR'
    description='错误数: 15; 警告数: 23',  # 自定义描述，限1000字符
    log_detail={'errors': 15, 'warnings': 23, 'items': [...]},  # 自定义详情，限3000字符
    date="2026-05-09"         # 透传输入参数
)

# 转为列表: ["巡检任务", "192.168.1.1", "ERROR", "错误数: 15; 警告数: 23", {...}, "2026-05-09"]
output = cli_result.to_list()
```

| 字段 | 类型 | 说明 |
|------|------|------|
| task_name | str | 透传输入的任务名称 |
| bmc_ip | str | 透传输入的BMC IP地址 |
| status | str | `'OK'` 或 `'ERROR'`，由插件根据分析结果决定 |
| description | str | 插件自定义的描述文本，最长1000字符 |
| log_detail | dict | 插件自定义的详情字典，序列化后最长3000字符 |
| date | str | 透传输入的日期 |

### AnalysisResult 格式

插件分析结果保存为 `plugin_result.json`，格式如下：

```json
{
  "CloudBMC_00001": {
    "meta": {
      "plugin_id": "CloudBMC_00001",
      "plugin_name": "Log Parser",
      "version": "2.0",
      "analysis_time": "2026-05-09 10:00:00",
      "log_files": ["system.log", "sub/error.log"],
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
| value | number/string | 统计值（数字类型才会被历史记录累加统计） |
| unit | string | 单位（可选） |
| severity | string | 严重程度：info/warning/error/success |
| icon | string | 图标名称（可选） |

### 统计规则

系统会自动统计各区块中 `severity == 'error'` 或 `'warning'` 的数量，用于历史记录和概况展示：

| 区块类型 | 统计方式 | 说明 |
|---------|---------|------|
| stats | value 值累加 | StatsItem.value 直接表示数量 |
| table | 行数累加 | 每行 severity=error/warning 计 1 次 |
| timeline | 事件数累加 | 每个事件 severity=error/warning 计 1 次 |
| cards | 卡片数累加 | 每个卡片 severity=error/warning 计 1 次 |

### 使用建议

**推荐模式：使用表格行 severity 统计错误**

```python
result.add_table("错误详情",
    rows=[
        {"line": 123, "message": "Error 1", "severity": "error"},
        {"line": 456, "message": "Error 2", "severity": "error"},
        {"line": 789, "message": "Warning 1", "severity": "warning"}
    ],
    severity="error"  # 区块级别（影响标题样式）
)
# 统计结果：errors=2, warnings=1
```

**避免重复统计**：如果 stat 和 table 都标记相同数据的 severity，会导致重复统计。正确做法是：
- 用 stat 展示汇总时，table 只展示部分数据（top N），行 severity 设为 info
- 或只用 table 统计，不用 stat 的 severity 统计

**注意**：历史记录统计只累加 `severity == 'error'` 或 `'warning'` 且 `value` 为数字类型的统计项。

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
| truncate | number | 截断长度（可选，默认50，超过则显示...） |

rows 数组中每行数据：

| 字段 | 类型 | 说明 |
|------|------|------|
| {key} | any | 对应 columns 中定义的 key 字段 |
| severity | string | 行严重程度（可选，影响行样式颜色） |

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
| timestamp | string | 时间戳（必需） |
| title | string | 事件标题（必需） |
| description | string | 事件描述（可选） |
| severity | string | 严重程度（必需） |
| icon | string | 图标名称（可选，默认 "circle"） |
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
| content | object | 卡片内容 |

**content 字段约定（HTML渲染只支持以下字段）：**

| 字段 | 类型 | 说明 |
|------|------|------|
| summary | string | 概要文本（主要显示） |
| description | string | 描述文本（灰色小字，可选） |
| metrics | dict | 键值对，渲染为标签形式 |
| details | array | 字符串数组，渲染为列表 |

> 注意：content 中其他字段会保存到 JSON 但不会被 HTML 渲染。

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
| labels | array | 标签数组（与 values 长度必须一致） |
| values | array | 值数组（与 labels 长度必须一致） |

> 注意：labels 和 values 数组长度必须一致，否则渲染会出错。

**search_box - 搜索框**

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 固定值 "search_box" |
| title | string | 区块标题 |
| icon | string | 图标名称 |
| placeholder | string | 搜索框提示文字（默认 "搜索..."） |
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
- JSON: `data/analysis_output/{timestamp}_log/plugin_result.json`
- HTML: `data/analysis_output/{timestamp}_log/plugin_result.html`

### Section 类型

#### stats - 统计概览

```python
result.add_stats("分析概览", [
    StatsItem(label="错误数", value=15, unit="个", severity="error", icon="x-circle"),
    StatsItem(label="警告数", value=23, unit="个", severity="warning", icon="alert-triangle")
])
```

#### table - 表格

区块级别 `severity` 影响标题样式，行级别 `severity` 影响行背景颜色：

```python
result.add_table("错误详情",
    columns=[
        {"key": "line", "label": "行号", "type": "number"},
        {"key": "message", "label": "消息", "type": "text", "truncate": 50}
    ],
    rows=[
        {"line": 123, "message": "Critical error", "severity": "error"},
        {"line": 456, "message": "Warning message", "severity": "warning"},
        {"line": 789, "message": "Info message"}  # 无 severity，使用默认样式
    ],
    severity="error",  # 区块级别
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
             content={
                 "summary": "发现内存持续增长",
                 "description": "需要进一步排查",
                 "metrics": {"影响": "高", "进程": "java"},
                 "details": ["增长速率: 1GB/h", "持续时间: 3小时"]
             }),
])
```

> 注意：content 只支持 summary/description/metrics/details 四个字段，其他字段不会被渲染。

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
html_path = render_html('data/analysis_output/xxx/plugin_result.json')
print(f'HTML文件: {html_path}')

# 或使用HtmlRenderer类
from plugins.renderer import HtmlRenderer

renderer = HtmlRenderer()
html_content = renderer.render(data_dict)
html_path = renderer.render_to_file('path/to/plugin_result.json')
```

### 输出文件

- JSON: `data/analysis_output/xxx/plugin_result.json`
- HTML: `data/analysis_output/xxx/plugin_result.html`

### HTML特性

- 独立静态HTML，无需JavaScript
- 内嵌Bootstrap CSS和图标
- 支持所有Section类型渲染
- 按插件分组展示

## 独立CLI工具

插件系统提供独立的命令行入口，可用于脚本集成和外部调用。

### 用法

```bash
# 列出可用插件
python plugins/cli_main.py plugin list

# 执行分析（从stdin读取JSON格式的日志内容）
echo '{"system.log": ["ERROR disk failure", "WARNING low memory"]}' | python plugins/cli_main.py analyze --plugin-id CloudBMC_00001

# 带额外参数的分析
echo '{"system.log": ["ERROR disk failure"]}' | python plugins/cli_main.py analyze \
    --plugin-id CloudBMC_00001 \
    --task-name "巡检任务" \
    --bmc-ip "192.168.1.100" \
    --date "2026-05-09"
```

### 输入格式

从 stdin 读取 JSON 格式的日志内容字典：

```json
{
    "system.log": ["行1", "行2", "行3"],
    "sub/error.log": ["错误行1", "错误行2"]
}
```

键为日志文件名或相对路径，值为行列表。

### 输出格式

分析结果以 JSON 数组输出到 stdout，格式为：

```json
["任务名称", "192.168.1.100", "ERROR", "错误数: 15; 警告数: 23", {"errors": 15, "warnings": 23, "items": [...]}, "2026-05-09"]
```

数组元素依次为：`[task_name, bmc_ip, status, description, log_detail, date]`

| 索引 | 字段 | 类型 | 说明 |
|------|------|------|------|
| 0 | task_name | string | 任务名称 |
| 1 | bmc_ip | string | BMC IP地址 |
| 2 | status | string | 状态：`'OK'` 或 `'ERROR'` |
| 3 | description | string | 错误/警告摘要（最长1000字符） |
| 4 | log_detail | object | `{'errors': int, 'warnings': int, 'items': [...]}` 或 `{}` |
| 5 | date | string | 日期 |

## 日志内容读取

`read_log_files_to_content()` 工具函数将文件/目录读取为日志内容字典，供 `run_analysis()` 使用：

```python
from src.utils.file_utils import read_log_files_to_content

# 单文件
log_content = read_log_files_to_content("/path/to/system.log")
# 返回: {"system.log": ["行1", "行2"]}

# 目录（递归读取所有有效日志文件）
log_content = read_log_files_to_content("/path/to/log_dir/")
# 返回: {"system.log": ["行1", ...], "sub/error.log": ["行1", ...]}
```

- 单文件时，键为文件名（`os.path.basename`）
- 目录时，键为相对路径（如 `sub/error.log`），使用 `/` 分隔
- 仅读取 `is_valid_log_file()` 判定的有效日志文件
- 编码为 UTF-8，忽略解码错误

## 内置插件

### CloudBMC_00001 (log_parser)

解析日志文件，提取错误和警告信息。

### CloudBMC_00002 (log_statistics)

分析日志统计信息，包括时间分布和日志级别分布。