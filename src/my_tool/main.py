"""零第三方依赖的实验室预约与风险提示 MVP。启动：python -m src.my_tool.main"""
import json, sqlite3, os
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from .core.rules import recommend, risk_hint

DB=Path(os.environ.get('LAB_DB',str(Path(__file__).resolve().parents[3]/'data'/'lab.db')))
WEB=Path(__file__).with_name('web.html')

def connect():
    DB.parent.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(DB)
    con.row_factory=sqlite3.Row
    return con

def setup():
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS rooms(id INTEGER PRIMARY KEY,name TEXT NOT NULL,capacity INTEGER NOT NULL,tags TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'available');
        CREATE TABLE IF NOT EXISTS bookings(id INTEGER PRIMARY KEY,room_id INTEGER NOT NULL,applicant TEXT NOT NULL,day TEXT NOT NULL,period TEXT NOT NULL,purpose TEXT NOT NULL,participants INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'pending',created_at TEXT NOT NULL,FOREIGN KEY(room_id) REFERENCES rooms(id));
        CREATE TABLE IF NOT EXISTS inspections(id INTEGER PRIMARY KEY,room_id INTEGER NOT NULL,description TEXT NOT NULL,risk_level TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'open',created_at TEXT NOT NULL);
        """)
        if not con.execute('SELECT COUNT(*) FROM rooms').fetchone()[0]:
            con.executemany('INSERT INTO rooms(name,capacity,tags,status) VALUES(?,?,?,?)',[
                ('计算机实验室 A101',36,'编程,Python,网络,开发','available'),
                ('物联网创新实验室 B203',24,'物联网,传感器,开发','available'),
                ('电子工程实验室 C302',18,'电路,焊接,实验','available'),
                ('高性能计算实验室 D401',12,'AI,人工智能,训练,开发','available')])

def rows(con,sql,args=()): return [dict(x) for x in con.execute(sql,args).fetchall()]

def process(method,path,payload=None,query=None):
    payload=payload or {}; query=query or {}
    with connect() as con:
        if method=='GET' and path=='/api/rooms': return 200,rows(con,'SELECT * FROM rooms ORDER BY id')
        if method=='GET' and path=='/api/bookings': return 200,rows(con,'SELECT b.*,r.name AS room_name FROM bookings b JOIN rooms r ON r.id=b.room_id ORDER BY b.id DESC')
        if method=='GET' and path=='/api/inspections': return 200,rows(con,'SELECT i.*,r.name AS room_name FROM inspections i JOIN rooms r ON r.id=i.room_id ORDER BY i.id DESC')
        if method=='GET' and path=='/api/summary':
            return 200,dict(rooms=con.execute('SELECT COUNT(*) FROM rooms').fetchone()[0],pending=con.execute("SELECT COUNT(*) FROM bookings WHERE status='pending'").fetchone()[0],approved=con.execute("SELECT COUNT(*) FROM bookings WHERE status='approved'").fetchone()[0],open_issues=con.execute("SELECT COUNT(*) FROM inspections WHERE status='open'").fetchone()[0])
        if method=='GET' and path=='/api/recommend':
            rooms_=rows(con,'SELECT * FROM rooms');return 200,recommend(rooms_,query.get('purpose',[''])[0],query.get('participants',['1'])[0])
        if method=='POST' and path=='/api/bookings':
            try:
                room_id=int(payload['room_id']); n=int(payload['participants']);person=str(payload['applicant']).strip(); purpose=str(payload['purpose']).strip();day=str(payload['day']);period=str(payload['period'])
                assert 1<=n<=200 and 1<=len(person)<=50 and 1<=len(purpose)<=200
                assert period in ('上午','下午','晚上')
                datetime.strptime(day,'%Y-%m-%d')
            except (KeyError,ValueError,AssertionError,TypeError): return 400,{'error':'提交参数无效，请检查姓名、日期、人数、用途及时间段'}
            room=con.execute('SELECT * FROM rooms WHERE id=?',(room_id,)).fetchone()
            if not room or room['status']!='available' or n>room['capacity']: return 400,{'error':'实验室不存在、停用或容量不足'}
            existing=con.execute("SELECT COUNT(*) FROM bookings WHERE room_id=? AND day=? AND period=? AND status IN ('pending','approved')",(room_id,day,period)).fetchone()[0]
            if existing:return 409,{'error':'该时段已有预约申请，请换时间段'}
            cur=con.execute('INSERT INTO bookings(room_id,applicant,day,period,purpose,participants,created_at) VALUES(?,?,?,?,?,?,?)',(room_id,person,day,period,purpose,n,datetime.now().isoformat(timespec='seconds')))
            return 201,{'id':cur.lastrowid,'status':'pending'}
        if method=='POST' and path.startswith('/api/bookings/') and path.endswith('/approve'):
            try: bid=int(path.split('/')[3])
            except (IndexError,ValueError):return 400,{'error':'无效的申请编号'}
            booking=con.execute('SELECT * FROM bookings WHERE id=?',(bid,)).fetchone()
            if not booking:return 404,{'error':'预约不存在'}
            if booking['status']!='pending':return 409,{'error':'只可审核待审批申请'}
            con.execute("UPDATE bookings SET status='approved' WHERE id=?",(bid,))
            return 200,{'id':bid,'status':'approved','notice':'演示模式：未做管理员鉴权，不可直接投入生产'}
        if method=='POST' and path=='/api/inspections':
            try: rid=int(payload['room_id']);desc=str(payload['description']).strip();assert 3<=len(desc)<=500
            except (KeyError,ValueError,TypeError,AssertionError): return 400,{'error':'请填写至少3字的隐患描述'}
            if not con.execute('SELECT id FROM rooms WHERE id=?',(rid,)).fetchone():return 404,{'error':'实验室不存在'}
            hint=risk_hint(desc)
            cur=con.execute('INSERT INTO inspections(room_id,description,risk_level,created_at) VALUES(?,?,?,?)',(rid,desc,hint['level'],datetime.now().isoformat(timespec='seconds')))
            return 201,{'id':cur.lastrowid,**hint,'notice':'仅辅助提示，紧急事故应立即按校方应急预案处理'}
        if method=='POST' and path.startswith('/api/inspections/') and path.endswith('/close'):
            try: iid=int(path.split('/')[3])
            except (IndexError,ValueError):return 400,{'error':'无效编号'}
            if not con.execute('SELECT id FROM inspections WHERE id=?',(iid,)).fetchone():return 404,{'error':'记录不存在'}
            con.execute("UPDATE inspections SET status='closed' WHERE id=?",(iid,));return 200,{'id':iid,'status':'closed'}
        return 404,{'error':'接口不存在'}

class Handler(BaseHTTPRequestHandler):
    def send_data(self,status,body,ctype='application/json; charset=utf-8'):
        data=body.encode('utf-8') if isinstance(body,str) else json.dumps(body,ensure_ascii=False).encode('utf-8')
        self.send_response(status);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(data)));self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(data)
    def do_GET(self):
        parsed=urlparse(self.path)
        if parsed.path in ('/','/index.html'):
            return self.send_data(200,WEB.read_text('utf-8'),'text/html; charset=utf-8')
        status,data=process('GET',parsed.path,query=parse_qs(parsed.query));return self.send_data(status,data)
    def do_POST(self):
        if not self.path.startswith('/api/'):return self.send_data(404,{'error':'not found'})
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n>10000: return self.send_data(413,{'error':'请求过大'})
            payload=json.loads(self.rfile.read(n)) if n else {}
        except (ValueError,json.JSONDecodeError):return self.send_data(400,{'error':'JSON格式错误'})
        status,data=process('POST',urlparse(self.path).path,payload);return self.send_data(status,data)

if __name__=='__main__':
    setup();host=os.environ.get('LAB_HOST','127.0.0.1');port=int(os.environ.get('LAB_PORT','8000'))
    print(f'实验室数智化管理MVP：http://{host}:{port}');ThreadingHTTPServer((host,port),Handler).serve_forever()
