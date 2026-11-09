"""教师端评分器。学生Python仅在无网络、无凭据的容器内执行。"""
import argparse,ast,json,os,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path

GROUPS=[('environment',4),('t',14),('s',10),('connect',14),('disconnect',10),('integration',8),('student_submission',4),('delivery',6),('report',30)]

def grade(workspace,report_dir,local=False,image='lab02-grader'):
    root=Path(workspace).resolve();out=Path(report_dir).resolve();out.mkdir(parents=True,exist_ok=True)
    if not local:out.chmod(0o777)
    parts={}
    for name,points in GROUPS:
        filename=f'grading/test_{name}.py';xml=out/f'{name}.xml'
        expected=sum(isinstance(n,ast.FunctionDef) and n.name.startswith('test_') for n in ast.parse((root/filename).read_text(encoding='utf-8')).body)
        if local:
            command=[sys.executable,'-m','pytest',filename,'-q','-p','no:cacheprovider',f'--junitxml={xml}']
        else:
            command=['docker','run','--rm','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges',
                '--pids-limit','128','--memory','512m','--cpus','1','--tmpfs','/tmp:rw,noexec,nosuid,size=128m',
                '--mount',f'type=bind,source={root},target=/work,readonly','--mount',f'type=bind,source={out},target=/out',
                image,'python','-m','pytest',filename,'-q','-p','no:cacheprovider',f'--junitxml=/out/{name}.xml']
        try:
            run=subprocess.run(command,cwd=root,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90)
        except subprocess.TimeoutExpired as e:
            parts[name]={'score':0,'max':points,'passed':0,'total':expected,'status':'timeout'}
            (out/f'{name}.log').write_text(str(e),encoding='utf-8');continue
        (out/f'{name}.log').write_text(run.stdout+'\n'+run.stderr,encoding='utf-8')
        if run.returncode in (125,126,127):raise RuntimeError(f'评分容器启动失败：{name}，请查看日志')
        if not xml.exists():
            parts[name]={'score':0,'max':points,'passed':0,'total':expected,'status':'student_execution_error','exit_code':run.returncode};continue
        try:cases=ET.parse(xml).findall('.//testcase')
        except ET.ParseError as e:raise RuntimeError(f'无法解析评分报告：{name}') from e
        # 不把代码导入失败、空报告或提前退出误判为测试全部通过。
        valid=run.returncode in (0,1) and len(cases)==expected
        passed=sum(not any(c.find(tag) is not None for tag in ('failure','error','skipped')) for c in cases) if valid else 0
        parts[name]={'score':round(points*passed/expected,2),'max':points,'passed':passed,'total':expected,
            'status':'completed' if valid else 'student_execution_error','exit_code':run.returncode}
    experiment_score=round(sum(v['score'] for k,v in parts.items() if k!='report'),2)
    report_score=parts['report']['score']
    report={'experiment_score':experiment_score,'report_score':report_score,'status':'completed','score':round(sum(v['score'] for v in parts.values()),2),'max_score':100,'parts':parts,
        'evaluation':'自动分仅评价公开可执行规则，报告与AI记录只评价结构及交付完整性'}
    (out/'grade_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    text=f'实验 {experiment_score}/70，报告 {report_score}/30，总分 '+str(report['score'])+'/100\n\n'+'\n'.join(f'{k}: {v["score"]}/{v["max"]}，{v["passed"]}/{v["total"]}，{v["status"]}' for k,v in parts.items())
    (out/'grade_result.txt').write_text(text,encoding='utf-8');print(text);return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--workspace',default='.');parser.add_argument('--output',default='.grade');parser.add_argument('--local',action='store_true',help='仅在本机可信代码上使用；云端固定使用容器')
    args=parser.parse_args();grade(args.workspace,args.output,args.local)
