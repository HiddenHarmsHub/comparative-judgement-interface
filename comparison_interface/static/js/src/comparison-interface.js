// prevent double submission
$('#item-selection-form').on('submit', function () {
    const $this = $(this);
    /** prevent double posting */
    if ($this.data().isSubmitted) {
        return false;
    }
    /** mark the form as processed, so we will not process it again */
    $this.data().isSubmitted = true;
    return true;
});

// enable space key activation for links styled as buttons using bootstrap btn class
$('a.btn').on('keydown', function (e) {
    if (e.key === ' ') {
        window.location = this.href;
    }
});
