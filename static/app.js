let draggedCard = null;
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".task-card").forEach(card => {
    card.addEventListener("dragstart", () => { draggedCard = card; card.classList.add("dragging"); });
    card.addEventListener("dragend", () => { card.classList.remove("dragging"); draggedCard = null; });
  });
  document.querySelectorAll(".task-list").forEach(list => {
    list.addEventListener("dragover", e => { e.preventDefault(); list.classList.add("drag-over"); });
    list.addEventListener("dragleave", () => list.classList.remove("drag-over"));
    list.addEventListener("drop", async e => {
      e.preventDefault(); list.classList.remove("drag-over");
      if (!draggedCard) return;
      const status = list.dataset.status;
      list.appendChild(draggedCard);
      const response = await fetch(`/api/tasks/${draggedCard.dataset.id}/status`, {
        method: "POST", headers: {"Content-Type":"application/json"},
        body: JSON.stringify({status})
      });
      if (!response.ok) { alert("Não foi possível mover a tarefa."); location.reload(); }
      updateCounts();
    });
  });
  if (document.querySelector(".kanban")) {
    setInterval(refreshBoard, 15000);
  }
});
function updateCounts() {
  document.querySelectorAll(".column").forEach(col => {
    col.querySelector(".count").textContent = col.querySelectorAll(".task-card").length;
  });
}
function filterTasks() {
  const term = document.getElementById("search").value.toLowerCase();
  document.querySelectorAll(".task-card").forEach(card => {
    card.style.display = card.dataset.title.includes(term) ? "" : "none";
  });
}
function openCreateModal() {
  const form = document.getElementById("taskForm");
  form.reset(); form.action = "/tasks/create";
  document.getElementById("modalTitle").textContent = "Nova tarefa";
  document.getElementById("taskModal").showModal();
}
function openEditModal(id) {
  const data = JSON.parse(document.getElementById(`task-${id}`).textContent);
  const form = document.getElementById("taskForm");
  form.reset(); form.action = `/tasks/${id}/edit`;
  Object.keys(data).forEach(key => {
    const field = form.elements[key];
    if (field) field.value = data[key] ?? "";
  });
  document.getElementById("modalTitle").textContent = "Editar tarefa";
  document.getElementById("taskModal").showModal();
}
function closeModal() { document.getElementById("taskModal").close(); }
async function refreshBoard() {
  // Recarrega se outro usuário tiver alterado o quadro; preserva a busca atual.
  try {
    const response = await fetch("/api/board", {cache:"no-store"});
    if (!response.ok) return;
    const remote = await response.json();
    const local = [...document.querySelectorAll(".task-card")].map(c => c.dataset.id).sort().join(",");
    const ids = remote.map(t => String(t.id)).sort().join(",");
    const state = remote.map(t => `${t.id}:${t.status}:${t.title}:${t.priority}:${t.assignee}:${t.due_date}`).sort().join("|");
    if (window.lastBoardState === undefined) window.lastBoardState = state;
    else if (state !== window.lastBoardState || local !== ids) location.reload();
  } catch (_) { /* A rede pode estar temporariamente indisponível. */ }
}
