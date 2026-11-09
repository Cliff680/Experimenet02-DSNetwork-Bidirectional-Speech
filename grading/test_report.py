"""报告30分只检查可执行的结构与完整性，不自动判断论述质量。"""
import re
from pathlib import Path

def report_section(title,minimum):
    text=Path('REPORT.md').read_text(encoding='utf-8')
    assert len(text)>=300 and '待填写' not in text and 'TODO' not in text
    match=re.search(r'^#{1,6} '+re.escape(title)+r'\s*\n(.*?)(?=^#{1,6} |\Z)',text,re.M|re.S)
    assert match and len(re.sub(r'\s','',match.group(1)))>=minimum

def test_principle_and_calculation():
    report_section('原理与手算',60)

def test_result_analysis():
    report_section('结果分析',60)

def test_counterexample_and_verification():
    report_section('反例与验证',60)

def test_limitations():
    report_section('局限',40)

def test_ai_record():
    text=Path('AI_LOG.md').read_text(encoding='utf-8')
    assert len(text)>=120 and '待填写' not in text and 'TODO' not in text
    for title in ['需求','建议与采纳','验证证据']:
        match=re.search(r'^#{1,6} '+title+r'\s*\n(.*?)(?=^#{1,6} |\Z)',text,re.M|re.S)
        assert match and len(re.sub(r'\s','',match.group(1)))>=20
