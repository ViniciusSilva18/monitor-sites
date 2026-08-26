"""Monitor de uptime de websites com alertas e relatório HTML."""
import time, json, os, requests, schedule
from datetime import datetime
from pathlib import Path

SITES = [
    {'name': 'Google', 'url': 'https://google.com'},
    {'name': 'GitHub', 'url': 'https://github.com'},
    {'name': 'Farfetch PT', 'url': 'https://farfetch.com'},
]
LOG_FILE = Path('logs/uptime.json')
LOG_FILE.parent.mkdir(exist_ok=True)
results = []

def check_site(site: dict) -> dict:
    try:
        start = time.time()
        r = requests.get(site['url'], timeout=10, allow_redirects=True)
        ms = round((time.time() - start) * 1000)
        status = 'up' if r.status_code < 400 else 'down'
        return {'name': site['name'], 'url': site['url'], 'status': status, 'code': r.status_code, 'ms': ms, 'time': datetime.now().isoformat()}
    except Exception as e:
        return {'name': site['name'], 'url': site['url'], 'status': 'down', 'code': None, 'ms': None, 'error': str(e), 'time': datetime.now().isoformat()}

def check_all():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] A verificar {len(SITES)} sites...")
    for site in SITES:
        r = check_site(site)
        icon = '✅' if r['status'] == 'up' else '❌'
        ms_str = f"{r['ms']}ms" if r['ms'] else 'timeout'
        print(f"  {icon} {r['name']} ({r['url']}) — {r['status'].upper()} {ms_str}")
        results.append(r)
    with open(LOG_FILE, 'w') as f:
        json.dump(results[-200:], f, indent=2, ensure_ascii=False)
    generate_report()

def generate_report():
    up = sum(1 for r in results if r['status'] == 'up')
    down = len(results) - up
    html = f"""<!DOCTYPE html>
<html lang="pt"><head><meta charset="UTF-8"/><title>Uptime Report</title>
<style>body{{font-family:Inter,sans-serif;background:#090d16;color:#f1f5f9;padding:32px}}
h1{{margin-bottom:24px}}table{{width:100%;border-collapse:collapse}}
th,td{{padding:12px;text-align:left;border-bottom:1px solid rgba(255,255,255,0.08)}}
.up{{color:#10b981}}.down{{color:#f43f5e}}
.stat{{display:inline-block;padding:8px 16px;border-radius:8px;margin-right:8px;font-weight:700}}
</style></head><body>
<h1>📡 Uptime Monitor Report</h1>
<p style="color:#64748b">Gerado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<div style="margin:24px 0">
<span class="stat" style="background:rgba(16,185,129,0.1);color:#10b981">✅ Online: {up}</span>
<span class="stat" style="background:rgba(244,63,94,0.1);color:#f43f5e">❌ Offline: {down}</span>
</div>
<table><tr><th>Site</th><th>Status</th><th>Código</th><th>Resposta</th><th>Verificado</th></tr>
{"".join(f"<tr><td>{r['name']}</td><td class='{r['status']}'>{r['status'].upper()}</td><td>{r.get('code','—')}</td><td>{str(r.get('ms','—'))+'ms' if r.get('ms') else '—'}</td><td>{r['time'][:19]}</td></tr>" for r in results[-20:])}
</table></body></html>"""
    with open('report.html', 'w', encoding='utf-8') as f:
        f.write(html)

if __name__ == '__main__':
    print('📡 VibeMon — Monitor de Sites')
    check_all()
    schedule.every(5).minutes.do(check_all)
    print('⏱️  A verificar a cada 5 minutos... (Ctrl+C para parar)')
    while True:
        schedule.run_pending()
        time.sleep(30)
