document.addEventListener('DOMContentLoaded', () => {
    const searchBtn = document.getElementById('search-btn');
    const searchInput = document.getElementById('search-input');
    const loading = document.getElementById('loading');

    // Areas to show/hide
    const resultsArea = document.getElementById('results-area');
    const aiResponseText = document.getElementById('ai-response-text');
    const sourcesGrid = document.getElementById('sources-grid');

    if (searchBtn) {
        searchBtn.addEventListener('click', handleSearch);
    }

    if (searchInput) {
        searchInput.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                handleSearch();
            }
        });
    }

    async function handleSearch() {
        const query = searchInput.value.trim();
        if (!query) return;

        // UI State: Loading
        searchBtn.disabled = true;
        searchBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Searching...';
        loading.classList.remove('hidden');
        resultsArea.classList.add('hidden');

        // Clear previous
        aiResponseText.innerHTML = '';
        sourcesGrid.innerHTML = '';

        try {
            const response = await fetch('/api/v1/search/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken') // Function to get CSRF
                },
                body: JSON.stringify({ query: query })
            });

            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();

            // Render AI Answer (Simple markdown parsing could happen here, currently plain text)
            aiResponseText.innerText = data.result;

            // Render Sources
            if (data.source_documents && data.source_documents.length > 0) {
                renderSources(data.source_documents);
            } else {
                sourcesGrid.innerHTML = '<p class="text-muted">No specific documents found.</p>';
            }

            // Show Results
            resultsArea.classList.remove('hidden');

        } catch (error) {
            console.error('Error:', error);
            alert('Error performing search. Please check your connection.');
        } finally {
            loading.classList.add('hidden');
            searchBtn.disabled = false;
            searchBtn.innerHTML = '<i class="fa-solid fa-magnifying-glass"></i> Search';
        }
    }

    function renderSources(docs) {
        docs.forEach(doc => {
            // Determine badge based on file type or source
            const sourceName = doc.source_name || 'Unknown';
            const badgeClass = sourceName.includes('resume') ? 'bg-primary' : 'bg-secondary';

            const card = document.createElement('div');
            card.className = 'source-card animate-fade';
            card.innerHTML = `
                <div class="source-badge">
                    <i class="fa-regular fa-file"></i> ${sourceName}
                </div>
                <div class="source-highlight">
                    "${doc.content.substring(0, 300)}..."
                </div>
            `;
            sourcesGrid.appendChild(card);
        });
    }

    // Helper to get CSRF token from Django cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
