/* Informes de calidad: flujo de 5 pasos + panel de detalle cargado por JSON. */
(function () {
    'use strict';

    function init() {
        var root = document.querySelector('[data-report-flow]');
        if (!root) return;

        var tabs = Array.prototype.slice.call(root.querySelectorAll('[role="tab"]'));
        var panel = root.querySelector('#rf-panel');
        var el = function (name) { return panel.querySelector('[data-rf-' + name + ']'); };

        var ui = {
            loading: el('loading'),
            error: el('error'),
            retry: el('retry'),
            content: el('content'),
            title: el('title'),
            badge: el('badge'),
            description: el('description'),
            meta: el('meta'),
            empty: el('empty'),
            deps: el('deps'),
            depsList: el('deps-list'),
            depsOk: el('deps-ok'),
            includes: el('includes'),
            form: el('form'),
            inputType: el('input-type'),
            inputTitle: el('input-title'),
            inputSkip: el('input-skip'),
            format: el('format'),
            formatHint: el('format-hint'),
            cycle: el('cycle'),
            cycleHint: el('cycle-hint'),
            confirm: el('confirm'),
            confirmYes: el('confirm-yes'),
            confirmNo: el('confirm-no'),
            generate: el('generate'),
            preview: el('preview'),
            download: el('download'),
            regenerate: el('regenerate')
        };

        var state = {
            step: root.dataset.selectedStep || (tabs[0] && tabs[0].dataset.step),
            data: null,
            controller: null,
            pendingSubmitter: null,
            confirmed: false,
            submitting: false
        };

        function apiUrl(step) {
            var url = root.dataset.apiUrl.replace('STEP', encodeURIComponent(step));
            var params = new URLSearchParams({ project: root.dataset.project, cycle: ui.cycle.value || 'all' });
            return url + '?' + params.toString();
        }

        /* ---------- Pestañas ---------- */

        function selectStep(step, options) {
            options = options || {};
            state.step = step;
            tabs.forEach(function (tab) {
                var selected = tab.dataset.step === step;
                tab.setAttribute('aria-selected', selected ? 'true' : 'false');
                tab.tabIndex = selected ? 0 : -1;
                if (selected) {
                    panel.setAttribute('aria-labelledby', tab.id);
                    if (options.focus) tab.focus();
                }
            });
            hideConfirm();
            updateUrl({ step: step });
            load();
        }

        tabs.forEach(function (tab, index) {
            tab.addEventListener('click', function () {
                if (tab.dataset.step !== state.step) selectStep(tab.dataset.step);
            });
            tab.addEventListener('keydown', function (event) {
                var target = null;
                switch (event.key) {
                    case 'ArrowDown':
                    case 'ArrowRight':
                        target = tabs[(index + 1) % tabs.length];
                        break;
                    case 'ArrowUp':
                    case 'ArrowLeft':
                        target = tabs[(index - 1 + tabs.length) % tabs.length];
                        break;
                    case 'Home':
                        target = tabs[0];
                        break;
                    case 'End':
                        target = tabs[tabs.length - 1];
                        break;
                    default:
                        return;
                }
                event.preventDefault();
                selectStep(target.dataset.step, { focus: true });
            });
        });

        /* ---------- Carga del detalle ---------- */

        function setView(view) {
            ui.loading.hidden = view !== 'loading';
            ui.error.hidden = view !== 'error';
            ui.content.hidden = view !== 'content';
            panel.setAttribute('aria-busy', view === 'loading' ? 'true' : 'false');
        }

        function load() {
            if (state.controller) state.controller.abort();
            var controller = new AbortController();
            state.controller = controller;
            // Solo mostramos el spinner si no hay contenido previo (evita parpadeos al cambiar el ciclo).
            if (!state.data || state.data.type !== state.step) setView('loading');

            fetch(apiUrl(state.step), {
                headers: { 'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
                credentials: 'same-origin',
                signal: controller.signal
            })
                .then(function (response) {
                    if (!response.ok) throw new Error('HTTP ' + response.status);
                    return response.json();
                })
                .then(function (data) {
                    if (controller !== state.controller) return;
                    state.data = data;
                    render(data);
                    setView('content');
                })
                .catch(function (error) {
                    if (error.name === 'AbortError') return;
                    state.data = null;
                    setView('error');
                });
        }

        ui.retry.addEventListener('click', load);

        /* ---------- Render ---------- */

        function render(data) {
            var generated = data.status === 'generado';

            ui.title.textContent = data.title;
            ui.description.textContent = data.description;
            ui.badge.textContent = generated ? 'Generado' : 'Pendiente';
            ui.badge.className = 'badge rf-badge ' + (generated ? 'rf-badge--done' : 'rf-badge--pending');

            if (generated) {
                ui.meta.textContent = 'Generado el ' + data.generated_at_display +
                    (data.generated_by ? ' por ' + data.generated_by : '');
                ui.meta.hidden = false;
            } else {
                ui.meta.hidden = true;
            }

            ui.empty.hidden = data.has_data;

            // Dependencias del informe final.
            var deps = data.dependencies;
            ui.depsList.innerHTML = '';
            if (deps && deps.missing.length) {
                deps.missing.forEach(function (item) {
                    var li = document.createElement('li');
                    var link = document.createElement('button');
                    link.type = 'button';
                    link.className = 'btn btn-link btn-sm p-0 align-baseline';
                    link.textContent = item.number + '. ' + item.title;
                    link.addEventListener('click', function () { selectStep(item.type, { focus: true }); });
                    li.appendChild(link);
                    ui.depsList.appendChild(li);
                });
            }
            ui.deps.hidden = !(deps && deps.missing.length);
            ui.depsOk.hidden = !(deps && deps.ready);

            // Checklist "Incluye".
            ui.includes.innerHTML = '';
            data.includes.forEach(function (item) {
                var li = document.createElement('li');
                li.className = 'rf-checklist__item' + (item.available ? '' : ' is-empty');
                var icon = document.createElement('i');
                icon.className = 'bi ' + (item.available ? 'bi-check-circle-fill' : 'bi-dash-circle');
                icon.setAttribute('aria-hidden', 'true');
                var label = document.createElement('span');
                label.className = 'rf-checklist__label';
                label.textContent = item.label;
                var value = document.createElement('span');
                value.className = 'rf-checklist__value';
                value.textContent = item.value;
                var sr = document.createElement('span');
                sr.className = 'visually-hidden';
                sr.textContent = item.available ? ' (con datos)' : ' (sin datos)';
                li.appendChild(icon);
                li.appendChild(label);
                li.appendChild(sr);
                li.appendChild(value);
                ui.includes.appendChild(li);
            });

            // Selects.
            var annexOption = ui.format.querySelector('option[value="pdf_annex"]');
            if (annexOption) {
                annexOption.disabled = !data.annex_available;
                if (!data.annex_available && ui.format.value === 'pdf_annex') ui.format.value = 'pdf';
            }
            ui.formatHint.hidden = data.annex_available;

            ui.cycle.disabled = !data.cycle.applies;
            ui.cycleHint.hidden = data.cycle.applies;

            // Formulario de generación.
            ui.inputType.value = data.report_type;
            ui.inputTitle.value = data.report_title;

            // Acciones.
            if (data.preview_url) {
                ui.preview.href = data.preview_url;
                ui.preview.classList.remove('disabled');
                ui.preview.removeAttribute('aria-disabled');
                ui.preview.removeAttribute('tabindex');
                ui.preview.title = '';
            } else {
                ui.preview.href = '#';
                ui.preview.classList.add('disabled');
                ui.preview.setAttribute('aria-disabled', 'true');
                ui.preview.setAttribute('tabindex', '-1');
                ui.preview.title = 'Registra un plan de pruebas para ver la vista previa';
            }

            ui.download.hidden = !generated;
            updateDownloadHref();
            if (ui.regenerate) ui.regenerate.hidden = !generated;
            setSubmitting(false);
        }

        function updateDownloadHref() {
            if (!state.data || !state.data.download_url) return;
            ui.download.href = state.data.download_url + '?format=' + encodeURIComponent(ui.format.value);
        }

        ui.format.addEventListener('change', updateDownloadHref);
        ui.cycle.addEventListener('change', load);

        /* ---------- Generar / regenerar ---------- */

        function missingDependencies() {
            var deps = state.data && state.data.dependencies;
            return deps ? deps.missing : [];
        }

        function showConfirm(submitter) {
            state.pendingSubmitter = submitter;
            ui.confirm.hidden = false;
            ui.confirmYes.focus();
        }

        function hideConfirm() {
            state.pendingSubmitter = null;
            state.confirmed = false;
            if (ui.confirm) ui.confirm.hidden = true;
        }

        function setSubmitting(submitting) {
            state.submitting = submitting;
            [ui.generate, ui.regenerate].forEach(function (button) {
                if (button) button.disabled = submitting;
            });
            if (ui.generate) {
                ui.generate.innerHTML = submitting
                    ? '<span class="spinner-border spinner-border-sm" aria-hidden="true"></span> Generando…'
                    : '<i class="bi bi-file-earmark-pdf" aria-hidden="true"></i> Generar PDF';
            }
        }

        ui.form.addEventListener('submit', function (event) {
            var submitter = event.submitter || state.pendingSubmitter || ui.generate;
            if (!state.data || state.submitting) {
                event.preventDefault();
                return;
            }
            if (state.data.type === 'final' && missingDependencies().length && !state.confirmed) {
                event.preventDefault();
                showConfirm(submitter);
                return;
            }
            // "Regenerar" actualiza el informe sin descargar; "Generar PDF" crea y descarga.
            ui.inputSkip.disabled = submitter !== ui.regenerate;
            ui.confirm.hidden = true;
            setSubmitting(true);
        });

        if (ui.confirmYes) {
            ui.confirmYes.addEventListener('click', function () {
                var submitter = state.pendingSubmitter || ui.generate;
                state.confirmed = true;
                if (typeof ui.form.requestSubmit === 'function') {
                    ui.form.requestSubmit(submitter);
                } else {
                    submitter.click();
                }
            });
        }
        if (ui.confirmNo) {
            ui.confirmNo.addEventListener('click', function () {
                var submitter = state.pendingSubmitter;
                hideConfirm();
                if (submitter) submitter.focus();
            });
        }

        /* ---------- URL y descarga automática ---------- */

        function updateUrl(changes, removals) {
            if (!window.history || !window.history.replaceState) return;
            var url = new URL(window.location.href);
            Object.keys(changes || {}).forEach(function (key) { url.searchParams.set(key, changes[key]); });
            (removals || []).forEach(function (key) { url.searchParams.delete(key); });
            window.history.replaceState(null, '', url.toString());
        }

        if (root.dataset.autoDownload) {
            // Tras "Generar PDF" el servidor redirige aquí; lanzamos la descarga del informe recién creado.
            var frame = document.createElement('iframe');
            frame.hidden = true;
            frame.src = root.dataset.autoDownload;
            document.body.appendChild(frame);
            updateUrl({}, ['download', 'format']);
        }

        // Al volver con el botón "atrás" (bfcache) los botones no deben quedar en "Generando…".
        window.addEventListener('pageshow', function (event) {
            if (event.persisted) setSubmitting(false);
        });

        load();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
