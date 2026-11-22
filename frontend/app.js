"use strict";

const roleOrder = ["TOP", "JGL", "MID", "BOT", "SUP"];
const metricOrder = ["Engage", "Frontline", "AP_AD_Balance", "Scaling", "Pick"];
const fallbackDDragon = "15.1.1";

const model = {
  matchups: [],
  champions: [],
  championById: new Map(),
  state: null,
  solve: null,
  ddragonVersion: fallbackDDragon,
  activeRole: "ALL",
  search: "",
  showLocks: true,
  solverLatency: 0,
};

const dom = {};

document.addEventListener("DOMContentLoaded", init);

async function init() {
  cacheDom();
  bindControls();
  syncLockToggle();
  renderRoleTabs();
  await loadDDragonVersion();
  await Promise.all([loadMatchups(), loadChampions()]);
  await refreshAll();
}

function cacheDom() {
  dom.matchupSelect = document.querySelector("#matchupSelect");
  dom.gridIndicator = document.querySelector("#gridIndicator");
  dom.seriesRibbon = document.querySelector("#seriesRibbon");
  dom.turnIndicator = document.querySelector("#turnIndicator");
  dom.turnLabel = document.querySelector("#turnLabel");
  dom.undoBtn = document.querySelector("#undoBtn");
  dom.nextGameBtn = document.querySelector("#nextGameBtn");
  dom.briefBtn = document.querySelector("#briefBtn");
  dom.demoBtn = document.querySelector("#demoBtn");
  dom.resetBtn = document.querySelector("#resetBtn");
  dom.evalRed = document.querySelector("#evalRed");
  dom.evalBlue = document.querySelector("#evalBlue");
  dom.evalReadout = document.querySelector("#evalReadout");
  dom.blueTeamName = document.querySelector("#blueTeamName");
  dom.redTeamName = document.querySelector("#redTeamName");
  dom.blueBans = document.querySelector("#blueBans");
  dom.redBans = document.querySelector("#redBans");
  dom.bluePicks = document.querySelector("#bluePicks");
  dom.redPicks = document.querySelector("#redPicks");
  dom.blueMetrics = document.querySelector("#blueMetrics");
  dom.roleTabs = document.querySelector("#roleTabs");
  dom.championSearch = document.querySelector("#championSearch");
  dom.lockToggle = document.querySelector("#lockToggle");
  dom.championGrid = document.querySelector("#championGrid");
  dom.solverSide = document.querySelector("#solverSide");
  dom.solverLatency = document.querySelector("#solverLatency");
  dom.solverRows = document.querySelector("#solverRows");
  dom.poolHealth = document.querySelector("#poolHealth");
  dom.briefModal = document.querySelector("#briefModal");
  dom.briefContent = document.querySelector("#briefContent");
  dom.copyBriefBtn = document.querySelector("#copyBriefBtn");
  dom.closeBriefBtn = document.querySelector("#closeBriefBtn");
}

function bindControls() {
  dom.matchupSelect.addEventListener("change", async () => {
    await postJson("/api/load-matchup", { matchup_id: dom.matchupSelect.value });
    await refreshAll();
  });

  dom.undoBtn.addEventListener("click", undo);
  dom.nextGameBtn.addEventListener("click", nextGame);
  dom.resetBtn.addEventListener("click", resetDraft);
  dom.demoBtn.addEventListener("click", loadDemo);
  dom.briefBtn.addEventListener("click", openBrief);
  dom.closeBriefBtn.addEventListener("click", closeBrief);
  dom.copyBriefBtn.addEventListener("click", copyBrief);

  dom.championSearch.addEventListener("input", () => {
    model.search = dom.championSearch.value.trim();
    renderChampionGrid();
  });

  dom.lockToggle.addEventListener("click", () => {
    model.showLocks = !model.showLocks;
    syncLockToggle();
    renderChampionGrid();
  });

  dom.championGrid.addEventListener("click", async (event) => {
    const tile = event.target.closest("[data-champion-id]");
    if (!tile || tile.disabled) {
      return;
    }
    await applyChampion(tile.dataset.championId);
  });

  dom.solverRows.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-apply-move]");
    if (!button) {
      return;
    }
    await applyChampion(button.dataset.applyMove, button.dataset.targetRole || null);
  });

  dom.poolHealth.addEventListener("click", (event) => {
    const row = event.target.closest("[data-role]");
    if (!row) {
      return;
    }
    model.activeRole = row.dataset.role;
    renderRoleTabs();
    renderChampionGrid();
    renderPoolHealth();
  });

  document.addEventListener("keydown", async (event) => {
    const key = event.key;
    const mod = event.ctrlKey || event.metaKey;
    if (key === "/" && document.activeElement !== dom.championSearch) {
      event.preventDefault();
      dom.championSearch.focus();
      return;
    }
    if (key === "Escape") {
      if (!dom.briefModal.hidden) {
        closeBrief();
        return;
      }
      if (dom.championSearch.value) {
        dom.championSearch.value = "";
        model.search = "";
        renderChampionGrid();
      }
      return;
    }
    if (key === "Enter" && document.activeElement === dom.championSearch) {
      const match = topSearchMatch();
      if (match) {
        await applyChampion(match.id);
      }
      return;
    }
    if (mod && key.toLowerCase() === "z") {
      event.preventDefault();
      await undo();
    }
  });
}

async function loadDDragonVersion() {
  try {
    const versions = await fetch("https://ddragon.leagueoflegends.com/api/versions.json", { cache: "force-cache" }).then(assertOk);
    model.ddragonVersion = versions[0] || fallbackDDragon;
  } catch {
    model.ddragonVersion = fallbackDDragon;
  }
}

async function loadMatchups() {
  model.matchups = await fetchJson("/api/matchups");
  dom.matchupSelect.innerHTML = model.matchups
    .map((matchup) => `<option value="${escapeHtml(matchup.id)}">${escapeHtml(matchup.name)}</option>`)
    .join("");
}

async function loadChampions() {
  model.champions = await fetchJson("/api/champions");
  model.championById = new Map(model.champions.map((champion) => [champion.id, champion]));
}

async function refreshAll() {
  model.state = await fetchJson("/api/state");
  const selected = model.matchups.find((matchup) => matchup.name === model.state.matchup);
  if (selected) {
    dom.matchupSelect.value = selected.id;
  }
  const started = performance.now();
  model.solve = await fetchJson("/api/solve");
  model.solverLatency = Math.round(performance.now() - started);
  renderAll();
}

async function fetchJson(url) {
  return fetch(url).then(assertOk);
}

async function postJson(url, payload = {}) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || response.statusText);
  }
  return response.json();
}

async function assertOk(response) {
  if (!response.ok) {
    throw new Error(response.statusText);
  }
  return response.json();
}

function renderAll() {
  renderCommandBar();
  renderEval();
  renderTeamPanel("BLUE", dom.blueBans, dom.bluePicks);
  renderTeamPanel("RED", dom.redBans, dom.redPicks);
  renderMetrics();
  renderChampionGrid();
  renderSolver();
  renderPoolHealth();
}

function syncLockToggle() {
  dom.lockToggle.classList.toggle("active", model.showLocks);
  dom.lockToggle.setAttribute("aria-pressed", String(model.showLocks));
  dom.lockToggle.textContent = model.showLocks ? "LOCKS ON" : "LOCKS OFF";
}

function renderCommandBar() {
  const game = model.state.game;
  const locksByGame = locksGroupedByGame();
  dom.gridIndicator.textContent = model.state.grid_feed || "GRID SNAPSHOT";
  dom.seriesRibbon.innerHTML = [1, 2, 3, 4, 5]
    .map((slot) => {
      const cls = slot < game ? "complete" : slot === game ? "active" : "upcoming";
      const count = locksByGame[`G${slot}`] || 0;
      return `<div class="series-segment ${cls}"><span>G${slot}</span><span class="lock-count num">${count}</span></div>`;
    })
    .join("");

  const turn = model.state.turn;
  dom.turnIndicator.classList.toggle("side-red", turn?.side === "RED");
  dom.turnIndicator.classList.toggle("side-blue", turn?.side !== "RED");
  dom.turnLabel.textContent = turn ? turnLabel(turn.side, turn.action_type) : "DRAFT COMPLETE";
  dom.nextGameBtn.disabled = model.state.step !== 20 || model.state.game >= 5;
}

function locksGroupedByGame() {
  const grouped = {};
  Object.values(model.state.fearless_locks || {}).forEach((gameTag) => {
    grouped[gameTag] = (grouped[gameTag] || 0) + 1;
  });
  return grouped;
}

function turnLabel(side, actionType) {
  const used = currentActions().filter((action) => action.side === side && action.action_type === actionType).length;
  return `${side} ${actionType} ${used + 1}`;
}

function renderEval() {
  const score = clamp(model.solve?.eval_score ?? 0, -10, 10);
  const bluePct = ((score + 10) / 20) * 100;
  const redPct = 100 - bluePct;
  dom.evalBlue.style.height = `${bluePct}%`;
  dom.evalRed.style.height = `${redPct}%`;
  dom.evalReadout.textContent = formatSigned(score, 1);
  dom.evalReadout.style.color = score >= 0 ? "var(--blue)" : "var(--red)";
}

function renderTeamPanel(side, banRoot, pickRoot) {
  const teamKey = side === "BLUE" ? "blue_team" : "red_team";
  const nameRoot = side === "BLUE" ? dom.blueTeamName : dom.redTeamName;
  nameRoot.textContent = model.state[teamKey]?.name || side;
  renderBanStrip(side, banRoot);
  renderPickSlots(side, pickRoot);
}

function renderBanStrip(side, root) {
  const bans = actionsFor(side, "BAN");
  const active = model.state.turn?.side === side && model.state.turn?.action_type === "BAN";
  root.innerHTML = Array.from({ length: 5 }, (_, index) => {
    const action = bans[index];
    const activeClass = active && index === bans.length ? `active-${side.toLowerCase()}` : "";
    if (!action) {
      return `<div class="ban-slot ${activeClass}"></div>`;
    }
    return `<div class="ban-slot slash">${portraitImage(action.champion_id, championName(action.champion_id))}</div>`;
  }).join("");
}

function renderPickSlots(side, root) {
  const picks = actionsFor(side, "PICK");
  const active = model.state.turn?.side === side && model.state.turn?.action_type === "PICK";
  const prefix = side === "BLUE" ? "B" : "R";
  root.innerHTML = Array.from({ length: 5 }, (_, index) => {
    const action = picks[index];
    const activeClass = active && index === picks.length ? "active" : "";
    if (!action) {
      return emptyPickSlot(prefix, index + 1, activeClass);
    }
    const champion = model.championById.get(action.champion_id);
    const damage = champion?.damage || "";
    const role = action.role || inferRoleForChampion(action.champion_id, side) || "--";
    return `
      <div class="pick-slot ${activeClass}">
        <div class="slot-code num">${prefix}${index + 1}</div>
        <div class="slot-portrait">${portraitImage(action.champion_id, championName(action.champion_id))}</div>
        <div class="slot-info">
          <div class="slot-name">${escapeHtml(championName(action.champion_id))}</div>
          <div class="slot-meta">
            <span class="tag">${escapeHtml(role)}</span>
            <span class="damage-badge ${damage.toLowerCase()}">${escapeHtml(damage)}</span>
          </div>
        </div>
      </div>
    `;
  }).join("");
}

function emptyPickSlot(prefix, number, activeClass) {
  return `
    <div class="pick-slot ${activeClass}">
      <div class="slot-code num">${prefix}${number}</div>
      <div class="slot-portrait"><span class="portrait-fallback">${prefix}${number}</span></div>
      <div class="slot-info">
        <div class="slot-name">OPEN</div>
        <div class="slot-meta"><span class="tag">ROLE</span><span class="damage-badge">--</span></div>
      </div>
    </div>
  `;
}

function renderMetrics() {
  const metrics = model.solve?.comp_radar?.BLUE || {};
  dom.blueMetrics.innerHTML = metricOrder.map((metric) => metricRow(metric, metrics[metric] || 0)).join("");
}

function metricRow(metric, value) {
  const label = metric.replace("AP_AD_Balance", "AP/AD");
  const width = clamp(value, 0, 10) * 10;
  return `
    <div class="metric-row">
      <span>${escapeHtml(label)}</span>
      <span class="metric-track"><span class="metric-fill" style="width:${width}%"></span></span>
      <span class="num">${Number(value).toFixed(1)}</span>
    </div>
  `;
}

function renderRoleTabs() {
  const roles = ["ALL", ...roleOrder];
  dom.roleTabs.innerHTML = roles
    .map((role) => `<button class="role-tab ${model.activeRole === role ? "active" : ""}" type="button" data-role-tab="${role}">${role}</button>`)
    .join("");
  dom.roleTabs.querySelectorAll("[data-role-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      model.activeRole = button.dataset.roleTab;
      renderRoleTabs();
      renderChampionGrid();
      renderPoolHealth();
    });
  });
}

function renderChampionGrid() {
  const champions = filteredChampions();
  dom.championGrid.innerHTML = champions.map(championTile).join("");
}

function filteredChampions() {
  const query = model.search.toLowerCase();
  return model.champions.filter((champion) => {
    if (model.activeRole !== "ALL" && !champion.roles.includes(model.activeRole)) {
      return false;
    }
    if (query && !champion.name.toLowerCase().includes(query) && !champion.id.toLowerCase().includes(query)) {
      return false;
    }
    if (!model.showLocks && priorLockTag(champion.id)) {
      return false;
    }
    return true;
  });
}

function championTile(champion) {
  const current = currentActionForChampion(champion.id);
  const priorLock = priorLockTag(champion.id);
  const disabled = Boolean(current || priorLock || !model.state.turn);
  const status = current ? current.action_type : priorLock;
  const classes = [current ? "used" : "", priorLock ? "locked" : ""].join(" ");
  const score = Number(champion.base_score).toFixed(1);
  return `
    <button class="champion-tile ${classes}" type="button" data-champion-id="${escapeHtml(champion.id)}" ${disabled ? "disabled" : ""}>
      ${status ? `<span class="tile-status num">${escapeHtml(status)}</span>` : ""}
      <div class="tile-portrait">${portraitImage(champion.id, champion.name)}</div>
      <div class="champion-name">${escapeHtml(champion.name)}</div>
      <div class="champion-subline">
        <span class="tag">${escapeHtml(champion.roles[0])}</span>
        <span class="num">${score}</span>
      </div>
    </button>
  `;
}

function renderSolver() {
  const turn = model.state.turn;
  dom.solverSide.textContent = turn ? `${turn.side} ${turn.action_type}` : "COMPLETE";
  dom.solverSide.style.color = turn?.side === "RED" ? "var(--red)" : "var(--blue)";
  dom.solverLatency.textContent = String(model.solverLatency);
  const moves = model.solve?.top_moves || [];
  dom.solverRows.innerHTML = moves.length
    ? moves.map((move, index) => solverRow(move, index)).join("")
    : `<div class="solver-row"><span class="num">--</span><span>No move</span><span></span><span></span><span></span><span></span></div>`;
}

function solverRow(move, index) {
  const champion = model.championById.get(move.champion_id);
  const deltaClass = move.eval_delta >= 0 ? "delta-positive" : "delta-negative";
  return `
    <div class="solver-row">
      <span class="num">#${index + 1}</span>
      <span class="move-champion">
        <span class="small-portrait">${portraitImage(move.champion_id, championName(move.champion_id))}</span>
        <span class="move-title">${escapeHtml(champion?.name || move.champion_id)} <span class="move-action">${escapeHtml(move.action_type)}</span></span>
      </span>
      <span class="num ${deltaClass}">${formatSigned(move.eval_delta, 2)} ADV</span>
      <span class="move-tag">${escapeHtml(move.pinch_tag)}</span>
      <span class="move-reason">${escapeHtml(move.reason)}</span>
      <button class="apply-button" type="button" data-apply-move="${escapeHtml(move.champion_id)}" data-target-role="${escapeHtml(move.target_role || "")}">Apply</button>
    </div>
  `;
}

function renderPoolHealth() {
  const health = model.solve?.red_pool_health || model.solve?.opponent_pool_health || {};
  const players = model.state.red_team?.players || {};
  dom.poolHealth.innerHTML = roleOrder.map((role) => {
    const row = health[role] || { remaining_comfort: 0, collapse_risk: "SAFE" };
    const status = row.collapse_risk.toLowerCase();
    const player = players[role]?.name || role;
    return `
      <button class="health-row ${status} ${model.activeRole === role ? "active" : ""}" type="button" data-role="${role}">
        <span class="role-code">${role}</span>
        <span class="player-name">${escapeHtml(player)}</span>
        <span class="tick-wrap" aria-label="${row.remaining_comfort} comfort picks">${tickBar(row.remaining_comfort)}</span>
        <span class="status-tag ${status}">${escapeHtml(row.collapse_risk)}</span>
      </button>
    `;
  }).join("");
}

function tickBar(count) {
  return Array.from({ length: 6 }, (_, index) => `<span class="tick ${index < count ? "on" : ""}"></span>`).join("");
}

async function applyChampion(championId, forcedRole = null) {
  if (!model.state?.turn) {
    return;
  }
  const body = { champion_id: championId };
  if (model.state.turn.action_type === "PICK") {
    body.role = forcedRole || inferRoleForChampion(championId, model.state.turn.side);
  }
  try {
    await postJson("/api/action", body);
    await refreshAll();
  } catch (error) {
    window.console.warn(error.message);
  }
}

async function undo() {
  await postJson("/api/undo");
  await refreshAll();
}

async function nextGame() {
  if (dom.nextGameBtn.disabled) {
    return;
  }
  await postJson("/api/next-game");
  await refreshAll();
}

async function resetDraft() {
  await postJson("/api/reset");
  await refreshAll();
}

async function loadDemo() {
  model.showLocks = true;
  syncLockToggle();
  await postJson("/api/demo-g3-pinch");
  await refreshAll();
}

async function openBrief() {
  const payload = await fetchJson("/api/dossier");
  dom.briefContent.textContent = payload.markdown;
  dom.briefModal.hidden = false;
}

function closeBrief() {
  dom.briefModal.hidden = true;
}

async function copyBrief() {
  await navigator.clipboard.writeText(dom.briefContent.textContent);
}

function topSearchMatch() {
  const matches = filteredChampions().filter((champion) => !currentActionForChampion(champion.id) && !priorLockTag(champion.id));
  if (matches.length === 1) {
    return matches[0];
  }
  const query = model.search.toLowerCase();
  return matches.find((champion) => champion.name.toLowerCase() === query || champion.id.toLowerCase() === query) || null;
}

function currentActions() {
  return (model.state?.actions || []).filter((action) => action.game === model.state.game);
}

function actionsFor(side, type) {
  return currentActions().filter((action) => action.side === side && action.action_type === type);
}

function currentActionForChampion(championId) {
  return currentActions().find((action) => action.champion_id === championId) || null;
}

function priorLockTag(championId) {
  const tag = model.state?.fearless_locks?.[championId];
  if (!tag) {
    return null;
  }
  const gameNumber = Number(tag.replace("G", ""));
  return gameNumber < model.state.game ? tag : null;
}

function inferRoleForChampion(championId, side) {
  const champion = model.championById.get(championId);
  if (!champion) {
    return null;
  }
  if (model.activeRole !== "ALL" && champion.roles.includes(model.activeRole)) {
    return model.activeRole;
  }
  const team = side === "BLUE" ? model.state.blue_team : model.state.red_team;
  for (const role of roleOrder) {
    const player = team?.players?.[role];
    const comfort = player?.comfort || {};
    const pool = [...(comfort.S || []), ...(comfort.A || []), ...(comfort.B || [])];
    if (pool.includes(championId) && champion.roles.includes(role)) {
      return role;
    }
  }
  return champion.roles[0] || null;
}

function portraitImage(championId, altText) {
  const src = `https://ddragon.leagueoflegends.com/cdn/${model.ddragonVersion}/img/champion/${encodeURIComponent(championId)}.png`;
  const fallback = monogram(altText || championId);
  return `<img src="${src}" alt="${escapeHtml(altText || championId)}" loading="lazy" onerror="this.hidden=true;this.nextElementSibling.hidden=false"><span class="portrait-fallback" hidden>${escapeHtml(fallback)}</span>`;
}

function championName(championId) {
  return model.championById.get(championId)?.name || championId;
}

function monogram(name) {
  const parts = String(name).replace(/[^A-Za-z0-9 ]/g, " ").trim().split(/\s+/).filter(Boolean);
  if (!parts.length) {
    return "--";
  }
  if (parts.length === 1) {
    return parts[0].slice(0, 2).toUpperCase();
  }
  return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
}

function formatSigned(value, digits) {
  const number = Number(value) || 0;
  return `${number >= 0 ? "+" : ""}${number.toFixed(digits)}`;
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
