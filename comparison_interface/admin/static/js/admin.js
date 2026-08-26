$('#clear-database').on('submit', function (event) {
    if (
        !confirm(
            'This will remove all participant data and all existing judgements from the database.\nThis action ' +
            'cannot be undone.\n\nAre you sure you want to clear the database?'
        )
    ) {
        event.preventDefault();
    }
});
