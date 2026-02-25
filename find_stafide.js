const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        locale: 'nl-NL',
    });
    const page = await context.newPage();
    
    const redirects = [];
    page.on('response', resp => {
        if (resp.status() >= 300 && resp.status() < 400) {
            redirects.push({status: resp.status(), url: resp.url(), location: resp.headers()['location']});
        }
    });
    
    try {
        await page.goto('https://englishjobsearch.nl/clickout/507bdd0c8c0ff5d5', {
            waitUntil: 'domcontentloaded',
            timeout: 30000
        });
        
        await page.waitForTimeout(3000);
        
        console.log('Final URL:', page.url());
        console.log('Redirects:', JSON.stringify(redirects, null, 2));
        console.log('Title:', await page.title());
        
        // Get all text content
        const text = await page.evaluate(() => document.body.innerText);
        console.log('Body text (first 1000):', text.substring(0, 1000));
        
        // Get all links
        const links = await page.evaluate(() => {
            return Array.from(document.querySelectorAll('a[href]')).map(a => ({text: a.innerText.trim().substring(0, 50), href: a.href}));
        });
        console.log('Links:', JSON.stringify(links.slice(0, 20), null, 2));
        
    } catch(e) {
        console.log('Error:', e.message);
    }
    
    await browser.close();
})();
