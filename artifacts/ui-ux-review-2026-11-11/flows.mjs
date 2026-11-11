const log = {};
for(const route of ['generate','quiz','browser','stats']) {
  await evaluate(`location.hash='#/${route}'`);
  await sleep(4500);
  await snap(route);
  log[route] = await evaluate(`({viewport:[innerWidth,innerHeight],scroll:[document.documentElement.scrollWidth,document.documentElement.scrollHeight],main:[...document.querySelectorAll('main')].map(e=>({client:e.clientHeight,scroll:e.scrollHeight})),buttons:[...document.querySelectorAll('button')].filter(e=>/Start|Generate PDF/.test(e.textContent)).map(e=>({text:e.textContent,y:e.getBoundingClientRect().y}))})`);
  if(route==='browser') {
    await evaluate(`document.querySelector('tbody button.font-mono').click()`);
    await sleep(3500);
    await snap('browser-question');
  }
  if(route==='stats') {
    log.tabs = await evaluate(`[...document.querySelectorAll('header button')].slice(0,2).map(e=>({text:e.textContent,color:getComputedStyle(e).color,background:getComputedStyle(e.parentElement).backgroundColor}))`);
    await evaluate(`[...document.querySelectorAll('button')].find(e=>e.textContent.trim()==='Filters').focus();[...document.querySelectorAll('button')].find(e=>e.textContent.trim()==='Filters').click()`);
    await sleep(300);
    log.modalFocus = await evaluate(`({active:document.activeElement.textContent,inside:!!document.activeElement.closest('[role=dialog]'),label:document.querySelector('[role=dialog]').getAttribute('aria-labelledby')})`);
    await snap('stats-modal');
    await call('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
  }
}
await call('Emulation.setDeviceMetricsOverride',{width:960,height:640,deviceScaleFactor:1,mobile:false});
await evaluate(`location.hash='#/browser'`);await sleep(4000);
await evaluate(`document.querySelector('tbody button.font-mono').click()`);await sleep(3000);
await snap('browser-960');
log.browser960 = await evaluate(`({viewport:innerWidth,body:document.documentElement.scrollWidth,main:document.querySelector('main').getBoundingClientRect().width,aside:document.querySelector('aside').getBoundingClientRect().width})`);
await evaluate(`location.hash='#/quiz'`);await sleep(3500);await snap('quiz-960');
await fs.writeFile(new URL('interaction-findings.json',out),JSON.stringify(log,null,2));
console.log(log);
