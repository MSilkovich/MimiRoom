#!/usr/bin/env python3
"""Configure the owner's provider key locally; never print or upload it."""
from pathlib import Path
import getpass,os,subprocess,sys
root=Path(__file__).resolve().parent.parent
print('МиМиРум · пробный ИИ-помощник')
print('Создайте API-ключ в https://console.groq.com/keys на Free Plan.')
print('Не подключайте платёжную карту для бесплатного теста. Приложение не определяет тариф ключа.')
try:key=getpass.getpass('Вставьте ключ Groq (ввод скрыт): ').strip()
except (KeyboardInterrupt,EOFError):sys.exit('\nНастройка отменена.')
if len(key)<20 or any(c.isspace() for c in key):sys.exit('Ключ не сохранён: проверьте значение.')
file=root/'.env.local';old=file.read_text() if file.exists() else ''
updates={'GROQ_API_KEY':key,'AI_ENABLED':'true','AI_MODEL':'openai/gpt-oss-20b'}
lines=[];seen=set()
for line in old.splitlines():
 name=line.split('=',1)[0].strip()
 if name in updates:lines.append(name+'='+updates[name]);seen.add(name)
 else:lines.append(line)
for name,value in updates.items():
 if name not in seen:lines.append(name+'='+value)
fd=os.open(file,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
os.fchmod(fd,0o600)
with os.fdopen(fd,'w') as f:f.write('\n'.join(lines)+'\n')
print('Ключ сохранён только на этом Mac. Запускаем поддержку; Telegram остаётся выключенным, если вы не включали его отдельно.')
subprocess.run(['node','server/http.mjs'],cwd=root,check=False)
