self.addEventListener('install', event => {
  console.log('Service Worker installé');
});

self.addEventListener('fetch', event => {
  // Optionnel : gérer cache ici
});
