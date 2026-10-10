let editor = null;
let serialSocket = null;
let videoSocket = null;
let currentJobInterval = null;

document.addEventListener("DOMContentLoaded", function () {
    initGridStack();
    initAceEditor();
    initSerialSocket();
    initVideoSocket();
    bindActionButtons();
});

function initGridStack() {
    const layoutKey = "stand_grid_layout_" + STAND_CONFIG.id;

    const grid = GridStack.init({
        column: 12,
        disableOneColumnMode: true,
        cellHeight: 70,
        margin: 10,
        handle: ".card-header",
        animate: true,
        resizable: {
            handles: "e, se, s, sw, w"
        }
    });

    const savedLayout = localStorage.getItem(layoutKey);
    if (savedLayout) {
        try {
            const layout = JSON.parse(savedLayout);
            grid.batchUpdate();
            grid.getGridItems().forEach(item => {
                const id = item.getAttribute("gs-id");
                if (id && layout[id]) {
                    grid.update(item, {
                        x: layout[id].x,
                        y: layout[id].y,
                        w: layout[id].w,
                        h: layout[id].h
                    });
                }
            });
            grid.commit();
        } catch (e) {
            localStorage.removeItem(layoutKey);
        }
    }

    grid.on("dragstop resizestop", function () {
        const layout = {};
        grid.getGridItems().forEach(item => {
            const id = item.getAttribute("gs-id");
            if (id && item.gridstackNode) {
                layout[id] = {
                    x: item.gridstackNode.x,
                    y: item.gridstackNode.y,
                    w: item.gridstackNode.w,
                    h: item.gridstackNode.h
                };
            }
        });
        localStorage.setItem(layoutKey, JSON.stringify(layout));
    });

    grid.on("resizestop", function () {
        if (editor) editor.resize();
    });
}

function resetStandLayout() {
    const layoutKey = "stand_grid_layout_" + STAND_CONFIG.id;
    localStorage.removeItem(layoutKey);
    window.location.reload();
}

function initAceEditor() {
    const editorElem = document.getElementById("editor");
    if (!editorElem) return;

    editor = ace.edit("editor");
    editor.setTheme("ace/theme/monokai");
    editor.session.setMode("ace/mode/c_cpp");
    editor.setFontSize(14);
    editor.setShowPrintMargin(false);

    const editorStorageKey = "stand_code_" + STAND_CONFIG.id;
    const savedCode = localStorage.getItem(editorStorageKey);
    if (savedCode !== null && savedCode.trim() !== "") {
        editor.setValue(savedCode, -1);
    }

    editor.session.on("change", function () {
        localStorage.setItem(editorStorageKey, editor.getValue());
    });

    const fileInput = document.getElementById("file-ino");
    if (fileInput) {
        fileInput.addEventListener("change", function (e) {
            const file = e.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = function (evt) {
                editor.setValue(evt.target.result, -1);
                localStorage.setItem(editorStorageKey, evt.target.result);
            };
            reader.readAsText(file);
        });
    }
}

function initVideoSocket() {
    const videoImg = document.getElementById("video-stream");
    if (!videoImg) return;

    const videoWsUrl = `${STAND_CONFIG.wsProtocol}${STAND_CONFIG.host}/ws/video/${STAND_CONFIG.id}/`;
    videoSocket = new WebSocket(videoWsUrl);

    videoSocket.onmessage = function (e) {
        try {
            const data = JSON.parse(e.data);
            if (data.type === "frame") {
                videoImg.src = "data:image/jpeg;base64," + data.data;
            }
        } catch (err) {
            console.error(err);
        }
    };

    videoSocket.onclose = function () {
        console.log("Відео-сокет закрито.");
    };
}

function initSerialSocket() {
    const monitorElem = document.getElementById("monitor");
    const serialInput = document.getElementById("serial-input");
    const btnSend = document.getElementById("btn-serial-send");

    const serialWsUrl = `${STAND_CONFIG.wsProtocol}${STAND_CONFIG.host}/ws/serial/${STAND_CONFIG.id}/`;
    serialSocket = new WebSocket(serialWsUrl);

    serialSocket.onmessage = function (e) {
        try {
            const data = JSON.parse(e.data);
            if (data.message) {
                monitorElem.textContent += data.message;
                monitorElem.scrollTop = monitorElem.scrollHeight;
            }
        } catch (err) {
            console.error(err);
        }
    };

    function sendSerialMsg() {
        if (!serialSocket || serialSocket.readyState !== WebSocket.OPEN) return;
        const msg = serialInput.value;
        if (!msg) return;
        serialSocket.send(JSON.stringify({ message: msg + "\n", sender: "user" }));
        serialInput.value = "";
    }

    if (btnSend) btnSend.addEventListener("click", sendSerialMsg);
    if (serialInput) {
        serialInput.addEventListener("keydown", function (e) {
            if (e.key === "Enter") sendSerialMsg();
        });
    }
}

function pollJobStatus(jobId, monitorElement, endpoint, onDoneCallback = null) {
    if (currentJobInterval) clearInterval(currentJobInterval);

    currentJobInterval = setInterval(() => {
        fetch(`${endpoint}${jobId}/`, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": STAND_CONFIG.csrfToken
            }
        })
        .then(res => res.json())
        .then(data => {
            if (!data) return;
            const status = data.status;
            const output = data.output || "";

            if (status === "completed" || status === "failed" || status === "cancelling") {
                clearInterval(currentJobInterval);
                monitorElement.textContent = `--- ЗАВДАННЯ #${jobId} ЗАВЕРШЕНО (Статус: ${status}) ---\n\n${output}`;
                monitorElement.scrollTop = monitorElement.scrollHeight;
                if (onDoneCallback) onDoneCallback(status === "completed");
            } else if (status === "running") {
                monitorElement.textContent = `[${new Date().toLocaleTimeString()}] Завдання #${jobId} виконується...\n\n(Агент: ${output || "..."})`;
            } else {
                monitorElement.textContent = `[${new Date().toLocaleTimeString()}] Завдання #${jobId} в черзі...`;
            }
        })
        .catch(err => {
            console.error(err);
            clearInterval(currentJobInterval);
        });
    }, 1000);
}

function sendJob(endpoint, payload, monitorElem) {
    return fetch(endpoint, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": STAND_CONFIG.csrfToken
        },
        body: JSON.stringify(payload)
    }).then(res => res.json());
}

function bindActionButtons() {
    const monitorElem = document.getElementById("monitor");
    const libLogElem = document.getElementById("lib-log");

    const btnFlash = document.getElementById("btn-flash");
    if (btnFlash) {
        btnFlash.addEventListener("click", function () {
            const baudSelect = document.getElementById("baud-rate");
            const baud = baudSelect ? parseInt(baudSelect.value) : 9600;
            const payload = {
                stand: STAND_CONFIG.id,
                code_to_flash: editor.getValue(),
                baud_rate: baud,
                status: "pending"
            };
            monitorElem.textContent = "Створення завдання на прошивку...";
            sendJob("/api/jobs/", payload, monitorElem).then(data => {
                pollJobStatus(data.id, monitorElem, "/api/jobs/");
            });
        });
    }

    const btnCompile = document.getElementById("btn-compile");
    if (btnCompile) {
        btnCompile.addEventListener("click", function () {
            const payload = {
                stand: STAND_CONFIG.id,
                code_to_compile: editor.getValue(),
                status: "pending"
            };
            monitorElem.textContent = "Створення завдання на компіляцію...";
            sendJob("/api/compile-jobs/", payload, monitorElem).then(data => {
                pollJobStatus(data.id, monitorElem, "/api/compile-jobs/");
            });
        });
    }

    const btnInstallLib = document.getElementById("btn-install-lib");
    if (btnInstallLib) {
        btnInstallLib.addEventListener("click", function () {
            const libName = document.getElementById("lib-name-input").value.trim();
            if (!libName) return;
            const payload = {
                stand: STAND_CONFIG.id,
                library_name: libName,
                status: "pending",
                job_type: "install"
            };
            libLogElem.textContent = `Встановлення ${libName}...`;
            sendJob("/api/lib-jobs/", payload, libLogElem).then(data => {
                pollJobStatus(data.id, libLogElem, "/api/lib-jobs/", (isSuccess) => {
                    if (isSuccess) setTimeout(() => location.reload(), 1000);
                });
            });
        });
    }

    const btnInstallZip = document.getElementById("btn-install-zip");
    if (btnInstallZip) {
        btnInstallZip.addEventListener("click", function () {
            const fileInput = document.getElementById("lib-zip-input");
            const file = fileInput.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append("stand", STAND_CONFIG.id);
            formData.append("status", "pending");
            formData.append("job_type", "install");
            formData.append("library_zip", file);

            libLogElem.textContent = "Завантаження архіву бібліотеки на сервер...";
            fetch("/api/lib-jobs/", {
                method: "POST",
                headers: { "X-CSRFToken": STAND_CONFIG.csrfToken },
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                pollJobStatus(data.id, libLogElem, "/api/lib-jobs/", (isSuccess) => {
                    if (isSuccess) setTimeout(() => location.reload(), 1000);
                });
            });
        });
    }
}

window.uninstallLibrary = function (libName) {
    if (!confirm(`Видалити бібліотеку ${libName}?`)) return;
    const libLogElem = document.getElementById("lib-log");
    const payload = {
        stand: STAND_CONFIG.id,
        library_name: libName,
        status: "pending",
        job_type: "uninstall"
    };
    libLogElem.textContent = `Видалення ${libName}...`;
    sendJob("/api/lib-jobs/", payload, libLogElem).then(data => {
        pollJobStatus(data.id, libLogElem, "/api/lib-jobs/", (isSuccess) => {
            if (isSuccess) setTimeout(() => location.reload(), 1000);
        });
    });
};
