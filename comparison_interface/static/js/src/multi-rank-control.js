$(function () {
    $('#rank-form').on('submit', checkSelection);
});

function checkSelection(event) {
    // prevent double submission
    if ($(event.target).data().isSubmitted) {
        return false;
    }
    if (event.originalEvent.submitter.id === 'confirm-button-d') {
        // check all expected questions have been answered
        const rankForm = $('#rank-form');
        const allowTies = rankForm.data('allow-ties');
        const allowSkip = rankForm.data('allow-skip');
        const formData = rankForm.serializeArray();
        const totalQuestions = rankForm.data('question-total');
        const submittedKeys = formData.map(item => item.name);
        const questionLabels = Array.from({ length: totalQuestions }, (_, i) => `question_${i + 1}`);
        for (question of questionLabels) {
            if (submittedKeys.indexOf(question) === -1) {
                alert(rankForm.data('incomplete-form-error'));
                return false;
            } 
        }
        if (allowTies && allowSkip) {
            // then we need to check that skip checkbox is appropriately used
            const questionData = Object.fromEntries(questionLabels.map(str => [str, []]));
            for (entry of formData) {
                if (questionLabels.indexOf(entry.name) !== -1) {
                    questionData[entry.name].push(entry.value);
                }
            }
            const failedCheck = Object.values(questionData).some(list => list.length >= 2 && list.includes(''));
            if (failedCheck) {
                alert(rankForm.data('skip-selection-error'))
                return false;
            }
        }
        $(event.target).data().isSubmitted = true;
        return true;
    }
}