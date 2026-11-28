from pathlib import Path
import base64,json,re,zipfile
root=Path(__file__).resolve().parent.parent;dist=root/'dist'
css=(dist/'styles.css').read_text()+'\n'+(dist/'client.css').read_text()+'\n'+(dist/'support.css').read_text()
for f in (dist/'assets/fonts').glob('*.ttf'):
 css=css.replace('/assets/fonts/'+f.name,'data:font/ttf;base64,'+base64.b64encode(f.read_bytes()).decode())
js='\n'.join(re.sub(r'^import.*$','',(dist/n).read_text(),flags=re.M).replace('export ','') for n in ['data.js','scheduling.js','api.js','support-catalog.js','care-knowledge.js','support-core.js','support-ui.js','team-tools.js','client.js','app.js'])
images={f.stem:'data:image/webp;base64,'+base64.b64encode(f.read_bytes()).decode() for f in (dist/'assets/pets').glob('*.webp')}
js=js.replace("const image=p=>'/assets/pets/'+(p.image||'maltipoo')+'.webp';",'const image=p=>('+json.dumps(images)+")[p.image||'maltipoo'];")
js=js.replace('/assets/pets/maltipoo.webp',images['maltipoo'])
html=(dist/'index.html').read_text().replace('<link rel="stylesheet" href="/styles.css">','<style>'+css+'</style>').replace('<link rel="stylesheet" href="/client.css">','').replace('<link rel="stylesheet" href="/support.css">','').replace('<script type="module" src="/app.js"></script>','<script>(()=>{\n'+js+'\n})()</script>')
(root/'MiMiRoom_CRM_Preview.html').write_text(html)
(root/'MiMiRoom_Client.html').write_text(html)
studio=html.replace("const entry=new URLSearchParams(location.search);", "const entry=new URLSearchParams(location.search);if(!entry.has('app'))entry.set('app','studio');").replace('<title>МиМиРум · Пространство заботы</title>','<title>МиМиРум · Команда</title>')
(root/'MiMiRoom_Studio.html').write_text(studio)
artifacts=root/'artifacts';artifacts.mkdir(exist_ok=True)
(artifacts/'preview-check.mjs').write_text(js)
version=json.loads((root/'package.json').read_text())['version']
archive=artifacts/('MiMiRoom_CRM_v'+version+'.zip')
# Явный список исходников: локальные ключи и данные не попадают в ZIP.
roots=['dist','docs','scripts','server','support','tests','.github',
       'package.json','package-lock.json','README.md','CONTRIBUTING.md',
       '.env.example','.gitignore','.gitattributes','.nvmrc',
       'MiMiRoom_Client.html','MiMiRoom_Studio.html','MiMiRoom_CRM_Preview.html']
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for name in roots:
  source=root/name
  if source.is_file():
   z.write(source,Path('MiMiRoom_CRM')/name)
  elif source.is_dir():
   for f in source.rglob('*'):
    if f.is_file() and not any(part.startswith('.') or part in ['node_modules','__pycache__'] for part in f.relative_to(source).parts) and f.suffix not in ['.pyc','.log']:
     z.write(f,Path('MiMiRoom_CRM')/f.relative_to(root))
print('Автономные HTML готовы. Архив: '+str(archive))
