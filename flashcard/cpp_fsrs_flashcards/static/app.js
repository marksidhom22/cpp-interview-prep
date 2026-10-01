document.addEventListener('click', (event) => {
  const speakButton = event.target.closest('.speak');
  if (speakButton && 'speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(speakButton.dataset.speak || '');
    utterance.rate = 0.95;
    window.speechSynthesis.speak(utterance);
  }
  if (event.target.closest('.stop-speech') && 'speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
});

document.querySelectorAll('.speak[data-autoplay="true"]').forEach((button) => button.click());

const mermaidNodes = [...document.querySelectorAll('pre code.language-mermaid')].map((code) => {
  const container = code.parentElement;
  container.classList.add('mermaid');
  container.textContent = code.textContent;
  return container;
});
if (mermaidNodes.length) {
  import('https://cdn.jsdelivr.net/npm/mermaid@12/dist/mermaid.esm.min.mjs')
    .then(async (module) => {
      module.default.initialize({ startOnLoad: false, securityLevel: 'strict', theme: 'dark' });
      await module.default.run({ nodes: mermaidNodes });
    })
    .catch(() => mermaidNodes.forEach((node) => node.classList.add('diagram-unavailable')));
}

document.querySelectorAll('[data-preview-links]').forEach((section) => {
  section.querySelectorAll('[data-preview-url]').forEach(async (link) => {
    try {
      const response = await fetch(`/preview?url=${encodeURIComponent(link.dataset.previewUrl)}`);
      const preview = await response.json();
      if (!response.ok) return;
      const heading = link.querySelector('strong');
      const description = link.querySelector('.preview-description');
      const site = link.querySelector('.preview-site');
      heading.textContent = preview.title;
      description.textContent = preview.description || 'Open website ↗';
      site.textContent = preview.site_name || new URL(preview.url).hostname;
      link.href = preview.url;
    } catch {
      // Keep the original link available if preview lookup fails.
    }
  });
});
