// Pre-push check: every sitemap page at 360px and 390px must not scroll sideways, and no internal link may 404.
// Usage: node scripts/check.js site   (serves site/ itself on port 8802)
const {chromium}=require('/opt/npm-tools/node_modules/playwright');
const fs=require('fs'),path=require('path'),http=require('http');
const DIST=path.resolve(process.argv[2]||'site');const PORT=8802;
const types={'.html':'text/html','.css':'text/css','.js':'text/javascript','.json':'application/json','.jpg':'image/jpeg','.png':'image/png','.svg':'image/svg+xml','.txt':'text/plain','.xml':'application/xml'};
const srv=http.createServer((q,r)=>{let u=decodeURIComponent(q.url.split('?')[0]);let f=path.join(DIST,u);if(fs.existsSync(f)&&fs.statSync(f).isDirectory())f=path.join(f,'index.html');if(!fs.existsSync(f)){r.writeHead(404);return r.end('nf')}r.writeHead(200,{'Content-Type':types[path.extname(f)]||'application/octet-stream'});fs.createReadStream(f).pipe(r)}).listen(PORT);
(async()=>{
 const sm=fs.readFileSync(path.join(DIST,'sitemap.xml'),'utf8');const urls=[...sm.matchAll(/<loc>https?:\/\/[^/]+(\/[^<]*)<\/loc>/g)].map(m=>m[1]);
 const exists=u=>{const p=u.split('#')[0].split('?')[0];const f=path.join(DIST,p);return fs.existsSync(f)&&(fs.statSync(f).isFile()||fs.existsSync(path.join(f,'index.html')))};
 const broken=new Set();
 for(const u of urls){const html=fs.readFileSync(path.join(DIST,u,'index.html'),'utf8').replace(/<script[\s\S]*?<\/script>/g,'');for(const m of html.matchAll(/href="(\/[^"#]*|#\/[^"]*)"/g)){let h=m[1];if(h.startsWith('#/'))h='/'+h.slice(2).replace(/\/?$/,'/');if(h.startsWith('//')||h.startsWith('/search'))continue;if(!exists(h))broken.add(u+' -> '+h)}}
 const b=await chromium.launch();const bad=[];
 for(const w of [360,390]){const p=await b.newPage({viewport:{width:w,height:800}});
  for(const u of urls){await p.goto(`http://localhost:${PORT}${u}`,{waitUntil:'load'});await p.waitForTimeout(80);
   const o=await p.evaluate(()=>{const W=document.documentElement.clientWidth;const sw=document.documentElement.scrollWidth;if(sw<=W+1)return null;const off=[...document.querySelectorAll('body *')].filter(e=>{const r=e.getBoundingClientRect();return r.right>W+1&&r.width>0}).slice(0,3).map(e=>e.tagName+'.'+e.className);return sw+' '+off.join(',')});
   if(o)bad.push(`${w}px ${u} ${o}`)}
  await p.close()}
 await b.close();srv.close();
 console.log(urls.length,'pages checked');
 if(broken.size)console.log('BROKEN LINKS\n'+[...broken].slice(0,50).join('\n'));
 if(bad.length)console.log('OVERFLOW\n'+bad.slice(0,50).join('\n'));
 process.exit(broken.size||bad.length?1:0);
})();
