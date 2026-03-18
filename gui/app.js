const API_BASE = "http://127.0.0.1:8000/api";
let currentProfile = null;
let isRecording = false;
let allProfiles = []; // Cache for populating sync/run modals

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

// ─── Fetch state periodically ────────────────────────────────
async function fetchProfiles() {
    try {
        const res = await fetch(`${API_BASE}/profiles`);
        const profiles = await res.json();
        allProfiles = profiles;
        renderProfiles(profiles);
        if (currentProfile) {
            const up = profiles.find(p => p.name === currentProfile.name);
            if (up) {
                currentProfile = up;
                updateMainView();
            }
        }
        updateSyncPanel(profiles);
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
        updateSyncStatusUI(status);
        updateMainView();
    } catch (e) { }
}

// ─── Renderers ───────────────────────────────────────────────
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
            <button class="btn-icon" title="Run script" onclick="openRunScriptModal('${s.name}')">
                <i class="fa-solid fa-play"></i>
            </button>
        `;
        scriptList.appendChild(el);
    });
}

// ─── Profile Selection & Main View ──────────────────────────
function selectProfile(profile) {
    currentProfile = profile;
    fetchProfiles();
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

    btnLaunch.style.display = isRunning ? "none" : "block";
    btnClose.style.display = isRunning ? "block" : "none";

    // Record UI
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

// ─── Launch / Close ──────────────────────────────────────────
btnLaunch.onclick = async () => {
    btnLaunch.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Launching...`;
    btnLaunch.disabled = true;
    try {
        await fetch(`${API_BASE}/browser/launch`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ profile_name: currentProfile.name })
        });
    } catch (e) { console.error("Launch failed", e); }
    btnLaunch.innerHTML = `<i class="fa-solid fa-play"></i> Launch`;
    btnLaunch.disabled = false;
    await fetchProfiles();
};

btnClose.onclick = async () => {
    btnClose.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Closing...`;
    btnClose.disabled = true;
    try {
        await fetch(`${API_BASE}/browser/close`, {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ profile_name: currentProfile.name })
        });
    } catch (e) { console.error("Close failed", e); }
    btnClose.innerHTML = `<i class="fa-solid fa-stop"></i> Close Browser`;
    btnClose.disabled = false;
    await fetchProfiles();
};

// ─── Record ──────────────────────────────────────────────────
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

document.getElementById("btn-submit-record").onclick = async () => {
    const fn = document.getElementById("inp-script-name").value || "script";
    await fetch(`${API_BASE}/record/stop`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: fn })
    });
    document.getElementById("modal-save-record").classList.remove("active");
    isRecording = false;
    updateMainView();
    fetchScripts();
};

// ─── Sync Panel ──────────────────────────────────────────────
function updateSyncPanel(profiles) {
    const running = profiles.filter(p => p.status === "running");
    const followerList = document.getElementById("sync-follower-list");
    const btnStart = document.getElementById("btn-sync-start");
    const rootLabel = document.getElementById("sync-root-label");

    if (!currentProfile || currentProfile.status !== "running") {
        rootLabel.innerText = "—";
        followerList.innerHTML = `<span class="text-dim text-sm">Profile phải đang chạy để đồng bộ</span>`;
        btnStart.disabled = true;
        return;
    }

    rootLabel.innerText = currentProfile.name + " (Root)";

    const otherRunning = running.filter(p => p.name !== currentProfile.name);
    if (otherRunning.length === 0) {
        followerList.innerHTML = `<span class="text-dim text-sm">Không có profile nào khác đang chạy</span>`;
        btnStart.disabled = true;
    } else {
        followerList.innerHTML = otherRunning.map(p => `
            <label class="checkbox-label">
                <input type="checkbox" class="sync-follower-cb" value="${p.name}" checked>
                <span>${p.name}</span>
            </label>
        `).join("");
        btnStart.disabled = false;
    }
}

function updateSyncStatusUI(status) {
    const btnStart = document.getElementById("btn-sync-start");
    const btnStop = document.getElementById("btn-sync-stop");
    const statusText = document.getElementById("sync-status-text");

    if (status.running && !status.record_mode) {
        btnStart.style.display = "none";
        btnStop.style.display = "flex";
        statusText.innerHTML = `<span class="text-success"><i class="fa-solid fa-circle fa-fade"></i> Đang đồng bộ: ${status.root} → ${status.followers.join(", ")}</span>`;
    } else {
        btnStart.style.display = "flex";
        btnStop.style.display = "none";
        statusText.innerText = "Chọn profile làm Root, các profile khác đang chạy sẽ trở thành Follower.";
    }
}

document.getElementById("btn-sync-start").onclick = async () => {
    const followers = Array.from(document.querySelectorAll(".sync-follower-cb:checked")).map(cb => cb.value);
    if (followers.length === 0) return alert("Chọn ít nhất 1 follower");

    const btn = document.getElementById("btn-sync-start");
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Starting...`;
    btn.disabled = true;

    try {
        await fetch(`${API_BASE}/sync/start`, {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ root_profile: currentProfile.name, followers })
        });
    } catch (e) { console.error("Sync start failed", e); }

    btn.innerHTML = `<i class="fa-solid fa-play"></i> Start Sync`;
    btn.disabled = false;
    await fetchSyncStatus();
};

document.getElementById("btn-sync-stop").onclick = async () => {
    const btn = document.getElementById("btn-sync-stop");
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Stopping...`;
    try {
        await fetch(`${API_BASE}/sync/stop`, { method: "POST" });
    } catch (e) { console.error("Sync stop failed", e); }
    btn.innerHTML = `<i class="fa-solid fa-stop"></i> Stop Sync`;
    await fetchSyncStatus();
};

// ─── Run Script Modal ────────────────────────────────────────
function openRunScriptModal(scriptName) {
    document.getElementById("run-script-name").value = scriptName;
    document.getElementById("run-loop").value = 1;
    document.getElementById("run-delay").value = 0;

    const targetList = document.getElementById("run-target-list");
    const running = allProfiles.filter(p => p.status === "running");
    if (running.length === 0) {
        targetList.innerHTML = `<span class="text-dim text-sm">Không có profile nào đang chạy</span>`;
    } else {
        targetList.innerHTML = running.map(p => `
            <label class="checkbox-label">
                <input type="checkbox" class="run-target-cb" value="${p.name}" ${currentProfile?.name === p.name ? 'checked' : ''}>
                <span>${p.name}</span>
            </label>
        `).join("");
    }
    document.getElementById("modal-run-script").classList.add("active");
}

document.getElementById("btn-submit-run-script").onclick = async () => {
    const scriptName = document.getElementById("run-script-name").value;
    const targets = Array.from(document.querySelectorAll(".run-target-cb:checked")).map(cb => cb.value);
    const loop = parseInt(document.getElementById("run-loop").value) || 1;
    const delay = parseInt(document.getElementById("run-delay").value) || 0;

    if (targets.length === 0) return alert("Chọn ít nhất 1 target profile");

    const btn = document.getElementById("btn-submit-run-script");
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Running...`;
    btn.disabled = true;

    try {
        await fetch(`${API_BASE}/scripts/run`, {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ script_name: scriptName, target_profiles: targets, loop, delay_ms: delay })
        });
    } catch (e) { console.error("Script run failed", e); }

    btn.innerHTML = `<i class="fa-solid fa-play"></i> Run`;
    btn.disabled = false;
    document.getElementById("modal-run-script").classList.remove("active");
};

// ─── Script Editor Modal ─────────────────────────────────────
document.getElementById("btn-new-script").onclick = () => {
    document.getElementById("editor-script-name").value = "";
    document.getElementById("editor-code").value = "";
    document.getElementById("editor-loop").value = 1;
    document.getElementById("editor-delay").value = 0;
    document.getElementById("modal-script-editor").classList.add("active");
};

document.getElementById("btn-save-script").onclick = async () => {
    const name = document.getElementById("editor-script-name").value;
    const code = document.getElementById("editor-code").value;
    const loop = parseInt(document.getElementById("editor-loop").value) || 1;
    const delay = parseInt(document.getElementById("editor-delay").value) || 0;

    if (!name) return alert("Nhập tên script");
    if (!code.trim()) return alert("Nhập code JavaScript");

    const btn = document.getElementById("btn-save-script");
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Saving...`;
    btn.disabled = true;

    try {
        await fetch(`${API_BASE}/scripts/save`, {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, code, loop, delay_ms: delay })
        });
    } catch (e) { console.error("Script save failed", e); }

    btn.innerHTML = `<i class="fa-solid fa-save"></i> Save Script`;
    btn.disabled = false;
    document.getElementById("modal-script-editor").classList.remove("active");
    fetchScripts();
};

// ─── Profile Modal ───────────────────────────────────────────
document.getElementById("btn-add-profile").onclick = () => {
    document.getElementById("modal-add-profile").classList.add("active");
};

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

// ─── Close any modal ─────────────────────────────────────────
document.querySelectorAll("#btn-close-modal, .btn-close-any-modal").forEach(el => {
    el.onclick = () => {
        document.querySelectorAll(".modal-overlay").forEach(m => m.classList.remove("active"));
    };
});

// Close modal on backdrop click
document.querySelectorAll(".modal-overlay").forEach(overlay => {
    overlay.addEventListener("click", (e) => {
        if (e.target === overlay) overlay.classList.remove("active");
    });
});

// ─── Initial pull & polling ──────────────────────────────────
fetchProfiles();
fetchScripts();
setInterval(fetchProfiles, 3000);
setInterval(fetchSyncStatus, 2000);
