// script.js — логика Mini‑App HonestRE, адаптированная под расширенную карточку
// Prod‑API: https://api.easychina.kz

const API_BASE = "https://api.easychina.kz";

/* ---------------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---------------- */
async function apiGet(path) {
  const resp = await fetch(`${API_BASE}${path}`);
  if (!resp.ok) throw new Error(await resp.text());
  return resp.json();
}

function renderReviewCard(r) {
  const gasDisplay = r.gas === 0 || r.gas === null ? "Отсутствует" : `${r.gas}/5`;
  const dateStr = new Date(r.date || r.created_at).toLocaleString("ru-RU");

  return `
<b>📄 ID ${r.id}</b><br>
🏙️ <b>${r.city}</b> <i>${r.complex_name}</i><br>
${r.status}<br>
🔥 Отопление: ${r.heating}/5 | ⚡ Электр: ${r.electricity}/5 | 🏭 Газ: ${gasDisplay}<br>
💧 Вода: ${r.water}/5 | 🔊 Шум: ${r.noise}/5 | 🏢 УК: ${r.mgmt}/5<br>
💰 Аренда: ${r.rent_price ?? "—"}<br>
👍 ${r.likes ?? ""}<br>
👎 ${r.annoy ?? ""}<br>
✅ Рекомендация: ${r.recommend ? "Да" : "Нет"}<br>
⏰ ${dateStr}
  `;
}

/* ---------------- СТРАНИЦА ПОИСКА (search.html) ---------------- */
const searchForm = document.getElementById("searchForm");
if (searchForm) {
  const resultBlock = document.getElementById("resultBlock");

  searchForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    resultBlock.innerHTML = "⏳ Поиск…";

    const queryInput = document.getElementById("query");
    const query = queryInput.value.trim();
    if (!query) {
      resultBlock.innerHTML = "Введите название ЖК";
      return;
    }

    try {
      const complexes = await apiGet(`/complexes?query=${encodeURIComponent(query)}`);
      if (complexes.length === 0) {
        resultBlock.innerHTML = "ЖК не найден, уточните запрос.";
        return;
      }

      const complex = complexes[0];
      const reviews = await apiGet(`/reviews?complex_id=${complex.id}&limit=3`);

      if (reviews.length === 0) {
        resultBlock.innerHTML = `Для <b>${complex.name}</b> пока нет отзывов.`;
        return;
      }

      resultBlock.innerHTML = reviews.map(renderReviewCard).join("<br><hr><br>");
    } catch (err) {
      resultBlock.innerHTML = `Ошибка: ${err.message}`;
    }
  });
}
