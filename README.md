# Log Analyzer Plugins

日志分析器插件系统，提供可扩展的日志分析能力。

## 安装

### 作为 Git Submodule 使用

```bash
# 在主项目中添加 submodule
git submodule add <repo_url> plugins

# 初始化 submodule
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
- `id`: 插件唯一标识（给程序用）
- `name`: 插件显示名称（给用户看）
- `version`: 版本号
- `description`: 中文描述
- `plugin_type`: 插件类型，可选值：`CloudBMC`、`iBMC`、`LxBMC`

### plugin.py 实现

只需实现 `analyze()` 方法：

```python
from plugins.base import BasePlugin, AnalysisResult, ResultMeta, StatsItem

class MyPlugin(BasePlugin):
    def analyze(self, log_file: str) -> AnalysisResult:
        """分析日志文件"""
        import os
        from datetime import datetime

        # 读取日志
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        # 创建元数据
        meta = ResultMeta(
            plugin_id=self.id,
            plugin_name=self.name,
            version=self.get_version(),
            analysis_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            log_file=os.path.basename(log_file),
            plugin_type=self.get_plugin_type()
        )

        result = AnalysisResult(meta=meta)

        # 添加统计概览
        result.add_stats("分析概览", [
            StatsItem(label="总行数", value=len(lines), severity="info", icon="file-text"),
            StatsItem(label="错误数", value=5, severity="error", icon="x-circle"),
        ])

        # 添加表格
        result.add_table("错误详情",
            columns=[
                {"key": "line", "label": "行号", "type": "number"},
                {"key": "message", "label": "消息", "type": "text"}
            ],
            rows=[{"line": 123, "message": "Error occurred"}],
            severity="error"
        )

        return result

# 导出插件类
plugin_class = MyPlugin
```

### 导出机制

插件必须导出 `plugin_class` 变量供 PluginManager 加载：

```python
class MyPlugin(BasePlugin):
    def analyze(self, log_file: str) -> AnalysisResult:
        ...

# 必需：导出插件类
plugin_class = MyPlugin
```

PluginManager 会查找模块中继承 BasePlugin 的类来实例化插件。

## API 文档

### PluginManager

```python
from plugins import get_plugin_manager

# 获取插件管理器
manager = get_plugin_manager()

# 获取所有插件
plugins = manager.get_all_plugins()

# 获取按类型分类的插件
categories = manager.get_plugins_categories()

# 运行分析
result = manager.run_analysis(["log_parser"], "/path/to/logfile")
```

### AnalysisResult 格式

插件返回值采用 `sections` 数组结构：

```json
{
  "meta": {
    "plugin_id": "log_parser",
    "plugin_name": "Log Parser",
    "version": "1.0.0",
    "analysis_time": "2026-04-10 14:30:00",
    "log_file": "server.log",
    "plugin_type": "CloudBMC"
  },
  "sections": [
    { "type": "stats", ... },
    { "type": "table", ... },
    { "type": "chart", ... }
  ]
}
```

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
        {"key": "message", "label": "消息", "type": "text"}
    ],
    rows=[{"line": 123, "message": "Error occurred"}],
    severity="error",
    icon="x-circle"
)
```

#### chart - 图表

`chart_type` 支持值：`bar`（柱状图）、`line`（折线图）、`pie`（饼图）

```python
from plugins.base import ChartData

result.add_chart("错误分布", chart_type="bar",
    data=ChartData(labels=["ERROR", "WARNING"], values=[15, 23]),
    options={"x_label": "级别", "y_label": "数量"}
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

展示多个独立的信息卡片。

```python
from plugins.base import CardItem

result.add_cards("问题卡片", [
    CardItem(title="内存泄漏", severity="error", icon="alert-triangle",
             content={"description": "发现内存持续增长", "impact": "高"}),
])
```

#### search_box - 搜索框

提供可搜索的数据列表。

```python
result.add_search_box("日志搜索",
    data=[{"line": 123, "content": "error msg"}],
    search_fields=["line", "content"],
    placeholder="输入关键词搜索"
)
```

#### raw - 原始数据

用于传递任意 JSON 数据，适合自定义扩展。

```python
result.add_raw("自定义数据", {"key": "value"})
```

### Severity 严重程度

| 值 | 说明 |
|----|------|
| info | 普通信息 |
| warning | 警告 |
| error | 错误 |
| critical | 严重 |
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

## 内置插件

### log_parser

解析日志文件，提取错误和警告信息。

### log_statistics

分析日志统计信息，包括时间分布和日志级别分布。