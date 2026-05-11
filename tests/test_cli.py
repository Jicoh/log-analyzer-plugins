"""
CLI功能测试
"""

import json
import subprocess
import sys
import os
import pytest

# plugins目录
PLUGINS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLI_SCRIPT = os.path.join(PLUGINS_DIR, 'cli_main.py')


def run_cli(*args, stdin_data=None):
    """运行CLI命令"""
    cmd = [sys.executable, CLI_SCRIPT] + list(args)
    result = subprocess.run(
        cmd,
        input=stdin_data,
        capture_output=True,
        text=True,
        cwd=os.path.dirname(PLUGINS_DIR)
    )
    return result


class TestPluginList:
    """plugin list 命令测试"""

    def test_plugin_list_output_format(self):
        result = run_cli('plugin', 'list')
        assert result.returncode == 0
        lines = result.stdout.strip().split('\n')
        assert len(lines) > 0
        # 验证输出格式: [类型] 名称(ID): 描述 (v版本)
        import re
        pattern = re.compile(r'^\[(CloudBMC|iBMC|LxBMC)\] .+\(.+\): .+ \(v.+\)$')
        for line in lines:
            assert pattern.match(line), f"输出格式不匹配: {line}"

    def test_plugin_list_contains_known_plugins(self):
        result = run_cli('plugin', 'list')
        assert 'CloudBMC_00001' in result.stdout
        assert 'CloudBMC_00002' in result.stdout


class TestAnalyzeStdin:
    """analyze 命令测试"""

    def test_analyze_error_log(self):
        log_content = json.dumps({"system.log": ["ERROR disk read failure"]})
        result = run_cli('analyze', '--plugin-id', 'CloudBMC_00001', stdin_data=log_content)
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert isinstance(output, list)
        assert len(output) == 6
        # [task_name, bmc_ip, status, description, log_detail, date]
        assert output[2] == 'ERROR'

    def test_analyze_clean_log(self):
        log_content = json.dumps({"system.log": ["INFO system started", "INFO running"]})
        result = run_cli('analyze', '--plugin-id', 'CloudBMC_00001', stdin_data=log_content)
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output[2] == 'OK'

    def test_analyze_with_optional_params(self):
        log_content = json.dumps({"system.log": ["INFO ok"]})
        result = run_cli(
            'analyze', '--plugin-id', 'CloudBMC_00001',
            '--task-name', 'my_task',
            '--bmc-ip', '192.168.1.1',
            '--date', '2024-01-01',
            stdin_data=log_content
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output[0] == 'my_task'
        assert output[1] == '192.168.1.1'
        assert output[5] == '2024-01-01'

    def test_analyze_invalid_json(self):
        result = run_cli('analyze', '--plugin-id', 'CloudBMC_00001', stdin_data='not json')
        assert result.returncode == 1
        assert '错误' in result.stderr

    def test_analyze_non_dict_json(self):
        result = run_cli('analyze', '--plugin-id', 'CloudBMC_00001', stdin_data='[1,2,3]')
        assert result.returncode == 1
        assert '字典格式' in result.stderr

    def test_analyze_description_field(self):
        log_content = json.dumps({"system.log": ["ERROR disk failure", "WARNING low memory"]})
        result = run_cli('analyze', '--plugin-id', 'CloudBMC_00001', stdin_data=log_content)
        assert result.returncode == 0
        output = json.loads(result.stdout)
        description = output[3]
        assert isinstance(description, str)
        assert len(description) <= 1000

    def test_analyze_log_detail_field(self):
        log_content = json.dumps({"system.log": ["ERROR failure", "WARNING issue"]})
        result = run_cli('analyze', '--plugin-id', 'CloudBMC_00001', stdin_data=log_content)
        assert result.returncode == 0
        output = json.loads(result.stdout)
        log_detail = output[4]
        assert isinstance(log_detail, str)
        assert len(log_detail) <= 3000
