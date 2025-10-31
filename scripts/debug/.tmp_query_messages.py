import sqlite3, json, os, sys
p='app/data.db'
if not os.path.exists(p):
    print('app/data.db not found')
    sys.exit(0)
con=sqlite3.connect(p)
cur=con.cursor()
for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'"):
    print(row[0])
try:
    cur.execute("PRAGMA table_info(messages);")
    cols=cur.fetchall()
    if not cols:
        print('no messages table')
    else:
        print('messages columns:')
        for c in cols:
            print(c)
        cur.execute("SELECT id, role, content, model, meta, ts FROM messages ORDER BY id DESC LIMIT 20;")
        rows=cur.fetchall()
        for r in rows:
            id,role,content,model,meta,ts=r
            print('---')
            print('id:',id,'role:',role,'ts:',ts,'model:',model)
            if meta:
                try:
                    mj=json.loads(meta)
                    print('meta keys:', list(mj.keys()))
                    if 'provider' in mj:
                        print('provider:',mj.get('provider'))
                except Exception as e:
                    print('meta parse error',e,str(meta)[:200])
            else:
                print('meta: None')
except Exception as e:
    print('error',e)
con.close()
