/* global require, beforeAll, afterAll, test, expect */

const pa11y = require('pa11y');
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

test('Test all the simple pages', async () => {
  const urls = ['http://localhost:5001/introduction',
                'http://localhost:5001/ethics-agreement',
                'http://localhost:5001/policies',
                'http://localhost:5001/register',
                'http://localhost:5001/does-not-exist',  // to test 404  
                ];
  await expect(urls).allToBeAccessible();
}, 5000 * 5);


test('Test the rank page', async () => {
  const page = await browser.newPage();
  const url = 'http://localhost:5001/rank';
  await page.goto(url, {waitUntil: 'networkidle0'});
  // accept the cookies
  await page.waitForSelector('#cookie-message-popup-accept', { visible: true });
  page.click('#cookie-message-popup-accept');
  // fill in the form (using the type function did not work for me)
  await page.waitForSelector('#cookie-message-popup-accept', { visible: false });
  await page.$eval('#name-input', el => el.value = 'My Name');
  page.click('#country-choice-1');
  await page.select('#allergies-select', 'Yes');
  await page.$eval('#age-input', el => el.value = '29');
  await page.$eval('#email-input', el => el.value = 'test@example.com');
  await page.$eval('#group-2', el => el.checked = 'true');
  await page.$eval('#accept-ethics-agreement', el => el.checked = 'true');
  expect(await page.$eval('#group-2', el => el.checked)).toBe(true);
  expect(await page.$eval('#accept-ethics-agreement', el => el.checked)).toBe(true);
  // submit the form
  page.click('#submit-button');

  // wait for the ranking page to load
  await page.waitForNavigation({ waitUntil: 'networkidle0' });
  await page.waitForSelector('#confirm-button-d', { visible: true });

  // run pa11y and test the report
  const report = await pa11y(url, {
      runners: ['axe', 'htmlcs'],
      standard: 'WCAG2AA',
      ignoreUrl: true,
      browser: browser,
      page: page,
      includeWarnings: false,
      includeNotices: false
  });
  await expect(report).toHaveNoErrors();
}, 50000);
