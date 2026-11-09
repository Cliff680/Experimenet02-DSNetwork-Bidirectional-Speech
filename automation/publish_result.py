"""独立的可信反馈进程；不导入学生代码，使用GitHub当前PR信息关联结果。"""
import csv,io,json,math,os,sys,urllib.request,html
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from identity import identify

REPO=os.environ['GITHUB_REPOSITORY'];TOKEN=os.environ['GH_TOKEN'];MARKER='<!-- lab02-grade:'
def api(route,method='GET',data=None):
    req=urllib.request.Request('https://api.github.com'+route,method=method,data=None if data is None else json.dumps(data).encode(),headers={'Authorization':'Bearer '+TOKEN,'Accept':'application/vnd.github+json','Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=45) as f:return json.loads(f.read() or '{}')

def pages(route):
    result=[];page=1
    while True:
        batch=api(route+('&' if '?' in route else '?')+f'per_page=100&page={page}');result.extend(batch)
        if len(batch)<100:return result
        page+=1

def own_grade(comments):
    for comment in reversed(comments):
        if comment['user']['login']!='github-actions[bot]' or MARKER not in comment['body']:continue
        encoded=comment['body'].split(MARKER,1)[1].split(' -->',1)[0]
        return json.loads(encoded)
    return None

def main():
    number=int(os.environ['PR_NUMBER']);pr=api(f'/repos/{REPO}/pulls/{number}')
    students=json.loads(os.environ['CLASS_ROSTER_JSON'])
    who=identify(pr['title'],students);run_url=f'https://github.com/{REPO}/actions/runs/{os.environ["GITHUB_RUN_ID"]}'
    report_path=Path('reports/grade_report.json');meta_path=Path('reports/submission.json')
    score=None;status='评分运行失败';details='查看运行链接中的失败步骤；本次未产生有效成绩。'
    if os.environ['GRADE_JOB_RESULT']=='success':
        report=json.loads(report_path.read_text(encoding='utf-8'));meta=json.loads(meta_path.read_text(encoding='utf-8'))
        if meta['pr_number']!=number:raise ValueError('报告PR编号不匹配')
        # 补交可能在前一次运行完成前发生，旧提交不能覆盖新提交的成绩。
        if meta['head_sha']!=pr['head']['sha']:
            print('Skipped stale revision; current revision has a separate grading run.');return
        score=report['score']
        if report['status']!='completed' or not isinstance(score,(int,float)) or not math.isfinite(score) or not 0<=score<=100:raise ValueError('评分报告值无效')
        status='已评分';details='\n'.join(f'- {k}：{v["score"]}/{v["max"]}，通过{v["passed"]}/{v["total"]}，{v["status"]}' for k,v in report['parts'].items())
    elif os.environ['GRADE_JOB_RESULT']=='cancelled':
        print('Cancelled superseded run; no current score overwritten.');return
    data={'experiment_score':report.get('experiment_score') if score is not None else None,'report_score':report.get('report_score') if score is not None else None,'sha':pr['head']['sha'],'score':score,'status':status,'identity':who,'run_url':run_url}
    identity_text=(who.get('name','')+' '+who.get('student_id','')) if who['status']!='invalid' else who['reason']
    text=f'## 实验二自动评分\n\n身份关联：{identity_text}\n\n'
    text+=(f'**实验：{report["experiment_score"]}/70，报告：{report["report_score"]}/30，总分：{score}/100**' if score is not None else '**评分未完成，请查看失败日志；不是0分。**')
    text+=f'\n\n提交：`{pr["head"]["sha"]}`\n\n{details}\n\n[运行日志与评分附件]({run_url})\n\n'
    if who['status']=='invalid':text+='**成绩尚未关联班级名单。修改PR标题后会自动重评并关联，无需教师操作。**\n\n'
    text+='报告与AI记录分仅评价结构及交付完整性，不代表内容质量评价。\n\n'+MARKER+json.dumps(data,ensure_ascii=False)+' -->'
    comments=pages(f'/repos/{REPO}/issues/{number}/comments')
    existing=next((c for c in comments if c['user']['login']=='github-actions[bot]' and MARKER in c['body']),None)
    if existing:api(f'/repos/{REPO}/issues/comments/{existing["id"]}','PATCH',{'body':text})
    else:api(f'/repos/{REPO}/issues/{number}/comments','POST',{'body':text})
    refresh_board(students,publish=False)

def refresh_board(students,publish=True):
    prs=pages(f'/repos/{REPO}/pulls?state=all&sort=updated&direction=desc')
    records={};extras=[]
    for pr in prs:
        who=identify(pr['title'],students)
        commits=pages(f'/repos/{REPO}/pulls/{pr["number"]}/commits')
        latest=commits[-1]['commit']['committer']['date'] if commits else pr['created_at']
        result=own_grade(pages(f'/repos/{REPO}/issues/{pr["number"]}/comments'))
        row={'GitHub用户名':pr['user']['login'],'最新PR':pr['html_url'],'最新PR状态':pr['state'],
             '提交次数':len(commits),'最近提交时间':latest,'评分状态':'待评分','实验分':'','报告分':'','最新评分':'','备注':''}
        if result and result['sha']==pr['head']['sha']:
            row['评分状态']=result['status']
            if result.get('experiment_score') is not None and result.get('report_score') is not None:
                row.update({'实验分':result['experiment_score'],'报告分':result['report_score'],'最新评分':result['score']})
            elif result['score'] is not None:row['评分状态']='待按7:3重评'
        if who['status']=='matched':records.setdefault(who['student_id'],[]).append(row)
        else:extras.append({**row,'身份状态':who['status']})
    fields=['序号','学号','姓名','GitHub用户名','是否提交代码','PR数量','提交次数','最新PR','最新PR状态','实验分','报告分','最新评分','评分状态','最近提交时间','备注'];rows=[]
    for student in students:
        matches=records.get(student['学号'],[])
        # 更新时间含机器人评论，不能用它判断学生最后一次提交。
        record=max(matches,key=lambda r:r['最近提交时间']) if matches else {}
        rows.append({**dict.fromkeys(fields,''),'序号':student['序号'],'学号':student['学号'],'姓名':student['姓名'],
            '是否提交代码':'是' if matches else '否','PR数量':len(matches),'提交次数':sum(r['提交次数'] for r in matches),
            '评分状态':'待提交',**record})
        rows[-1]['提交次数']=sum(r['提交次数'] for r in matches)
    folder=Path('tracking');folder.mkdir(exist_ok=True)
    with (folder/'student_grades.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    (folder/'unmatched_and_demo.json').write_text(json.dumps(extras,ensure_ascii=False,indent=2),encoding='utf-8')
    submitted=sum(r['是否提交代码']=='是' for r in rows);graded=sum(r['最新评分']!='' for r in rows)
    title='现代交换实验02作业实时跟踪表'
    summary=f'学生总数：{len(rows)}；已提交代码：{submitted}；已获得自动评分：{graded}。实验70分，报告30分。'
    md=f'# {title}\n\n{summary}\n\n空白表示未提交或未完成评分；补交未评分时不沿用旧分。提交次数为关联PR中的提交记录数量之和。\n\n'
    md+='|'+'|'.join(fields)+'|\n|'+'|'.join(['---']*len(fields))+'|\n'
    def value(row,key,markdown=False):
        v=str(row[key])
        if key=='最新PR' and v and markdown:return f'[#{v.rsplit("/",1)[-1]}]({v})'
        return v.replace('|','\\|').replace('\n',' ')
    md+='\n'.join('|'+'|'.join(value(r,k,True) for k in fields)+'|' for r in rows)
    md+=f'\n\n未匹配或模拟提交：{len(extras)}，单独记录，不计入班级成绩。报告分只评价结构与完整性，不代表论述质量评价。\n'
    (folder/'student_grades.md').write_text(md,encoding='utf-8')
    heads=''.join('<th>'+html.escape(k)+'</th>' for k in fields)
    body=''.join('<tr>'+''.join('<td>'+ (f'<a href="{html.escape(str(r[k]),quote=True)}">PR #{str(r[k]).rsplit("/",1)[-1]}</a>' if k=='最新PR' and r[k] else html.escape(str(r[k])))+'</td>' for k in fields)+'</tr>' for r in rows)
    (folder/'student_grades.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>'+title+'</title><style>body{font-family:SimSun,serif;color:#183A60;padding:14px}table{border-collapse:collapse;white-space:nowrap}th,td{border:1px solid #cdd8e5;padding:9px 12px}tr:nth-child(even){background:#f4f7fa}th{background:#eaf0f6}a{color:#06c}</style><h1>'+title+'</h1><p>'+summary+'</p><p>实验满分70，报告满分30，总分100。报告只评价结构与完整性。</p><table><thead><tr>'+heads+'</tr></thead><tbody>'+body+'</tbody></table></html>',encoding='utf-8')
    Path(os.environ['GITHUB_STEP_SUMMARY']).write_text(md,encoding='utf-8')
    if not publish:return
    issue=int(os.environ['TRACKING_ISSUE_NUMBER']);marker='<!-- lab02-class-board -->'
    comments=pages(f'/repos/{REPO}/issues/{issue}/comments')
    old=next((c for c in comments if c['user']['login']=='github-actions[bot]' and marker in c['body']),None)
    if old:api(f'/repos/{REPO}/issues/comments/{old["id"]}','PATCH',{'body':marker+'\n'+md})
    else:api(f'/repos/{REPO}/issues/{issue}/comments','POST',{'body':marker+'\n'+md})

if __name__=='__main__':main()
