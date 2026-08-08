/* ============================================
GreenProof — Shared notification system
Persists pending card-generation jobs and
completed notifications across page loads via
localStorage, and polls the backend for status.
Include this script on any page with the
notification bell (dashboard, profile, etc).
============================================ */

(function(){
  const PENDING_KEY = 'greenproof-pending-cards';
  const NOTIF_KEY = 'greenproof-notifications';
  const POLL_INTERVAL = 4000;

  function getPending(){
    try{ return JSON.parse(localStorage.getItem(PENDING_KEY)) || []; }
    catch(e){ return []; }
  }
  function setPending(list){
    localStorage.setItem(PENDING_KEY, JSON.stringify(list));
  }
  function getNotifications(){
    try{ return JSON.parse(localStorage.getItem(NOTIF_KEY)) || []; }
    catch(e){ return []; }
  }
  function setNotifications(list){
    localStorage.setItem(NOTIF_KEY, JSON.stringify(list));
    renderNotifications();
  }

  function addNotification(notif){
    const list = getNotifications();
    list.unshift(notif);
    setNotifications(list.slice(0, 20)); // cap history
  }

  function markAllRead(){
    const list = getNotifications().map(n => ({...n, read:true}));
    setNotifications(list);
  }

  function renderNotifications(){
    const badge = document.getElementById('notifBadge');
    const list = document.getElementById('notifList');
    const empty = document.getElementById('notifEmpty');
    if(!badge || !list) return;

    const notifs = getNotifications();
    const unread = notifs.filter(n => !n.read).length;

    if(unread > 0){
      badge.textContent = unread > 9 ? '9+' : unread;
      badge.style.display = 'flex';
    } else {
      badge.style.display = 'none';
    }

    list.innerHTML = '';
    if(notifs.length === 0){
      empty.style.display = 'flex';
      return;
    }
    empty.style.display = 'none';

    notifs.forEach(n => {
      const item = document.createElement('a');
      item.href = n.link || '#';
      item.className = 'notif-item' + (n.read ? '' : ' notif-item--unread');
      item.innerHTML = `
        <span class="notif-icon">${n.icon || '🌿'}</span>
        <div class="notif-body">
          <span class="notif-title">${n.title}</span>
          <span class="notif-time">${timeAgo(n.createdAt)}</span>
        </div>
      `;
      list.appendChild(item);
    });
  }

  function timeAgo(ts){
    const diff = Math.floor((Date.now() - ts) / 1000);
    if(diff < 60) return 'Just now';
    if(diff < 3600) return Math.floor(diff/60) + 'm ago';
    if(diff < 86400) return Math.floor(diff/3600) + 'h ago';
    return Math.floor(diff/86400) + 'd ago';
  }

  /* ── Card generation flow ──
     Generation itself runs synchronously on the server (it waits on the
     Ollama call), so there is no separate "status" endpoint to poll — the
     fetch() response IS the result. We still track an in-flight job in
     localStorage so the button stays disabled/labelled correctly if the
     user navigates to another GreenProof page (dashboard <-> profile)
     while the request is running. */

  function startCardGeneration(productId, productName, endpoints){
    const pending = getPending();
    if(pending.some(p => p.productId === productId)) return; // already in progress
    pending.push({ productId, productName, startedAt: Date.now() });
    setPending(pending);

    updateGenerateButton(productId, 'pending');
    runGeneration(productId, productName, endpoints);
  }

  function runGeneration(productId, productName, endpoints){
    fetch(endpoints.start(productId), {
      method: 'POST',
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
      .then(res => res.json().then(data => ({ ok: res.ok, data })))
      .then(({ ok, data }) => {
        if(ok && data.status === 'ready'){
          completeCardGeneration(productId, productName, data.url);
        } else {
          failCardGeneration(productId, productName, data.message || 'Card generation failed.');
        }
      })
      .catch(() => {
        failCardGeneration(productId, productName, 'Could not reach the server. Check your connection and try again.');
      });
  }

  function completeCardGeneration(productId, productName, url){
    const pending = getPending().filter(p => p.productId !== productId);
    setPending(pending);

    addNotification({
      id: 'card-' + productId + '-' + Date.now(),
      title: `Card is ready — ${productName}`,
      link: url,
      icon: '✅',
      read: false,
      createdAt: Date.now()
    });

    updateGenerateButton(productId, 'ready', url);
    showToast(`Card is ready for "${productName}"`, url, 'success');
  }

  function failCardGeneration(productId, productName, message){
    const pending = getPending().filter(p => p.productId !== productId);
    setPending(pending);

    addNotification({
      id: 'card-error-' + productId + '-' + Date.now(),
      title: `Card generation failed — ${productName}`,
      link: '#',
      icon: '⚠️',
      read: false,
      createdAt: Date.now()
    });

    updateGenerateButton(productId, 'error');
    showToast(message, null, 'error');
  }

  function updateGenerateButton(productId, state, url){
    const btn = document.querySelector(`[data-generate-card="${productId}"]`);
    if(!btn) return; // user may have navigated away — notification still fires
    if(state === 'pending'){
      btn.disabled = true;
      btn.classList.remove('btn-generate--ready', 'btn-generate--error');
      btn.classList.add('btn-generate--pending');
      btn.innerHTML = '<span class="btn-generate-spinner"></span> Generating…';
    } else if(state === 'ready'){
      btn.disabled = false;
      btn.classList.remove('btn-generate--pending', 'btn-generate--error');
      btn.classList.add('btn-generate--ready');
      btn.innerHTML = 'View card →';
      btn.onclick = (e) => { e.stopPropagation(); window.location.href = url; };
    } else if(state === 'error'){
      btn.disabled = false;
      btn.classList.remove('btn-generate--pending', 'btn-generate--ready');
      btn.classList.add('btn-generate--error');
      btn.innerHTML = 'Retry generation';
      btn.onclick = null;
    }
  }

  function showToast(message, url, kind){
    const toast = document.createElement('div');
    toast.className = 'gp-toast' + (kind === 'error' ? ' gp-toast--error' : '');
    toast.innerHTML = `
      <span class="gp-toast-icon">${kind === 'error' ? '⚠️' : '✅'}</span>
      <span class="gp-toast-text">${message}</span>
      ${url ? `<a href="${url}" class="gp-toast-link">View</a>` : ''}
    `;
    document.body.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('gp-toast--visible'));
    setTimeout(() => {
      toast.classList.remove('gp-toast--visible');
      setTimeout(() => toast.remove(), 300);
    }, 6000);
  }

  /* ── Resume any job still marked in-flight after a page navigation ── */
  function resumePendingJobs(endpoints){
    getPending().forEach(p => {
      // Generation is a single synchronous request — if we're loading a
      // fresh page and a job is still marked pending, the original
      // request either already finished (tab was reloaded) or was lost
      // (browser closed mid-request). Either way there's nothing left to
      // poll, so just clear the stale flag instead of hanging forever.
      const stale = Date.now() - p.startedAt > POLL_INTERVAL;
      if(stale){
        setPending(getPending().filter(x => x.productId !== p.productId));
        updateGenerateButton(p.productId, 'error');
      } else {
        updateGenerateButton(p.productId, 'pending');
      }
    });
  }

  /* ── Bell dropdown toggle ── */
  function initBell(){
    const trigger = document.getElementById('notifTrigger');
    const menu = document.getElementById('notifMenu');
    if(!trigger || !menu) return;

    trigger.addEventListener('click', () => {
      const open = menu.classList.toggle('open');
      trigger.setAttribute('aria-expanded', open);
      if(open) markAllRead();
    });
    document.addEventListener('click', (e) => {
      if(!trigger.contains(e.target) && !menu.contains(e.target)){
        menu.classList.remove('open');
        trigger.setAttribute('aria-expanded', 'false');
      }
    });
  }

  window.GreenProofNotifications = {
    init(endpoints){
      initBell();
      renderNotifications();
      resumePendingJobs(endpoints);
    },
    startCardGeneration
  };
})();