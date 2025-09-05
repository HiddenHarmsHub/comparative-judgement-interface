/* global require, beforeAll, afterAll, test, expect */

const puppeteer = require('puppeteer');

let browser;

beforeAll(async () => {
  browser = await puppeteer.launch({
    headless: "new",
    args: ['--no-sandbox']
  });
});
  
afterAll(async () => {
  await browser.close();
});

test('Test the admin dashboard', async () => {
    const url = 'http://localhost:5001/admin/dashboard';
    const actions = [
      'navigate to http://127.0.0.1:5001/admin/dashboard',
      'set field input[id="email"] to test@example.co.uk',
      'set field input[id="password"] to password',
      'click element #submit',
      'wait for element #cookie-message-popup-accept to be visible',
      'click element #cookie-message-popup-accept',
      'wait for element #start-new-study to be visible',
      ] 
      await expect(url).toBeAccessible(actions);
  }, 50000);
  