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

  /* Safari restores the previous scroll position on reload, and when a
     backgrounded tab is reopened — which lands you mid-page on what feels like
     a fresh visit. Take that over: a bare URL starts at the top, and a URL
     carrying a hash goes to its section because that is what it asked for. */
  if ('scrollRestoration' in history) history.scrollRestoration = 'manual';

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

  /* --- in-page navigation -------------------------------------------------- */
  /* Smooth scrolling travels through every section between here and the target,
     and the observer reveals each one in flight — so the section you asked for
     has finished animating before you arrive, while the one below it is caught
     half-drawn. Handle these jumps explicitly instead: show everything passed
     over without animating it, hold the target back, and reveal it on landing. */
  /* A section's box starts about 130px of padding above its first line of
     content, so scrolling to the box leaves the page looking like it stopped
     short. Aim at the content instead, clearing the sticky header. */
  function navScrollTop(el) {
    var hdr = document.getElementById('hdr');
    var h = hdr ? hdr.getBoundingClientRect().height : 0;
    var wrap = el.querySelector(':scope > .wrap');
    var anchor = (wrap && wrap.firstElementChild) ? wrap.firstElementChild : el;
    return Math.max(0, anchor.getBoundingClientRect().top + window.scrollY - h - 20);
  }

  /* Reveal the target as it comes into view rather than once the scroll has
     fully stopped. The animation then overlaps the tail of the travel instead
     of starting after a dead pause. */
  function revealWhenNear(target, el) {
    var fired = false;
    function show() {
      if (fired) return;
      fired = true;
      target.classList.add('is-nav', 'is-in');
    }
    (function tick() {
      if (fired) return;
      var atEnd = window.innerHeight + window.scrollY >=
                  document.documentElement.scrollHeight - 2;
      if (el.getBoundingClientRect().top < window.innerHeight * 0.7 || atEnd) return show();
      requestAnimationFrame(tick);
    }());
    setTimeout(show, 800);                    // safety net
  }

  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest ? e.target.closest('a[href^="#"]') : null;
    if (!a || a.hasAttribute('data-cal-link')) return;
    var id = a.getAttribute('href').slice(1);
    if (!id) return;
    var el = document.getElementById(id);
    if (!el) return;

    e.preventDefault();
    var target = el.matches('[data-reveal]') ? el : el.closest('[data-reveal]');

    Array.prototype.forEach.call(sections, function (s) {
      if (s !== target && s.offsetTop < el.offsetTop) {
        s.classList.add('no-anim', 'is-in');
        if (io) io.unobserve(s);
      }
    });

    if (target && !reduced) {
      var r = el.getBoundingClientRect();
      var alreadyThere = r.top < window.innerHeight * 0.6 && r.bottom > 0;
      if (!alreadyThere) {
        target.classList.remove('is-in', 'no-anim');
        if (io) io.unobserve(target);
        revealWhenNear(target, el);
      }
    }

    /* Deliberately not writing the hash to the URL. Doing so left whichever
       section you last clicked stuck in the address bar, so returning to the
       site from history reopened it partway down; it also cost a history entry
       per click, making Back walk backwards through sections instead of leaving.
       An inbound link that already carries a hash is still honoured below. */
    window.scrollTo({ top: navScrollTop(el), behavior: reduced ? 'auto' : 'smooth' });
  });

  /* Arriving on a link straight to a section: same problem, same treatment. */
  if (location.hash.length > 1) {
    var landed = document.getElementById(location.hash.slice(1));
    if (landed) {
      Array.prototype.forEach.call(sections, function (s) {
        if (s.offsetTop < landed.offsetTop) {
          s.classList.add('no-anim', 'is-in');
          if (io) io.unobserve(s);
        }
      });
      var settle = function () {
        window.scrollTo({ top: navScrollTop(landed), behavior: 'auto' });
      };
      if (document.fonts && document.fonts.ready) document.fonts.ready.then(settle);
      setTimeout(settle, 350);
    }
  }

  /* --- booking buttons ---------------------------------------------------- */
  /* Each booking button is a real link to the Cal.com page, so a blocked embed
     still gets the visitor to the calendar. Cal opens its own modal on click
     but does not stop the link, so stop it here — only once Cal is loaded, and
     only for a plain left click, so cmd-click still opens a new tab. */
  Array.prototype.forEach.call(document.querySelectorAll('[data-cal-link]'), function (el) {
    el.addEventListener('click', function (e) {
      if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      if (window.Cal && window.Cal.ns && window.Cal.ns.intake) e.preventDefault();
    });
  });

  /* --- the custody plan -------------------------------------------------- */
  var plan = document.getElementById('plan');
  if (!plan) return;

  var CHANNELS = [
    {
      ref: 'Ch. 01 — Phishing',
      read: 'Signing what you did not mean to sign. Checks approvals, addresses, and on-device verification.'
    },
    {
      ref: 'Ch. 02 — Device',
      read: 'Where the wallet is sourced, updated and used. Checks firmware, authenticity, clean signing.'
    },
    {
      ref: 'Ch. 03 — Backup loss',
      read: 'One copy, one location, one point of failure. Checks redundancy, medium, geography, passphrase.'
    },
    {
      ref: 'Ch. 04 — Succession',
      read: 'Nobody else can get in, including those who should. Checks whether recovery is written and tested.'
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
