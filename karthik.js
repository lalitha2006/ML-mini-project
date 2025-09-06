function resolveBackendBase() {
  const meta = document.querySelector('meta[name="backend-base"]');
  const fromMeta = meta ? meta.content : '';
  const fromStore = localStorage.getItem('backend_base') || '';
  const params = new URLSearchParams(window.location.search);
  const fromQuery = params.get('backend') || '';
  return fromQuery || fromStore || fromMeta || window.location.origin;
}

const backendBase = resolveBackendBase();

function qs(id) { return document.getElementById(id); }

const registerBtn = qs('registerBtn');
const loginBtn = qs('loginBtn');
const logoutBtn = qs('logoutBtn');
const predictBtn = qs('predictBtn');

const regEmail = qs('regEmail');
const regPassword = qs('regPassword');
const loginEmail = qs('loginEmail');
const loginPassword = qs('loginPassword');
const authState = qs('authState');

const registerMsg = qs('registerMsg');
const loginMsg = qs('loginMsg');
const predictMsg = qs('predictMsg');

const newsText = qs('newsText');
const result = qs('result');
const labelEl = qs('label');
const confEl = qs('confidence');

function setToken(token) {
  if (token) localStorage.setItem('access_token', token);
}

function getToken() {
  return localStorage.getItem('access_token');
}

function clearToken() {
  localStorage.removeItem('access_token');
}

function updateAuthUI() {
  const token = getToken();
  if (token) {
    authState.textContent = 'Logged in';
    logoutBtn.style.display = '';
    predictBtn.disabled = false;
  } else {
    authState.textContent = 'Not logged in';
    logoutBtn.style.display = 'none';
    predictBtn.disabled = true;
  }
}

async function register() {
  registerMsg.textContent = '';
  try {
    const res = await fetch(`${backendBase}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: regEmail.value.trim(), password: regPassword.value })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Registration failed');
    registerMsg.textContent = 'Registered successfully. You can login now.';
    registerMsg.className = 'message success';
  } catch (e) {
    registerMsg.textContent = e.message;
    registerMsg.className = 'message error';
  }
}

async function login() {
  loginMsg.textContent = '';
  try {
    const body = new URLSearchParams();
    body.append('username', loginEmail.value.trim());
    body.append('password', loginPassword.value);
    const res = await fetch(`${backendBase}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Login failed');
    setToken(data.access_token);
    loginMsg.textContent = 'Logged in';
    loginMsg.className = 'message success';
    updateAuthUI();
  } catch (e) {
    loginMsg.textContent = e.message;
    loginMsg.className = 'message error';
  }
}

async function predict() {
  predictMsg.textContent = '';
  result.hidden = true;
  try {
    const token = getToken();
    if (!token) {
      predictMsg.textContent = 'Please login first';
      predictMsg.className = 'message error';
      return;
    }
    const res = await fetch(`${backendBase}/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ text: newsText.value })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Prediction failed');
    const label = data.label;
    const confidence = (data.confidence * 100).toFixed(2) + '%';
    labelEl.textContent = label;
    labelEl.className = `badge ${label.toLowerCase()}`;
    confEl.textContent = confidence;
    result.hidden = false;
  } catch (e) {
    predictMsg.textContent = e.message;
    predictMsg.className = 'message error';
  }
}

function logout() {
  clearToken();
  updateAuthUI();
}

registerBtn.addEventListener('click', register);
loginBtn.addEventListener('click', login);
predictBtn.addEventListener('click', predict);
logoutBtn.addEventListener('click', logout);

updateAuthUI();

