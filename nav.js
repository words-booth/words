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
    ? { x: touch.clientX, y: touch.clientY, time: Date.now() }
    : null;
}, { passive: true });

document.addEventListener("touchend", (event) => {
  if (!swipe) return;
  const touch = event.changedTouches[0];
  const dx = touch.clientX - swipe.x;
  const dy = touch.clientY - swipe.y;
  const quick = Date.now() - swipe.time < 800;
  swipe = null;
  if (!quick || Math.abs(dx) < 60 || Math.abs(dx) < Math.abs(dy) * 1.5) return;
  follow(dx < 0 ? "a.next" : "a.prev");
}, { passive: true });

document.addEventListener("touchcancel", () => { swipe = null; }, { passive: true });
