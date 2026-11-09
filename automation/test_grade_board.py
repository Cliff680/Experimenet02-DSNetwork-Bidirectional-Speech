"""用虚构身份验证公开成绩表及新旧评分迁移，不访问网络。"""
import importlib.util,json,os,sys
from pathlib import Path

def test_board_full_identity_latest_commit_and_demo(tmp_path,monkeypatch):
    monkeypatch.setenv('GITHUB_REPOSITORY','test/course');monkeypatch.setenv('GH_TOKEN','test')
    monkeypatch.setenv('GITHUB_STEP_SUMMARY',str(tmp_path/'summary.md'))
    monkeypatch.chdir(tmp_path)
    path=Path(__file__).with_name('publish_result.py')
    sys.path.insert(0,str(path.parent))
    spec=importlib.util.spec_from_file_location('board_under_test',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    def pr(n,title,sha):return {'number':n,'title':title,'user':{'login':'student'},'html_url':f'https://github.com/test/course/pull/{n}','state':'open','head':{'sha':sha},'created_at':'2026-01-01'}
    prs=[pr(1,'现代交换实验02-测试甲-10001','old'),pr(2,'现代交换实验02-测试甲-10001','new'),pr(3,'[流程测试] demo','demo')]
    def pages(route):
        if '/pulls?' in route:return prs
        n=int(route.split('/')[5])
        if route.endswith('/commits'):return [{'commit':{'committer':{'date':f'2026-01-0{n}'}}}]
        data={'sha':'new' if n==2 else 'old','score':91,'experiment_score':65,'report_score':26,'status':'已评分'}
        return [{'user':{'login':'github-actions[bot]'},'body':m.MARKER+json.dumps(data)+' -->'}]
    monkeypatch.setattr(m,'pages',pages)
    m.refresh_board([{'序号':'1','学号':'10001','姓名':'测试甲'},{'序号':'2','学号':'10002','姓名':'测试乙'}],publish=False)
    import csv
    rows=list(csv.DictReader(Path('tracking/student_grades.csv').open(encoding='utf-8-sig')))
    assert len(rows)==2 and rows[0]['姓名']=='测试甲' and rows[0]['学号']=='10001'
    assert rows[0]['最新PR'].endswith('/2') and rows[0]['PR数量']=='2' and rows[0]['提交次数']=='2'
    assert rows[0]['实验分']=='65' and rows[0]['报告分']=='26' and rows[0]['最新评分']=='91'
    assert rows[1]['评分状态']=='待提交' and rows[1]['最新评分']==''
    assert len(json.loads(Path('tracking/unmatched_and_demo.json').read_text(encoding='utf-8')))==1
    assert '<table>' in Path('tracking/student_grades.html').read_text(encoding='utf-8')
    assert '测试甲' in Path('tracking/student_grades.md').read_text(encoding='utf-8')
