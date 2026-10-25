$(function () {
    $('#rank-form').on('submit', checkSelection);
});

function checkSelection(event) {
    // prevent double submission
    if ($(event.target).data().isSubmitted) {
        return false;
    }
    const rankForm = $('#rank-form');
    const allowTies = rankForm.data('allow-ties');
    if (allowTies) {
        // then we need to check that skip checkbox is appropriately used

    }   
    console.log(allowTies)
    console.log('form submitted');
}