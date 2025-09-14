function initBurgerMenu() {
  const burger = document.getElementById('burger-menu');
  const nav = document.querySelector('.main-nav');
  if (!burger || !nav) return;

  function checkWidth() {
    if (window.innerWidth <= 800) {
      burger.style.display = 'block';
      nav.style.display = 'none';
    } else {
      burger.style.display = 'none';
      nav.style.display = 'flex';
    }
  }

  burger.addEventListener('click', function() {
    if (nav.style.display === 'none' || nav.style.display === '') {
      nav.style.display = 'flex';
    } else {
      nav.style.display = 'none';
    }
  });

  window.addEventListener('resize', checkWidth);
  checkWidth();
}

window.addEventListener('DOMContentLoaded', function() {
  // Warte, bis der Header geladen ist
  const headerCheck = setInterval(() => {
    if (document.getElementById('burger-menu')) {
      clearInterval(headerCheck);
      initBurgerMenu();
    }
  }, 50);
});