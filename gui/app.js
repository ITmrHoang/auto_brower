const API_BASE = "http://127.0.0.1:8000/api";
let currentProfile = null;
let isRecording = false;

// DOM Elements
const profileList = document.getElementById("profile-list");
const scriptList = document.getElementById("script-list");
const selectedProfileName = document.getElementById("selected-profile-name");
const emptyState = document.getElementById("empty-state");
const profileDetails = document.getElementById("profile-details");
const mainActions = document.getElementById("main-actions");

const btnLaunch = document.getElementById("btn-launch");
const btnClose = document.getElementById("btn-close");
const btnStartRecord = document.getElementById("btn-start-record");
const btnStopRecord = document.getElementById("btn-stop-record");

// Fetch state periodically
async function fetchProfiles() {
    try {
        const res = await fetch(`${API_BASE}/profiles`);
        const profiles = await res.json();
        renderProfiles(profiles);
        // Retain selection info if needed
        if (currentProfile) {
            const up = profiles.find(p => p.name === currentProfile.name);
            if (up) {
                currentProfile = up;
                updateMainView();
            }
        }
    } catch (e) { console.error("API error fetching profiles", e); }
}

async function fetchScripts() {
    try {
        const res = await fetch(`${API_BASE}/scripts`);
        const scripts = await res.json();
        renderScripts(scripts);
    } catch (e) { }
}

async function fetchSyncStatus() {
    try {
        const res = await fetch(`${API_BASE}/sync/status`);
        const status = await res.json();
        isRecording = status.record_mode && status.running && status.root === (currentProfile ? currentProfile.name : null);
        updateMainView();
    } catch (e) { }
}

function renderProfiles(profiles) {
    profileList.innerHTML = "";
    profiles.forEach(p => {
        const el = document.createElement("div");
        el.className = `sidebar-item ${currentProfile?.name === p.name ? 'active' : ''}`;
        el.onclick = () => selectProfile(p);

        el.innerHTML = `
            <div class="profile-info">
                <i class="fa-solid fa-user profile-icon"></i>
                <span>${p.name}</span>
            </div>
            <div class="status-indicator ${p.status === 'running' ? 'running' : ''}" title="${p.status}"></div>
        `;
        profileList.appendChild(el);
    });
}

function renderScripts(scripts) {
    scriptList.innerHTML = "";
    scripts.forEach(s => {
        const el = document.createElement("div");
        el.className = 'sidebar-item';
        el.innerHTML = `
            <div class="profile-info">
                <i class="fa-brands fa-js profile-icon"></i>
                <span>${s.name}</span>
            </div>
            <button class="btn-icon" title="Run on selected" onclick="runScript('${s.name}')">
                <i class="fa-solid fa-play"></i>
            </button>
        `;
        scriptList.appendChild(el);
    });
}

function selectProfile(profile) {
    currentProfile = profile;
    fetchProfiles(); // updates active state in list
    updateMainView();
}

function updateMainView() {
    if (!currentProfile) {
        emptyState.style.display = "flex";
        profileDetails.style.display = "none";
        mainActions.style.display = "none";
        return;
    }

    emptyState.style.display = "none";
    profileDetails.style.display = "block";
    mainActions.style.display = "flex";

    selectedProfileName.innerText = currentProfile.name;
    document.getElementById("lbl-proxy").innerText = currentProfile.proxy || "System Interface";

    const isRunning = currentProfile.status === "running";

    // Toggle launch/close
    btnLaunch.style.display = isRunning ? "none" : "block";
    btnClose.style.display = isRunning ? "block" : "none";

    // Toggle Record UI
    if (isRunning) {
        btnStartRecord.disabled = false;
        if (isRecording) {
            btnStartRecord.style.display = "none";
            btnStopRecord.style.display = "flex";
            document.getElementById("record-status").innerHTML = `<span class="text-danger"><i class="fa-solid fa-circle fa-fade"></i> Recording actions...</span>`;
        } else {
            btnStartRecord.style.display = "flex";
            btnStopRecord.style.display = "none";
            document.getElementById("record-status").innerText = "Ready to record actions.";
        }
    } else {
        btnStartRecord.disabled = true;
        btnStartRecord.style.display = "flex";
        btnStopRecord.style.display = "none";
        document.getElementById("record-status").innerText = "Browser must be running to record.";
    }
}

// Actions
btnLaunch.onclick = async () => {
    btnLaunch.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Launching...`;
    await fetch(`${API_BASE}/browser/launch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            profile_name: currentProfile.name
        })
    });
    setTimeout(fetchProfiles, 1500);
};

btnClose.onclick = async () => {
    await fetch(`${API_BASE}/browser/close`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile_name: currentProfile.name })
    });
    setTimeout(fetchProfiles, 1000);
};

// Record mechanism
btnStartRecord.onclick = async () => {
    await fetch(`${API_BASE}/record/start`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ root_profile: currentProfile.name })
    });
    isRecording = true;
    updateMainView();
};

btnStopRecord.onclick = () => {
    document.getElementById("modal-save-record").classList.add("active");
};

// Add Profile Modal logic
document.getElementById("btn-add-profile").onclick = () => {
    document.getElementById("modal-add-profile").classList.add("active");
};

document.querySelectorAll("#btn-close-modal").forEach(el => {
    el.onclick = () => {
        document.getElementById("modal-add-profile").classList.remove("active");
        document.getElementById("modal-save-record").classList.remove("active");
    };
});

document.getElementById("btn-submit-profile").onclick = async () => {
    const name = document.getElementById("inp-profile-name").value;
    const proxy = document.getElementById("inp-proxy").value;
    const puser = document.getElementById("inp-proxy-user").value;
    const ppass = document.getElementById("inp-proxy-pass").value;

    if (!name) return alert("Name required");

    await fetch(`${API_BASE}/profiles`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, proxy: proxy || null, proxy_username: puser || null, proxy_password: ppass || null })
    });
    document.getElementById("modal-add-profile").classList.remove("active");
    fetchProfiles();
};

document.getElementById("btn-delete").onclick = async () => {
    if (confirm("Delete " + currentProfile.name + "?")) {
        await fetch(`${API_BASE}/profiles/${currentProfile.name}`, { method: "DELETE" });
        currentProfile = null;
        fetchProfiles();
    }
};

document.getElementById("btn-submit-record").onclick = async () => {
    const fn = document.getElementById("inp-script-name").value || "script";
    const res = await fetch(`${API_BASE}/record/stop`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: fn })
    });
    const data = await res.json();
    document.getElementById("modal-save-record").classList.remove("active");
    isRecording = false;
    updateMainView();
    fetchScripts();
};

async function runScript(name) {
    if (!currentProfile) return alert("Select a profile target first");
    alert(`Running ${name} on ${currentProfile.name}`);
    await fetch(`${API_BASE}/scripts/run`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ script_name: name, target_profiles: [currentProfile.name] })
    });
}

// Initial pull
fetchProfiles();
fetchScripts();
setInterval(fetchProfiles, 3000);
setInterval(fetchSyncStatus, 2000);
