document.addEventListener('DOMContentLoaded', function () {
    function addFieldHelpIcons() {
        Array.prototype.slice.call(document.querySelectorAll('[data-help]')).forEach(function (field) {
            var helpText = field.getAttribute('data-help');
            var id = field.getAttribute('id');
            var label = id ? document.querySelector('label[for="' + id + '"]') : null;

            if (!helpText || !label || label.querySelector('.field-help')) {
                return;
            }

            var help = document.createElement('button');
            help.className = 'field-help';
            help.type = 'button';
            help.textContent = '?';
            help.setAttribute('aria-label', 'Ayuda: ' + helpText);
            help.setAttribute('data-bs-toggle', 'tooltip');
            help.setAttribute('data-bs-placement', 'top');
            help.setAttribute('data-bs-custom-class', 'field-help-tooltip');
            help.setAttribute('title', helpText);

            label.appendChild(help);
        });

        if (window.bootstrap && bootstrap.Tooltip) {
            Array.prototype.slice.call(document.querySelectorAll('.field-help[data-bs-toggle="tooltip"]')).forEach(function (help) {
                bootstrap.Tooltip.getOrCreateInstance(help);
            });
        }
    }

    addFieldHelpIcons();

    function bindAutoCodeFields() {
        Array.prototype.slice.call(document.querySelectorAll('[data-next-codes][data-code-target]')).forEach(function (source) {
            var target = document.getElementById(source.getAttribute('data-code-target'));
            var codes = {};

            try {
                codes = JSON.parse(source.getAttribute('data-next-codes') || '{}');
            } catch (error) {
                codes = {};
            }

            if (!target) {
                return;
            }

            function renderCode() {
                var fallback = target.getAttribute('data-default-code') || target.getAttribute('placeholder') || '';
                target.value = codes[source.value] || fallback;
            }

            source.addEventListener('change', renderCode);

            if (!target.value) {
                renderCode();
            }
        });
    }

    bindAutoCodeFields();

    Array.prototype.slice.call(document.querySelectorAll('[data-requirements-by-plan][data-requirement-target]')).forEach(function (planField) {
        var requirementField = document.getElementById(planField.getAttribute('data-requirement-target'));
        var requirementsByPlan = {};

        try {
            requirementsByPlan = JSON.parse(planField.getAttribute('data-requirements-by-plan') || '{}');
        } catch (error) {
            requirementsByPlan = {};
        }

        if (!requirementField) {
            return;
        }

        function renderRequirements() {
            var previousValue = requirementField.value;
            var requirements = requirementsByPlan[planField.value] || [];

            requirementField.innerHTML = '';

            var placeholder = document.createElement('option');
            placeholder.value = '';
            placeholder.textContent = requirements.length
                ? 'Selecciona un requisito'
                : 'El plan seleccionado no tiene requisitos disponibles';
            requirementField.appendChild(placeholder);

            requirements.forEach(function (requirement) {
                var option = document.createElement('option');
                option.value = String(requirement.value);
                option.textContent = requirement.label;
                option.selected = String(requirement.value) === previousValue;
                requirementField.appendChild(option);
            });

            requirementField.disabled = requirements.length === 0;
        }

        planField.addEventListener('change', renderRequirements);
        renderRequirements();
    });

    Array.prototype.slice.call(document.querySelectorAll('[data-risks-by-plan][data-risk-target]')).forEach(function (planField) {
        var riskField = document.getElementById(planField.getAttribute('data-risk-target'));
        var requirementField = document.getElementById(planField.getAttribute('data-requirement-target'));
        var risksByPlan = {};

        try {
            risksByPlan = JSON.parse(planField.getAttribute('data-risks-by-plan') || '{}');
        } catch (error) {
            risksByPlan = {};
        }

        if (!riskField) {
            return;
        }

        function renderRisks() {
            var selectedValues = Array.prototype.slice.call(riskField.selectedOptions || []).map(function (option) {
                return option.value;
            });
            var requirementValue = requirementField ? requirementField.value : '';
            var risks = risksByPlan[planField.value] || [];

            riskField.innerHTML = '';

            risks
                .filter(function (risk) {
                    return !risk.requirement || !requirementValue || String(risk.requirement) === String(requirementValue);
                })
                .forEach(function (risk) {
                    var option = document.createElement('option');
                    option.value = String(risk.value);
                    option.textContent = risk.label;
                    option.selected = selectedValues.indexOf(String(risk.value)) !== -1;
                    riskField.appendChild(option);
                });

            riskField.disabled = riskField.options.length === 0;
        }

        planField.addEventListener('change', renderRisks);
        if (requirementField) {
            requirementField.addEventListener('change', renderRisks);
        }
        renderRisks();
    });

    var themeToggles = Array.prototype.slice.call(document.querySelectorAll('[data-theme-toggle]'));
    var themeIcons = Array.prototype.slice.call(document.querySelectorAll('[data-theme-icon]'));
    var root = document.documentElement;

    function setTheme(theme) {
        var isDark = theme === 'dark';

        root.classList.toggle('theme-dark', isDark);
        localStorage.setItem('istqb-theme', theme);

        themeIcons.forEach(function (themeIcon) {
            themeIcon.classList.toggle('bi-moon', !isDark);
            themeIcon.classList.toggle('bi-sun', isDark);
        });

        themeToggles.forEach(function (themeToggle) {
            themeToggle.setAttribute('title', isDark ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro');
            themeToggle.setAttribute('aria-label', isDark ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro');
        });
    }

    setTheme(root.classList.contains('theme-dark') ? 'dark' : 'light');

    themeToggles.forEach(function (themeToggle) {
        themeToggle.addEventListener('click', function () {
            setTheme(root.classList.contains('theme-dark') ? 'light' : 'dark');
        });
    });

    var sidebarToggles = Array.prototype.slice.call(document.querySelectorAll('[data-sidebar-toggle]'));
    var sidebarToggleIcon = document.querySelector('[data-sidebar-toggle-icon]');
    var mobileSidebarQuery = window.matchMedia ? window.matchMedia('(max-width: 760px)') : null;

    function isMobileSidebar() {
        return mobileSidebarQuery ? mobileSidebarQuery.matches : window.innerWidth <= 760;
    }

    function renderSidebarState() {
        var isCollapsed = root.classList.contains('sidebar-collapsed');
        var isMobileOpen = root.classList.contains('mobile-sidebar-open');

        if (!isMobileSidebar()) {
            localStorage.setItem('istqb-sidebar', isCollapsed ? 'collapsed' : 'expanded');
        }

        sidebarToggles.forEach(function (toggle) {
            var label = isMobileSidebar()
                ? (isMobileOpen ? 'Cerrar menu' : 'Abrir menu')
                : (isCollapsed ? 'Expandir menu' : 'Minimizar menu');
            toggle.setAttribute('title', label);
            toggle.setAttribute('aria-label', label);
            toggle.setAttribute('aria-expanded', isMobileSidebar() && isMobileOpen ? 'true' : 'false');
        });

        if (sidebarToggleIcon) {
            sidebarToggleIcon.classList.toggle('bi-chevron-left', !isCollapsed && !isMobileSidebar());
            sidebarToggleIcon.classList.toggle('bi-chevron-right', isCollapsed && !isMobileSidebar());
            sidebarToggleIcon.classList.toggle('bi-list', isMobileSidebar() && !isMobileOpen);
            sidebarToggleIcon.classList.toggle('bi-x-lg', isMobileSidebar() && isMobileOpen);
        }
    }

    if (sidebarToggles.length) {
        sidebarToggles.forEach(function (toggle) {
            toggle.addEventListener('click', function () {
                if (isMobileSidebar()) {
                    root.classList.toggle('mobile-sidebar-open');
                } else {
                    root.classList.toggle('sidebar-collapsed');
                }
                renderSidebarState();
            });
        });

        document.addEventListener('click', function (event) {
            if (!root.classList.contains('mobile-sidebar-open')) {
                return;
            }

            if (event.target.closest('.sidebar-nav a')) {
                root.classList.remove('mobile-sidebar-open');
                renderSidebarState();
                return;
            }

            if (!event.target.closest('.app-sidebar') && !event.target.closest('[data-sidebar-toggle]')) {
                root.classList.remove('mobile-sidebar-open');
                renderSidebarState();
            }
        });

        if (mobileSidebarQuery && mobileSidebarQuery.addEventListener) {
            mobileSidebarQuery.addEventListener('change', function () {
                root.classList.remove('mobile-sidebar-open');
                renderSidebarState();
            });
        }

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
            var fileName = input.files && input.files.length ? input.files[0].name : 'Adjuntar evidencia';
            var label = input.closest('.execution-upload');
            var target = label ? label.querySelector('[data-file-name]') : null;

            if (target) {
                target.textContent = fileName;
            }
        });
    });

    Array.prototype.slice.call(document.querySelectorAll('[data-bulk-select-all]')).forEach(function (selectAll) {
        var group = selectAll.getAttribute('data-bulk-select-all');
        var items = Array.prototype.slice.call(document.querySelectorAll('[data-bulk-select-item="' + group + '"]'));
        var actions = Array.prototype.slice.call(document.querySelectorAll('[data-bulk-action="' + group + '"]'));

        function syncBulkState() {
            var checkedItems = items.filter(function (item) {
                return item.checked;
            });

            selectAll.checked = items.length > 0 && checkedItems.length === items.length;
            selectAll.indeterminate = checkedItems.length > 0 && checkedItems.length < items.length;

            actions.forEach(function (action) {
                action.disabled = checkedItems.length === 0;
            });
        }

        selectAll.addEventListener('change', function () {
            items.forEach(function (item) {
                item.checked = selectAll.checked;
            });
            syncBulkState();
        });

        items.forEach(function (item) {
            item.addEventListener('change', syncBulkState);
        });

        syncBulkState();
    });

    Array.prototype.slice.call(document.querySelectorAll('[data-requirement-import-form]')).forEach(function (form) {
        var countLabel = document.querySelector('[data-requirement-import-count]');
        var submitButton = form.querySelector('button[type="submit"]');

        function getRows() {
            return Array.prototype.slice.call(form.querySelectorAll('[data-requirement-import-row]'));
        }

        function renderRequirementImportRows() {
            var rows = getRows();

            rows.forEach(function (row, index) {
                var number = row.querySelector('[data-requirement-import-number]');

                if (number) {
                    number.textContent = String(index + 1);
                }
            });

            if (countLabel) {
                countLabel.textContent = String(rows.length);
            }

            if (submitButton) {
                submitButton.disabled = rows.length === 0;
            }
        }

        form.addEventListener('click', function (event) {
            var removeButton = event.target.closest('[data-requirement-import-remove]');

            if (!removeButton) {
                return;
            }

            var row = removeButton.closest('[data-requirement-import-row]');

            if (row) {
                row.remove();
                renderRequirementImportRows();
            }
        });

        renderRequirementImportRows();
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

    var confirmModalElement = document.getElementById('confirmActionModal');
    var confirmModal = confirmModalElement && window.bootstrap
        ? new bootstrap.Modal(confirmModalElement)
        : null;
    var confirmModalMessage = confirmModalElement
        ? confirmModalElement.querySelector('[data-confirm-modal-message]')
        : null;
    var confirmModalAccept = confirmModalElement
        ? confirmModalElement.querySelector('[data-confirm-modal-accept]')
        : null;
    var pendingConfirmForm = null;
    var pendingConfirmSubmitter = null;

    document.addEventListener('submit', function (event) {
        var confirmButton = event.submitter && event.submitter.matches('[data-confirm-message]')
            ? event.submitter
            : null;

        if (!confirmButton || event.target.getAttribute('data-confirm-approved') === 'true') {
            if (event.target.getAttribute('data-confirm-approved') === 'true') {
                event.target.removeAttribute('data-confirm-approved');
            }
            return;
        }

        if (!confirmModal || !confirmModalMessage || !confirmModalAccept) {
            return;
        }

        event.preventDefault();
        pendingConfirmForm = event.target;
        pendingConfirmSubmitter = confirmButton;
        confirmModalMessage.textContent = confirmButton.getAttribute('data-confirm-message');
        confirmModal.show();
    });

    if (confirmModalAccept) {
        confirmModalAccept.addEventListener('click', function () {
            if (!pendingConfirmForm) {
                return;
            }

            pendingConfirmForm.setAttribute('data-confirm-approved', 'true');
            confirmModal.hide();

            if (pendingConfirmForm.requestSubmit && pendingConfirmSubmitter) {
                pendingConfirmForm.requestSubmit(pendingConfirmSubmitter);
            } else {
                pendingConfirmForm.submit();
            }

            pendingConfirmForm = null;
            pendingConfirmSubmitter = null;
        });
    }

    if (confirmModalElement) {
        confirmModalElement.addEventListener('hidden.bs.modal', function () {
            pendingConfirmForm = null;
            pendingConfirmSubmitter = null;
        });
    }

    document.addEventListener('keydown', function (event) {
        if (event.key !== 'Escape') {
            return;
        }

        Array.prototype.slice.call(document.querySelectorAll('.project-actions.open')).forEach(function (menu) {
            menu.classList.remove('open');
            menu.querySelector('[data-project-menu-toggle]').setAttribute('aria-expanded', 'false');
        });

        if (root.classList.contains('mobile-sidebar-open')) {
            root.classList.remove('mobile-sidebar-open');
            renderSidebarState();
        }
    });

    var executionType = document.getElementById('id_execution_type');
    var relatedDefectField = document.querySelector('[data-related-defect-field]');

    if (executionType && relatedDefectField) {
        var toggleRelatedDefect = function () {
            var isConfirmation = executionType.value === 'CONFIRMATION';
            relatedDefectField.hidden = !isConfirmation;
        };

        executionType.addEventListener('change', toggleRelatedDefect);
        toggleRelatedDefect();
    }

    var executionModeShell = document.querySelector('[data-execution-mode-shell]');

    if (executionModeShell) {
        var executionModeTabs = Array.prototype.slice.call(executionModeShell.querySelectorAll('[data-execution-mode-tab]'));
        var executionModePanels = Array.prototype.slice.call(executionModeShell.querySelectorAll('[data-execution-mode-panel]'));

        function setExecutionMode(mode, updateHash) {
            executionModeShell.classList.toggle('execution-mode-automated', mode === 'automated');

            executionModeTabs.forEach(function (tab) {
                var isActive = tab.getAttribute('data-execution-mode-tab') === mode;

                tab.classList.toggle('active', isActive);
                tab.setAttribute('aria-pressed', isActive ? 'true' : 'false');
            });

            executionModePanels.forEach(function (panel) {
                panel.hidden = panel.getAttribute('data-execution-mode-panel') !== mode;
            });

            if (updateHash && window.history && window.history.replaceState) {
                var nextHash = mode === 'automated' ? '#automation' : '';
                window.history.replaceState(null, '', window.location.pathname + window.location.search + nextHash);
            }
        }

        executionModeTabs.forEach(function (tab) {
            tab.addEventListener('click', function () {
                setExecutionMode(tab.getAttribute('data-execution-mode-tab'), true);
            });
        });

        setExecutionMode(window.location.hash === '#automation' ? 'automated' : 'manual', false);
    }

    var validationTypeField = document.getElementById('id_validation_type');

    if (validationTypeField) {
        var ruleHelp = document.querySelector('[data-rule-type-help]');
        var ruleFieldMap = {
            FIELD_REQUIRED: ['name', 'step_number', 'validation_type', 'target_url', 'selector_type', 'selector_value', 'secondary_selector_value', 'timeout_seconds', 'browser', 'capture_evidence', 'is_active'],
            EMAIL_FORMAT: ['name', 'step_number', 'validation_type', 'target_url', 'selector_type', 'selector_value', 'secondary_selector_value', 'input_value', 'timeout_seconds', 'browser', 'capture_evidence', 'is_active'],
            MAX_LENGTH: ['name', 'step_number', 'validation_type', 'target_url', 'selector_type', 'selector_value', 'secondary_selector_value', 'input_value', 'max_length', 'timeout_seconds', 'browser', 'capture_evidence', 'is_active'],
            MIN_LENGTH: ['name', 'step_number', 'validation_type', 'target_url', 'selector_type', 'selector_value', 'secondary_selector_value', 'input_value', 'min_length', 'timeout_seconds', 'browser', 'capture_evidence', 'is_active'],
            TEXT_VISIBLE: ['name', 'step_number', 'validation_type', 'target_url', 'expected_text', 'timeout_seconds', 'browser', 'capture_evidence', 'is_active'],
            ELEMENT_VISIBLE: ['name', 'step_number', 'validation_type', 'target_url', 'selector_type', 'selector_value', 'timeout_seconds', 'browser', 'capture_evidence', 'is_active'],
            REDIRECT_URL: ['name', 'step_number', 'validation_type', 'target_url', 'selector_type', 'selector_value', 'expected_url', 'timeout_seconds', 'browser', 'capture_evidence', 'is_active'],
            HTTP_STATUS: ['name', 'step_number', 'validation_type', 'target_url', 'expected_http_status', 'timeout_seconds', 'is_active'],
            BUTTON_DISABLED: ['name', 'step_number', 'validation_type', 'target_url', 'selector_type', 'selector_value', 'timeout_seconds', 'browser', 'capture_evidence', 'is_active'],
            FORM_SUBMISSION_BLOCKED: ['name', 'step_number', 'validation_type', 'target_url', 'selector_type', 'selector_value', 'secondary_selector_value', 'input_value', 'timeout_seconds', 'browser', 'capture_evidence', 'is_active']
        };
        var ruleHelpText = {
            FIELD_REQUIRED: 'Valida que un campo obligatorio no permita enviar el formulario vacio. Usa selector principal para el campo y selector secundario para el boton de envio.',
            EMAIL_FORMAT: 'Escribe un correo invalido en el campo principal y comprueba que el formulario lo rechace.',
            MAX_LENGTH: 'Escribe un texto mayor al permitido y comprueba que el campo o el formulario respeten la longitud máxima.',
            MIN_LENGTH: 'Escribe un texto menor al mínimo y comprueba que el formulario bloquee el envío.',
            TEXT_VISIBLE: 'Comprueba que la página muestre un texto. No necesitas selector principal para este tipo.',
            ELEMENT_VISIBLE: 'Comprueba que un elemento específico exista y sea visible.',
            REDIRECT_URL: 'Hace clic en el elemento principal y valida que la página termine en la URL esperada.',
            HTTP_STATUS: 'Comprueba que la URL objetivo responda con el código HTTP esperado. No usa navegador ni selectores.',
            BUTTON_DISABLED: 'Comprueba que un boton o control este deshabilitado.',
            FORM_SUBMISSION_BLOCKED: 'Intenta enviar un formulario y valida que no navegue ni acepte datos invalidos.'
        };

        function renderRuleFields() {
            var visibleFields = ruleFieldMap[validationTypeField.value] || ['name', 'step_number', 'validation_type', 'target_url', 'timeout_seconds', 'is_active'];

            Array.prototype.slice.call(document.querySelectorAll('[data-rule-field]')).forEach(function (fieldWrapper) {
                var fieldName = fieldWrapper.getAttribute('data-rule-field');
                fieldWrapper.hidden = visibleFields.indexOf(fieldName) === -1;
            });

            if (ruleHelp) {
                var title = validationTypeField.options[validationTypeField.selectedIndex]
                    ? validationTypeField.options[validationTypeField.selectedIndex].text
                    : 'Selecciona un tipo de validación';
                ruleHelp.querySelector('strong').textContent = title;
                ruleHelp.querySelector('span').textContent = ruleHelpText[validationTypeField.value] || 'El formulario mostrara solo los campos necesarios para esa regla.';
            }
        }

        validationTypeField.addEventListener('change', renderRuleFields);
        renderRuleFields();
    }
});
