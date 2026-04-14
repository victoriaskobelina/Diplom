function getCookie(name) {
    const cookieValue = document.cookie
        .split(";")
        .map((item) => item.trim())
        .find((item) => item.startsWith(`${name}=`));
    return cookieValue ? decodeURIComponent(cookieValue.split("=")[1]) : "";
}

function toggleAcademicGroupField() {
    const roleField = document.getElementById("id_role");
    const groupField = document.querySelector('[data-field-name="academic_group"]');
    if (!roleField || !groupField) {
        return;
    }
    const visible = roleField.value === "student";
    groupField.style.display = visible ? "" : "none";
}

function initRoleDependentFields() {
    const roleField = document.getElementById("id_role");
    if (!roleField) {
        return;
    }
    roleField.addEventListener("change", toggleAcademicGroupField);
    toggleAcademicGroupField();
}

function initTestAutosave() {
    const radios = document.querySelectorAll('input[type="radio"][data-save-url]');
    const statusNode = document.querySelector("[data-save-status]");
    if (!radios.length) {
        return;
    }

    radios.forEach((radio) => {
        radio.addEventListener("change", async () => {
            const formData = new FormData();
            formData.append("option_id", radio.value);
            try {
                const response = await fetch(radio.dataset.saveUrl, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": getCookie("csrftoken"),
                    },
                    body: formData,
                });
                const payload = await response.json();
                if (statusNode) {
                    statusNode.dataset.state = payload.ok ? "saved" : "error";
                    statusNode.textContent = payload.message || "Ответ сохранён";
                }
            } catch (error) {
                if (statusNode) {
                    statusNode.dataset.state = "error";
                    statusNode.textContent = "Не удалось сохранить ответ. Попробуйте ещё раз.";
                }
            }
        });
    });
}

function initTestTimer() {
    const timerPanel = document.querySelector("[data-timer-seconds]");
    const timerDisplay = document.querySelector("[data-timer-display]");
    const finishForm = document.getElementById("finish-form");
    if (!timerPanel || !timerDisplay || !finishForm) {
        return;
    }

    let seconds = parseInt(timerPanel.dataset.timerSeconds, 10);
    if (Number.isNaN(seconds)) {
        return;
    }

    const render = () => {
        const minutes = Math.floor(seconds / 60);
        const remainder = seconds % 60;
        timerDisplay.textContent = `${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`;
    };

    render();
    const interval = window.setInterval(() => {
        seconds -= 1;
        render();
        if (seconds <= 0) {
            window.clearInterval(interval);
            finishForm.submit();
        }
    }, 1000);
}

document.addEventListener("DOMContentLoaded", () => {
    initRoleDependentFields();
    initTestAutosave();
    initTestTimer();
});
