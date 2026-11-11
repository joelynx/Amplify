import fs from 'node:fs/promises';
const out = new URL('./', import.meta.url);
const targets = await (await fetch('http://127.0.0.1:9239/json')).json();
const ws = new WebSocket(targets.find(x => x.type === 'page').webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener('open', r, {once: true}));
let id = 0;
const pending = new Map();
ws.addEventListener('message', e => {
  const msg = JSON.parse(e.data);
  if (pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
});
async function call(method, params={}) {
  const key = ++id;
  const p = new Promise(r => pending.set(key, r));
  ws.send(JSON.stringify({id:key,method,params}));
  const result = await p;
  if(result.error) throw new Error(JSON.stringify(result.error));
  return result.result;
}
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function evaluate(expression) {
  const r = await call('Runtime.evaluate', {expression, awaitPromise:true, returnByValue:true});
  if(r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails));
  return r.result.value;
}
async function snap(name) {
  await sleep(1400);
  const {data} = await call('Page.captureScreenshot', {format:'png'});
  await fs.writeFile(new URL(name+'.png',out),Buffer.from(data,'base64'));
  const text = await evaluate('document.body.innerText');
  await fs.writeFile(new URL(name+'.txt',out),text);
  console.log(name, text.length);
}
const bridge = `window.reviewErrors=[];addEventListener('error',e=>window.reviewErrors.push(e.message));addEventListener('unhandledrejection',e=>window.reviewErrors.push(String(e.reason)));window.pywebview={api:new Proxy({}, {get:(_, method)=>method==='then'?undefined:async (...args)=>{
  const res=await fetch('http://127.0.0.1:8766/',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({method,args})});
  const body=await res.json();if(body.error)throw new Error(body.error);return body.value;
}})};`;
await call('Page.enable');
await call('Runtime.enable');
await call('Emulation.setDeviceMetricsOverride',{width:1280,height:820,deviceScaleFactor:1,mobile:false});
const task=process.argv[2] || 'capture';
if(task==='close') {
  await call('Browser.close');
} else if(task==='run') {
  await new (async function(){}.constructor)('call','evaluate','snap','sleep','fs','out',await fs.readFile(new URL(process.argv[3],out),'utf8'))(call,evaluate,snap,sleep,fs,out);
} else if(task==='file') {
  console.log(JSON.stringify(await evaluate(await fs.readFile(new URL(process.argv[3],out),'utf8')),null,2));
} else if(task==='eval') {
  console.log(JSON.stringify(await evaluate(process.argv[3]),null,2));
} else if(task==='snap') {
  await snap(process.argv[3]);
} else {
  await call('Page.addScriptToEvaluateOnNewDocument',{source:bridge});
  await call('Emulation.setDeviceMetricsOverride',{width:1280,height:820,deviceScaleFactor:1,mobile:false});
  await call('Page.navigate',{url:'http://127.0.0.1:5179/'});
  await sleep(6500);
  for(const route of ['','generate','quiz','browser','stats','history','subjects','themes','settings']) {
    await evaluate(`location.hash=${JSON.stringify('#/'+route)}`);
    await snap(route || 'home');
  }
}
ws.close();
