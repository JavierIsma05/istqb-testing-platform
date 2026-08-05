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

    Array.prototype.slice.call(document.querySelectorAll('[data-plans-by-project]')).forEach(function (projectField) {
        var projectSelect = document.getElementById('planReportProject');
        var planField = document.getElementById('planReportPlan');
        var goButton = document.getElementById('planReportGo');
        var plansByProject = {};

        try {
            plansByProject = JSON.parse(projectField.getAttribute('data-plans-by-project') || '{}');
        } catch (error) {
            plansByProject = {};
        }

        if (!projectSelect || !planField) {
            return;
        }

        function renderPlans() {
            var projectId = projectSelect.value;
            var plans = plansByProject[projectId] || [];

            planField.innerHTML = '';

            var placeholder = document.createElement('option');
            placeholder.value = '';
            placeholder.textContent = plans.length
                ? 'Selecciona un plan de pruebas'
                : 'El proyecto seleccionado no tiene planes de pruebas';
            planField.appendChild(placeholder);

            plans.forEach(function (plan) {
                var option = document.createElement('option');
                option.value = String(plan.value);
                option.textContent = plan.label;
                planField.appendChild(option);
            });

            planField.disabled = plans.length === 0;
            planField.value = '';
            if (goButton) {
                goButton.disabled = true;
            }
        }

        projectSelect.addEventListener('change', renderPlans);
        planField.addEventListener('change', function () {
            if (goButton) {
                goButton.disabled = !planField.value;
            }
        });
        renderPlans();
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

    var sidebarGroups = Array.prototype.slice.call(document.querySelectorAll('[data-sidebar-group-toggle]'));

    function syncSidebarGroups() {
        sidebarGroups.forEach(function (toggle) {
            var menu = toggle.parentElement.querySelector('.sidebar-group-menu');

            if (!menu) {
                return;
            }

            var hasActiveChild = !!menu.querySelector('a.active');

            menu.classList.toggle('open', hasActiveChild);
            toggle.setAttribute('aria-expanded', hasActiveChild ? 'true' : 'false');
        });
    }

    sidebarGroups.forEach(function (toggle) {
        toggle.addEventListener('click', function () {
            if (root.classList.contains('sidebar-collapsed') && !isMobileSidebar()) {
                root.classList.remove('sidebar-collapsed');
                renderSidebarState();
                return;
            }

            var menu = toggle.parentElement.querySelector('.sidebar-group-menu');

            if (!menu) {
                return;
            }

            var isOpen = menu.classList.toggle('open');
            toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
        });
    });

    syncSidebarGroups();

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

        setExecutionMode(
            executionModeShell.getAttribute('data-default-mode') === 'automated' || window.location.hash === '#automation' ? 'automated' : 'manual',
            false
        );
    }

    var actionTypeField = document.getElementById('id_action_type');

    if (actionTypeField) {
        var stepHelp = document.querySelector('[data-step-action-help]');
        var stepFieldMap = {
            OPEN_URL: ['name', 'step_number', 'action_type', 'target_url', 'timeout_seconds', 'is_critical'],
            CLICK: ['name', 'step_number', 'action_type', 'selector_value', 'timeout_seconds', 'is_critical'],
            FILL_TEXT: ['name', 'step_number', 'action_type', 'selector_value', 'input_value', 'timeout_seconds', 'is_critical'],
            VERIFY: ['name', 'step_number', 'action_type', 'selector_value', 'expected_value', 'comparison_type', 'timeout_seconds', 'is_critical'],
            WAIT: ['name', 'step_number', 'action_type', 'selector_value', 'input_value', 'timeout_seconds', 'is_critical']
        };
        var stepHelpText = {
            OPEN_URL: 'Abre la URL especificada en el navegador. Solo se requiere el campo "URL a abrir".',
            CLICK: 'Hace clic en el elemento especificado. Solo se requiere el campo "Elemento" (selector CSS).',
            FILL_TEXT: 'Escribe el dato especificado en el campo de texto. Requiere "Elemento" (selector CSS) y "Dato" (acepta variables como {{usuario}}).',
            VERIFY: 'Verifica que un elemento, texto o URL cumpla una condición. Requiere "Elemento" (o "URL actual"), "Resultado esperado" y "Tipo de comparación".',
            WAIT: 'Espera un tiempo en segundos o a que un elemento sea visible. Usa "Dato" para segundos o "Elemento" para esperar un selector.'
        };

        function renderStepFields() {
            var visibleFields = stepFieldMap[actionTypeField.value] || ['name', 'step_number', 'action_type', 'is_critical'];

            Array.prototype.slice.call(document.querySelectorAll('[data-step-field]')).forEach(function (fieldWrapper) {
                var fieldName = fieldWrapper.getAttribute('data-step-field');
                fieldWrapper.hidden = visibleFields.indexOf(fieldName) === -1;
            });

            if (stepHelp) {
                var title = actionTypeField.options[actionTypeField.selectedIndex]
                    ? actionTypeField.options[actionTypeField.selectedIndex].text
                    : 'Selecciona una acción';
                stepHelp.querySelector('strong').textContent = title;
                stepHelp.querySelector('span').textContent = stepHelpText[actionTypeField.value] || 'El formulario mostrara solo los campos necesarios para ese paso.';
            }
        }

        actionTypeField.addEventListener('change', renderStepFields);
        renderStepFields();
    }

    // Template selector for automated steps
    var templateSelect = document.querySelector('[data-template-select]');
    
    if (templateSelect) {
        var templates = {
            'login': {
                'action_type': 'OPEN_URL',
                'target_url': 'http://localhost:8000/login/',
                'selector_value': '',
                'input_value': '',
                'expected_value': '',
                'comparison_type': 'EXACT',
                'timeout_seconds': 10
            },
            'search': {
                'action_type': 'FILL_TEXT',
                'target_url': '',
                'selector_value': 'input[name="q"]',
                'input_value': '{{termino_busqueda}}',
                'expected_value': '',
                'comparison_type': 'EXACT',
                'timeout_seconds': 10
            },
            'form_submit': {
                'action_type': 'CLICK',
                'target_url': '',
                'selector_value': 'button[type="submit"]',
                'input_value': '',
                'expected_value': '',
                'comparison_type': 'EXACT',
                'timeout_seconds': 10
            }
        };

        templateSelect.addEventListener('change', function() {
            var template = templates[templateSelect.value];
            if (!template) return;

            var actionField = document.getElementById('id_action_type');
            var targetUrlField = document.getElementById('id_target_url');
            var selectorField = document.getElementById('id_selector_value');
            var inputField = document.getElementById('id_input_value');
            var expectedField = document.getElementById('id_expected_value');
            var comparisonField = document.getElementById('id_comparison_type');
            var timeoutField = document.getElementById('id_timeout_seconds');

            if (actionField) actionField.value = template.action_type;
            if (targetUrlField) targetUrlField.value = template.target_url;
            if (selectorField) selectorField.value = template.selector_value;
            if (inputField) inputField.value = template.input_value;
            if (expectedField) expectedField.value = template.expected_value;
            if (comparisonField) comparisonField.value = template.comparison_type;
            if (timeoutField) timeoutField.value = template.timeout_seconds;

            // Trigger the action type change to update field visibility
            if (actionField) {
                var event = new Event('change', { bubbles: true });
                actionField.dispatchEvent(event);
            }
        });
    }

    function bindCurrentYearDateValidation() {
        Array.prototype.slice.call(document.querySelectorAll('form')).forEach(function (form) {
            var dateInputs = Array.prototype.slice.call(form.querySelectorAll('input[type="date"][min][max]'));
            if (!dateInputs.length) {
                return;
            }

            form.addEventListener('submit', function (event) {
                var firstInvalid = null;

                dateInputs.forEach(function (input) {
                    if (!input.value) {
                        return;
                    }

                    var min = input.getAttribute('min');
                    var max = input.getAttribute('max');
                    if (!min || !max) {
                        return;
                    }

                    if (input.value < min || input.value > max) {
                        var errorBox = input.closest('.date-field');
                        var help = errorBox
                            ? errorBox.querySelector('.current-year-error')
                            : input.parentElement.querySelector('.current-year-error');

                        if (!help) {
                            help = document.createElement('div');
                            help.className = 'form-error current-year-error';
                            help.textContent = 'La fecha debe estar dentro del año académico vigente (' + max.slice(0, 4) + ').';
                            var anchor = errorBox || input.parentElement;
                            anchor.appendChild(help);
                        }

                        if (!firstInvalid) {
                            firstInvalid = input;
                        }
                    }
                });

                if (firstInvalid) {
                    event.preventDefault();
                    firstInvalid.focus();
                }
            });
        });
    }

    bindCurrentYearDateValidation();

    function initFormDrafts() {
        var forms = Array.prototype.slice.call(document.querySelectorAll('form[data-draft-module]'));

        forms.forEach(function (form) {
            var module = form.getAttribute('data-draft-module');
            var saveUrl = form.getAttribute('data-draft-save-url');
            var getUrl = form.getAttribute('data-draft-get-url');
            var clearUrl = form.getAttribute('data-draft-clear-url');
            var objectId = form.getAttribute('data-draft-object-id') || '0';
            var projectSelector = form.getAttribute('data-draft-project-select');
            var staticProject = form.getAttribute('data-draft-project') || '0';

            if (!module || !saveUrl || !getUrl || !clearUrl) {
                return;
            }

            var csrfInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
            var csrfToken = csrfInput ? csrfInput.value : '';

            function currentProject() {
                if (projectSelector) {
                    var field = form.querySelector(projectSelector);
                    return field && field.value ? field.value : '0';
                }
                return staticProject;
            }

            function currentKey() {
                return module + ':' + currentProject() + ':' + objectId;
            }

            function getLocalStorageKey() {
                return 'istqb-draft:' + currentKey();
            }

            function serialize() {
                var data = {};
                var elements = form.elements;

                for (var i = 0; i < elements.length; i++) {
                    var field = elements[i];
                    if (field.disabled || !field.name || field.type === 'submit' || field.type === 'button' || field.type === 'file') {
                        continue;
                    }
                    if (field.type === 'checkbox' || field.type === 'radio') {
                        if (field.checked) {
                            var existing = data[field.name];
                            if (existing === undefined) {
                                data[field.name] = [field.value];
                            } else if (Array.isArray(existing)) {
                                existing.push(field.value);
                            }
                        } else if (data[field.name] === undefined) {
                            data[field.name] = [];
                        }
                        continue;
                    }
                    if (field.tagName === 'SELECT' && field.multiple) {
                        var values = Array.prototype.slice.call(field.selectedOptions || []).map(function (option) {
                            return option.value;
                        });
                        data[field.name] = values;
                        continue;
                    }
                    data[field.name] = field.value;
                }

                return data;
            }

            function saveToLocal(data) {
                try {
                    localStorage.setItem(getLocalStorageKey(), JSON.stringify(data));
                } catch (error) {}
            }

            function readLocal() {
                try {
                    var raw = localStorage.getItem(getLocalStorageKey());
                    return raw ? JSON.parse(raw) : null;
                } catch (error) {
                    return null;
                }
            }

            function clearLocal() {
                try {
                    localStorage.removeItem(getLocalStorageKey());
                } catch (error) {}
            }

            function hasContent(data) {
                if (!data) {
                    return false;
                }
                return Object.keys(data).some(function (name) {
                    var value = data[name];
                    if (Array.isArray(value)) {
                        return value.length > 0;
                    }
                    return value !== '' && value !== null && value !== undefined;
                });
            }

            function applyData(data) {
                if (!data) {
                    return;
                }
                var elements = form.elements;

                for (var i = 0; i < elements.length; i++) {
                    var field = elements[i];
                    if (!field.name || !(field.name in data)) {
                        continue;
                    }
                    var value = data[field.name];
                    if (field.type === 'checkbox') {
                        field.checked = Array.isArray(value) ? value.indexOf(field.value) !== -1 : String(value) === String(field.value);
                    } else if (field.tagName === 'SELECT' && field.multiple) {
                        var selected = Array.isArray(value) ? value.map(String) : [];
                        Array.prototype.slice.call(field.options).forEach(function (option) {
                            option.selected = selected.indexOf(String(option.value)) !== -1;
                        });
                    } else {
                        field.value = value;
                    }
                }

                var dependentSource = form.querySelector('[data-requirements-by-plan]') || form.querySelector('[data-risks-by-plan]');
                if (dependentSource) {
                    dependentSource.dispatchEvent(new Event('change'));
                }
            }

            var status = document.createElement('div');
            status.className = 'draft-status';
            status.setAttribute('role', 'status');
            form.appendChild(status);

            var statusTimer = null;
            function setStatus(message, state) {
                status.textContent = message;
                status.setAttribute('data-state', state || '');
                if (statusTimer) {
                    clearTimeout(statusTimer);
                }
                statusTimer = setTimeout(function () {
                    status.textContent = '';
                    status.setAttribute('data-state', '');
                }, 5000);
            }

            var pendingSave = false;

            function doSave() {
                var data = serialize();
                saveToLocal(data);
                if (pendingSave) {
                    return;
                }
                pendingSave = true;
                setStatus('Guardando...', 'saving');

                fetch(saveUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify({
                        module: module,
                        project_id: currentProject(),
                        object_id: objectId,
                        data: data
                    })
                }).then(function (response) {
                    if (!response.ok) {
                        throw new Error('Draft no guardado');
                    }
                    return response.json();
                }).then(function () {
                    setStatus('Guardado automáticamente', 'saved');
                }).catch(function () {
                    setStatus('Sin conexión — guardado localmente', 'offline');
                }).then(function () {
                    pendingSave = false;
                });
            }

            var debounceTimer = null;
            function scheduleSave() {
                if (debounceTimer) {
                    clearTimeout(debounceTimer);
                }
                debounceTimer = setTimeout(doSave, 5000);
            }

            form.addEventListener('input', scheduleSave);
            form.addEventListener('change', scheduleSave);
            form.addEventListener('blur', function () {
                if (debounceTimer) {
                    clearTimeout(debounceTimer);
                    debounceTimer = null;
                }
                doSave();
            }, true);

            form.addEventListener('submit', function () {
                if (debounceTimer) {
                    clearTimeout(debounceTimer);
                    debounceTimer = null;
                }
                clearLocal();
            });

            window.addEventListener('beforeunload', function () {
                if (debounceTimer) {
                    clearTimeout(debounceTimer);
                    debounceTimer = null;
                }
                saveToLocal(serialize());
            });

            function showDraftBanner(data, localOnly) {
                var banner = document.createElement('div');
                banner.className = 'draft-banner';
                banner.setAttribute('data-draft-banner', '');
                banner.innerHTML =
                    '<div class="draft-banner-text">' +
                    '<strong>Borrador encontrado</strong>' +
                    '<span>' + (localOnly ? 'Guardado en este navegador.' : 'Guardado automáticamente.') + '</span>' +
                    '</div>' +
                    '<div class="draft-banner-actions">' +
                    '<button type="button" class="btn btn-sm btn-brand" data-draft-continue>Continuar</button>' +
                    '<button type="button" class="btn btn-sm btn-outline-brand" data-draft-discard>Descartar</button>' +
                    '</div>';
                form.insertBefore(banner, form.firstChild);

                banner.querySelector('[data-draft-continue]').addEventListener('click', function () {
                    applyData(data);
                    banner.remove();
                    setStatus('Borrador restaurado', 'saved');
                });

                banner.querySelector('[data-draft-discard]').addEventListener('click', function () {
                    fetch(clearUrl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken
                        },
                        credentials: 'same-origin',
                        body: JSON.stringify({
                            module: module,
                            project_id: currentProject(),
                            object_id: objectId
                        })
                    }).catch(function () {});
                    clearLocal();
                    banner.remove();
                    setStatus('Borrador descartado', 'saved');
                });
            }

            function loadDraft() {
                var separator = getUrl.indexOf('?') === -1 ? '?' : '&';
                var url = getUrl + separator +
                    'module=' + encodeURIComponent(module) +
                    '&project_id=' + encodeURIComponent(currentProject()) +
                    '&object_id=' + encodeURIComponent(objectId);

                fetch(url, { credentials: 'same-origin' })
                    .then(function (response) {
                        return response.json();
                    })
                    .then(function (payload) {
                        if (payload.found && hasContent(payload.data)) {
                            showDraftBanner(payload.data, false);
                        } else if (!payload.found) {
                            var local = readLocal();
                            if (local && hasContent(local)) {
                                showDraftBanner(local, true);
                            }
                        }
                    })
                    .catch(function () {
                        var local = readLocal();
                        if (local && hasContent(local)) {
                            showDraftBanner(local, true);
                        }
                    });
            }

            loadDraft();
        });
    }

    initFormDrafts();
});
