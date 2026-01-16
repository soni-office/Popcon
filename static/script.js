// Global state
let prospects = [];
let currentProspectId = null;

// API Base URL
const API_BASE = '';

// DOM Elements
const searchForm = document.getElementById('searchForm');
const searchBtn = document.getElementById('searchBtn');
const searchBtnText = document.getElementById('searchBtnText');
const searchBtnSpinner = document.getElementById('searchBtnSpinner');
const statusCard = document.getElementById('statusCard');
const prospectsCard = document.getElementById('prospectsCard');
const prospectsList = document.getElementById('prospectsList');
const prospectsCount = document.getElementById('prospectsCount');
const sendEmailsBtn = document.getElementById('sendEmailsBtn');
const detailModal = document.getElementById('detailModal');
const closeModal = document.querySelector('.close');
const themeSelect = document.getElementById('themeSelect');
const authGmailBtn = document.getElementById('authGmailBtn');
const authGmailText = document.getElementById('authGmailText');
const authGmailSpinner = document.getElementById('authGmailSpinner');
const authStatus = document.getElementById('authStatus');
const emailInput = document.getElementById('email');

// Status elements
const totalProspectsEl = document.getElementById('totalProspects');
const emailsFoundEl = document.getElementById('emailsFound');
const emailsSentEl = document.getElementById('emailsSent');
const statusMessageEl = document.getElementById('statusMessage');

// ============================================
// Theme Management
// ============================================
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    themeSelect.value = savedTheme;
    applyTheme(savedTheme);
}

function applyTheme(theme) {
    document.body.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
}

themeSelect.addEventListener('change', (e) => {
    applyTheme(e.target.value);
});

// Initialize theme on load
initTheme();

// ============================================
// Event Listeners
// ============================================
searchForm.addEventListener('submit', handleSearch);
if (sendEmailsBtn) {
    sendEmailsBtn.addEventListener('click', handleSendEmails);
}
if (closeModal) {
    closeModal.addEventListener('click', () => {
        detailModal.style.display = 'none';
    });
}
if (authGmailBtn) {
    authGmailBtn.addEventListener('click', handleGmailAuth);
}
if (emailInput) {
    emailInput.addEventListener('blur', checkGmailAuth);
}

window.addEventListener('click', (e) => {
    if (e.target === detailModal) {
        detailModal.style.display = 'none';
    }
});

// ============================================
// Search Handler
// ============================================
async function handleSearch(e) {
    e.preventDefault();
    
    const formData = {
        name: document.getElementById('name').value,
        email: document.getElementById('email').value,
        skills: document.getElementById('skills').value,
        goal: document.getElementById('goal').value
    };
    
    // Validate
    if (!formData.goal.trim()) {
        alert('Please enter your job search goal');
        return;
    }
    
    // Show loading state
    setLoading(true);
    statusCard.style.display = 'block';
    prospectsCard.style.display = 'none';
    updateStatusMessage('Searching for prospects...');
    
    try {
        const response = await fetch(`${API_BASE}/api/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            prospects = data.prospects || [];
            console.log('Received prospects:', prospects); // Debug log
            updateStatus(data.status);
            displayProspects(prospects);
            updateStatusMessage('Prospects found! Click on any prospect to view details.');
            
            // Check Gmail auth status after search
            checkGmailAuth();
            
            if (prospects.length > 0 && prospects.some(p => p && p.email)) {
                sendEmailsBtn.style.display = 'block';
            }
        } else {
            updateStatusMessage(`Error: ${data.error || data.message || 'Unknown error'}`);
            alert(data.message || 'Failed to search prospects');
        }
    } catch (error) {
        console.error('Search error:', error);
        updateStatusMessage(`Error: ${error.message}`);
        alert('Failed to search prospects. Please try again.');
    } finally {
        setLoading(false);
    }
}

// ============================================
// Send Emails Handler
// ============================================
async function handleSendEmails() {
    if (!confirm(`Are you sure you want to send emails to ${prospects.filter(p => p.email).length} prospects?`)) {
        return;
    }
    
    setLoading(true);
    updateStatusMessage('Sending emails... This may take a few minutes.');
    sendEmailsBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/api/send-emails`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ dry_run: false })
        });
        
        const data = await response.json();
        
        if (data.success) {
            updateStatus(data.status);
            updateStatusMessage(`✅ ${data.message}`);
            alert(`Successfully sent ${data.status.emails_sent} emails!`);
        } else {
            updateStatusMessage(`Error: ${data.error || data.message}`);
            alert(data.message || 'Failed to send emails');
        }
    } catch (error) {
        console.error('Send emails error:', error);
        updateStatusMessage(`Error: ${error.message}`);
        alert('Failed to send emails. Please try again.');
    } finally {
        setLoading(false);
        sendEmailsBtn.disabled = false;
    }
}

// ============================================
// Display Prospects (Accordion)
// ============================================
function displayProspects(prospectsData) {
    if (!prospectsData || !Array.isArray(prospectsData)) {
        console.error('Invalid prospects data:', prospectsData);
        prospectsList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">⚠️</div>
                <p>Invalid data received. Please try again.</p>
            </div>
        `;
        return;
    }
    
    prospectsCard.style.display = 'block';
    prospectsCount.textContent = prospectsData.length;
    
    if (prospectsData.length === 0) {
        prospectsList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🔍</div>
                <p>No prospects found. Try a different search query.</p>
            </div>
        `;
        return;
    }
    
    const accordionHTML = prospectsData.map((prospect, index) => {
        // Handle name extraction more robustly
        let fullName = 'Unknown';
        if (prospect.full_name) {
            fullName = prospect.full_name.trim();
        } else if (prospect.first_name || prospect.last_name) {
            fullName = `${prospect.first_name || ''} ${prospect.last_name || ''}`.trim();
        }
        
        if (!fullName || fullName === 'Unknown') {
            // Try to get name from email or other fields
            if (prospect.email) {
                fullName = prospect.email.split('@')[0].replace(/[._]/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            } else {
                fullName = `Prospect ${index + 1}`;
            }
        }
        
        const initials = getInitials(fullName);
        const companyName = (prospect.company_name && prospect.company_name.trim()) || 'Not specified';
        const email = (prospect.email && prospect.email.trim()) || null;
        const linkedin = (prospect.linkedin_profile && prospect.linkedin_profile.trim()) || null;
        const companyDomain = (prospect.company_domain && prospect.company_domain.trim()) || null;
        
        return `
            <div class="accordion-item" data-index="${index}">
                <div class="accordion-header" data-accordion-index="${index}">
                    <div class="accordion-header-content">
                        <div class="accordion-icon">${initials}</div>
                        <div class="accordion-title">${fullName}</div>
                    </div>
                    <div class="accordion-chevron">▼</div>
                </div>
                <div class="accordion-content">
                    <div class="accordion-details">
                        <div class="detail-row">
                            <div class="detail-icon">👤</div>
                            <div class="detail-content">
                                <div class="detail-label">Person Name</div>
                                <div class="detail-value">${fullName}</div>
                            </div>
                        </div>
                        <div class="detail-row">
                            <div class="detail-icon">🏢</div>
                            <div class="detail-content">
                                <div class="detail-label">Company Name</div>
                                <div class="detail-value">${companyName}</div>
                            </div>
                        </div>
                        ${email ? `
                        <div class="detail-row">
                            <div class="detail-icon">📧</div>
                            <div class="detail-content">
                                <div class="detail-label">Work Email</div>
                                <div class="detail-value">
                                    <a href="mailto:${email}">${email}</a>
                                </div>
                            </div>
                        </div>
                        <div class="detail-row">
                            <div class="detail-icon"></div>
                            <div class="detail-content">
                                <button class="btn-send-email" data-prospect-index="${index}" onclick="sendSingleEmail(${index}, event)">
                                    <span class="btn-send-text">📨 Send Email</span>
                                    <span class="btn-send-spinner" style="display: none;">⏳</span>
                                </button>
                            </div>
                        </div>
                        ` : `
                        <div class="detail-row">
                            <div class="detail-icon">📧</div>
                            <div class="detail-content">
                                <div class="detail-label">Work Email</div>
                                <div class="detail-value empty">Not available</div>
                            </div>
                        </div>
                        `}
                        ${linkedin ? `
                        <div class="detail-row">
                            <div class="detail-icon">💼</div>
                            <div class="detail-content">
                                <div class="detail-label">LinkedIn Profile</div>
                                <div class="detail-value">
                                    <a href="${linkedin}" target="_blank" rel="noopener noreferrer">${linkedin}</a>
                                </div>
                            </div>
                        </div>
                        ` : `
                        <div class="detail-row">
                            <div class="detail-icon">💼</div>
                            <div class="detail-content">
                                <div class="detail-label">LinkedIn Profile</div>
                                <div class="detail-value empty">Not available</div>
                            </div>
                        </div>
                        `}
                        ${companyDomain ? `
                        <div class="detail-row">
                            <div class="detail-icon">🌐</div>
                            <div class="detail-content">
                                <div class="detail-label">Company Domain</div>
                                <div class="detail-value">${companyDomain}</div>
                            </div>
                        </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    prospectsList.innerHTML = accordionHTML;
    
    // Add event listeners to accordion headers
    document.querySelectorAll('.accordion-header').forEach(header => {
        header.addEventListener('click', function(e) {
            e.stopPropagation();
            const index = parseInt(this.getAttribute('data-accordion-index'));
            toggleAccordion(index);
        });
    });
}

// ============================================
// Accordion Toggle
// ============================================
function toggleAccordion(index) {
    console.log('Toggling accordion for index:', index); // Debug log
    const item = document.querySelector(`.accordion-item[data-index="${index}"]`);
    if (!item) {
        console.error('Accordion item not found for index:', index);
        return;
    }
    
    const isActive = item.classList.contains('active');
    
    // Close all other accordions (optional - remove if you want multiple open)
    document.querySelectorAll('.accordion-item').forEach(otherItem => {
        if (otherItem !== item) {
            otherItem.classList.remove('active');
        }
    });
    
    // Toggle current item
    if (isActive) {
        item.classList.remove('active');
    } else {
        item.classList.add('active');
    }
}

// Make toggleAccordion available globally
window.toggleAccordion = toggleAccordion;

// ============================================
// Send Single Email
// ============================================
async function sendSingleEmail(index, event) {
    if (event) {
        event.stopPropagation();
    }
    
    const prospect = prospects[index];
    if (!prospect || !prospect.email) {
        alert('No email address available for this prospect');
        return;
    }
    
    // Check if Gmail is authenticated
    const userEmail = document.getElementById('email').value.trim();
    if (!userEmail) {
        alert('Please enter your email address first');
        return;
    }
    
    try {
        const authCheck = await fetch(`${API_BASE}/api/oauth/check`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: userEmail })
        });
        const authData = await authCheck.json();
        
        if (!authData.success || !authData.authenticated) {
            if (confirm('Gmail is not authenticated. Would you like to authenticate now?')) {
                await handleGmailAuth();
                // Re-check after auth
                const recheck = await fetch(`${API_BASE}/api/oauth/check`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: userEmail })
                });
                const recheckData = await recheck.json();
                if (!recheckData.success || !recheckData.authenticated) {
                    alert('Please authenticate Gmail before sending emails');
                    return;
                }
            } else {
                return;
            }
        }
    } catch (error) {
        console.error('Auth check error:', error);
    }
    
    if (!confirm(`Send email to ${prospect.full_name || 'this prospect'}?`)) {
        return;
    }
    
    const btn = document.querySelector(`.btn-send-email[data-prospect-index="${index}"]`);
    const btnText = btn.querySelector('.btn-send-text');
    const btnSpinner = btn.querySelector('.btn-send-spinner');
    
    // Show loading state
    btn.disabled = true;
    btnText.style.display = 'none';
    btnSpinner.style.display = 'inline';
    
    try {
        const response = await fetch(`${API_BASE}/api/send-email/${index}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update button to show success
            btnText.textContent = '✅ Sent';
            btnText.style.display = 'inline';
            btnSpinner.style.display = 'none';
            btn.style.background = 'var(--success)';
            btn.disabled = true;
            
            // Update global status
            if (data.status) {
                updateStatus(data.status);
            }
            
            // Show success message
            setTimeout(() => {
                alert(`Email sent successfully to ${prospect.full_name || prospect.email}!`);
            }, 100);
        } else {
            btnText.textContent = '❌ Failed';
            btnText.style.display = 'inline';
            btnSpinner.style.display = 'none';
            btn.style.background = '#ef4444';
            alert(data.error || 'Failed to send email');
        }
    } catch (error) {
        console.error('Send email error:', error);
        btnText.textContent = '❌ Error';
        btnText.style.display = 'inline';
        btnSpinner.style.display = 'none';
        btn.style.background = '#ef4444';
        alert('Failed to send email. Please try again.');
    } finally {
        // Re-enable after a delay if failed
        if (!btn.disabled || btn.style.background === '#ef4444') {
            setTimeout(() => {
                btn.disabled = false;
                btnText.textContent = '📨 Send Email';
                btn.style.background = '';
            }, 3000);
        }
    }
}

// Make sendSingleEmail available globally
window.sendSingleEmail = sendSingleEmail;

// ============================================
// Helper Functions
// ============================================
function getInitials(name) {
    if (!name) return '?';
    const parts = name.trim().split(' ');
    if (parts.length >= 2) {
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
}

// Show prospect details in modal (kept for backward compatibility)
async function showProspectDetails(index) {
    currentProspectId = index;
    const prospect = prospects[index];
    
    // Display immediately with available data
    displayProspectDetails(prospect);
    
    // Optionally fetch fresh data from server
    try {
        const response = await fetch(`${API_BASE}/api/prospect/${index}`);
        const data = await response.json();
        if (data.success) {
            displayProspectDetails(data.prospect);
        }
    } catch (error) {
        console.error('Error fetching prospect details:', error);
    }
    
    detailModal.style.display = 'block';
}

// Display prospect details (for modal - kept for compatibility)
function displayProspectDetails(prospect) {
    const detailsEl = document.getElementById('prospectDetails');
    
    detailsEl.innerHTML = `
        <div class="detail-item">
            <span class="detail-label">Full Name</span>
            <div class="detail-value">${prospect.full_name || `${prospect.first_name} ${prospect.last_name}`}</div>
        </div>
        
        <div class="detail-item">
            <span class="detail-label">Company Name</span>
            <div class="detail-value">${prospect.company_name || 'Not specified'}</div>
        </div>
        
        ${prospect.company_domain ? `
        <div class="detail-item">
            <span class="detail-label">Company Domain</span>
            <div class="detail-value">${prospect.company_domain}</div>
        </div>
        ` : ''}
        
        ${prospect.email ? `
        <div class="detail-item">
            <span class="detail-label">Email Address</span>
            <div class="detail-value">
                <a href="mailto:${prospect.email}">${prospect.email}</a>
            </div>
        </div>
        ` : '<div class="detail-item"><div class="detail-value" style="color: #f59e0b;">⚠️ Email not found</div></div>'}
        
        ${prospect.linkedin_profile ? `
        <div class="detail-item">
            <span class="detail-label">LinkedIn Profile</span>
            <div class="detail-value">
                <a href="${prospect.linkedin_profile}" target="_blank" rel="noopener noreferrer">
                    ${prospect.linkedin_profile}
                </a>
            </div>
        </div>
        ` : ''}
        
        ${prospect.job_title ? `
        <div class="detail-item">
            <span class="detail-label">Job Title</span>
            <div class="detail-value">${prospect.job_title}</div>
        </div>
        ` : ''}
    `;
}

// ============================================
// Status Updates
// ============================================
function updateStatus(status) {
    totalProspectsEl.textContent = status.total_prospects || 0;
    emailsFoundEl.textContent = status.emails_found || 0;
    emailsSentEl.textContent = status.emails_sent || 0;
    
    if (status.current_step) {
        updateStatusMessage(status.current_step);
    }
}

function updateStatusMessage(message) {
    statusMessageEl.textContent = message;
}

function setLoading(loading) {
    searchBtn.disabled = loading;
    if (loading) {
        searchBtnText.style.display = 'none';
        searchBtnSpinner.style.display = 'inline-block';
    } else {
        searchBtnText.style.display = 'inline';
        searchBtnSpinner.style.display = 'none';
    }
}

// ============================================
// Gmail OAuth Authentication
// ============================================
async function checkGmailAuth() {
    if (!emailInput || !authStatus) return;
    
    const email = emailInput.value.trim();
    if (!email) {
        if (authStatus) authStatus.style.display = 'none';
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/oauth/check`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email: email })
        });
        
        const data = await response.json();
        if (data.success && data.authenticated) {
            showAuthStatus('✅ Gmail authenticated', 'success');
            if (authGmailText) authGmailText.textContent = '✅ Authenticated';
            if (authGmailBtn) authGmailBtn.disabled = true;
        } else {
            showAuthStatus('⚠️ Gmail not authenticated. Click to authenticate.', 'warning');
            if (authGmailText) authGmailText.textContent = '🔐 Authenticate Gmail';
            if (authGmailBtn) authGmailBtn.disabled = false;
        }
    } catch (error) {
        console.error('Error checking auth:', error);
        if (authStatus) showAuthStatus('⚠️ Could not check authentication status', 'warning');
    }
}

async function handleGmailAuth() {
    if (!emailInput) {
        alert('Email input not found');
        return;
    }
    
    const email = emailInput.value.trim();
    if (!email) {
        alert('Please enter your email address first');
        emailInput.focus();
        return;
    }
    
    if (!confirm(`This will open your browser to authenticate Gmail for ${email}.\n\nMake sure you have credentials.json file in the project root.\n\nContinue?`)) {
        return;
    }
    
    // Show loading
    if (authGmailText) authGmailText.style.display = 'none';
    if (authGmailSpinner) authGmailSpinner.style.display = 'inline-block';
    if (authGmailBtn) authGmailBtn.disabled = true;
    showAuthStatus('Opening browser for Gmail authentication...', 'info');
    
    try {
        const response = await fetch(`${API_BASE}/api/oauth/authenticate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email: email })
        });
        
        const data = await response.json();
        
        if (data.success && data.authenticated) {
            showAuthStatus('✅ Gmail authenticated successfully!', 'success');
            if (authGmailText) {
                authGmailText.textContent = '✅ Authenticated';
                authGmailText.style.display = 'inline';
            }
            if (authGmailBtn) authGmailBtn.disabled = true;
            alert('Gmail authentication successful! You can now send emails.');
        } else if (data.credentials_missing || (data.error && data.error.includes('credentials'))) {
            const errorMsg = data.error || 'OAuth credentials not configured';
            showAuthStatus('❌ OAuth credentials not configured', 'error');
            alert(errorMsg + '\n\nPlease:\n1. Download credentials.json from Google Cloud Console\n2. Place it in the project root directory\n3. See OAUTH_SETUP.md for detailed instructions');
        } else {
            const errorMsg = data.error || 'Authentication failed';
            showAuthStatus(`⚠️ ${errorMsg}`, 'error');
            alert(`Authentication failed: ${errorMsg}`);
            if (authGmailText) {
                authGmailText.textContent = '🔐 Authenticate Gmail';
                authGmailText.style.display = 'inline';
            }
            if (authGmailBtn) authGmailBtn.disabled = false;
        }
    } catch (error) {
        console.error('Auth error:', error);
        showAuthStatus('❌ Error during authentication: ' + error.message, 'error');
        alert('Failed to authenticate. Error: ' + error.message + '\n\nMake sure the Flask server is running and credentials.json exists.');
        if (authGmailText) {
            authGmailText.textContent = '🔐 Authenticate Gmail';
            authGmailText.style.display = 'inline';
        }
        if (authGmailBtn) authGmailBtn.disabled = false;
    } finally {
        if (authGmailSpinner) authGmailSpinner.style.display = 'none';
    }
}

function showAuthStatus(message, type) {
    if (!authStatus) return;
    authStatus.textContent = message;
    authStatus.className = `auth-status auth-${type}`;
    authStatus.style.display = 'block';
}

// Make functions available globally
window.handleGmailAuth = handleGmailAuth;
window.checkGmailAuth = checkGmailAuth;
