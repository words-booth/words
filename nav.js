document.addEventListener("keydown", (event) => {
  if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
  const target = { ArrowLeft: "a.prev", ArrowRight: "a.next" }[event.key];
  const link = target && document.querySelector(target);
  if (link) window.location.href = link.href;
});
