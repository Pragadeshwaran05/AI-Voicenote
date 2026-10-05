document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const textInput = document.getElementById('textInput');
    const charCount = document.getElementById('charCount');
    const clearBtn = document.getElementById('clearBtn');
    const generateBtn = document.getElementById('generateBtn');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const enhanceBtn = document.getElementById('enhanceBtn');
    const summarizeBtn = document.getElementById('summarizeBtn');
    
    const languageSelect = document.getElementById('languageSelect');
    const voiceSelect = document.getElementById('voiceSelect');
    const speedSelect = document.getElementById('speedSelect');
    const readingModeSelect = document.getElementById('readingModeSelect');
    
    const statWords = document.getElementById('statWords');
    const statSentences = document.getElementById('statSentences');
    const statChars = document.getElementById('statChars');
    const statTime = document.getElementById('statTime');
    
    const aiLanguage = document.getElementById('aiLanguage');
    const aiSentiment = document.getElementById('aiSentiment');
    const aiEmotion = document.getElementById('aiEmotion');
    const aiKeywords = document.getElementById('aiKeywords');
    
    const audioSection = document.getElementById('audioSection');
    const audioPlayer = document.getElementById('audioPlayer');
    const downloadBtn = document.getElementById('downloadBtn');
    
    const recentMiniList = document.getElementById('recentMiniList');
    
    const MAX_CHARS = 5000;
    
    // Check for draft
    const draft = localStorage.getItem('voicenote_draft');
    if (draft) {
        textInput.value = draft;
        localStorage.removeItem('voicenote_draft');
        updateCounts();
        debounceAnalyzeText();
    }
    
    // Load voices
    loadVoices();
    // Load recent
    loadRecentMini();
    // Load stats
    loadStats();

    async function loadStats() {
        try {
            const response = await fetch('/api/stats');
            if (response.ok) {
                const data = await response.json();
                document.getElementById('globalTotalGen').textContent = data.total_generations || 0;
                document.getElementById('globalSaved').textContent = data.saved_voices || 0;
                document.getElementById('globalLang').textContent = data.most_used_lang || '-';
            }
        } catch (error) {
            console.error('Error fetching global stats', error);
        }
    }
    
    // Event Listeners
    textInput.addEventListener('input', () => {
        updateCounts();
        debounceAnalyzeText();
    });
    
    clearBtn.addEventListener('click', () => {
        textInput.value = '';
        updateCounts();
        resetStats();
        audioSection.classList.add('hidden');
    });
    
    generateBtn.addEventListener('click', generateVoice);
    analyzeBtn.addEventListener('click', fullAIAnalysis);
    enhanceBtn.addEventListener('click', enhanceText);
    summarizeBtn.addEventListener('click', summarizeText);
    
    languageSelect.addEventListener('change', loadVoices);
    
    // Functions
    function updateCounts() {
        const text = textInput.value;
        const length = text.length;
        charCount.textContent = `${length} / ${MAX_CHARS}`;
        
        if (length > MAX_CHARS) {
            charCount.style.color = 'var(--danger)';
            textInput.value = text.substring(0, MAX_CHARS);
            charCount.textContent = `${MAX_CHARS} / ${MAX_CHARS}`;
        } else {
            charCount.style.color = 'var(--text-secondary)';
        }
    }
    
    let debounceTimer;
    function debounceAnalyzeText() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(basicStatsOnly, 500);
    }
    
    async function basicStatsOnly() {
        const text = textInput.value.trim();
        if (!text) {
            resetStats();
            return;
        }
        try {
            const response = await fetch('/api/text-stats', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            if (response.ok) {
                const stats = await response.json();
                statWords.textContent = stats.words;
                statSentences.textContent = stats.sentences;
                statChars.textContent = stats.characters;
                statTime.textContent = `${stats.reading_time_mins} min ${stats.reading_time_secs} sec`;
            }
        } catch (error) {
            console.error(error);
        }
    }

    async function fullAIAnalysis() {
        const text = textInput.value.trim();
        if (!text) {
            showToast('Please enter some text to analyze.', 'warning');
            return;
        }
        
        const originalBtnHTML = analyzeBtn.innerHTML;
        analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Analyzing...</span>';
        analyzeBtn.disabled = true;
        
        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    // Update basic stats
                    statWords.textContent = data.statistics.words;
                    statSentences.textContent = data.statistics.sentences;
                    statChars.textContent = data.statistics.characters;
                    statTime.textContent = `${data.statistics.reading_time_mins} min ${data.statistics.reading_time_secs} sec`;
                    
                    // Update AI stats
                    aiLanguage.textContent = `${data.language.name} (${data.language.code})`;
                    aiSentiment.innerHTML = `${data.sentiment.label} <span class="text-muted" style="font-size:0.8em;font-weight:normal;">(${Math.round(data.sentiment.score*100)}%)</span>`;
                    aiEmotion.innerHTML = `${data.emotion.label} <span class="text-muted" style="font-size:0.8em;font-weight:normal;">(${Math.round(data.emotion.score*100)}%)</span>`;
                    
                    // Keywords
                    aiKeywords.innerHTML = '';
                    if (data.keywords && data.keywords.length > 0) {
                        data.keywords.forEach(kw => {
                            const span = document.createElement('span');
                            span.className = 'keyword-tag';
                            span.textContent = kw;
                            aiKeywords.appendChild(span);
                        });
                    } else {
                        aiKeywords.innerHTML = '<span class="text-muted">No keywords extracted</span>';
                    }
                    
                    showToast('AI Analysis Complete!', 'success');
                }
            }
        } catch (error) {
            console.error(error);
            showToast('Analysis failed.', 'error');
        } finally {
            analyzeBtn.innerHTML = originalBtnHTML;
            analyzeBtn.disabled = false;
        }
    }
    
    async function enhanceText() {
        const text = textInput.value.trim();
        if (!text) return showToast('Please enter text to enhance.', 'warning');
        
        const originalBtnHTML = enhanceBtn.innerHTML;
        enhanceBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        enhanceBtn.disabled = true;
        
        try {
            const response = await fetch('/api/enhance', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            const data = await response.json();
            if (data.success) {
                textInput.value = data.enhanced_text;
                updateCounts();
                showToast('Text enhanced successfully.', 'success');
            }
        } catch (e) {
            showToast('Enhancement failed.', 'error');
        } finally {
            enhanceBtn.innerHTML = originalBtnHTML;
            enhanceBtn.disabled = false;
        }
    }
    
    async function summarizeText() {
        const text = textInput.value.trim();
        if (!text) return showToast('Please enter text to summarize.', 'warning');
        
        const originalBtnHTML = summarizeBtn.innerHTML;
        summarizeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        summarizeBtn.disabled = true;
        
        try {
            const response = await fetch('/api/summarize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            const data = await response.json();
            if (data.success) {
                textInput.value = data.summary;
                updateCounts();
                showToast('Summary created.', 'success');
            }
        } catch (e) {
            showToast('Summarization failed.', 'error');
        } finally {
            summarizeBtn.innerHTML = originalBtnHTML;
            summarizeBtn.disabled = false;
        }
    }
    
    function resetStats() {
        statWords.textContent = '0';
        statSentences.textContent = '0';
        statChars.textContent = '0';
        statTime.textContent = '0 min 0 sec';
        
        aiLanguage.textContent = '-';
        aiSentiment.textContent = '-';
        aiEmotion.textContent = '-';
        aiKeywords.innerHTML = '<span class="text-muted">No keywords yet</span>';
    }
    
    async function loadVoices() {
        const lang = languageSelect.value;
        try {
            const response = await fetch(`/api/voices?language=${lang}`);
            if (response.ok) {
                const voices = await response.json();
                voiceSelect.innerHTML = '';
                
                if (voices.length === 0) {
                    voiceSelect.innerHTML = '<option value="default">Default System Voice</option>';
                    return;
                }
                
                voices.forEach(voice => {
                    const option = document.createElement('option');
                    option.value = voice.id;
                    option.textContent = voice.name;
                    voiceSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading voices:', error);
        }
    }
    
    async function generateVoice() {
        const text = textInput.value.trim();
        
        if (!text) {
            showToast('Please enter some text to generate voice.', 'error');
            return;
        }
        
        // Set loading state
        const originalBtnHTML = generateBtn.innerHTML;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Generating...</span>';
        generateBtn.disabled = true;
        
        try {
            const response = await fetch('/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: text,
                    language: languageSelect.value,
                    voice: voiceSelect.value,
                    speed: speedSelect.value,
                    reading_mode: readingModeSelect.value
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showToast(data.message, 'success');
                
                // Show audio player
                audioPlayer.src = data.audio_url;
                downloadBtn.href = `/download/${data.filename}`;
                audioSection.classList.remove('hidden');
                
                // Reload recent list
                loadRecentMini();
                
                // Update button
                generateBtn.innerHTML = '<i class="fas fa-check"></i> <span>Voice Generated</span>';
                setTimeout(() => {
                    generateBtn.innerHTML = originalBtnHTML;
                    generateBtn.disabled = false;
                }, 2000);
                
            } else {
                showToast(data.error || 'Failed to generate voice.', 'error');
                resetBtn();
            }
        } catch (error) {
            console.error('Generation error:', error);
            showToast('Network error occurred.', 'error');
            resetBtn();
        }
        
        function resetBtn() {
            generateBtn.innerHTML = originalBtnHTML;
            generateBtn.disabled = false;
        }
    }
    
    async function loadRecentMini() {
        try {
            const response = await fetch('/api/history');
            if (response.ok) {
                const records = await response.json();
                
                if (records.length === 0) {
                    recentMiniList.innerHTML = '<p class="text-muted text-center py-4">No recent generations.</p>';
                    return;
                }
                
                recentMiniList.innerHTML = '';
                // Just show top 3
                records.slice(0, 3).forEach(record => {
                    const el = document.createElement('div');
                    el.className = 'recent-mini-item';
                    
                    const date = new Date(record.created_at).toLocaleDateString();
                    
                    el.innerHTML = `
                        <div class="recent-mini-text">${record.text}</div>
                        <div class="recent-mini-meta">
                            <span>${date}</span>
                            <a href="javascript:void(0)" onclick="playAudio('${record.audio_filename}')"><i class="fas fa-play-circle"></i> Play</a>
                        </div>
                    `;
                    recentMiniList.appendChild(el);
                });
            }
        } catch (error) {
            recentMiniList.innerHTML = '<p class="text-danger text-center">Failed to load recent.</p>';
        }
    }
});

// Global function for inline play button in mini list
window.playAudio = function(filename) {
    const audioSection = document.getElementById('audioSection');
    const audioPlayer = document.getElementById('audioPlayer');
    const downloadBtn = document.getElementById('downloadBtn');
    
    audioPlayer.src = `/audio/${filename}`;
    downloadBtn.href = `/download/${filename}`;
    audioSection.classList.remove('hidden');
    audioPlayer.play();
};
