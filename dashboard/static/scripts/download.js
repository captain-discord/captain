$(document).ready(() => {
    $("#download-button").attr("href", window.URL.createObjectURL(new Blob([$("#raw-text").text()], {type: 'text/plain'})));
});