/* KeyCompass — site behaviour.
   Three jobs: the load sequence, the scroll reveals, and the custody plan. */
(function () {
  'use strict';

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* --- year -------------------------------------------------------------- */
  var yr = document.getElementById('yr');
  if (yr) yr.textContent = new Date().getFullYear();

  /* --- load sequence ----------------------------------------------------- */
  function start() { document.body.classList.add('is-ready'); }
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(start);
    setTimeout(start, 900); // never wait on a slow font
  } else {
    start();
  }

  /* --- sticky header ----------------------------------------------------- */
  var hdr = document.getElementById('hdr');
  if (hdr) {
    var stuck = false;
    var onScroll = function () {
      var next = window.scrollY > 8;
      if (next !== stuck) { stuck = next; hdr.classList.toggle('is-stuck', stuck); }
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* --- scroll reveals ---------------------------------------------------- */
  var sections = document.querySelectorAll('[data-reveal]');
  if (!('IntersectionObserver' in window) || reduced) {
    Array.prototype.forEach.call(sections, function (s) { s.classList.add('is-in'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); }
      });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.08 });
    Array.prototype.forEach.call(sections, function (s) { io.observe(s); });
  }

  /* --- the custody plan -------------------------------------------------- */
  var plan = document.getElementById('plan');
  if (!plan) return;

  var CHANNELS = [
    {
      ref: 'Ch. 01 — Phishing',
      read: 'Signing something you did not mean to sign. Checked: on-device verification, address handling, approval hygiene.'
    },
    {
      ref: 'Ch. 02 — Device',
      read: 'Where the wallet is sourced, updated, and used. Checked: firmware and authenticity, a clean signing environment, what else runs on that machine.'
    },
    {
      ref: 'Ch. 03 — Backup loss',
      read: 'One copy, one location, one point of failure. Checked: how many backups exist, what they are made of, where they live, and how the passphrase is held.'
    },
    {
      ref: 'Ch. 04 — Succession',
      read: 'Nobody else can get in, including the people who should be able to. Checked: whether a recovery route exists, is written down, and has ever been tested by someone other than you.'
    }
  ];

  var DEFAULT_REF = 'Rev A · N.T.S.';
  var DEFAULT_READ = 'Four ways a setup fails. A review checks all four. <span class="tblock__hint">Hover a channel.</span>';

  var chs = plan.querySelectorAll('.ch');
  var refEl = document.getElementById('plan-ref');
  var readEl = document.getElementById('plan-read');
  var pinned = -1;

  function paint(i) {
    Array.prototype.forEach.call(chs, function (c, n) {
      c.classList.toggle('is-on', n === i);
      c.setAttribute('aria-pressed', String(n === pinned));
    });
    if (i < 0) {
      refEl.textContent = DEFAULT_REF;
      readEl.innerHTML = DEFAULT_READ;
    } else {
      refEl.textContent = CHANNELS[i].ref;
      readEl.textContent = CHANNELS[i].read;
    }
  }

  Array.prototype.forEach.call(chs, function (ch, i) {
    ch.addEventListener('mouseenter', function () { paint(i); });
    ch.addEventListener('mouseleave', function () { paint(pinned); });
    ch.addEventListener('focus', function () { paint(i); });
    ch.addEventListener('blur', function () { paint(pinned); });
    ch.addEventListener('click', function () {
      pinned = pinned === i ? -1 : i;
      paint(pinned);
    });
    ch.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar') {
        e.preventDefault();
        pinned = pinned === i ? -1 : i;
        paint(pinned);
      }
    });
  });
}());
