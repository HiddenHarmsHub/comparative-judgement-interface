// called from register template
function handleData() {  // eslint-disable-line no-unused-vars
    // Verify that a group preference was selected by the user
    var form_data = new FormData(document.querySelector("form"));
    if (!form_data.has("group_ids")) {
        document.getElementById("group-selection-error").style.visibility = "visible";
        return false;
    }

    document.querySelector(".submit").disabled = true;
    if (document.getElementById("group-selection-error")) {
        document.getElementById("group-selection-error").style.visibility = "hidden";
    }
    return true;
}
