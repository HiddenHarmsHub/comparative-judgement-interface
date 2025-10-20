// This function allows to add custom styling to google embed iframes
document.addEventListener("DOMContentLoaded", function () {
    // get all iframes that were parsed before this tag
    var iframes = document.getElementsByTagName("iframe");

    for (let i = 0; i < iframes.length; i++) {
        var url = iframes[i].getAttribute("src");
        if (url && url.startsWith("https://docs.google.com/document/d/")) {
            // create div and replace iframe
            let d = document.createElement('div');
            d.classList.add("embedded-doc"); // optional
            iframes[i].parentElement.replaceChild(d, iframes[i]);

            // CORS request
            var xhr = new XMLHttpRequest();
            xhr.open('GET', url, true);
            xhr.onload = function () {
                // display response
                d.innerHTML = xhr.responseText;
            };
            xhr.send();
        }
    }
});