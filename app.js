/* ════════════════════════════════════════════════════════════════
   mBrothers — interaction engine  (Frente A: "living hero")
   ────────────────────────────────────────────────────────────────
   • Pointer parallax 3D on the planetary stage
   • Drag-to-rotate the planet, with release momentum + return-to-base
   • Real telemetry bound to the live simulation (clock, FPS, uptime,
     rotation rad/s, moon distance, surface temp)
   • CRT phosphor terminal (state machine, loops the boot sequence)
   All vanilla. No dependencies. Honours prefers-reduced-motion.
   ════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  /* Motion preference resolution:
       OS prefers-reduced-motion is the default, but an in-page toggle lets the
       visitor force 'full' (override the OS) or 'calm'. Choice persists. */
  var prefersReduce = !!(window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  var motionPref = null;
  try { motionPref = localStorage.getItem('mb-motion'); } catch (e) {}   // 'full' | 'calm' | null
  if (motionPref === 'full') document.documentElement.classList.add('motion-full');
  var reduce = motionPref === 'full' ? false
             : motionPref === 'calm' ? true
             : prefersReduce;

  /* ── tiny helpers ───────────────────────────────────────────── */
  var $ = function (id) { return document.getElementById(id); };
  function clamp(v, lo, hi) { return v < lo ? lo : (v > hi ? hi : v); }
  function mod(a, n) { return ((a % n) + n) % n; }
  function pad2(n) { return (n < 10 ? '0' : '') + n; }
  function setText(el, s) { if (el && el.textContent !== s) el.textContent = s; }

  /* ════════════════ CRT TERMINAL ════════════════ */
  function initTerminal() {
    var el = $('crtLines');
    if (!el) return;

    var sequence = [
      { type: 'type', prompt: true,  text: 'deploy mBrothers --mode=orbital',      speed: 55 },
      { type: 'wait', ms: 420 },
      { type: 'line' },
      { type: 'type', prompt: false, text: 'Developing practical solutions for small planetary systems', speed: 42 },
      { type: 'wait', ms: 1400 },
      { type: 'line' },
      { type: 'type', prompt: true,  text: 'ping orbital-relay --signal stable',  speed: 50 },
      { type: 'wait', ms: 380 },
      { type: 'line' },
      { type: 'type', prompt: false, text: 'reply from 38.7°N · 9.1°W : 4ms', speed: 28, muted: true },
      { type: 'wait', ms: 900 },
      { type: 'line' },
      { type: 'type', prompt: true,  text: 'sys.handshake --listen',  speed: 50 },
      { type: 'wait', ms: 320 },
      { type: 'line' },
      { type: 'type', prompt: false, text: 'all systems nominal · standing by.', speed: 30, muted: true },
      { type: 'wait', ms: 1800 },
      { type: 'clear' },
      { type: 'wait', ms: 600 }
    ];

    var MAX_LINES = 3;
    var lines = [];
    var cursor = null;

    function newLine(promptOn, mutedOn) {
      var line = document.createElement('div');
      line.className = 'crt-line';
      if (promptOn) {
        var p = document.createElement('span');
        p.className = 'prompt';
        p.textContent = '> ';
        line.appendChild(p);
      }
      var text = document.createElement('span');
      if (mutedOn) text.className = 'muted';
      line.appendChild(text);

      if (cursor && cursor.parentNode) cursor.parentNode.removeChild(cursor);
      cursor = document.createElement('span');
      cursor.className = 'crt-cursor';
      line.appendChild(cursor);

      el.appendChild(line);
      lines.push({ line: line, text: text });
      while (lines.length > MAX_LINES) lines.shift().line.remove();
      return text;
    }
    function clearAll() {
      lines.forEach(function (l) { l.line.remove(); });
      lines = [];
      if (cursor && cursor.parentNode) cursor.parentNode.removeChild(cursor);
    }
    function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
    function typeText(target, str, speed) {
      var i = 0;
      return new Promise(function (resolve) {
        (function step() {
          if (i >= str.length) return resolve();
          target.textContent += str[i++];
          if (cursor && target.nextSibling !== cursor) target.parentNode.appendChild(cursor);
          setTimeout(step, speed + Math.random() * 30);
        })();
      });
    }
    // Easter egg: rotate the deploy flag each loop (orbital → quiet → …).
    var MODES = ['orbital', 'quiet', 'patient', 'lighthouse', 'slow'];
    var modeIdx = 0;

    async function runLoop() {
      while (true) {
        sequence[0].text = 'deploy mBrothers --mode=' + MODES[modeIdx++ % MODES.length];
        for (var k = 0; k < sequence.length; k++) {
          var step = sequence[k];
          if (step.type === 'type') {
            await typeText(newLine(step.prompt, step.muted), step.text, step.speed);
          } else if (step.type === 'wait') {
            await sleep(step.ms);
          } else if (step.type === 'clear') {
            clearAll();
          }
        }
      }
    }

    // The phosphor terminal is the heart of the page — keep it typing even in
    // calm/reduced mode (letter-by-letter text is mild, non-vestibular motion).
    runLoop();
  }

  /* ════════════════ STAGE: parallax + drag + telemetry ════════════════ */
  function initStage() {
    var hero       = document.querySelector('header.hero');
    var stage      = document.querySelector('.stage');
    var planetWrap = document.querySelector('.planet-wrap');
    var surface    = document.querySelector('.planet .surface');
    var clouds     = document.querySelector('.planet .clouds');
    var moonOrbit  = document.querySelector('.moon-orbit');
    var highlight  = document.querySelector('.planet .highlight');
    var stars      = document.querySelector('.stage .stars');
    var nebula     = document.querySelector('.stage .nebula');
    if (!stage || !planetWrap || !surface) return;

    /* telemetry nodes */
    var elClock = $('utcClock'), elRec = $('recTimer'), elDist = $('distAU'),
        elRot = $('rot'), elTemp = $('temp'), elFps = $('fps'), elUptime = $('uptime');

    /* simulation constants */
    var BASE     = 1 / 80;        // planet revolutions per second (base spin)
    var CLOUD_K  = 80 / 120;      // clouds run at 2/3 the planet's rate (parallax)
    var MOON     = 1 / 30;        // moon orbital revolutions per second
    var SPAN     = 200 / 3;       // 66.666% — the seamless-loop shift of the strip
    var SENS     = 0.0014;        // turns per pixel of drag
    var TILT     = 9;             // max parallax tilt (deg)

    /* ── reduced motion: stay alive, just calmer ──
       Keep a gentle ambient rotation (a slow, distant planet spin is
       non-vestibular) and the live clock, but drop the parallax tilt and the
       entrance zoom. The jarring CSS effects (scanbeam, shooting star,
       twinkle, CRT flicker, blinking dots) are already off via the global
       reduced-motion rule. Drag stays — it is user-initiated motion. */
    if (reduce) TILT = 0;

    /* ── state ── */
    var phase = 0, cloudPhase = -0.15, moonPhase = 0;  // cloudPhase offset ≈ original -10%
    var vel = BASE;                 // current spin (turns/s)
    var dragging = false, lastX = 0, lastT = 0, instVel = BASE;
    var targetMX = 0, targetMY = 0, mx = 0, my = 0;     // pointer, normalised + smoothed
    var intro = reduce ? 1 : 0;     // 0→1 entrance ease (no zoom under reduced motion)
    var touched = false;
    function markTouched() {
      if (touched) return;
      touched = true;
      stage.classList.add('touched');
    }

    /* ── pointer parallax over the hero (skipped under reduced motion) ── */
    if (!reduce) {
      hero.addEventListener('pointermove', function (e) {
        var r = stage.getBoundingClientRect();
        targetMX = clamp((e.clientX - (r.left + r.width / 2)) / (r.width / 2), -1, 1);
        targetMY = clamp((e.clientY - (r.top + r.height / 2)) / (r.height / 2), -1, 1);
      });
      hero.addEventListener('pointerleave', function () {
        targetMX = 0; targetMY = 0;
      });
    }

    /* ── drag-to-rotate the planet ── */
    planetWrap.addEventListener('pointerdown', function (e) {
      dragging = true;
      markTouched();
      planetWrap.classList.add('dragging');
      lastX = e.clientX;
      lastT = performance.now() / 1000;
      if (planetWrap.setPointerCapture) {
        try { planetWrap.setPointerCapture(e.pointerId); } catch (err) {}
      }
      e.preventDefault();
    });
    planetWrap.addEventListener('pointermove', function (e) {
      if (!dragging) return;
      var now = performance.now() / 1000;
      var dt2 = Math.max(1 / 200, now - lastT);
      var dphi = (e.clientX - lastX) * SENS;
      phase += dphi;
      cloudPhase += dphi * CLOUD_K;
      instVel = clamp(dphi / dt2, -3, 3);
      lastX = e.clientX; lastT = now;
    });
    function endDrag() {
      if (!dragging) return;
      dragging = false;
      planetWrap.classList.remove('dragging');
      vel = instVel;                // release with momentum; loop eases it back to BASE
    }
    planetWrap.addEventListener('pointerup', endDrag);
    planetWrap.addEventListener('pointercancel', endDrag);

    /* ── Easter egg: Konami code → "engage the engines" (spin impulse) ── */
    var konami = ['arrowup','arrowup','arrowdown','arrowdown','arrowleft','arrowright','arrowleft','arrowright','b','a'];
    var kpos = 0;
    window.addEventListener('keydown', function (e) {
      var k = (e.key || '').toLowerCase();
      kpos = (k === konami[kpos]) ? kpos + 1 : (k === konami[0] ? 1 : 0);
      if (kpos === konami.length) {
        kpos = 0;
        vel = 3.2;                         // big spin; friction eases it back to base
        document.documentElement.classList.add('warp');
        setTimeout(function () { document.documentElement.classList.remove('warp'); }, 1400);
      }
    });

    /* ── telemetry throttle + fps ── */
    var t0 = performance.now() / 1000;
    var telAcc = 0, fpsAcc = 0, fpsFrames = 0, fps = 60;

    /* ── main loop ── */
    var last = performance.now() / 1000;
    function frame(nowMs) {
      var now = nowMs / 1000;
      var dt = clamp(now - last, 0, 0.05);
      last = now;

      // entrance ease
      if (intro < 1) intro = clamp(intro + dt / 1.1, 0, 1);

      // smoothed pointer
      var k = Math.min(1, dt * 6);
      mx += (targetMX - mx) * k;
      my += (targetMY - my) * k;

      // spin integration (drag handles its own advance in pointermove)
      if (!dragging) {
        vel += (BASE - vel) * Math.min(1, dt * 1.2);   // friction → return to base
        phase += vel * dt;
        cloudPhase += vel * CLOUD_K * dt;
      }
      moonPhase += MOON * dt;

      // strip transforms
      surface.style.transform = 'translateX(' + (-mod(phase, 1) * SPAN) + '%)';
      clouds.style.transform  = 'translateX(' + (-(10 + mod(cloudPhase, 1) * SPAN)) + '%)';
      if (moonOrbit) moonOrbit.style.transform = 'rotate(' + (moonPhase * 360) + 'deg)';

      // parallax / tilt
      var tilt = TILT * intro;
      var sc = 0.965 + 0.035 * intro;
      planetWrap.style.transform =
        'scale(' + sc + ') rotateY(' + (mx * tilt) + 'deg) rotateX(' + (-my * tilt) + 'deg)';
      if (stars)  stars.style.transform  = 'translate(' + (-mx * 16) + 'px,' + (-my * 16) + 'px)';
      if (nebula) nebula.style.transform = 'rotate(-15deg) translate(' + (-mx * 24) + 'px,' + (-my * 24) + 'px)';
      if (highlight) highlight.style.transform = 'translate(' + (mx * 14) + 'px,' + (my * 14) + 'px)';

      // fps
      fpsFrames++; fpsAcc += dt;
      if (fpsAcc >= 0.5) { fps = Math.round(fpsFrames / fpsAcc); fpsFrames = 0; fpsAcc = 0; }

      // telemetry (~8 Hz)
      telAcc += dt;
      if (telAcc >= 0.12) {
        telAcc = 0;
        var elapsed = now - t0;
        var mm = Math.floor(elapsed / 60), ss = Math.floor(elapsed % 60);
        var stamp = pad2(mm) + ':' + pad2(ss);
        var d = new Date();
        setText(elClock, pad2(d.getUTCHours()) + ':' + pad2(d.getUTCMinutes()) + ':' + pad2(d.getUTCSeconds()) + ' UTC');
        setText(elRec, stamp);
        setText(elUptime, stamp);
        setText(elFps, String(fps));
        var curVel = dragging ? instVel : vel;
        setText(elRot, (Math.abs(curVel) * 2 * Math.PI).toFixed(3));
        setText(elDist, (0.0021 + 0.0009 * Math.cos(moonPhase * 2 * Math.PI)).toFixed(4));
        setText(elTemp, '+' + Math.round(286 + 2 * Math.sin(now * 0.4)));
      }

      requestAnimationFrame(frame);
    }

    /* Hand control from the CSS fallback animations to this engine — done as
       the very last step so any earlier failure leaves the fallback running. */
    document.documentElement.classList.add('js-driving');
    requestAnimationFrame(frame);
  }

  /* ── motion toggle ── */
  function initMotionToggle() {
    var btn = $('motionToggle');
    if (!btn) return;
    // Only surface the toggle when it's meaningful: the OS asks for reduced
    // motion, or the visitor previously set an explicit preference.
    if (!prefersReduce && !motionPref) return;

    btn.hidden = false;
    btn.textContent = reduce ? '▸ full motion' : 'motion · full';
    btn.setAttribute('aria-pressed', reduce ? 'false' : 'true');
    btn.title = reduce
      ? 'Enable the full animated experience (overrides the system setting)'
      : 'Full motion on — click to follow the system setting again';

    btn.addEventListener('click', function () {
      try {
        if (reduce) localStorage.setItem('mb-motion', 'full');  // force full
        else localStorage.removeItem('mb-motion');              // back to system default
      } catch (e) {}
      location.reload();
    });
  }

  /* ── boot sequence overlay ── */
  function initBoot() {
    var root = document.documentElement;
    if (!root.classList.contains('booting')) return;
    var boot = $('boot'), log = $('bootLog');
    if (!boot || !log) { root.classList.remove('booting'); return; }

    var lines = [
      ['> initializing subsystems', 'ok'],
      ['> establishing orbital relay', 'ok'],
      ['> calibrating telemetry array', 'ok'],
      ['> rendering planetary stage', 'ok'],
      ['> sys.handshake --listen', 'signal acquired']
    ];
    var done = false;
    function sleepB(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
    function finish() {
      if (done) return;
      done = true;
      boot.classList.add('done');
      var gone = function () { if (boot && boot.parentNode) boot.remove(); root.classList.remove('booting'); };
      boot.addEventListener('animationend', gone);
      setTimeout(gone, 650);
    }
    boot.addEventListener('click', finish);
    window.addEventListener('keydown', function once() { window.removeEventListener('keydown', once); finish(); });

    (async function () {
      for (var i = 0; i < lines.length && !done; i++) {
        log.textContent += lines[i][0];
        for (var d = 0; d < 4 && !done; d++) { await sleepB(55); log.textContent += '.'; }
        await sleepB(90);
        log.textContent += ' ' + lines[i][1] + '\n';
        await sleepB(150);
      }
      await sleepB(360);
      finish();
    })();
  }

  /* ── canvas starfield (depth + drift behind the planet) ── */
  function initStarfield() {
    if (reduce) return;
    var cv = $('starfield');
    if (!cv || !cv.getContext) return;
    var ctx = cv.getContext('2d');
    var DPR = Math.min(2, window.devicePixelRatio || 1);
    var stars = [], cw = 0, ch = 0;

    function seed() {
      var r = cv.getBoundingClientRect();
      cw = r.width; ch = r.height;
      cv.width = Math.max(1, Math.round(cw * DPR));
      cv.height = Math.max(1, Math.round(ch * DPR));
      ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
      var n = Math.max(40, Math.min(160, Math.round(cw * ch / 7000)));
      stars = [];
      for (var i = 0; i < n; i++) {
        stars.push({
          x: Math.random() * cw, y: Math.random() * ch,
          z: Math.random() * 0.8 + 0.2,            // depth 0.2..1
          ph: Math.random() * 6.283                 // twinkle phase
        });
      }
    }

    var last = 0, t = 0;
    function frame(nowMs) {
      var now = nowMs / 1000;
      var dt = Math.min(0.05, now - last || 0); last = now; t += dt;
      ctx.clearRect(0, 0, cw, ch);
      for (var i = 0; i < stars.length; i++) {
        var s = stars[i];
        s.x += s.z * 3.2 * dt;                      // nearer stars drift faster
        if (s.x > cw + 2) { s.x = -2; s.y = Math.random() * ch; }
        var tw = 0.55 + 0.45 * Math.sin(t * 1.4 + s.ph);
        var a = (0.25 + s.z * 0.6) * tw;
        var rad = s.z * 1.4;
        ctx.beginPath();
        ctx.fillStyle = 'rgba(244,236,216,' + a.toFixed(3) + ')';
        ctx.arc(s.x, s.y, rad, 0, 6.283);
        ctx.fill();
      }
      requestAnimationFrame(frame);
    }

    seed();
    var rt;
    window.addEventListener('resize', function () { clearTimeout(rt); rt = setTimeout(seed, 200); });
    requestAnimationFrame(frame);
  }

  /* ── day / night theme ── */
  function initTheme() {
    var btn = $('themeToggle');
    if (!btn) return;
    var meta = document.querySelector('meta[name="theme-color"]');
    function paint() {
      var night = document.documentElement.classList.contains('night');
      btn.textContent = night ? '☀' : '☾';
      btn.setAttribute('aria-pressed', night ? 'true' : 'false');
      if (meta) meta.setAttribute('content', night ? '#0c0f17' : '#f4ecd8');
    }
    paint();
    var root = document.documentElement;
    var themingTimer;
    btn.addEventListener('click', function () {
      // engage the slow crossfade (dusk/dawn), then flip the theme
      root.classList.add('theming');
      void root.offsetWidth;                       // force a reflow so the swap animates
      var night = root.classList.toggle('night');
      try { localStorage.setItem('mb-theme', night ? 'night' : 'day'); } catch (e) {}
      paint();
      clearTimeout(themingTimer);
      themingTimer = setTimeout(function () { root.classList.remove('theming'); }, 1900);
    });
  }

  /* ── product cards: cursor spotlight + subtle 3D tilt ── */
  function initCards() {
    if (reduce) return;                      // tilt is motion; calm mode skips it
    var cards = document.querySelectorAll('article.product:not(.placeholder)');
    Array.prototype.forEach.call(cards, function (card) {
      card.addEventListener('pointermove', function (e) {
        var r = card.getBoundingClientRect();
        var px = (e.clientX - r.left) / r.width;
        var py = (e.clientY - r.top) / r.height;
        card.style.setProperty('--gx', (px * 100).toFixed(1) + '%');
        card.style.setProperty('--gy', (py * 100).toFixed(1) + '%');
        card.style.setProperty('--glow', '0.13');
        card.style.transform =
          'rotateX(' + ((0.5 - py) * 5).toFixed(2) + 'deg) rotateY(' + ((px - 0.5) * 5).toFixed(2) + 'deg)';
      });
      card.addEventListener('pointerleave', function () {
        card.style.setProperty('--glow', '0');
        card.style.transform = '';
      });
    });
  }

  /* ── service worker (offline support; network-first keeps versions honest) ── */
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('sw.js').catch(function () {});
    });
  }

  /* ── boot ── */
  function boot() {
    // Liveness + version marker: confirms JS actually executed, and which build.
    var b = $('buildTag');
    if (b) {
      b.textContent = b.getAttribute('data-build') + (reduce ? ' · JS ✓ (calm)' : ' · JS ✓');
      b.classList.add('ok');
    }
    initBoot();
    initTheme();
    initMotionToggle();
    initCards();
    initStarfield();
    initTerminal();
    initStage();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
