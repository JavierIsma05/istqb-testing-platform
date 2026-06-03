document.addEventListener('DOMContentLoaded', function () {
    var themeToggle = document.querySelector('[data-theme-toggle]');
    var themeIcon = document.querySelector('[data-theme-icon]');
    var root = document.documentElement;

    function setTheme(theme) {
        var isDark = theme === 'dark';

        root.classList.toggle('theme-dark', isDark);
        localStorage.setItem('istqb-theme', theme);

        if (themeIcon) {
            themeIcon.classList.toggle('bi-moon', !isDark);
            themeIcon.classList.toggle('bi-sun', isDark);
        }

        if (themeToggle) {
            themeToggle.setAttribute('title', isDark ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro');
            themeToggle.setAttribute('aria-label', isDark ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro');
        }
    }

    setTheme(root.classList.contains('theme-dark') ? 'dark' : 'light');

    if (themeToggle) {
        themeToggle.addEventListener('click', function () {
            setTheme(root.classList.contains('theme-dark') ? 'light' : 'dark');
        });
    }

    var sidebarToggles = Array.prototype.slice.call(document.querySelectorAll('[data-sidebar-toggle]'));
    var sidebarToggleIcon = document.querySelector('[data-sidebar-toggle-icon]');

    function renderSidebarState() {
        var isCollapsed = root.classList.contains('sidebar-collapsed');

        localStorage.setItem('istqb-sidebar', isCollapsed ? 'collapsed' : 'expanded');

        sidebarToggles.forEach(function (toggle) {
            toggle.setAttribute('title', isCollapsed ? 'Expandir menu' : 'Minimizar menu');
            toggle.setAttribute('aria-label', isCollapsed ? 'Expandir menu' : 'Minimizar menu');
        });

        if (sidebarToggleIcon) {
            sidebarToggleIcon.classList.toggle('bi-chevron-left', !isCollapsed);
            sidebarToggleIcon.classList.toggle('bi-chevron-right', isCollapsed);
        }
    }

    if (sidebarToggles.length) {
        sidebarToggles.forEach(function (toggle) {
            toggle.addEventListener('click', function () {
                root.classList.toggle('sidebar-collapsed');
                renderSidebarState();
            });
        });
        renderSidebarState();
    }

    var wizard = document.querySelector('.wizard-page');

    if (wizard) {
        var panels = Array.prototype.slice.call(wizard.querySelectorAll('[data-step-panel]'));
        var dots = Array.prototype.slice.call(wizard.querySelectorAll('[data-step-dot]'));
        var prev = wizard.querySelector('[data-wizard-prev]');
        var next = wizard.querySelector('[data-wizard-next]');
        var submit = wizard.querySelector('.wizard-submit');
        var current = 1;

        if (panels.length && dots.length && prev && next && submit) {
            function renderWizard() {
                panels.forEach(function (panel) {
                    panel.classList.toggle('active', Number(panel.getAttribute('data-step-panel')) === current);
                });

                dots.forEach(function (dot) {
                    var step = Number(dot.getAttribute('data-step-dot'));
                    var marker = dot.querySelector('span');

                    dot.classList.toggle('active', step === current);
                    dot.classList.toggle('done', step < current);

                    if (marker) {
                        marker.textContent = step < current ? '\u2713' : String(step);
                    }
                });

                prev.disabled = current === 1;
                next.hidden = current === panels.length;
                submit.classList.toggle('active', current === panels.length);
            }

            prev.addEventListener('click', function (event) {
                event.preventDefault();
                current = Math.max(1, current - 1);
                renderWizard();
            });

            next.addEventListener('click', function (event) {
                event.preventDefault();
                current = Math.min(panels.length, current + 1);
                renderWizard();
            });

            dots.forEach(function (dot) {
                dot.addEventListener('click', function () {
                    current = Number(dot.getAttribute('data-step-dot'));
                    renderWizard();
                });
            });

            renderWizard();
        }
    }

    Array.prototype.slice.call(document.querySelectorAll('[data-file-input]')).forEach(function (input) {
        input.addEventListener('change', function () {
            var fileName = input.files && input.files.length ? input.files[0].name : 'Adjuntar capturas de pantalla';
            var label = input.closest('.execution-upload');
            var target = label ? label.querySelector('[data-file-name]') : null;

            if (target) {
                target.textContent = fileName;
            }
        });
    });

    document.addEventListener('click', function (event) {
        var toggle = event.target.closest('[data-project-menu-toggle]');
        var openMenus = Array.prototype.slice.call(document.querySelectorAll('.project-actions.open'));

        if (toggle) {
            var actions = toggle.closest('.project-actions');

            openMenus.forEach(function (menu) {
                if (menu !== actions) {
                    menu.classList.remove('open');
                    menu.querySelector('[data-project-menu-toggle]').setAttribute('aria-expanded', 'false');
                }
            });

            actions.classList.toggle('open');
            toggle.setAttribute('aria-expanded', actions.classList.contains('open') ? 'true' : 'false');
            return;
        }

        if (!event.target.closest('[data-project-menu]')) {
            openMenus.forEach(function (menu) {
                menu.classList.remove('open');
                menu.querySelector('[data-project-menu-toggle]').setAttribute('aria-expanded', 'false');
            });
        }
    });

    document.addEventListener('submit', function (event) {
        var confirmButton = event.submitter && event.submitter.matches('[data-confirm-message]')
            ? event.submitter
            : null;

        if (confirmButton && !window.confirm(confirmButton.getAttribute('data-confirm-message'))) {
            event.preventDefault();
        }
    });

    document.addEventListener('keydown', function (event) {
        if (event.key !== 'Escape') {
            return;
        }

        Array.prototype.slice.call(document.querySelectorAll('.project-actions.open')).forEach(function (menu) {
            menu.classList.remove('open');
            menu.querySelector('[data-project-menu-toggle]').setAttribute('aria-expanded', 'false');
        });
    });
});
