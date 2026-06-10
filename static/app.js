// Select DOM Elements
const bodyEl = document.documentElement;
const themeToggleBtn = document.getElementById('themeToggleBtn');
const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
const sidebarCloseBtn = document.getElementById('sidebarCloseBtn');
const sidebarEl = document.getElementById('sidebar');

const apiUrlInput = document.getElementById('apiUrlInput');
const statusIndicator = document.getElementById('statusIndicator');
const systemSpecsTrigger = document.getElementById('systemSpecsTrigger');
const systemSpecsContent = document.getElementById('systemSpecsContent');

const specModel = document.getElementById('specModel');
const specApiKey = document.getElementById('specApiKey');
const specCollection = document.getElementById('specCollection');
const specChunks = document.getElementById('specChunks');
const specDbPath = document.getElementById('specDbPath');

const apiKeyStatusBox = document.getElementById('apiKeyStatusBox');
const groqApiKeyInput = document.getElementById('groqApiKeyInput');
const togglePasswordVisibility = document.getElementById('togglePasswordVisibility');

const indexTopKSlider = document.getElementById('indexTopK');
const indexTopKValue = document.getElementById('indexTopKValue');
const rerankerTopNSlider = document.getElementById('rerankerTopN');
const rerankerTopNValue = document.getElementById('rerankerTopNValue');

const ingestBtn = document.getElementById('ingestBtn');
const ingestStatus = document.getElementById('ingestStatus');

const clearChatBtn = document.getElementById('clearChatBtn');
const chatViewport = document.getElementById('chatViewport');
const welcomeScreen = document.getElementById('welcomeScreen');
const messagesLog = document.getElementById('messagesLog');
const chatForm = document.getElementById('chatForm');
const chatInput = document.getElementById('chatInput');

// State Variables
let apiBaseUrl = apiUrlInput.value.trim() || 'http://localhost:8000';
let chatHistory = [];
let statusInterval = null;

// ==========================================
// 1. Theme Configuration (Dark/Light)
// ==========================================
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    bodyEl.setAttribute('data-theme', savedTheme);
}

themeToggleBtn.addEventListener('click', () => {
    const currentTheme = bodyEl.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    bodyEl.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
});

// ==========================================
// 2. Responsive Mobile Sidebar
// ==========================================
sidebarToggleBtn.addEventListener('click', () => {
    sidebarEl.classList.add('mobile-open');
});

sidebarCloseBtn.addEventListener('click', () => {
    sidebarEl.classList.remove('mobile-open');
});

// Close sidebar when clicking outside of it on mobile
document.addEventListener('click', (e) => {
    if (window.innerWidth <= 900) {
        if (!sidebarEl.contains(e.target) && !sidebarToggleBtn.contains(e.target)) {
            sidebarEl.classList.remove('mobile-open');
        }
    }
});

// ==========================================
// 3. Form Field Controls (Passwords & Sliders)
// ==========================================
togglePasswordVisibility.addEventListener('click', () => {
    const type = groqApiKeyInput.getAttribute('type') === 'password' ? 'text' : 'password';
    groqApiKeyInput.setAttribute('type', type);
    
    const icon = togglePasswordVisibility.querySelector('i');
    icon.classList.toggle('fa-eye');
    icon.classList.toggle('fa-eye-slash');
});

// Sync Sliders values
indexTopKSlider.addEventListener('input', (e) => {
    indexTopKValue.textContent = e.target.value;
});

rerankerTopNSlider.addEventListener('input', (e) => {
    rerankerTopNValue.textContent = e.target.value;
});

// Collapsible Specs Sidebar Action
systemSpecsTrigger.addEventListener('click', () => {
    systemSpecsTrigger.classList.toggle('active');
    systemSpecsContent.classList.toggle('expanded');
});

// ==========================================
// 4. API Endpoints Polling & Config
// ==========================================
apiUrlInput.addEventListener('change', () => {
    let value = apiUrlInput.value.trim();
    if (!value.startsWith('http://') && !value.startsWith('https://')) {
        value = 'http://' + value;
        apiUrlInput.value = value;
    }
    apiBaseUrl = value;
    checkApiStatus();
});

async function checkApiStatus() {
    statusIndicator.className = 'status-badge status-checking';
    statusIndicator.innerHTML = '<span class="status-dot"></span> Checking';

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 4000);
        
        const response = await fetch(`${apiBaseUrl}/status`, { signal: controller.signal });
        clearTimeout(timeoutId);

        if (response.ok) {
            const data = await response.json();
            
            // Update Status Widget
            statusIndicator.className = 'status-badge status-online';
            statusIndicator.innerHTML = '<span class="status-dot"></span> Online';
            
            specModel.textContent = data.llm_model || 'Unknown';
            specDbPath.textContent = data.chroma_db_path || '-';
            specCollection.textContent = data.collection_name || '-';
            specChunks.textContent = data.collection_size !== undefined ? data.collection_size : '-';
            
            if (data.api_key_configured) {
                specApiKey.textContent = 'Yes';
                specApiKey.className = 'badge-neutral';
                apiKeyStatusBox.className = 'api-key-status success';
                apiKeyStatusBox.innerHTML = '<i class="fa-solid fa-circle-check"></i> Server Key Ready';
            } else {
                specApiKey.textContent = 'No';
                specApiKey.className = 'badge-neutral';
                apiKeyStatusBox.className = 'api-key-status warning';
                apiKeyStatusBox.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Server Key Missing';
            }
        } else {
            setOfflineStatus();
        }
    } catch (err) {
        setOfflineStatus();
    }
}

function setOfflineStatus() {
    statusIndicator.className = 'status-badge status-offline';
    statusIndicator.innerHTML = '<span class="status-dot"></span> Offline';
    
    specModel.textContent = '-';
    specDbPath.textContent = '-';
    specCollection.textContent = '-';
    specChunks.textContent = '-';
    specApiKey.textContent = '-';
    
    apiKeyStatusBox.className = 'api-key-status warning';
    apiKeyStatusBox.innerHTML = '<i class="fa-solid fa-circle-exclamation"></i> Offline: Cannot verify';
}

function startPolling() {
    checkApiStatus();
    if (statusInterval) clearInterval(statusInterval);
    statusInterval = setInterval(checkApiStatus, 10000);
}

// ==========================================
// 5. Corpus Ingestion
// ==========================================
ingestBtn.addEventListener('click', async () => {
    ingestBtn.disabled = true;
    ingestBtn.querySelector('.btn-text').classList.add('hidden');
    ingestBtn.querySelector('.spinner').classList.remove('hidden');
    
    ingestStatus.className = 'ingest-status-box hidden';
    ingestStatus.innerHTML = '';

    try {
        const response = await fetch(`${apiBaseUrl}/ingest`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        ingestStatus.classList.remove('hidden');

        if (response.ok && data.status === 'success') {
            ingestStatus.className = 'ingest-status-box success';
            ingestStatus.innerHTML = `
                <strong>Success!</strong> Ingested PDF documents.<br>
                - Total Chunks: ${data.total_chunks}<br>
                - Files: ${data.ingested_files.join(', ')}
            `;
            checkApiStatus(); // Refresh chunks indexed count
        } else if (data.status === 'no_files') {
            ingestStatus.className = 'ingest-status-box warning';
            ingestStatus.innerHTML = `<strong>Notice:</strong> ${data.message}`;
        } else {
            ingestStatus.className = 'ingest-status-box error';
            ingestStatus.innerHTML = `<strong>Error:</strong> ${data.message || 'Corpus ingestion failed.'}`;
        }
    } catch (err) {
        ingestStatus.classList.remove('hidden');
        ingestStatus.className = 'ingest-status-box error';
        ingestStatus.innerHTML = `<strong>Network Error:</strong> Failed to connect to server.`;
    } finally {
        ingestBtn.disabled = false;
        ingestBtn.querySelector('.btn-text').classList.remove('hidden');
        ingestBtn.querySelector('.spinner').classList.add('hidden');
    }
});

// ==========================================
// 6. Chat Functionality & Persistence
// ==========================================
function loadHistory() {
    const saved = localStorage.getItem('chat_history');
    if (saved) {
        try {
            chatHistory = JSON.parse(saved);
            if (chatHistory.length > 0) {
                welcomeScreen.classList.add('hidden');
                chatHistory.forEach(msg => appendMessageUI(msg.role, msg.content, msg.contexts));
            }
        } catch (e) {
            chatHistory = [];
        }
    }
}

function saveHistory() {
    localStorage.setItem('chat_history', JSON.stringify(chatHistory));
}

function clearHistory() {
    chatHistory = [];
    localStorage.removeItem('chat_history');
    messagesLog.innerHTML = '';
    welcomeScreen.classList.remove('hidden');
}

clearChatBtn.addEventListener('click', clearHistory);

// Expand dynamic height of input textarea as user types
chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = (chatInput.scrollHeight) + 'px';
});

// Allow enter to send (but Shift+Enter inserts newline)
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.requestSubmit();
    }
});

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const queryText = chatInput.value.trim();
    if (!queryText) return;

    // Add user message to UI
    appendMessage(queryText, 'user');
    chatInput.value = '';
    chatInput.style.height = '36px'; // Reset height

    // Add loading skeleton
    const skeletonId = appendSkeletonUI();

    try {
        const payload = {
            query: queryText,
            index_top_k: parseInt(indexTopKSlider.value, 10),
            reranker_top_n: parseInt(rerankerTopNSlider.value, 10)
        };
        
        const overrideKey = groqApiKeyInput.value.trim();
        if (overrideKey) {
            payload.groq_api_key = overrideKey;
        }

        const response = await fetch(`${apiBaseUrl}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        // Remove loading state
        removeSkeletonUI(skeletonId);

        if (response.ok) {
            const data = await response.json();
            appendMessage(data.answer, 'assistant', data.contexts || []);
        } else {
            const errorText = await response.text();
            let errDetail = 'Unknown server error';
            try {
                const errJson = JSON.parse(errorText);
                errDetail = errJson.detail || errDetail;
            } catch (e) {}
            appendMessage(`⚠️ API Error (Status ${response.status}): ${errDetail}`, 'assistant');
        }
    } catch (err) {
        removeSkeletonUI(skeletonId);
        appendMessage(`⚠️ Failed to connect to API backend: ${err.message}`, 'assistant');
    }
});

// Quick prompt suggestions clicks
document.querySelectorAll('.quick-prompt-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        chatInput.value = btn.textContent.trim();
        chatInput.focus();
        // Trigger resize
        chatInput.style.height = 'auto';
        chatInput.style.height = (chatInput.scrollHeight) + 'px';
    });
});

// Function to append messages to history and trigger rendering
function appendMessage(content, role, contexts = []) {
    chatHistory.push({ role, content, contexts });
    saveHistory();
    welcomeScreen.classList.add('hidden');
    appendMessageUI(role, content, contexts);
}

// Low-level UI rendering function for message bubbles
function appendMessageUI(role, content, contexts = []) {
    const wrapper = document.createElement('div');
    wrapper.className = `message-wrapper ${role}`;
    
    // Bubble
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    
    // Convert basic markdown/newlines for text
    bubble.innerHTML = formatMarkdown(content);
    wrapper.appendChild(bubble);

    // If assistant has source contexts, add research accordion
    if (role === 'assistant' && contexts && contexts.length > 0) {
        const traceContainer = document.createElement('div');
        traceContainer.className = 'research-trace';

        const trigger = document.createElement('div');
        trigger.className = 'research-trigger';
        trigger.innerHTML = `
            <span><i class="fa-solid fa-magnifying-glass"></i> Agent Research Trace (${contexts.length} actions)</span>
            <i class="fa-solid fa-chevron-down chevron"></i>
        `;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'research-content';

        contexts.forEach((chunk, index) => {
            const chunkDiv = document.createElement('div');
            chunkDiv.className = 'context-chunk';
            chunkDiv.innerHTML = `
                <div class="context-chunk-title">Chunk #${index + 1}</div>
                <div>${escapeHtml(chunk)}</div>
            `;
            contentDiv.appendChild(chunkDiv);
        });

        trigger.addEventListener('click', () => {
            trigger.classList.toggle('active');
            contentDiv.classList.toggle('expanded');
        });

        traceContainer.appendChild(trigger);
        traceContainer.appendChild(contentDiv);
        wrapper.appendChild(traceContainer);
    }

    messagesLog.appendChild(wrapper);
    scrollToBottom();
}

// Skeleton loading bubble methods
function appendSkeletonUI() {
    const id = 'skeleton-' + Date.now();
    const wrapper = document.createElement('div');
    wrapper.className = 'message-wrapper assistant';
    wrapper.id = id;

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';

    bubble.innerHTML = `
        <div class="skeleton-wrapper">
            <div class="skeleton-line"></div>
            <div class="skeleton-line medium"></div>
            <div class="skeleton-line short"></div>
        </div>
    `;

    wrapper.appendChild(bubble);
    messagesLog.appendChild(wrapper);
    scrollToBottom();
    return id;
}

function removeSkeletonUI(id) {
    const el = document.getElementById(id);
    if (el) {
        el.remove();
    }
}

// Helper: Scroll chat to bottom
function scrollToBottom() {
    setTimeout(() => {
        chatViewport.scrollTo({
            top: chatViewport.scrollHeight,
            behavior: 'smooth'
        });
    }, 50);
}

// Helper: Parse very basic markdown tags (bold, code blocks, bullet points)
function formatMarkdown(text) {
    if (!text) return '';
    let html = escapeHtml(text);
    
    // Replace markdown bold (**text**)
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Replace markdown inline code (`code`)
    html = html.replace(/`(.*?)`/g, '<code>$1</code>');
    
    // Handle bullet points at start of lines
    html = html.split('\n').map(line => {
        if (line.trim().startsWith('- ')) {
            return `<li>${line.trim().substring(2)}</li>`;
        }
        return line;
    }).join('\n');
    
    // Wrap lists if they exist
    html = html.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');
    
    // Convert remaining newlines to line breaks
    html = html.replace(/\n/g, '<br>');
    
    return html;
}

// Helper: Escaping HTML input
function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}

// ==========================================
// 7. Initialization
// ==========================================
initTheme();
loadHistory();
startPolling();
// Detect window sizes for layout changes
window.addEventListener('resize', () => {
    if (window.innerWidth > 900) {
        sidebarEl.classList.remove('mobile-open');
    }
});
