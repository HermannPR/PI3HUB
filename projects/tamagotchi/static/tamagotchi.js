// Tamagotchi pixel art — TV head, one woman's eye, humanoid body
// Canvas: 192×224px (pixel size = 6px, so 32×37 pixel grid)

const canvas = document.getElementById("tama-canvas");
const ctx = canvas.getContext("2d");
const PX = 6; // pixel size

const C = {
  bg:       "#0a0a0f",
  body:     "#1e1a2e",
  bodyDark: "#12101e",
  tv:       "#2a2040",
  tvBorder: "#7b5ea7",
  screen:   "#0f1a2e",
  screenOn: "#1a3a6e",
  eye:      "#e0c0ff",
  pupil:    "#1a0a2e",
  lash:     "#c4b0ff",
  antenna:  "#7b5ea7",
  static:   "#c4b0ff",
  star:     "#ffd700",
  zzz:      "#7b5ea7",
  shine:    "#ffffff",
};

// --- pixel drawing helper ---
function px(gx, gy, color) {
  ctx.fillStyle = color;
  ctx.fillRect(gx * PX, gy * PX, PX, PX);
}

function rect(gx, gy, gw, gh, color) {
  ctx.fillStyle = color;
  ctx.fillRect(gx * PX, gy * PX, gw * PX, gh * PX);
}

// --- state machine ---
const State = { IDLE: "idle", HAPPY: "happy", GLITCH: "glitch", SLEEP: "sleep" };
let state = State.IDLE;
let lastClick = Date.now();
let score = 0;
let bounceY = 0;
let bounceDir = 1;
let bounceFrame = 0;
let stars = [];
let zzzs = [];
let blinkTimer = 0;
let eyeOpen = true;
let staticNoise = [];
let cooldown = false;
let frame = 0;

// generate random static pixels for glitch state
function makeStatic() {
  staticNoise = [];
  for (let i = 0; i < 30; i++) {
    staticNoise.push({
      x: 6 + Math.floor(Math.random() * 12),
      y: 7 + Math.floor(Math.random() * 7),
      c: Math.random() > 0.5 ? C.static : C.tvBorder,
    });
  }
}

function spawnStars() {
  for (let i = 0; i < 5; i++) {
    stars.push({
      x: 7 + Math.random() * 18,
      y: 5 + Math.random() * 10,
      life: 20,
      maxLife: 20,
      vx: (Math.random() - 0.5) * 0.3,
      vy: -0.15 - Math.random() * 0.15,
    });
  }
}

function spawnZzz() {
  zzzs.push({
    x: 20 + Math.random() * 4,
    y: 4,
    life: 60,
    maxLife: 60,
  });
}

// --- draw functions ---
function drawBackground() {
  ctx.fillStyle = C.bg;
  ctx.fillRect(0, 0, canvas.width, canvas.height);
}

function drawBody(dy) {
  // torso
  rect(8, 18 + dy, 16, 10, C.body);
  rect(9, 19 + dy, 14, 8, C.bodyDark);
  // left arm
  rect(5, 19 + dy, 3, 7, C.body);
  rect(4, 24 + dy, 3, 2, C.bodyDark); // hand
  // right arm
  rect(24, 19 + dy, 3, 7, C.body);
  rect(25, 24 + dy, 3, 2, C.bodyDark);
  // legs
  rect(10, 28 + dy, 5, 6, C.body);
  rect(17, 28 + dy, 5, 6, C.body);
  rect(10, 33 + dy, 5, 2, C.bodyDark); // feet
  rect(17, 33 + dy, 5, 2, C.bodyDark);
}

function drawTV(dy, blink, isGlitch) {
  // TV outer shell
  rect(5, 4 + dy, 22, 15, C.tvBorder);
  rect(6, 5 + dy, 20, 13, C.tv);
  // screen
  const screenColor = isGlitch ? C.screenOn : (state === State.SLEEP ? C.screen : C.screenOn);
  rect(7, 6 + dy, 18, 10, screenColor);
  // antenna
  px(14, 2 + dy, C.antenna);
  px(15, 3 + dy, C.antenna);
  px(16, 2 + dy, C.antenna);
  px(15, 4 + dy, C.antenna);

  if (isGlitch) {
    // TV static
    staticNoise.forEach(s => px(s.x, s.y + dy, s.c));
  } else if (state === State.SLEEP) {
    // dim screen
  } else {
    drawEye(dy, blink);
  }
}

function drawEye(dy, blink) {
  // woman's eye — right side of screen
  // whites
  rect(14, 8 + dy, 8, 5, C.eye);
  // top lashes
  px(14, 7 + dy, C.lash);
  px(15, 7 + dy, C.lash);
  px(16, 6 + dy, C.lash);
  px(17, 7 + dy, C.lash);
  px(18, 7 + dy, C.lash);
  px(19, 7 + dy, C.lash);
  px(20, 7 + dy, C.lash);
  px(21, 7 + dy, C.lash);
  // pupil
  if (!blink) {
    rect(17, 9 + dy, 3, 3, C.pupil);
    px(17, 9 + dy, C.shine); // shine
  } else {
    // closed eye — lash line
    rect(14, 10 + dy, 8, 1, C.lash);
  }
  // bottom lashes
  px(15, 13 + dy, C.lash);
  px(18, 13 + dy, C.lash);
  px(21, 13 + dy, C.lash);

  // decorative left side of screen (scan lines)
  for (let row = 7; row <= 14; row += 2) {
    px(8, row + dy, "#1a2a4e");
    px(9, row + dy, "#1a2a4e");
    px(10, row + dy, "#1a2a4e");
    px(11, row + dy, "#1a2a4e");
    px(12, row + dy, "#1a2a4e");
  }
}

function drawStars(dy) {
  stars.forEach(s => {
    const alpha = s.life / s.maxLife;
    ctx.globalAlpha = alpha;
    px(Math.round(s.x), Math.round(s.y) + dy, C.star);
    ctx.globalAlpha = 1;
    s.x += s.vx;
    s.y += s.vy;
    s.life--;
  });
  stars = stars.filter(s => s.life > 0);
}

function drawZzz(dy) {
  zzzs.forEach(z => {
    const alpha = z.life / z.maxLife;
    ctx.globalAlpha = alpha;
    const gx = Math.round(z.x);
    const gy = Math.round(z.y) + dy;
    // draw Z
    px(gx, gy, C.zzz); px(gx+1, gy, C.zzz); px(gx+2, gy, C.zzz);
    px(gx+2, gy+1, C.zzz);
    px(gx+1, gy+2, C.zzz);
    px(gx, gy+3, C.zzz); px(gx+1, gy+3, C.zzz); px(gx+2, gy+3, C.zzz);
    ctx.globalAlpha = 1;
    z.y -= 0.05;
    z.life--;
  });
  zzzs = zzzs.filter(z => z.life > 0);
}

// --- main loop ---
function updateState() {
  const elapsed = (Date.now() - lastClick) / 1000;
  if (state === State.HAPPY && bounceFrame <= 0) {
    state = State.IDLE;
  }
  if (elapsed > 120 && state !== State.SLEEP) {
    state = State.SLEEP;
  } else if (elapsed > 30 && elapsed <= 120 && state !== State.GLITCH && state !== State.HAPPY) {
    state = State.GLITCH;
    makeStatic();
  }
}

function loop() {
  frame++;
  updateState();

  // blink logic (idle only)
  if (state === State.IDLE || state === State.HAPPY) {
    blinkTimer++;
    if (blinkTimer > 180) blinkTimer = 0;
    eyeOpen = blinkTimer < 175;
  }

  // bounce
  let dy = 0;
  if (state === State.HAPPY) {
    bounceFrame--;
    bounceY += bounceDir * 0.5;
    if (Math.abs(bounceY) > 3) bounceDir *= -1;
    dy = Math.round(bounceY);
    if (frame % 3 === 0) spawnStars();
  } else {
    bounceY = 0;
    bounceDir = 1;
  }

  // glitch flicker
  if (state === State.GLITCH && frame % 8 === 0) makeStatic();

  // zzz spawn
  if (state === State.SLEEP && frame % 90 === 0) spawnZzz();

  drawBackground();
  drawBody(dy);
  drawTV(dy, !eyeOpen, state === State.GLITCH);
  drawStars(dy);
  drawZzz(dy);

  // status message
  const msg = document.getElementById("status-msg");
  if (state === State.SLEEP) msg.textContent = "zzzz...";
  else if (state === State.GLITCH) msg.textContent = "feed me";
  else if (state === State.HAPPY) msg.textContent = "♥";
  else msg.textContent = "";

  requestAnimationFrame(loop);
}

// --- click handler ---
const SESSION_ID = Math.random().toString(36).slice(2);
const API = window.API_BASE || "";

canvas.addEventListener("click", async () => {
  if (cooldown) return;
  const res = await fetch(`${API}/click`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: SESSION_ID }),
  });
  if (res.status === 429) return;
  if (!res.ok) return;

  score++;
  document.getElementById("score-display").textContent = `SCORE: ${score}`;
  state = State.HAPPY;
  bounceFrame = 40;
  lastClick = Date.now();
  spawnStars();

  // cooldown visual
  cooldown = true;
  canvas.classList.add("cooldown");
  setTimeout(() => {
    cooldown = false;
    canvas.classList.remove("cooldown");
  }, 3000);
});

loop();
