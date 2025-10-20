/* global test, expect */


function login() {
  const email = 'test@example.co.uk';
  const password = 'password';
  return [
    'navigate to http://127.0.0.1:5001/admin/login',
    'set field input[id="email"] to ' + email,
    'set field input[id="password"] to ' + password,
    'click element #submit',
    'wait for element #start-new-study to be visible',
  ];
}


test('Test the admin dashboard', async () => {
  const url = 'http://localhost:5001/admin/dashboard';
  const actions = login()
  await expect(url).toBeAccessible(actions);
}, 50000);
  

test('Test the image upload', async () => {
  const url = 'http://localhost:5001/admin/upload-images';
  const actions = login()
  await expect(url).toBeAccessible(actions);
}, 50000);


test('Test the config upload', async () => {
  const url = 'http://localhost:5001/admin/upload-config';
  const actions = login()
  await expect(url).toBeAccessible(actions);
}, 50000);


test('Test the csv upload', async () => {
  const url = 'http://localhost:5001/admin/upload-csv';
  const actions = login()
  await expect(url).toBeAccessible(actions);
}, 50000);
