/**
 * staff_cascade.js
 * Lógica de selects en cascada para el Panel de Carga Staff.
 *
 * Flujo: Oposición → Temas → Capítulos → Artículos → Preview
 *
 * Cada select llama a su endpoint JSON correspondiente y rellena
 * el siguiente select de la cadena, deshabilitando los posteriores.
 */

'use strict';

(function () {
    // ── Referencias a los selects ─────────────────────────────────────────────
    const selOposicion = document.getElementById('id_oposicion_selector');
    const selTema      = document.getElementById('id_tema_selector');
    const selCapitulo  = document.getElementById('id_capitulo_selector');
    const selArticulo  = document.getElementById('id_articulo');
    const previewBox   = document.getElementById('staff-articulo-preview');

    if (!selOposicion) return; // No estamos en la página del wizard

    // ── Utilidades ────────────────────────────────────────────────────────────

    /**
     * Rellena un <select> con las opciones recibidas del servidor.
     * @param {HTMLSelectElement} sel - El elemento select a rellenar.
     * @param {Array<{id: number, label: string}>} opciones
     * @param {string} placeholder - Texto del primer option vacío.
     */
    function poblarSelect(sel, opciones, placeholder) {
        sel.innerHTML = `<option value="">${placeholder}</option>`;
        opciones.forEach(({ id, label }) => {
            const opt = document.createElement('option');
            opt.value = id;
            opt.textContent = label;
            sel.appendChild(opt);
        });
        sel.disabled = opciones.length === 0;
    }

    /**
     * Vacía un <select> y lo deshabilita, mostrando un placeholder.
     * @param {HTMLSelectElement} sel
     * @param {string} placeholder
     */
    function resetSelect(sel, placeholder) {
        sel.innerHTML = `<option value="">${placeholder}</option>`;
        sel.disabled = true;
    }

    /**
     * Realiza un fetch JSON a la URL indicada y devuelve los datos.
     * @param {string} url
     * @returns {Promise<any>}
     */
    async function fetchJson(url) {
        const resp = await fetch(url, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (!resp.ok) throw new Error(`HTTP error ${resp.status}`);
        return resp.json();
    }

    /** Marca un select como "cargando" */
    function setLoading(sel, loading) {
        if (loading) {
            sel.classList.add('staff-select-loading');
        } else {
            sel.classList.remove('staff-select-loading');
        }
    }

    // ── Paso 1: Oposición → Temas ─────────────────────────────────────────────
    selOposicion.addEventListener('change', async function () {
        const oposicionId = this.value;

        // Reiniciar cascada hacia abajo
        resetSelect(selTema,      '-- Primero elige una oposición --');
        resetSelect(selCapitulo,  '-- Primero elige un tema --');
        resetSelect(selArticulo,  '-- Primero elige un capítulo --');
        ocultarPreview();

        if (!oposicionId) return;

        setLoading(selTema, true);
        try {
            const data = await fetchJson(`/examen/staff/api/temas/?oposicion_id=${oposicionId}`);
            const opciones = data.temas.map(t => ({
                id: t.id,
                label: t.bloque ? `[${t.bloque}] ${t.titulo}` : t.titulo,
            }));
            poblarSelect(selTema, opciones, '-- Selecciona un tema --');
        } catch (e) {
            console.error('Error cargando temas:', e);
            resetSelect(selTema, '-- Error al cargar temas --');
        } finally {
            setLoading(selTema, false);
        }
    });

    // ── Paso 2: Tema → Capítulos ──────────────────────────────────────────────
    selTema.addEventListener('change', async function () {
        const temaId = this.value;

        resetSelect(selCapitulo, '-- Primero elige un tema --');
        resetSelect(selArticulo, '-- Primero elige un capítulo --');
        ocultarPreview();

        if (!temaId) return;

        setLoading(selCapitulo, true);
        try {
            const data = await fetchJson(`/examen/staff/api/capitulos/?tema_id=${temaId}`);
            const opciones = data.capitulos.map(c => ({
                id: c.id,
                label: c.titulo,
            }));
            poblarSelect(selCapitulo, opciones, '-- Selecciona un capítulo --');
        } catch (e) {
            console.error('Error cargando capítulos:', e);
            resetSelect(selCapitulo, '-- Error al cargar capítulos --');
        } finally {
            setLoading(selCapitulo, false);
        }
    });

    // ── Paso 3: Capítulo → Artículos ──────────────────────────────────────────
    selCapitulo.addEventListener('change', async function () {
        const capituloId = this.value;

        resetSelect(selArticulo, '-- Primero elige un capítulo --');
        ocultarPreview();

        if (!capituloId) return;

        setLoading(selArticulo, true);
        try {
            const data = await fetchJson(`/examen/staff/api/articulos/?capitulo_id=${capituloId}`);

            // Guardamos el contenido de cada artículo en el propio option para el preview
            selArticulo.innerHTML = '<option value="">-- Selecciona un artículo --</option>';
            data.articulos.forEach(art => {
                const opt = document.createElement('option');
                opt.value = art.id;
                opt.textContent = `Art. ${art.numero}`;
                opt.dataset.contenido = art.contenido || '';
                selArticulo.appendChild(opt);
            });
            selArticulo.disabled = data.articulos.length === 0;

        } catch (e) {
            console.error('Error cargando artículos:', e);
            resetSelect(selArticulo, '-- Error al cargar artículos --');
        } finally {
            setLoading(selArticulo, false);
        }
    });

    // ── Paso 4: Artículo → Preview de contenido ───────────────────────────────
    selArticulo.addEventListener('change', function () {
        const selectedOption = this.options[this.selectedIndex];
        const contenido = selectedOption ? selectedOption.dataset.contenido : '';

        if (contenido && previewBox) {
            previewBox.innerHTML = contenido
                .substring(0, 600)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/\n/g, '<br>');
            if (contenido.length > 600) {
                previewBox.innerHTML += '<em>… (texto truncado)</em>';
            }
            previewBox.classList.remove('staff-preview-placeholder');
        } else {
            ocultarPreview();
        }
    });

    function ocultarPreview() {
        if (previewBox) {
            previewBox.innerHTML = '<em class="staff-preview-placeholder">El contenido del artículo seleccionado aparecerá aquí.</em>';
        }
    }

    // ── Activar el step-card correcto visualmente ─────────────────────────────
    const stepCards = document.querySelectorAll('.staff-step-card');

    function activarStep(cardId) {
        stepCards.forEach(c => c.classList.remove('active'));
        const card = document.getElementById(cardId);
        if (card) card.classList.add('active');
    }

    selOposicion?.addEventListener('change', () => activarStep('step-tema'));
    selTema?.addEventListener('change',      () => activarStep('step-capitulo'));
    selCapitulo?.addEventListener('change',  () => activarStep('step-articulo'));
    selArticulo?.addEventListener('change',  () => activarStep('step-pregunta'));

})();
