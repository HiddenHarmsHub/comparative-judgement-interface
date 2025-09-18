/* global test, expect */


test('Test all the simple pages', async () => {
  const urls = [
    'http://localhost:5001/introduction',
    'http://localhost:5001/ethics-agreement',
    'http://localhost:5001/policies',
    'http://localhost:5001/register',
    'http://localhost:5001/does-not-exist',  // to test 404
  ];
  await expect(urls).allToBeAccessible();
}, 5000 * 5);

test('Test the rank page', async () => {
  const url = 'http://localhost:5001/rank';
  const actions = [
    'navigate to http://127.0.0.1:5001/register',
    'set field input[id="name-input"] to Test Name',
    'click element #country-choice-1',
    'set field select[id="allergies-select"] to Yes',
    'set field input[id="age-input"] to 29',
    'set field input[id="email-input"] to test@example.com',
    'click element #group-2',
    'click element #accept-ethics-agreement',
    'click element #submit-button',
    'wait for element #cookie-message-popup-accept to be visible',
    'click element #cookie-message-popup-accept',
    'wait for element #confirm-button-d to be visible',
    ] 
    await expect(url).toBeAccessible(actions);
}, 50000);

test('Test the thank you page', async () => {
  const url = 'http://localhost:5001/thankyou'
  const actions = [
    'navigate to http://127.0.0.1:5001/register',
    'set field input[id="name-input"] to Test Name',
    'click element #country-choice-1',
    'set field select[id="allergies-select"] to Yes',
    'set field input[id="age-input"] to 29',
    'set field input[id="email-input"] to test@example.com',
    'click element #group-2',
    'click element #accept-ethics-agreement',
    'click element #submit-button',
    'wait for element #cookie-message-popup-accept to be visible',
    'click element #cookie-message-popup-accept',
    'wait for element #confirm-button-d to be visible',
    'navigate to http://127.0.0.1:5001/thankyou',
    ] 
  await expect(url).toBeAccessible(actions);
}, 50000);
