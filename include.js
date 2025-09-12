function includeHTML(id, url) {
  fetch(url)
    .then(response => {
      if (!response.ok) throw new Error('Datei nicht gefunden: ' + url);
      return response.text();
    })
    .then(data => document.getElementById(id).innerHTML = data)
    .catch(err => console.error(err));
}

window.addEventListener('DOMContentLoaded', function() {
  includeHTML('site-header', 'header.html');
  includeHTML('site-footer', 'footer.html');
});