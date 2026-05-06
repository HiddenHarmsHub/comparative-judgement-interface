// on load function to get the id provided
$(function () {
    const params = new URLSearchParams(window.location.search);
    const id = params.get('id');
    if (id === null) {
        alert('You must complete the first study before moving onto this one');
        document.getElementById('redirect').style.display = 'block';
        document.getElementById('submit-button').disabled = 'disabled';
    } else {
        document.getElementById('first_study_id-input').value = id;
    }
});