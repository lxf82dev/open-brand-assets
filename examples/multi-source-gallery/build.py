import argparse
import base64
import os
import concurrent.futures
import datetime as dt
import hashlib
import html
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

parser=argparse.ArgumentParser(description='Build a live/saved HTML gallery using the find-brand-logo skill. Network access required.')
parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parent/'generated')
parser.add_argument('--cache-dir',default=str(Path(os.getenv('XDG_CACHE_HOME',Path.home()/'.cache'))/'open-brand-assets'))
args=parser.parse_args()
REPO=Path(__file__).resolve().parents[2]
ROOT=args.output.expanduser().resolve()
CLI=REPO/'skills/find-brand-logo/scripts/logos.py'
ROOT.mkdir(parents=True,exist_ok=True)
(ROOT/'assets').mkdir(exist_ok=True)
(ROOT/'notices').mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('logo_skill',CLI)
skill=importlib.util.module_from_spec(spec);spec.loader.exec_module(skill)
CASES=[
 ('ours','HeyGen','heygen-symbol-black-logo','HeyGen','Official kit · embedded PNG in SVG'),
 ('ours','Higgsfield','site-icon','Higgsfield','Website icon · PNG'),
 ('svgl','Astro','route-light','Astro','SVGL · light-background variant'),
 ('lobe','Claude','claude-color','Claude','Lobe Icons · color variant'),
 ('simple-icons','GitHub','mono','GitHub','Simple Icons · monochrome'),
 ('thesvg','Vercel','light','Vercel','theSVG · light-background variant'),
 ('gilbarbara','Higgsfield','higgsfield-icon','Higgsfield','Gilbarbara · symbol'),
 ('vectorlogozone','Slack','slack-icon','Slack','Vector Logo Zone · icon'),
 ('devicon','Python','python-original','Python','Devicon · original variant'),
 ('selfhst','Nextcloud','nextcloud','Nextcloud','selfh.st · supplied color'),
 ('dashboard-icons','AdGuard','adguard-home','AdGuard Home','Dashboard Icons · supplied color'),
 ('crypto','Bitcoin','color','Bitcoin','Cryptocurrency Icons · color'),
]

def retrieve(case):
 source,query,variant,label,subtitle=case
 command=['python3',str(CLI),'search',query,'--source',source,'--limit','100','--json','--cache-dir',args.cache_dir]
 result=subprocess.run(command,capture_output=True,text=True,check=True)
 search=json.loads(result.stdout)
 if search['errors']:raise ValueError(search['errors'])
 chosen=next((row for row in search['results'] if row['variant']==variant),None)
 if chosen is None:raise ValueError(f'{source} has no exact {variant}; returned '+str([(r['brand'],r['variant']) for r in search['results']]))
 suffix='.'+chosen.get('format','svg')
 destination=ROOT/'assets'/(source+'-'+variant+suffix)
 if source=='ours':
  fetch=['python3',str(CLI),'fetch',chosen['id'],'--variant',variant,'--output',str(destination),'--force']
  subprocess.run(fetch,capture_output=True,text=True,check=True)
  data=destination.read_bytes()
 else:
  data=skill.request_bytes(chosen['url'])
  skill.check_image(data,suffix)
  destination.write_bytes(data)
 checksum=hashlib.sha256(data).hexdigest()
 if chosen.get('sha256') and checksum!=chosen['sha256']:raise ValueError('Checksum mismatch')
 if source=='svgl':
  license_url='https://raw.githubusercontent.com/pheralb/svgl/main/LICENSE'
 elif source=='ours':
  license_url='https://raw.githubusercontent.com/lxf82dev/open-brand-assets/main/TRADEMARKS.md'
 else:
  license_url=chosen['license_url']
 license_data=skill.request_bytes(license_url)
 (ROOT/'notices'/(source+'-LICENSE.txt')).write_bytes(license_data)
 return {'source':source,'label':label,'subtitle':subtitle,'query':query,'variant':variant,'url':chosen['url'],
  'revision':chosen.get('revision'),'file':str(destination.relative_to(ROOT)),'sha256':checksum,
  'bytes':len(data),'format':suffix[1:],'selection':chosen,'license_url':license_url,
  'search_command':['python3','<skill>/scripts/logos.py',*command[2:-2]],
  'saved_uri':'data:image/'+('svg+xml' if suffix=='.svg' else 'png')+';base64,'+base64.b64encode(data).decode()}

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 items=list(pool.map(retrieve,CASES))

cards=[]
for item in items:
 esc=lambda value:html.escape(str(value),quote=True)
 selection=item['selection']
 attribution=selection.get('attribution') or ''
 rights=selection.get('rights_note') or selection.get('usage',{}).get('note') or 'Check the source collection and brand guidelines for the intended use.'
 cards.append(f'''<article class="logo-card" data-source="{esc(item['source'])}">
 <div class="tile"><img width="92" height="72" alt="{esc(item['label'])} logo" data-live="{esc(item['url'])}" data-saved="{esc(item['saved_uri'])}" data-id="{esc(item['source']+'-'+item['variant'])}"></div>
 <div class="card-body"><div class="eyebrow">{esc(item['source'])}</div><h2>{esc(item['label'])}</h2><p class="sub">{esc(item['subtitle'])}</p>
 <div class="card-foot"><a href="{esc(item['url'])}" target="_blank" rel="noreferrer">Asset source ↗</a><span class="state" role="status">Loading</span></div>
 <details><summary>Provenance &amp; rights</summary><p>{esc(item['variant'])}<br>SHA-256: <code>{esc(item['sha256'])}</code></p><p>{esc(attribution)}</p><p>{esc(rights)}</p><a href="{esc(item['license_url'])}" target="_blank" rel="noreferrer">Collection terms ↗</a></details></div></article>''')

page='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Open Brand Assets — multi-source gallery test</title>
<style>
:root{color-scheme:light dark;--foreground:light-dark(#172033,#e7edf5);--muted-foreground:light-dark(#546174,#9eabc0);--card:light-dark(#f5f7fb,#182236);--border:light-dark(#d6dde8,#354258);--primary:light-dark(#5145a6,#a8b6ff);--primary-foreground:light-dark(#ffffff,#101627);--success:light-dark(#087554,#6ee7b7);--destructive:light-dark(#b32235,#ff8585)}*{box-sizing:border-box}body{margin:0;font:15px/1.5 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--foreground,#e7edf5);background:transparent}main{max-width:1140px;margin:auto}a{color:var(--primary,#a8b6ff);text-underline-offset:3px}header{padding:24px 0}.kicker{font-size:11px;font-weight:750;letter-spacing:.16em;color:var(--muted-foreground,#9eabc0)}h1{font-size:clamp(28px,5vw,46px);line-height:1.12;letter-spacing:-.04em;margin:10px 0 14px}header p{max-width:740px;color:var(--muted-foreground,#9eabc0);margin:0}.toolbar{display:flex;gap:14px;align-items:center;justify-content:space-between;flex-wrap:wrap;margin:4px 0 22px}.switch{display:flex;gap:4px;padding:4px;border:1px solid var(--border,#354258);border-radius:12px;background:var(--card,#182236)}button{border:0;background:transparent;color:var(--foreground,#e7edf5);font:600 13px system-ui;padding:10px 15px;border-radius:8px;cursor:pointer}button[aria-pressed=true]{background:var(--primary,#a8b6ff);color:var(--primary-foreground,#101627)}button:focus-visible,summary:focus-visible,a:focus-visible{outline:2px solid var(--ring,#a8b6ff);outline-offset:3px}#summary{font-size:13px;color:var(--muted-foreground,#9eabc0)}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.logo-card{overflow:hidden;border:1px solid var(--border,#354258);border-radius:16px;background:var(--card,#182236)}.tile{height:124px;margin:10px;border-radius:10px;background:#fff;display:flex;align-items:center;justify-content:center}.tile img{display:block;max-width:78%;object-fit:contain}.card-body{padding:7px 16px 15px}.eyebrow{font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted-foreground,#9eabc0);overflow-wrap:anywhere}h2{font-size:18px;letter-spacing:-.02em;margin:5px 0}.sub{font-size:12px;color:var(--muted-foreground,#9eabc0);margin:0 0 16px;min-height:36px}.card-foot{display:flex;gap:10px;align-items:center;justify-content:space-between;font-size:11px}.state{color:var(--muted-foreground,#9eabc0)}.state.pass{color:var(--success,#6ee7b7)}.state.fail{color:var(--destructive,#ff8585)}details{font-size:11px;margin-top:14px;color:var(--muted-foreground,#9eabc0)}summary{cursor:pointer}details code{overflow-wrap:anywhere;font-size:10px}footer{font-size:12px;color:var(--muted-foreground,#9eabc0);padding:22px 0}#mode-note{font-size:12px;color:var(--muted-foreground,#9eabc0);margin-top:0} @media(max-width:900px){.grid{grid-template-columns:repeat(3,minmax(0,1fr))}}@media(max-width:620px){.grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.card-body{padding:4px 12px 12px}.tile{height:100px}.toolbar{align-items:flex-start}h2{font-size:16px}}@media(max-width:340px){.grid{grid-template-columns:1fr}}
</style></head><body><main><header><div class="kicker">OPEN BRAND ASSETS · BROWSER INTEGRATION TEST</div><h1>One gallery. Eleven sources.</h1><p>Twelve real logos selected with the find-brand-logo skill. Original artwork, exact variants, and source records — with a saved-copy mode for offline use.</p></header>
<div class="toolbar"><div class="switch" role="group" aria-label="Image transport"><button type="button" data-mode="live" aria-pressed="true">Live sources</button><button type="button" data-mode="saved" aria-pressed="false">Saved copies</button></div><div id="summary" role="status" aria-live="polite">Loading images…</div></div><p id="mode-note">Direct image requests to the source URLs returned by the skill.</p><section class="grid" aria-label="Logos from eleven collections">'''+''.join(cards)+'''</section><footer>Marks belong to their respective owners. This is an integration test, not an endorsement or usage clearance. selfh.st collection credit: <a href="https://github.com/selfhst/icons">selfh.st Icons contributors</a> · CC-BY-4.0. Expand a card for provenance and rights. No third-party fonts or UI libraries.</footer></main>
<script>
window.galleryErrors=[];window.addEventListener('error',e=>{if(e.message)galleryErrors.push(e.message)});window.addEventListener('unhandledrejection',e=>galleryErrors.push(String(e.reason)));
let generation=0;window.galleryState={};
async function setGalleryMode(mode){const current=++generation;document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===mode)));document.querySelector('#mode-note').textContent=mode==='live'?'Direct image requests to the source URLs returned by the skill.':'Self-contained saved copies. All twelve images now use embedded data URLs; no image requests are needed.';const images=[...document.querySelectorAll('.tile img')];const state={mode,total:images.length,loaded:0,failed:0,done:false,results:[]};window.galleryState=state;
const update=()=>{document.querySelector('#summary').textContent=`${state.loaded} / ${state.total} loaded${state.failed?' · '+state.failed+' failed':''}`};update();
const work=images.map(async img=>{const status=img.closest('article').querySelector('.state');status.textContent='Loading';status.className='state';const url=mode==='live'?img.dataset.live:img.dataset.saved;img.src=url;let timer;try{await Promise.race([img.decode(),new Promise((_,reject)=>{timer=setTimeout(()=>reject(new Error('Image decode timed out')),20000)})]);if(current!==generation)return;if(!img.naturalWidth||!img.naturalHeight)throw new Error('Zero dimensions');state.loaded++;status.textContent='Loaded';status.className='state pass';state.results.push({id:img.dataset.id,loaded:true,width:img.naturalWidth,height:img.naturalHeight,transport:img.currentSrc.startsWith('data:')?'saved':'remote'})}catch(error){if(current!==generation)return;state.failed++;status.textContent='Failed';status.className='state fail';state.results.push({id:img.dataset.id,loaded:false,error:String(error),url:mode==='live'?url:'embedded'})}finally{clearTimeout(timer);if(current===generation)update()}});
window.galleryReady=Promise.all(work).then(()=>{if(current===generation){state.done=true;update()}return state});return window.galleryReady}
document.querySelectorAll('[data-mode]').forEach(button=>button.addEventListener('click',()=>setGalleryMode(button.dataset.mode)));setGalleryMode('live');
</script></body></html>'''
(ROOT/'index.html').write_text(page)
manifest={'tested_at':dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),'skill':str(CLI),'skill_commit':subprocess.run(['git','rev-parse','HEAD'],cwd=REPO,capture_output=True,text=True,check=True).stdout.strip(),'skill_cli_sha256':hashlib.sha256(CLI.read_bytes()).hexdigest(),'sources':sorted({item['source'] for item in items}),'images':[{key:value for key,value in item.items() if key!='saved_uri'} for item in items]}
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'html':str(ROOT/'index.html'),'manifest':str(ROOT/'manifest.json'),'images':len(items),'sources':manifest['sources'],'bytes':sum(item['bytes'] for item in items)},indent=2))
