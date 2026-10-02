/* Run with Playwright installed. Never contacts retailer or model services. */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const {pathToFileURL}=require('node:url');
const path=require('node:path');
(async()=>{
 const browser=await chromium.launch({headless:true});
 try {
  for(const viewport of [{width:1440,height:1000},{width:390,height:844}]){
   const context=await browser.newContext({viewport});const page=await context.newPage(),errors=[];
   page.on('pageerror',error=>errors.push(error.message));
   await page.route('https://**/*',route=>route.abort());
   await page.goto(pathToFileURL(path.resolve('ski-deals/index.html')).href);
   await page.waitForSelector('#list article, #list .empty');
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'No horizontal overflow');
   await page.getByRole('button',{name:'Preferences',exact:true}).click();
   assert.match(await page.locator('[name=my_ski_sizes]').inputValue(),/167/);
   assert.match(await page.locator('[name=my_ski_sizes]').inputValue(),/169/);
   await page.locator('[name=ski_budget]').fill('200');
   await page.getByRole('button',{name:'Save in this browser',exact:true}).click();
   await page.reload();await page.getByRole('button',{name:'Preferences',exact:true}).click();
   assert.equal(await page.locator('[name=ski_budget]').inputValue(),'200');
   await page.getByRole('button',{name:'Restore published preferences',exact:true}).click();
   await page.getByRole('button',{name:'Close preferences',exact:true}).click();
   await page.getByRole('button',{name:'All deals',exact:true}).click();
   await page.locator('.filters summary').click();
   await page.locator('#search').fill('NO_SUCH_SKIS_987654321');
   await page.waitForSelector('.empty');
   await page.getByRole('button',{name:'Clear filters',exact:true}).click();
   assert.equal(await page.locator('#search').inputValue(),'');
   await page.screenshot({path:`/tmp/gear-${viewport.width}.png`,fullPage:false});
   assert.deepEqual(errors,[],'No JavaScript runtime errors');await context.close();
  }
  console.log('Desktop and mobile smoke tests passed.');
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
