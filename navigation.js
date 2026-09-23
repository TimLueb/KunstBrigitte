function initNavigation() {
  const nav = document.querySelector('.site-nav');
  if (!nav || nav.dataset.ready) return;
  nav.dataset.ready = 'true';
  const burger = nav.querySelector('#burger-menu');
  const mobile = window.matchMedia('(max-width: 1100px)');
  const toggles = Array.from(nav.querySelectorAll('.submenu-toggle'));

  function closeSubmenus(except) {
    toggles.forEach(button => {
      if (button === except) return;
      button.setAttribute('aria-expanded', 'false');
      document.getElementById(button.getAttribute('aria-controls')).hidden = true;
    });
  }
  function closeMenu() {
    burger.setAttribute('aria-expanded', 'false');
    nav.classList.remove('is-open');
    closeSubmenus();
  }
  burger.addEventListener('click', () => {
    const open = burger.getAttribute('aria-expanded') !== 'true';
    burger.setAttribute('aria-expanded', String(open));
    nav.classList.toggle('is-open', open);
    if (!open) closeSubmenus();
  });
  toggles.forEach(button => button.addEventListener('click', () => {
    const open = button.getAttribute('aria-expanded') !== 'true';
    closeSubmenus(button);
    button.setAttribute('aria-expanded', String(open));
    document.getElementById(button.getAttribute('aria-controls')).hidden = !open;
  }));
  nav.addEventListener('keydown', event => {
    if (event.key !== 'Escape') return;
    const expanded = toggles.find(button => button.getAttribute('aria-expanded') === 'true');
    if (expanded) {
      closeSubmenus();
      expanded.focus();
    } else if (mobile.matches && nav.classList.contains('is-open')) {
      closeMenu();
      burger.focus();
    }
  });
  nav.addEventListener('click', event => {
    if (event.target.closest('a')) closeMenu();
  });
  document.addEventListener('click', event => {
    if (!nav.contains(event.target)) closeMenu();
  });
  nav.addEventListener('focusout', event => {
    if (!nav.contains(event.relatedTarget)) closeMenu();
  });
  mobile.addEventListener('change', () => {
    const focused = document.activeElement;
    const hadFocus = nav.contains(focused);
    closeMenu();
    if (hadFocus) {
      (mobile.matches ? burger : nav.querySelector('.main-nav > li > a')).focus();
    }
  });
}
document.addEventListener('site:included', initNavigation);
document.addEventListener('DOMContentLoaded', initNavigation);
initNavigation();
