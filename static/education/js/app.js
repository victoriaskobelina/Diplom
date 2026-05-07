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

function normalizePhoneDigits(value, maxDigits = 14) {
    const rawDigits = value.replace(/\D/g, "");
    if (!rawDigits) {
        return "";
    }

    let digits = rawDigits;
    if (digits.startsWith("8")) {
        digits = `7${digits.slice(1)}`;
    } else if (!digits.startsWith("7")) {
        digits = `7${digits}`;
    }
    return digits.slice(0, maxDigits);
}

function formatPhoneValue(value, maxDigits = 14) {
    const digits = normalizePhoneDigits(value, maxDigits);
    if (!digits) {
        return "";
    }

    const local = digits.slice(1, 11);
    const extension = digits.slice(11);
    let formatted = "+7";

    if (local.length) {
        formatted += ` (${local.slice(0, 3)}`;
    }
    if (local.length >= 3) {
        formatted += ")";
    }
    if (local.length > 3) {
        formatted += ` ${local.slice(3, 6)}`;
    }
    if (local.length > 6) {
        formatted += `-${local.slice(6, 8)}`;
    }
    if (local.length > 8) {
        formatted += `-${local.slice(8, 10)}`;
    }
    if (extension.length) {
        formatted += ` ${extension}`;
    }

    return formatted;
}

function formatPersonNameValue(value) {
    return value
        .replace(/[^A-Za-zА-Яа-яЁё\s-]/g, "")
        .replace(/\s{2,}/g, " ");
}

function formatEmailValue(value) {
    return value
        .toLowerCase()
        .replace(/\s+/g, "")
        .replace(/[^a-z0-9@._%+-]/g, "");
}

function initInputMasks() {
    const phoneFields = document.querySelectorAll('input[data-mask="phone"]');
    phoneFields.forEach((field) => {
        const maxDigits = parseInt(field.dataset.maxDigits || "14", 10);
        field.addEventListener("beforeinput", (event) => {
            if (event.inputType.startsWith("insert") && event.data && /\D/.test(event.data)) {
                event.preventDefault();
            }
        });
        field.addEventListener("input", () => {
            field.value = formatPhoneValue(field.value, maxDigits);
        });
        field.addEventListener("blur", () => {
            field.value = formatPhoneValue(field.value, maxDigits);
        });
        field.value = formatPhoneValue(field.value, maxDigits);
    });

    const personNameFields = document.querySelectorAll('input[data-mask="person-name"]');
    personNameFields.forEach((field) => {
        field.addEventListener("input", () => {
            field.value = formatPersonNameValue(field.value);
        });
        field.addEventListener("blur", () => {
            field.value = formatPersonNameValue(field.value).trim();
        });
    });

    const emailFields = document.querySelectorAll('input[data-mask="email"]');
    emailFields.forEach((field) => {
        field.addEventListener("beforeinput", (event) => {
            if (event.inputType.startsWith("insert") && event.data && /\s/.test(event.data)) {
                event.preventDefault();
            }
        });
        field.addEventListener("input", () => {
            field.value = formatEmailValue(field.value);
        });
        field.addEventListener("blur", () => {
            field.value = formatEmailValue(field.value);
        });
        field.value = formatEmailValue(field.value);
    });
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

window.enforceSingleCorrectCheckbox = function(currentCheckbox) {
    if (!currentCheckbox || !currentCheckbox.checked) {
        return;
    }

    const scope =
        currentCheckbox.closest(".formset-grid") ||
        currentCheckbox.closest("form") ||
        document;

    scope
        .querySelectorAll('input[type="checkbox"][data-single-correct="true"]')
        .forEach((otherCheckbox) => {
            if (otherCheckbox !== currentCheckbox) {
                otherCheckbox.checked = false;
            }
        });
};

function initSingleCorrectCheckboxes() {
    const checkboxes = document.querySelectorAll('input[type="checkbox"][data-single-correct="true"]');
    if (!checkboxes.length) {
        return;
    }

    checkboxes.forEach((checkbox) => {
        checkbox.addEventListener("change", () => {
            window.enforceSingleCorrectCheckbox(checkbox);
        });
    });
}

function initConfirmationModal() {
    const modal = document.querySelector("[data-confirm-modal]");
    const messageNode = modal?.querySelector("[data-confirm-modal-message]");
    const approveButton = modal?.querySelector("[data-confirm-approve]");
    const cancelButtons = modal?.querySelectorAll("[data-confirm-cancel]");
    const confirmationTriggers = document.querySelectorAll("[data-confirm-message]");
    if (!modal || !messageNode || !approveButton || !cancelButtons?.length || !confirmationTriggers.length) {
        return;
    }

    let pendingAction = null;
    let previouslyFocusedElement = null;

    const focusableSelector = [
        "button:not([disabled])",
        "[href]",
        "input:not([disabled])",
        "select:not([disabled])",
        "textarea:not([disabled])",
        '[tabindex]:not([tabindex="-1"])',
    ].join(", ");

    const getFocusableElements = () =>
        Array.from(modal.querySelectorAll(focusableSelector)).filter((element) => !element.hidden);

    const closeModal = ({ restoreFocus = true } = {}) => {
        modal.hidden = true;
        document.body.classList.remove("confirm-modal-open");
        messageNode.textContent = "";
        pendingAction = null;

        if (restoreFocus && previouslyFocusedElement && typeof previouslyFocusedElement.focus === "function") {
            previouslyFocusedElement.focus();
        }
    };

    const openModal = (message, action) => {
        pendingAction = action;
        previouslyFocusedElement = document.activeElement;
        messageNode.textContent = message;
        modal.hidden = false;
        document.body.classList.add("confirm-modal-open");
        approveButton.focus();
    };

    approveButton.addEventListener("click", () => {
        if (!pendingAction) {
            closeModal();
            return;
        }

        const action = pendingAction;
        closeModal({ restoreFocus: false });

        if (action.type === "submitter" && action.submitter?.form) {
            action.submitter.form.requestSubmit(action.submitter);
            return;
        }

        if (action.type === "link" && action.link?.href) {
            window.location.assign(action.link.href);
        }
    });

    cancelButtons.forEach((button) => {
        button.addEventListener("click", () => {
            closeModal();
        });
    });

    document.addEventListener("keydown", (event) => {
        if (modal.hidden) {
            return;
        }

        if (event.key === "Escape") {
            event.preventDefault();
            closeModal();
            return;
        }

        if (event.key !== "Tab") {
            return;
        }

        const focusableElements = getFocusableElements();
        if (!focusableElements.length) {
            return;
        }

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (event.shiftKey && document.activeElement === firstElement) {
            event.preventDefault();
            lastElement.focus();
        } else if (!event.shiftKey && document.activeElement === lastElement) {
            event.preventDefault();
            firstElement.focus();
        }
    });

    confirmationTriggers.forEach((element) => {
        element.addEventListener("click", (event) => {
            const message = element.dataset.confirmMessage;
            if (!message) {
                return;
            }

            if (element.tagName === "A") {
                event.preventDefault();
                openModal(message, { type: "link", link: element });
                return;
            }

            if (element.form) {
                event.preventDefault();
                openModal(message, { type: "submitter", submitter: element });
            }
        });
    });
}

document.addEventListener("DOMContentLoaded", () => {
    initRoleDependentFields();
    initInputMasks();
    initTestAutosave();
    initTestTimer();
    initSingleCorrectCheckboxes();
    initConfirmationModal();
});
