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
const sendEmailsBtn = document.getElementById('sendEmailsBtn');
const detailModal = document.getElementById('detailModal');
const closeModal = document.querySelector('.close');

// Status elements
const totalProspectsEl = document.getElementById('totalProspects');
const emailsFoundEl = document.getElementById('emailsFound');
const emailsSentEl = document.getElementById('emailsSent');
const statusMessageEl = document.getElementById('statusMessage');

// Event Listeners
searchForm.addEventListener('submit', handleSearch);
sendEmailsBtn.addEventListener('click', handleSendEmails);
closeModal.addEventListener('click', () => {
    detailModal.style.display = 'none';
});

window.addEventListener('click', (e) => {
    if (e.target === detailModal) {
        detailModal.style.display = 'none';
    }
});

// Handle search form submission
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
            prospects = data.prospects;
            updateStatus(data.status);
            displayProspects(prospects);
            updateStatusMessage('Prospects found! Click on any prospect to view details.');
            
            if (prospects.length > 0 && prospects.some(p => p.email)) {
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

// Handle send emails
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

// Display prospects list
function displayProspects(prospectsList) {
    prospectsCard.style.display = 'block';
    
    if (prospectsList.length === 0) {
        prospectsList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🔍</div>
                <p>No prospects found. Try a different search query.</p>
            </div>
        `;
        return;
    }
    
    prospectsList.innerHTML = prospectsList.map((prospect, index) => `
        <div class="prospect-item" onclick="showProspectDetails(${index})">
            <div>
                <div class="prospect-name">${prospect.full_name || `${prospect.first_name} ${prospect.last_name}`}</div>
                <div class="prospect-company">${prospect.company_name || 'Unknown Company'}</div>
                ${prospect.email ? `<div class="prospect-email">📧 ${prospect.email}</div>` : ''}
            </div>
            <div class="view-details">View Details →</div>
        </div>
    `).join('');
}

// Show prospect details in modal
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

// Display prospect details
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

// Update status display
function updateStatus(status) {
    totalProspectsEl.textContent = status.total_prospects || 0;
    emailsFoundEl.textContent = status.emails_found || 0;
    emailsSentEl.textContent = status.emails_sent || 0;
    
    if (status.current_step) {
        updateStatusMessage(status.current_step);
    }
}

// Update status message
function updateStatusMessage(message) {
    statusMessageEl.textContent = message;
}

// Set loading state
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

// Poll for status updates (optional, for real-time updates)
function startStatusPolling() {
    setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/api/status`);
            const data = await response.json();
            if (data.success) {
                updateStatus(data.status);
            }
        } catch (error) {
            console.error('Status polling error:', error);
        }
    }, 2000); // Poll every 2 seconds
}

// Start status polling when page loads
// startStatusPolling();
