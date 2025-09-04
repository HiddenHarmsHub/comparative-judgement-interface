
$('#save-button').on('click', function(event) {
    event.preventDefault();
    $(easyMDE.codemirror.getTextArea()).val(easyMDE.value());
    data = $('#edit-page-form').serialize();
    if (easyMDE.value().length === 0) {
        alert('You must add text to the page.')
    } else {
        $('#edit-page-form').submit();
    }
    
});

const easyMDE = new EasyMDE(
    {
        toolbar: [
            'bold', 'italic', 'heading', '|', 'unordered-list', 'ordered-list', '|', 'quote', 'link', '|', 'preview', '|', 'guide' 
        ],
        shortcuts: {
            "toggleSideBySide": null,
            "toggleFullScreen": null
        }
    }
    
);

// these three setting make the typing area (not the menu bar) keyboard accessible
// and stops the focus getting stuck in the markdown area
easyMDE.codemirror.options.tabindex = 0;
easyMDE.codemirror.options.extraKeys.Tab = false;
easyMDE.codemirror.options.extraKeys['Shift-Tab'] = false;

// This line makes the buttons on the menu bar keyboard accessible
$('.editor-toolbar > button').attr('tabindex', '0');

// set the text if we have some
const current_text = document.getElementById('current_text').value;
easyMDE.value(current_text);

easyMDE.codemirror.on('blur', function () {
    $(easyMDE.codemirror.getTextArea()).val(easyMDE.value());
});


