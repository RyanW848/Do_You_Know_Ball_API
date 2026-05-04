async function loadApiKeyStatus() {
  const container = document.getElementById("apikeyContainer");

  try {
    const response = await fetch("/api-keys/status", {
      method: "GET",
      credentials: "include",
      headers: { "Content-Type": "application/json" }
    });

    const data = await response.json();

    if (!response.ok) {
      container.innerHTML = `<div class="apikeys-error">Error: ${data.error || "Failed to load API key status"}</div>`;
      return;
    }

    if (data.has_key) {
      renderKeyStatus(data);
    } else {
      renderNoKeyState();
    }
  } catch (err) {
    container.innerHTML = `<div class="apikeys-error">An error occurred. Please try again.</div>`;
    console.error(err);
  }
}

function renderNoKeyState() {
  const container = document.getElementById("apikeyContainer");

  container.innerHTML = `
    <div class="apikeys-warning">
      <strong>No API Key Found</strong><br/>
      You haven't generated an API key yet. Generate one now to start using the API.
    </div>

    <h2>Generate API Key</h2>
    <p style="font-size: 0.9rem; color: #4a3520; margin-bottom: 1.5rem;">
      Once generated, your API key will be displayed once. Store it securely — you won't be able to view it again.
    </p>

    <button class="apikeys-btn" id="generateBtn" onclick="generateApiKey()">Generate API Key</button>
    <div class="apikeys-error" id="generateError" style="display:none;"></div>
  `;
}

function renderKeyStatus(data) {
  const container = document.getElementById("apikeyContainer");

  const requestsLeftPercentage = Math.round((data.requests_left / 100) * 100);

  container.innerHTML = `
    <h2>API Key Status</h2>

    <div class="apikeys-section">
      <div class="apikeys-label">Account</div>
      <div class="apikeys-value">${data.username}</div>
    </div>

    <div class="apikeys-section">
      <div class="apikeys-label">Usage</div>
      <div style="background: #fff9f5; border: 1px solid #fde0c8; border-radius: 4px;">
        <div class="apikeys-stat">
          <span class="apikeys-stat-label">Requests Used Today</span>
          <span class="apikeys-stat-value">${data.daily_requests} / 100</span>
        </div>
        <div class="apikeys-stat">
          <span class="apikeys-stat-label">Requests Remaining</span>
          <span class="apikeys-stat-value">${data.requests_left}</span>
        </div>
        <div class="apikeys-stat" style="border-bottom: none;">
          <span class="apikeys-stat-label">Current Balance</span>
          <span class="apikeys-stat-value">$${data.balance.toFixed(2)}</span>
        </div>
      </div>
    </div>

    <div class="apikeys-section">
      <p style="font-size: 0.85rem; color: #a3681e; margin-top: 1rem;">
        Your daily free quota resets at 00:00 UTC. Additional requests are billed at $0.01 per request.
      </p>
    </div>
  `;
}

function renderKeyGenerated(apiKey) {
  const container = document.getElementById("apikeyContainer");

  container.innerHTML = `
    <div class="apikeys-warning">
      <strong>API Key Generated Successfully!</strong><br/>
      Save your API key now. You won't be able to view it again.
    </div>

    <h2>Your API Key</h2>
    <div class="apikeys-value" id="apiKeyDisplay">${apiKey}</div>
    <button class="apikeys-copy-btn" onclick="copyApiKey('${apiKey}')">Copy to Clipboard</button>

    <div class="apikeys-section" style="margin-top: 2rem;">
      <button class="apikeys-btn" onclick="loadApiKeyStatus()">Done</button>
    </div>
  `;
}

async function generateApiKey() {
  const btn = document.getElementById("generateBtn");
  const errorDiv = document.getElementById("generateError");

  btn.disabled = true;
  errorDiv.style.display = "none";

  try {
    const token = getCookie("token");
    
    const response = await fetch("/api-keys/generate", {
      method: "POST",
      credentials: "include",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      }
    });

    const data = await response.json();

    if (!response.ok) {
      errorDiv.textContent = data.error || "Failed to generate API key";
      errorDiv.style.display = "block";
      btn.disabled = false;
      return;
    }

    renderKeyGenerated(data.api_key);
  } catch (err) {
    errorDiv.textContent = "An error occurred. Please try again.";
    errorDiv.style.display = "block";
    btn.disabled = false;
    console.error(err);
  }
}

function copyApiKey(apiKey) {
  navigator.clipboard.writeText(apiKey).then(() => {
    alert("API key copied to clipboard!");
  }).catch(err => {
    console.error("Failed to copy:", err);
    alert("Failed to copy. Please copy manually.");
  });
}

document.addEventListener("DOMContentLoaded", loadApiKeyStatus);