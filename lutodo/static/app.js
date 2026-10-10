document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-password-toggle]").forEach((button) => {
        const input = document.getElementById(button.dataset.passwordToggle);
        if (!input) return;
        button.addEventListener("click", () => {
            const showing = input.type === "text";
            input.type = showing ? "password" : "text";
            button.textContent = showing ? "Show" : "Hide";
            button.setAttribute("aria-pressed", String(!showing));
        });
    });

    document.querySelectorAll("[data-count]").forEach((field) => {
        const output = document.querySelector(field.dataset.count);
        if (!output) return;
        const updateCount = () => {
            const maximum = field.getAttribute("maxlength");
            output.textContent = maximum ? `${field.value.length}/${maximum}` : `${field.value.length} characters`;
        };
        field.addEventListener("input", updateCount);
        updateCount();
    });

    const password = document.querySelector("[data-password-strength]");
    if (password) {
        const bar = document.querySelector("[data-strength-bar]");
        const label = document.querySelector("[data-strength-label]");
        const updateStrength = () => {
            const value = password.value;
            const checks = [value.length >= 8, /[a-z]/.test(value) && /[A-Z]/.test(value), /\d/.test(value), /[^A-Za-z0-9]/.test(value)];
            const score = checks.filter(Boolean).length;
            const labels = ["Not entered", "Weak", "Fair", "Good", "Strong"];
            const colours = ["#d8e0e7", "#b63b4a", "#d38335", "#c59b32", "#2e8a64"];
            if (bar) {
                bar.style.width = value ? `${Math.max(score, 1) * 25}%` : "0";
                bar.style.backgroundColor = colours[value ? Math.max(score, 1) : 0];
            }
            if (label) label.textContent = labels[value ? Math.max(score, 1) : 0];
        };
        password.addEventListener("input", updateStrength);
        updateStrength();
    }

    const projectSearch = document.querySelector("[data-project-search]");
    if (projectSearch) {
        const cards = [...document.querySelectorAll("[data-project-card]")];
        const empty = document.querySelector("[data-search-empty]");
        const updateProjects = () => {
            const query = projectSearch.value.trim().toLowerCase();
            let visible = 0;
            cards.forEach((card) => {
                const matches = card.textContent.toLowerCase().includes(query);
                card.classList.toggle("d-none", !matches);
                if (matches) visible += 1;
            });
            if (empty) empty.classList.toggle("d-none", visible !== 0 || !query);
        };
        projectSearch.addEventListener("input", updateProjects);
    }

    const taskFilters = document.querySelectorAll("[data-task-filter]");
    if (taskFilters.length) {
        const tasks = [...document.querySelectorAll("[data-task-card]")];
        taskFilters.forEach((button) => {
            button.addEventListener("click", () => {
                taskFilters.forEach((item) => item.classList.remove("active"));
                button.classList.add("active");
                const filter = button.dataset.taskFilter;
                tasks.forEach((task) => {
                    const matches = filter === "all" || task.dataset.status === filter || task.dataset.priority === filter;
                    task.classList.toggle("d-none", !matches);
                });
            });
        });
    }

    document.querySelectorAll("form[data-loading]").forEach((form) => {
        form.addEventListener("submit", (event) => {
            if (event.submitter && event.submitter.matches("[data-no-loading]")) return;
            const button = event.submitter || form.querySelector("button[type='submit']");
            if (!button) return;
            button.dataset.originalText = button.textContent;
            button.textContent = "Working...";
            button.disabled = true;
        });
    });

    document.querySelectorAll(".alert[data-auto-dismiss]").forEach((alert) => {
        window.setTimeout(() => {
            alert.style.opacity = "0";
            alert.style.transition = "opacity 220ms ease";
            window.setTimeout(() => alert.remove(), 230);
        }, 4500);
    });
});
