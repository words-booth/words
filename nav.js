function follow(selector) {
  const link = document.querySelector(selector);
  if (link) window.location.href = link.href;
}

document.addEventListener("keydown", (event) => {
  if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
  const target = { ArrowLeft: "a.prev", ArrowRight: "a.next" }[event.key];
  if (target) follow(target);
});

let swipe = null;

document.addEventListener("touchstart", (event) => {
  const touch = event.touches[0];
  // Swipes starting at the screen edges belong to the browser's own back/forward gestures.
  const edge = 24;
  swipe = event.touches.length === 1 && touch.clientX > edge && touch.clientX < window.innerWidth - edge
    ? { x: touch.clientX, y: touch.clientY, lastX: touch.clientX, lastY: touch.clientY, time: Date.now() }
    : null;
}, { passive: true });

document.addEventListener("touchmove", (event) => {
  if (!swipe) return;
  if (event.touches.length !== 1) { swipe = null; return; }
  swipe.lastX = event.touches[0].clientX;
  swipe.lastY = event.touches[0].clientY;
}, { passive: true });

// iOS Safari often ends a sideways swipe with touchcancel instead of touchend.
function finish(event) {
  if (!swipe) return;
  const touch = event.changedTouches && event.changedTouches[0];
  const x = touch ? touch.clientX : swipe.lastX;
  const y = touch ? touch.clientY : swipe.lastY;
  const dx = (x || swipe.lastX) - swipe.x;
  const dy = (y || swipe.lastY) - swipe.y;
  const quick = Date.now() - swipe.time < 800;
  swipe = null;
  if (!quick || Math.abs(dx) < 60 || Math.abs(dx) < Math.abs(dy) * 1.5) return;
  follow(dx < 0 ? "a.next" : "a.prev");
}

document.addEventListener("touchend", finish, { passive: true });
document.addEventListener("touchcancel", finish, { passive: true });
