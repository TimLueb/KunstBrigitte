(function() {
    const images = Array.from(document.querySelectorAll('.gallery img'));
    const lightbox = document.getElementById('lightbox');
    const lightboxImg = lightbox.querySelector('.lightbox-img');
    const closeBtn = lightbox.querySelector('.close');
    const prevBtn = lightbox.querySelector('.prev');
    const nextBtn = lightbox.querySelector('.next');
    const thumbs = lightbox.querySelector('.lightbox-thumbs');
    let current = 0;
    let opener = null;

    // Thumbnails in Lightbox generieren
    function renderThumbs() {
        thumbs.innerHTML = '';
        images.forEach((img, idx) => {
            const thumb = document.createElement('img');
            thumb.src = img.dataset.thumb || img.src;
            thumb.loading = 'lazy';
            thumb.decoding = 'async';
            thumb.width = 54;
            thumb.height = 48;
            thumb.alt = img.alt;
            thumb.tabIndex = 0;
            if (idx === current) thumb.classList.add('active');
            thumb.addEventListener('click', () => showImage(idx));
            thumb.addEventListener('keydown', e => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    showImage(idx);
                }
            });
            thumbs.appendChild(thumb);
        });
    }

    function showImage(idx) {
        current = idx;
        // Full-quality originals are requested only for the selected artwork.
        lightboxImg.src = images[current].dataset.original || images[current].src;
        lightboxImg.alt = images[current].alt;
        Array.from(thumbs.children).forEach((t, i) => {
            t.classList.toggle('active', i === current);
            if (i === current) t.scrollIntoView({ block: 'nearest', inline: 'nearest' });
        });
    }

    function openLightbox(idx) {
        current = idx;
        opener = images[idx];
        lightbox.style.display = 'flex';
        if (!thumbs.children.length) renderThumbs();
        showImage(current);
        document.body.style.overflow = 'hidden';
        setTimeout(() => closeBtn.focus(), 100);
    }

    function closeLightbox() {
        lightbox.style.display = 'none';
        document.body.style.overflow = '';
        if (opener) opener.focus({ preventScroll: true });
    }

    function nextImage() {
        current = (current + 1) % images.length;
        showImage(current);
    }

    function prevImage() {
        current = (current - 1 + images.length) % images.length;
        showImage(current);
    }

    images.forEach((img, idx) => {
        img.addEventListener('click', () => openLightbox(idx));
        img.addEventListener('keydown', e => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                openLightbox(idx);
            }
        });
    });

    closeBtn.addEventListener('click', closeLightbox);
    closeBtn.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') closeLightbox();
    });
    nextBtn.addEventListener('click', nextImage);
    prevBtn.addEventListener('click', prevImage);

    // Tastatursteuerung
    document.addEventListener('keydown', function(e) {
        if (lightbox.style.display === 'flex') {
            if (e.key === 'ArrowRight') { nextImage(); }
            else if (e.key === 'ArrowLeft') { prevImage(); }
            else if (e.key === 'Escape') { closeLightbox(); }
        }
    });

    // Klick außerhalb des Bildes schließt Lightbox
    lightbox.addEventListener('click', function(e) {
        if (e.target === lightbox) closeLightbox();
    });
})();
