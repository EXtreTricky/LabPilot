"""可解释规则辅助决策：不是调用大模型，不得误标为真实AI预测。"""
def recommend(rooms, purpose, participants):
    purpose = (purpose or '').strip().lower()
    try: participants=int(participants)
    except (TypeError,ValueError): participants=1
    if participants<1: return []
    items=[]
    for r in rooms:
        if r['capacity'] < participants or r['status']!='available': continue
        tags=(r.get('tags') or '').lower()
        score=50+min(25, max(0,r['capacity']-participants))*(-1) # 大容量空置略扣分
        score=50-max(0,r['capacity']-participants)*2
        reasons=[]
        if purpose and purpose in tags: score+=35;reasons.append('用途与实验室标签匹配')
        if participants<=r['capacity']: reasons.append('满足人数容量')
        items.append(dict(id=r['id'],name=r['name'],score=max(0,score),reason='；'.join(reasons)))
    return sorted(items,key=lambda x:(-x['score'],x['id']))[:3]

def risk_hint(description):
    txt=(description or '').lower()
    terms=['漏电','冒烟','异味','起火','危险化学品','泄漏','触电','烟雾']
    hits=[x for x in terms if x in txt]
    return dict(level='高' if hits else '待人工核验', reason=('命中风险关键词：'+','.join(hits)) if hits else '未命中演示规则；仍须管理员人工判断', human_review_required=True)
