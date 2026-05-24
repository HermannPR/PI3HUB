const API = window.API_BASE || "";

async function fetchBoard() {
  try {
    const res = await fetch(`${API}/leaderboard`);
    const data = await res.json();
    const tbody = document.getElementById("board-body");
    tbody.innerHTML = data.map(r =>
      `<tr><td>#${r.rank}</td><td>${r.nick}</td><td>${r.score}</td></tr>`
    ).join("") || `<tr><td colspan="3" style="color:#3a2a5a;font-size:7px;text-align:center;padding:8px">NO SCORES YET</td></tr>`;
  } catch (_) {}
}

// nick input — auto-advance, uppercase only
const boxes = document.querySelectorAll(".nick-box");
boxes.forEach((box, i) => {
  box.addEventListener("keydown", e => {
    if (e.key === "Backspace" && box.value === "" && i > 0) {
      boxes[i - 1].focus();
    }
  });
  box.addEventListener("input", () => {
    box.value = box.value.replace(/[^a-zA-Z0-9]/, "").toUpperCase();
    if (box.value && i < boxes.length - 1) boxes[i + 1].focus();
  });
});

document.getElementById("submit-btn").addEventListener("click", async () => {
  const nick = Array.from(boxes).map(b => b.value).join("").trim().toUpperCase();
  if (nick.length < 1) return;
  const score = window.score || 0;
  if (score < 1) {
    document.getElementById("submit-msg").textContent = "click first!";
    return;
  }
  const btn = document.getElementById("submit-btn");
  btn.disabled = true;
  try {
    await fetch(`${API}/submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nick, score }),
    });
    document.getElementById("submit-msg").textContent = "saved!";
    boxes.forEach(b => b.value = "");
    await fetchBoard();
  } catch (_) {
    document.getElementById("submit-msg").textContent = "error";
  } finally {
    setTimeout(() => {
      btn.disabled = false;
      document.getElementById("submit-msg").textContent = "";
    }, 3000);
  }
});

// expose score to leaderboard.js from tamagotchi.js
Object.defineProperty(window, "score", {
  get: () => {
    const el = document.getElementById("score-display");
    return parseInt(el?.textContent?.replace("SCORE: ", "") || "0");
  }
});

fetchBoard();
setInterval(fetchBoard, 30000);
