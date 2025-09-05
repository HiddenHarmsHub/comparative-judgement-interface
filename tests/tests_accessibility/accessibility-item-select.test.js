/* global test, expect */


test('Test the item selection page', async () => {
    const url = 'http://localhost:5001/selection/items';
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
        'wait for path to be /selection/items',
        ] 
    await expect(url).toBeAccessible(actions);
});
