$(function () {
    $('#rank-form').on('submit', checkSelection);
});

function checkSelection(event) {
    // prevent double submission
    if ($(event.target).data().isSubmitted) {
        return false;
    }
    if (event.originalEvent.submitter.id === 'confirm-button-d') {
        const rankForm = $('#rank-form');
        const allowTies = rankForm.data('allow-ties');
        if (allowTies) {
            // then we need to check that skip checkbox is appropriately used

        }   
        console.log(allowTies)
        console.log('form submitted');
        $(event.target).data().isSubmitted = true;
        return true;
    } else {
        // just submit the form this is a rejudge request
        console.log('general submission triggered')
        $(event.target).data().isSubmitted = true;
        return true;
    }
    
}