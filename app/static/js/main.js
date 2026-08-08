/* ═══════════════════════════════════
   GreenProof — Home Page JS
   1. Leaf particle canvas (hero + CTA)
   2. Navbar scroll shadow
   3. Scroll-triggered fade-in
═══════════════════════════════════ */

/* ── 1. Leaf / particle canvas (reusable) ── */
function initLeafCanvas(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  let W, H, particles;

  const COLORS = [
    'rgba(62, 207, 142, 0.65)',
    'rgba(62, 207, 142, 0.38)',
    'rgba(255, 255, 255, 0.15)',
    'rgba(100, 220, 160, 0.45)',
    'rgba(46, 180, 120, 0.3)',
  ];

  function resize() {
    W = canvas.width  = canvas.offsetWidth;
    H = canvas.height = canvas.offsetHeight;
  }

  function randomBetween(a, b) {
    return a + Math.random() * (b - a);
  }

  function createParticle(fromBottom) {
    return {
      x:      randomBetween(0, W),
      y:      fromBottom ? randomBetween(H * 0.2, H) : H + 10,
      r:      randomBetween(1.8, 5),
      speed:  randomBetween(0.3, 1.0),
      drift:  randomBetween(-0.3, 0.3),
      color:  COLORS[Math.floor(Math.random() * COLORS.length)],
      angle:  randomBetween(0, Math.PI * 2),
      spin:   randomBetween(-0.015, 0.015),
      shape:  Math.random() > 0.45 ? 'leaf' : 'circle',
    };
  }

  function initParticles() {
    const count = Math.min(Math.floor(W / 10), 95);
    particles = Array.from({ length: count }, () => createParticle(true));
  }

  function drawLeaf(ctx, p) {
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.rotate(p.angle);
    ctx.beginPath();
    ctx.moveTo(0, -p.r * 2);
    ctx.bezierCurveTo( p.r * 1.2, -p.r,  p.r * 1.2, p.r,  0, p.r * 2);
    ctx.bezierCurveTo(-p.r * 1.2,  p.r, -p.r * 1.2, -p.r, 0, -p.r * 2);
    ctx.fillStyle = p.color;
    ctx.fill();
    ctx.restore();
  }

  function drawCircle(ctx, p) {
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
    ctx.fillStyle = p.color;
    ctx.fill();
  }

  function step() {
    ctx.clearRect(0, 0, W, H);

    for (const p of particles) {
      p.y -= p.speed;
      p.x += p.drift;
      p.angle += p.spin;

      if (p.y < -20 || p.x < -20 || p.x > W + 20) {
        Object.assign(p, createParticle(false));
      }

      if (p.shape === 'leaf') {
        drawLeaf(ctx, p);
      } else {
        drawCircle(ctx, p);
      }
    }

    requestAnimationFrame(step);
  }

  function init() {
    resize();
    initParticles();
    step();
  }

  window.addEventListener('resize', () => {
    resize();
    initParticles();
  });

  init();
}

/* Boot both canvases */
initLeafCanvas('leaf-canvas');
initLeafCanvas('cta-canvas');


/* ── 2. Navbar scroll shadow ── */
(function initNavbar() {
  const navbar = document.querySelector('.navbar');
  if (!navbar) return;

  function onScroll() {
    if (window.scrollY > 12) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
  }

  window.addEventListener('scroll', onScroll, { passive: true });
})();


/* ── 3. Scroll-triggered fade-in ── */
(function initFadeIn() {
  const targets = document.querySelectorAll('.feature-card, .features-header, .cta-inner');

  if (!('IntersectionObserver' in window)) {
    targets.forEach(el => el.classList.add('visible'));
    return;
  }

  targets.forEach(el => el.classList.add('fade-up'));

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12 }
  );

  targets.forEach(el => observer.observe(el));
})();


/* ── 4. Auto-dismiss flash messages (inherited from main.js) ── */
document.addEventListener('DOMContentLoaded', () => {
  const flashes = document.querySelectorAll('.flash');
  flashes.forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity 0.4s';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 400);
    }, 4000);
  });
});