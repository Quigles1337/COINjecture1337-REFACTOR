// Tabs
const tabs = document.querySelectorAll('.tab');
const panels = {
  docs: document.getElementById('tab-docs'),
  console: document.getElementById('tab-console')
};

tabs.forEach(btn => {
  btn.addEventListener('click', () => {
    tabs.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    Object.values(panels).forEach(p => p.classList.remove('active'));
    panels[btn.dataset.tab].classList.add('active');
  });
});

// Render API README
async function loadDocs() {
  try {
    const res = await fetch('./API.README.md', { cache: 'no-store' });
    if (!res.ok) throw new Error('Failed to load API docs');
    const md = await res.text();
    document.getElementById('docs-content').innerHTML = marked.parse(md);
  } catch (err) {
    document.getElementById('docs-content').innerHTML = `<p style="color:#ff8">${err.message}</p>`;
  }
}
loadDocs();

// Live Console
const endpointInput = document.getElementById('endpoint');
const fetchBtn = document.getElementById('fetchBtn');
const responsePre = document.getElementById('responsePre');
const statusEl = document.getElementById('status');
const autoRefresh = document.getElementById('autoRefresh');
const refreshIntervalSelect = document.getElementById('refreshInterval');

let timer = null;

async function fetchData() {
  const url = endpointInput.value.trim();
  if (!url) return;
  setStatus('Fetching…');
  try {
    const res = await fetch(url, { cache: 'no-store' });
    const text = await res.text();
    // Try parse json, else print raw
    try {
      const data = JSON.parse(text);
      responsePre.textContent = JSON.stringify(data, null, 2);
    } catch (_) {
      responsePre.textContent = text;
    }
    setStatus(res.ok ? 'OK' : `HTTP ${res.status}`);
  } catch (e) {
    setStatus('Network error');
    responsePre.textContent = String(e);
  }
}

function setStatus(msg) {
  statusEl.textContent = msg;
}

function startAutoRefresh() {
  stopAutoRefresh();
  const seconds = Number(refreshIntervalSelect.value || '10');
  timer = setInterval(fetchData, seconds * 1000);
}

function stopAutoRefresh() {
  if (timer) clearInterval(timer);
  timer = null;
}

fetchBtn.addEventListener('click', fetchData);
autoRefresh.addEventListener('change', () => {
  if (autoRefresh.checked) {
    startAutoRefresh();
  } else {
    stopAutoRefresh();
  }
});
refreshIntervalSelect.addEventListener('change', () => {
  if (autoRefresh.checked) startAutoRefresh();
});

// Initial fetch
fetchData();


