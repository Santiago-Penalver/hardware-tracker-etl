const liveSearchInput = document.getElementById('liveSearchInput');
const liveSearchResults = document.getElementById('liveSearchResults');

liveSearchInput.addEventListener('input', async (e) => {
    const query = e.target.value.trim();

     // Si se borra dos caracteres, se limpia los resultados.
    if (query.length < 2) {
        liveSearchResults.innerHTML = '';
        return;
    }

    try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const products = await response.json();

        if (products.length === 0) {
            liveSearchResults.innerHTML = '<p style= "color: #aaa; grid-column: 1 / -1; text-align: center;">No se encontraron productos.</p>'
            return;
        }

        let html = '';
        products.forEach(p => {
            html += `
                <div style="background: #181b22; border: 1px solid #2d323d; border-radius: 8px; padding: 15px; display: flex; flex-direction: column; justify-content: space-between;">
                    <span style="font-size: 12px; color: #f39c12; font-weight: bold; text-transform: uppercase;">${p.tienda}</span>
                    <h4 style="font-size: 14px; color: #e0e0e0; margin: 10px 0; line-height: 1.4;">${p.nombre}</h4>
                    <p style="font-size: 16px; color: #2ecc71; font-weight: bold; margin: 0;">$${p.precio.toLocaleString('es-AR')}</p>
                </div>
            `;
        })

        liveSearchResults.innerHTML = html;
    } catch(error) {
        console.error("Error al buscar productos:", error);
    }

});