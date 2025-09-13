/* global module */

// on load function to display current state if we are rejudging
$(function () {
    if (document.getElementById('comparison_id') && document.getElementById('comparison_id').value !== '') {
        const initialSelectedItemId = document.getElementById('initial_selected_item_id').value;
        if (document.getElementById('initial_state').value === 'tied') {
            // aria-select both images
            $('#left-item').attr('aria-checked', 'true');
            $('#right-item').attr('aria-checked', 'true');
            //  add equal hint to both images
            addVisualHint('selection-tied', document.getElementById('left-item'), 'tied');
            addVisualHint('selection-tied', document.getElementById('right-item'), 'tied');
        } else if (document.getElementById('initial_state').value === 'selected') {
            // set the previously selected item id
            setSelectedItem(initialSelectedItemId);

            // find the correct image and select it and add the hint
            if (document.getElementById('item_1_id').value === initialSelectedItemId) {
                $('#left-item').attr('aria-checked', 'true');
                addVisualHint('selected-item', document.getElementById('left-item'), 'selected');

            } else if (document.getElementById('item_2_id').value === initialSelectedItemId) {
                $('#right-item').attr('aria-checked', 'true');
                addVisualHint('selected-item', document.getElementById('right-item'), 'selected');
            }

        } else if (document.getElementById('initial_state').value === 'skipped') {
            addVisualHint('selection-skipped', document.getElementById('left-item'), 'skipped');
            addVisualHint('selection-skipped', document.getElementById('right-item'), 'skipped');

        }
    }
});

$("img, svg").on('click', function () {
    hintItem($(this));
});

$("img, svg").on('keypress', function () {
    hintItem($(this));
});

// called from rank template on form submission
function checkSelection(event) {
    // validates the ranking form before submission
    // this also handles the double click prevention for the rank form because otherwise the submit triggers too early
    // and if the selection is not accepted it prevents further submission
    if ($(event.target).data().isSubmitted) {
        return false;
    }
    if (event.submitter.id === 'skip-button') {
        // then we need to check nothing has been selected
        if ($('#left-item').attr('aria-checked') === 'false' && $('#right-item').attr('aria-checked') === 'false') {
            $(event.target).data().isSubmitted = true;
            return true;
        }
        alert(document.getElementById('skip_button_error').value);
        return false;

    } else if (event.submitter.id === 'confirm-button-d') {
        // then we need to ensure something has been selected
        if ($('#left-item').attr('aria-checked') === 'true' || $('#right-item').attr('aria-checked') === 'true') {
            $(event.target).data().isSubmitted = true;
            return true;
        }
        alert(document.getElementById('confirm_button_error').value);
        return false;
    } else {
        // just submit the form
        $(event.target).data().isSubmitted = true;
        return true;
    }

};

function hintItem(clickedItem) {
    let itemId, selected, allowTies;
    const clickedItem1 = clickedItem.hasClass("left-item");
    const clickedItem2 = clickedItem.hasClass("right-item");
    const item1 = document.getElementById("left-item");
    const item2 = document.getElementById("right-item");
    const isItem1Selected = item1.classList.contains('selected-item') || item1.classList.contains('selection-tied');
    const isItem2Selected = item2.classList.contains('selected-item') || item2.classList.contains('selection-tied');
    const idItem1 = document.getElementById('item_1_id').value;
    const idItem2 = document.getElementById('item_2_id').value;
    const allowTiesSetting = document.getElementById('allow-ties').value;

    // Set the clicked item DOM object
    clickedItem = item1;
    if (clickedItem2) {
        clickedItem = item2;
    }

    allowTies = true;
    if (allowTiesSetting == 'false')    {
        allowTies = false;
    }

    // Case 1: No item is already selected. Result: One item is selected
    if (!isItem1Selected && !isItem2Selected) {
        // Clean the all visual hints
        cleanVisualHint('selected-item', item1, item2);
        cleanVisualHint('selection-tied', item1, item2);
        cleanVisualHint('selection-skipped', item1, item2);
        resetAriaChecked(item1, item2);

        // Show the item item as selected
        addVisualHint('selected-item', clickedItem, 'selected');
        $(clickedItem).attr('aria-checked', 'true');

        // Set the selected item
        itemId = idItem1;
        if (clickedItem2) {
            itemId = idItem2;
        }
        setSelectedItem(itemId);

        return;
    }

    // Case 2: Just one item was selected and ties are allowed. Result: Tied case.
    if (
        ((clickedItem1 && !isItem1Selected && isItem2Selected) ||
         (clickedItem2 && !isItem2Selected && isItem1Selected)) &&
        allowTies === true
    ) {
        // Clean the selected-items class
        cleanVisualHint('selected-item', item1, item2);
        cleanVisualHint('selection-tied', item1, item2);
        cleanVisualHint('selection-skipped', item1, item2);
        resetAriaChecked(item1, item2);

        // Show both items as selected (Tied case)
        addVisualHint('selection-tied', item1, 'tied');
        addVisualHint('selection-tied', item2, 'tied');
        $(item1).attr('aria-checked', 'true');
        $(item2).attr('aria-checked', 'true');

        // Clean the selected item value
        setSelectedItem("");

        return
    }

    // Case 3: Just one item was selected and ties are not allowed. Result: One item selected (previously selected
    // item unselected).
    if (
        ((clickedItem1 && !isItem1Selected && isItem2Selected) ||
         (clickedItem2 && !isItem2Selected && isItem1Selected)) &&
        allowTies === false
    ) {
        // Clean the selected-items class
        cleanVisualHint('selected-item', item1, item2);
        cleanVisualHint('selection-tied', item1, item2);
        cleanVisualHint('selection-skipped', item1, item2);
        resetAriaChecked(item1, item2);

        addVisualHint('selected-item', clickedItem, 'selected');
        $(clickedItem).attr('aria-checked', 'true');

        // Set the selected item
        itemId = idItem1;
        if (clickedItem2) {
            itemId = idItem2;
        }
        setSelectedItem(itemId);

        return
    }

    // Case 4: One item was unselected. Result: The other item gets the 'higher' label
    if (isItem1Selected && isItem2Selected) {
        // Clean the tied selection class
        cleanVisualHint('selected-item', item1, item2);
        cleanVisualHint('selection-tied', item1, item2);
        cleanVisualHint('selection-skipped', item1, item2);
        resetAriaChecked(item1, item2);

        // Defined the selected and unselected items. The selected item will be
        // the item not clicked.
        selected = item1;
        if (clickedItem1) {
            selected = item2;
        }

        // Mark as selected the not clicked item.
        addVisualHint('selected-item', selected, 'selected');
        $(selected).attr('aria-checked', 'true');

        // Set as selected id the value of the not clicked item.
        itemId = idItem2;
        if (clickedItem2) {
            itemId = idItem1;
        }
        setSelectedItem(itemId);
        return;
    }

    // Case 5: The only selected item is unselected. Result: Confirm button is disabled
    if (
        (clickedItem2 && isItem2Selected && !isItem1Selected) ||
        (clickedItem1 && isItem1Selected && !isItem2Selected)
    ) {
        // Clean the selected-items class
        cleanVisualHint('selected-item', item1, item2);
        cleanVisualHint('selection-tied', item1, item2);
        cleanVisualHint('selection-skipped', item1, item2);
        resetAriaChecked(item1, item2);

        // Clean the selected item id
        setSelectedItem("");

        return;
    }
}

function cleanVisualHint(itemClass, item1, item2) {
    item1.classList.remove(itemClass);
    item2.classList.remove(itemClass);
    $(".selected-hint").remove();
}

function addVisualHint(itemClass, item, type) {
    const selectedItemIndicator = document.getElementById('selected_item_indicator').value;
    const tiedComparisonIndicator = document.getElementById('tied_items_indicator').value;
    const skippedComparisonIndicator = document.getElementById('skipped_items_indicator').value;

    const div = document.createElement('div');
    div.setAttribute('class', 'selected-hint');
    div.setAttribute('aria-hidden', true);
    div.setAttribute('style', 'pointer-events:none;');
    const span = document.createElement('span');
    span.setAttribute('class', 'fs-1 fw-bold bg-white p-1 border border-success text-success');
    span.textContent = selectedItemIndicator;
    if (type == 'tied') {
        span.setAttribute('class', 'fs-1 fw-bold bg-white p-1 border border-primary text-primary');
        span.textContent = tiedComparisonIndicator;
    } else if (type == 'skipped') {
        span.setAttribute('class', 'fs-1 fw-bold bg-white p-1 border border-black');
        span.textContent = skippedComparisonIndicator;
    }
    div.appendChild(span);
    item.classList.add(itemClass);
    item.after(div);
}

function setSelectedItem(value) {
    document.getElementById("selected_item_id").value = value;
}

function resetAriaChecked(item1, item2) {
    $(item1).attr('aria-checked', 'false');
    $(item2).attr('aria-checked', 'false');
}


try {

    module.exports = {
        checkSelection,
        hintItem,
        cleanVisualHint,
        addVisualHint,
        setSelectedItem,
        resetAriaChecked
    }
// eslint-disable-next-line no-unused-vars
} catch (e) {
    // nodejs is not available which is fine as long as we are not running tests.
}
