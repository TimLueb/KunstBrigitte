function includeHTML(id, url) {
  fetch(url)
    .then(response => response.text())
    .then(data => document.getElementById(id).innerHTML = data);
}

window.addEventListener('DOMContentLoaded', function() {
  includeHTML('site-header', 'header.html');
  includeHTML('site-footer', 'footer.html');
});