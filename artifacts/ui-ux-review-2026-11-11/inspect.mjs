for(const route of ['generate','quiz','browser','stats']) {
  await evaluate(`location.hash='#/${route}'`);
  await sleep(8000);
  await snap(route);
}
console.log(await evaluate('window.reviewErrors'));
