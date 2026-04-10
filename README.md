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
├── __init__.py      # 可选
├── plugin.py        # 必需：插件实现
└── plugin.json      # 可选：插件元数据
```

### BasePlugin 接口

所有插件必须继承 `BasePlugin` 类并实现以下属性和方法：

```python
from plugins.base import BasePlugin, PluginCategory, AnalysisResult

class MyPlugin(BasePlugin):
    @property
    def id(self) -> str:
        """插件唯一标识"""
        return "my_plugin"

    @property
    def name(self) -> str:
        """插件名称"""
        return "My Plugin"

    @property
    def version(self) -> str:
        """版本号"""
        return "1.0.0"

    @property
    def description(self) -> str:
        """描述"""
        return "插件描述"

    @property
    def category(self) -> PluginCategory:
        """分类: PARSER, ANALYZER, DETECTOR, REPORTER, OTHER"""
        return PluginCategory.ANALYZER

    def analyze(self, log_file: str) -> AnalysisResult:
        """分析日志文件，返回分析结果"""
        # 实现分析逻辑
        return AnalysisResult(
            plugin_id=self.id,
            plugin_name=self.name,
            analysis_time="2024-01-01 00:00:00",
            log_file="example.log",
            error_count=0,
            warning_count=0,
            errors=[],
            warnings=[],
            statistics={}
        )
```

### 可选属性

```python
@property
def author(self) -> str:
    return "作者名"

@property
def tags(self) -> List[str]:
    return ["tag1", "tag2"]

@property
def capabilities(self) -> List[str]:
    return ["能力1", "能力2"]

@property
def target_keywords(self) -> List[str]:
    return ["关键词1", "关键词2"]
```

### plugin.json 格式

```json
{
    "id": "my_plugin",
    "name": "My Plugin",
    "version": "1.0.0",
    "description": "插件描述",
    "category": "analyzer",
    "author": "作者",
    "tags": ["tag1", "tag2"],
    "capabilities": ["能力1"],
    "target_keywords": ["关键词1"],
    "enabled": true
}
```

### 插件分类

| 分类 | 说明 |
|------|------|
| PARSER | 日志解析插件 |
| ANALYZER | 日志分析插件 |
| DETECTOR | 问题检测插件 |
| REPORTER | 报告生成插件 |
| OTHER | 其他插件 |

## API 文档

### PluginManager

```python
from plugins import get_plugin_manager

# 获取插件管理器
manager = get_plugin_manager()

# 获取所有插件
plugins = manager.get_all_plugins()

# 按分类获取插件
from plugins.base import PluginCategory
parsers = manager.get_plugins_by_category(PluginCategory.PARSER)

# 运行分析
result = manager.run_analysis(["log_parser"], "/path/to/logfile")

# 获取插件信息
info = manager.get_plugins_info()
```

### AnalysisResult 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| plugin_id | str | 插件ID |
| plugin_name | str | 插件名称 |
| analysis_time | str | 分析时间 |
| log_file | str | 日志文件名 |
| error_count | int | 错误数量 |
| warning_count | int | 警告数量 |
| errors | List[Dict] | 错误列表 |
| warnings | List[Dict] | 警告列表 |
| statistics | Dict | 统计信息 |

## 内置插件

### log_parser

解析日志文件，提取错误、警告和统计信息。

**能力**: error_detection, warning_extraction, log_parsing, component_analysis

### log_statistics

分析日志统计信息，包括时间分布、组件活动和模式检测。

**能力**: statistics_analysis, time_distribution, pattern_detection, component_activity