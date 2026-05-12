# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run tests
pytest tests/                          # Run all tests
pytest tests/test_manager.py -v        # Run single test file with verbose output
pytest tests/test_plugins.py -v        # Run plugin interface tests
pytest tests/test_cli.py -v            # Run CLI integration tests

# CLI usage (independent of main project)
python plugins/cli_main.py plugin list
echo '{"system.log": ["ERROR disk failure"]}' | python plugins/cli_main.py analyze --plugin-id example_00001
echo '{"system.log": ["内容"]}' | python plugins/cli_main.py analyze --plugin-id CloudBMC_00001 --task-name "任务" --bmc-ip "192.168.1.1" --date "2026-05-09"
```

## Architecture

This is a git submodule (`log-analyzer-plugins`) for the main BMC log analyzer project. It provides an extensible plugin system for log analysis.

### Core Components

| Component | File | Purpose |
|-----------|------|---------|
| BasePlugin | `base.py` | Abstract base class all plugins must implement |
| PluginManager | `manager.py` | Discovers, loads, and executes plugins |
| CliResult | `base.py` | CLI-mode return format (list of 6 elements) |
| AnalysisResult | `base.py` | Web/system-mode return format (meta + sections) |
| HtmlRenderer | `renderer/html_renderer.py` | Converts JSON results to static HTML |

### Plugin Directory Structure

```
builtin/
├── CloudBMC/          # CloudBMC plugins (only loaded in main project)
├── iBMC/              # iBMC plugins (only loaded in main project)
├── LxBMC/             # LxBMC plugins (only loaded in main project)
└── example/           # Demo plugins (only loaded in development mode)
    └── demo_plugin/
        ├── plugin.py    # Required: implements BasePlugin
        └── plugin.json  # Required: metadata
```

### Dual Return Format

Every plugin must implement `analyze()` to return different formats based on `source` parameter:

- `source='system'`: Returns `AnalysisResult` for Web UI (meta + sections)
- `source='cli'`: Returns `CliResult` for CLI/script integration (6-element list)

Plugins must **build both formats internally** and return based on `source`. See `builtin/example/demo_plugin/plugin.py` for a complete reference.

### Plugin ID Format

All plugin IDs must follow: `{plugin_type}_{5-digit-number}` (e.g., `CloudBMC_00001`, `example_00001`)

### Development Mode Detection

- `sys.frozen` determines if running from packaged exe or source
- Example plugins (`builtin/example/`) only load in development mode (source code)
- Production mode (packaged exe) excludes example plugins

## Plugin Development

### Creating a New Plugin

1. Create directory: `builtin/{type}/my_plugin/` or `custom_plugins/my_plugin/`
2. Create `plugin.json` with required fields (id, name, version, description, plugin_type)
3. Create `plugin.py` implementing `BasePlugin.analyze()` returning both formats

### Key Interfaces

```python
from plugins.base import BasePlugin, AnalysisResult, ResultMeta, StatsItem, CliResult

class MyPlugin(BasePlugin):
    def analyze(self, log_content: Dict[str, List[str]],
                task_name: str = "", bmc_ip: str = "", date: str = "",
                source: str = "system") -> Union[AnalysisResult, CliResult]:
        # log_content format: {"filename.log": ["line1", "line2"]}
        # Build both AnalysisResult and CliResult
        # Return based on source parameter
        pass

plugin_class = MyPlugin  # Required export
```

### Section Types

`AnalysisResult` supports these section types via helper methods:
- `add_stats()` - Statistics overview with items
- `add_table()` - Data table with columns and rows
- `add_timeline()` - Chronological events
- `add_cards()` - Card-based grouped display
- `add_chart()` - Bar/pie/line charts
- `add_search_box()` - Searchable data list
- `add_raw()` - Custom JSON data

### CliResult Format

```python
CliResult(
    task_name=task_name,  # Pass through from input
    bmc_ip=bmc_ip,        # Pass through from input
    status='ERROR' | 'OK',  # Determined by plugin analysis
    description='...',    # Max 1000 chars
    log_detail='...',     # JSON string, max 3000 chars
    date=date             # Pass through from input
).to_list()  # Returns [task_name, bmc_ip, status, description, log_detail, date]
```

## Testing

Tests use pytest with fixtures. Key test files:
- `test_manager.py` - PluginManager API tests
- `test_plugins.py` - Plugin interface and return format tests
- `test_cli.py` - CLI subprocess integration tests

When adding new plugins, verify:
1. Plugin ID format matches `{type}_\d{5}`
2. Both `source='system'` and `source='cli'` return correct types
3. `CliResult.log_detail` length <= 3000 chars
4. `CliResult.description` length <= 1000 chars
