/* Escape external data in text and quoted HTML attribute contexts. */
function escapeHtml(value) {
    const entities = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
    return String(value == null ? '' : value).replace(/[&<>"']/g, character => entities[character]);
}
if (typeof module !== 'undefined' && module.exports) module.exports = { escapeHtml };
