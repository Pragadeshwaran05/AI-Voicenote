document.addEventListener('DOMContentLoaded', () => {
    const tableBody = document.getElementById('historyTableBody');
    const refreshBtn = document.getElementById('refreshBtn');
    const emptyState = document.getElementById('emptyState');
    
    window.loadHistory();
    
    refreshBtn.addEventListener('click', () => {
        refreshBtn.classList.add('fa-spin');
        window.loadHistory().then(() => {
            setTimeout(() => refreshBtn.classList.remove('fa-spin'), 500);
        });
    });
    
    window.loadHistory = async function() {
        try {
            const response = await fetch('/api/history');
            if (response.ok) {
                const records = await response.json();
                window.renderHistory(records);
            } else {
                showToast('Failed to load history', 'error');
            }
        } catch (error) {
            console.error(error);
            showToast('Network error loading history', 'error');
        }
    }
    
    window.renderHistory = function(records) {
        tableBody.innerHTML = '';
        
        if (records.length === 0) {
            tableBody.closest('table').classList.add('hidden');
            emptyState.classList.remove('hidden');
            return;
        }
        
        tableBody.closest('table').classList.remove('hidden');
        emptyState.classList.add('hidden');
        
        records.forEach(record => {
            const tr = document.createElement('tr');
            
            tr.innerHTML = `
                <td class="date-cell">${formatDate(record.created_at)}</td>
                <td class="text-cell">
                    <div class="text-preview" title="${record.text}">${record.text}</div>
                </td>
                <td class="settings-cell">
                    <span class="settings-badge">${record.language.toUpperCase()}</span>
                    <span class="settings-badge">${record.speed}x</span>
                    ${record.sentiment ? `<span class="settings-badge" style="color:var(--primary);"><i class="fas fa-smile"></i> ${record.sentiment}</span>` : ''}
                    ${record.emotion ? `<span class="settings-badge" style="color:var(--secondary);"><i class="fas fa-heart"></i> ${record.emotion}</span>` : ''}
                    ${record.reading_mode ? `<span class="settings-badge"><i class="fas fa-book"></i> ${record.reading_mode}</span>` : ''}
                </td>
                <td class="actions-cell">
                    <div class="action-buttons">
                        <button class="mini-player-btn" onclick="playRowAudio('${record.audio_filename}')" title="Play">
                            <i class="fas fa-play"></i>
                        </button>
                        <button class="mini-player-btn" onclick="toggleFav(${record.id}, ${record.is_favorite ? 0 : 1})" title="Favorite" style="${record.is_favorite ? 'color: gold;' : ''}">
                            <i class="${record.is_favorite ? 'fas' : 'far'} fa-star"></i>
                        </button>
                        <a href="/download/${record.audio_filename}" class="btn-secondary" style="padding: 6px 12px;" title="Download">
                            <i class="fas fa-download"></i>
                        </a>
                        <button class="btn-text text-danger" onclick="deleteRecord(${record.id}, this)" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            `;
            
            tableBody.appendChild(tr);
        });
    }
});

let currentAudio = null;

window.playRowAudio = function(filename) {
    if (currentAudio) {
        currentAudio.pause();
    }
    
    currentAudio = new Audio(`/audio/${filename}`);
    currentAudio.play();
    
    showToast('Playing audio...', 'info');
};

window.deleteRecord = async function(id, btnElement) {
    if (!confirm('Are you sure you want to delete this generation?')) return;
    
    try {
        const response = await fetch(`/delete/${id}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                const row = btnElement.closest('tr');
                row.remove();
                showToast('Record deleted.', 'success');
                
                const tableBody = document.getElementById('historyTableBody');
                if (tableBody.children.length === 0) {
                    tableBody.closest('table').classList.add('hidden');
                    document.getElementById('emptyState').classList.remove('hidden');
                }
            }
        } else {
            showToast('Failed to delete.', 'error');
        }
    } catch (error) {
        console.error(error);
        showToast('Network error.', 'error');
    }
};


window.toggleFav = async function(id, newState) {
    try {
        const res = await fetch(`/api/favorite/${id}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({is_favorite: Boolean(newState)})
        });
        if(res.ok) {
            if (typeof window.loadHistory === 'function') {
                window.loadHistory();
            }
        }
    } catch(e) { console.error(e); }
};

document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const modeFilter = document.getElementById('modeFilter');
    
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            clearTimeout(window.searchTimeout);
            window.searchTimeout = setTimeout(() => {
                window.loadHistory();
            }, 500);
        });
    }
    
    if (modeFilter) {
        modeFilter.addEventListener('change', window.loadHistory);
    }
    
    const originalLoadHistory = window.loadHistory;
    window.loadHistory = async function() {
        // Only override if not already in library page
        if (window.location.pathname === '/library') {
            originalLoadHistory();
            return;
        }
        
        try {
            let url = '/api/history';
            if (searchInput || modeFilter) {
                const s = searchInput ? searchInput.value : '';
                const m = modeFilter ? modeFilter.value : '';
                url += `?search=${encodeURIComponent(s)}&mode=${encodeURIComponent(m)}`;
            }
            const response = await fetch(url);
            if (response.ok) {
                const records = await response.json();
                if (typeof renderHistory === 'function') {
                    renderHistory(records);
                } else if (typeof window.renderHistory === 'function') {
                    window.renderHistory(records);
                }
            }
        } catch (error) {
            console.error('Error fetching history:', error);
        }
    };
});
