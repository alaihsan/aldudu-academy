// Rasch Glossary modal functionality (_rasch_glossary.html)

function openRaschGlossary() {
  document.getElementById('rasch-glossary-modal').classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}

function closeRaschGlossary() {
  document.getElementById('rasch-glossary-modal').classList.add('hidden');
  document.body.style.overflow = '';
  // Reset search and filters
  const searchInput = document.getElementById('glossary-search');
  if (searchInput) searchInput.value = '';
  filterGlossary('');
  filterCategory('all');
}

function filterGlossary(query) {
  const items = document.querySelectorAll('.glossary-item');
  const sections = document.querySelectorAll('.glossary-section');
  const emptyState = document.getElementById('glossary-empty');
  let hasResults = false;

  query = query.toLowerCase().trim();

  items.forEach(item => {
    const terms = item.getAttribute('data-terms') || '';
    const text = item.textContent.toLowerCase();
    const matches = !query || terms.includes(query) || text.includes(query);
    item.style.display = matches ? '' : 'none';
    if (matches) hasResults = true;
  });

  // Show/hide section headers based on visible items
  sections.forEach(section => {
    const visibleItems = section.querySelectorAll('.glossary-item:not([style*="display: none"])');
    const header = section.querySelector('h3');
    if (header) header.style.display = visibleItems.length > 0 ? '' : 'none';
  });

  if (emptyState) {
    emptyState.classList.toggle('hidden', hasResults);
  }
}

function filterCategory(category) {
  // Update button styles
  document.querySelectorAll('.glossary-cat-btn').forEach(btn => {
    if (btn.getAttribute('data-cat') === category) {
      btn.classList.add('text-primary-600', 'border-primary-600', 'font-bold');
      btn.classList.remove('text-gray-500', 'dark:text-gray-400', 'border-transparent', 'font-medium');
    } else {
      btn.classList.remove('text-primary-600', 'border-primary-600', 'font-bold');
      btn.classList.add('text-gray-500', 'dark:text-gray-400', 'border-transparent', 'font-medium');
    }
  });

  const sections = document.querySelectorAll('.glossary-section');
  sections.forEach(section => {
    const sectionCat = section.getAttribute('data-category');
    if (category === 'all' || sectionCat === category) {
      section.style.display = '';
    } else {
      section.style.display = 'none';
    }
  });
}

// Close modal with Escape key
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') closeRaschGlossary();
});
