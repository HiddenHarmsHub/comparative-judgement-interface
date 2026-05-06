// on load function to get the id provided
$(function () {
    const params = new URLSearchParams(window.location.search);
    console.log(params);
    const id = params.get('id');
    console.log('id is ' + id)
    document.getElementById('first-study-id').value = id;
});