// Global Game & Simulator State
let gameState = [12, true, 0, 0]; // [remaining, is_max_turn, max_score, min_score]
let boardConfig = []; // Array of plank types
let slipProb = 0.2;
let playMode = "normal";
let evolvedWeights = [2.0, -3.0, 1.5, -2.0];

// Chart.js Instances
let qChartInstance = null;
let gaChartInstance = null;

// DOM Elements
const canvas = document.getElementById("arenaCanvas");
const ctx = canvas.getContext("2d");
const logBox = document.getElementById("game-log");

// Initialize
document.addEventListener("DOMContentLoaded", () => {
    setupEventListeners();
    resetGameInBackend();
    initCharts();
});

function setupEventListeners() {
    // Arena Controls
    document.getElementById("btn-step1").addEventListener("click", () => takeMove(1));
    document.getElementById("btn-leap2").addEventListener("click", () => takeMove(2));
    document.getElementById("btn-ai-play").addEventListener("click", playAiTurn);
    
    // Config Updates
    document.getElementById("btn-reconfigure").addEventListener("click", resetGameInBackend);
    
    // Prune/Depth Updates
    document.getElementById("check-prune").addEventListener("change", updateTreeVisualizer);
    document.getElementById("range-depth").addEventListener("input", (e) => {
        document.getElementById("depth-label").innerText = e.target.value;
        updateTreeVisualizer();
    });
    
    // Trainer Buttons
    document.getElementById("btn-train-q").addEventListener("click", trainQLearning);
    document.getElementById("btn-ga-1").addEventListener("click", () => evolveGA(1));
    document.getElementById("btn-ga-10").addEventListener("click", () => evolveGA(10));
    document.getElementById("btn-ga-reset").addEventListener("click", resetGA);
    document.getElementById("btn-apply-weights").addEventListener("click", applyEvolvedWeights);
    
    // Agent Selection Updates UI
    document.getElementById("agentSelect").addEventListener("change", (e) => {
        const isPlayer = (e.target.value === "player");
        document.getElementById("btn-step1").disabled = !isPlayer;
        document.getElementById("btn-leap2").disabled = !isPlayer;
        document.getElementById("btn-ai-play").disabled = isPlayer;
        
        // Disable player step/leap buttons if move 2 is illegal (e.g. only 1 plank left)
        if (isPlayer) {
            updatePlayerButtonsState();
        }
    });
}

function updatePlayerButtonsState() {
    const remaining = gameState[0];
    document.getElementById("btn-step1").disabled = (remaining <= 0);
    document.getElementById("btn-leap2").disabled = (remaining <= 1);
}

// ----------------- ENVIRONMENT BACKEND SYNC -----------------

async function resetGameInBackend() {
    const n = parseInt(document.getElementById("setup-n").value);
    slipProb = parseFloat(document.getElementById("setup-p").value);
    playMode = document.getElementById("setup-mode").value;
    
    // Display updates in UI config bar
    document.getElementById("val-config-n").innerText = n;
    document.getElementById("val-config-p").innerText = slipProb.toFixed(2);
    document.getElementById("val-config-mode").innerText = playMode === "normal" ? "Normal Play" : "Misere Play";

    try {
        const res = await fetch("/api/game/reset", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                n_planks: n,
                slip_prob: slipProb,
                play_mode: playMode
            })
        });
        const data = await res.json();
        
        gameState = data.state;
        boardConfig = data.plank_types;
        
        clearLog();
        addLog("system", `System reconfigured. Bridge length: ${n} planks. Play mode: ${playMode.toUpperCase()}.`);
        updateScoreboard();
        drawArena();
        updateTreeVisualizer();
        
        // Reset player buttons state
        const agent = document.getElementById("agentSelect").value;
        if (agent === "player") {
            updatePlayerButtonsState();
        }
    } catch (err) {
        console.error("Error resetting game:", err);
    }
}

async function takeMove(intendedMove) {
    const agent = document.getElementById("agentSelect").value;
    try {
        const res = await fetch("/api/game/step", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                agent_type: agent,
                intended_move: intendedMove,
                state: gameState,
                weights: evolvedWeights
            })
        });
        
        if (res.status === 400) {
            const errData = await res.json();
            addLog("system", `Move rejected: ${errData.detail}`);
            return;
        }
        
        const data = await res.json();
        const prevRemaining = gameState[0];
        const prevPlayerName = gameState[1] ? "MAX" : "MIN";
        
        gameState = data.next_state;
        
        // Write to chronicles
        let logClass = prevPlayerName.toLowerCase();
        let logMsg = `${prevPlayerName} chose `;
        if (data.intended_move === 1) {
            logMsg += `Step 1. Safely advanced 1 plank.`;
        } else {
            logMsg += `Leap 2. `;
            if (data.is_slip) {
                logMsg += `SLIPPED! Handled hazard, advanced only 1 plank.`;
            } else {
                logMsg += `Success! Sprang forward 2 planks.`;
            }
        }
        
        // Check landing type
        const landedIdx = boardConfig.length - 1 - gameState[0];
        if (landedIdx >= 0 && landedIdx < boardConfig.length) {
            const type = boardConfig[landedIdx];
            if (type === "treasure") {
                logMsg += ` Collected treasure (+2).`;
            } else if (type === "trap") {
                logMsg += ` Slipped into void trap (-3).`;
            }
        }
        
        addLog(logClass, logMsg);
        
        // Terminal Win/Loss log
        if (data.is_terminal) {
            const winText = (gameState[2] > gameState[3]) ? "MAX (Traveler) Wins!" : 
                            (gameState[3] > gameState[2]) ? "MIN (Specter) Wins!" : "Exact Draw!";
            addLog("system", `Game Over! Final Scores: MAX: ${gameState[2]} | MIN: ${gameState[3]}. ${winText}`);
        }
        
        updateScoreboard();
        animateStep(prevRemaining, gameState[0], data.is_slip);
        updateTreeVisualizer();
        
        if (agent === "player") {
            updatePlayerButtonsState();
        }
    } catch (err) {
        console.error("Step execution error:", err);
    }
}

async function playAiTurn() {
    // Disable step buttons during active turn
    document.getElementById("btn-ai-play").disabled = true;
    await takeMove(null);
    document.getElementById("btn-ai-play").disabled = false;
}

// ----------------- SCOREBOARD & CHRONICLE LOGS -----------------

function updateScoreboard() {
    document.getElementById("score-max").innerText = gameState[2];
    document.getElementById("score-min").innerText = gameState[3];
    
    const turnText = gameState[1] ? "MAX" : "MIN";
    const turnBox = document.getElementById("active-player");
    turnBox.innerText = turnText;
    
    if (gameState[1]) {
        turnBox.className = "score-value text-green";
    } else {
        turnBox.className = "score-value text-red";
    }
    
    if (gameState[0] <= 0) {
        turnBox.innerText = "OVER";
        turnBox.className = "score-value text-muted";
    }
}

function addLog(className, text) {
    const entry = document.createElement("div");
    entry.className = `log-entry ${className}`;
    entry.innerText = text;
    logBox.appendChild(entry);
    logBox.scrollTop = logBox.scrollHeight;
}

function clearLog() {
    logBox.innerHTML = "";
}

// ----------------- HTML5 CANVAS BRIDGE RENDERING -----------------

let animTarget = null;
let animCurrent = null;

function drawArena() {
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    
    // Draw clean background
    ctx.fillStyle = "#fafafa";
    ctx.fillRect(0, 0, w, h);
    
    // Draw mist particles (subtle accent glow)
    ctx.fillStyle = "rgba(0, 113, 227, 0.02)";
    ctx.beginPath();
    ctx.arc(w/2, h + 50, 150, 0, Math.PI * 2);
    ctx.fill();

    // Plank spacing calculations
    const n = boardConfig.length - 1; // Number of planks excluding starting area
    const total_segments = n + 2; // starting area (0), planks (1..n), target end area
    const seg_width = w / total_segments;
    const plank_y = h / 2 + 10;
    
    // 1. Draw Starting Area
    drawPlankArea(0, plank_y, seg_width - 8, 20, "start");
    
    // 2. Draw Planks
    for (let i = 1; i <= n; i++) {
        const type = boardConfig[i];
        drawPlankArea(i * seg_width, plank_y, seg_width - 8, 14, type, i);
    }
    
    // 3. Draw Finish area
    drawPlankArea((n + 1) * seg_width, plank_y, seg_width - 8, 20, "end");
    
    // Draw Bridge ropes
    ctx.strokeStyle = "rgba(139, 90, 43, 0.4)";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(10, plank_y - 12);
    ctx.lineTo(w - 10, plank_y - 12);
    ctx.stroke();
    
    // 4. Draw Player / Traveler
    let playerPlankIdx = n - (animCurrent !== null ? animCurrent : gameState[0]);
    // Clip index
    if (playerPlankIdx < 0) playerPlankIdx = 0;
    if (playerPlankIdx > n + 1) playerPlankIdx = n + 1;
    
    const p_x = playerPlankIdx * seg_width + (seg_width - 8) / 2;
    const p_y = plank_y - 25;
    
    drawTraveler(p_x, p_y);
}

function drawPlankArea(x, y, width, height, type, idx) {
    ctx.save();
    
    // Design matching colors
    let strokeColor = "#d2d2d7";
    let fillColor = "#ffffff";
    
    if (type === "start") {
        fillColor = "#e5e5e7";
        strokeColor = "#86868b";
    } else if (type === "end") {
        fillColor = "#e2f6e9";
        strokeColor = "#34c759";
    } else if (type === "treasure") {
        fillColor = "#e2f6e9";
        strokeColor = "#34c759";
    } else if (type === "trap") {
        fillColor = "#fce8e6";
        strokeColor = "#ff3b30";
    } else if (type === "slippery") {
        fillColor = "#e8f2fc";
        strokeColor = "#0071e3";
    }
    
    // Draw wood block
    ctx.fillStyle = fillColor;
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.roundRect(x, y, width, height, 4);
    ctx.fill();
    ctx.stroke();
    
    // Write index number for planks
    if (idx !== undefined) {
        ctx.fillStyle = "rgba(0, 0, 0, 0.4)";
        ctx.shadowBlur = 0;
        ctx.font = "bold 9px monospace";
        ctx.textAlign = "center";
        ctx.fillText(idx, x + width/2, y + height + 10);
    }
    
    ctx.restore();
}

function drawTraveler(x, y) {
    ctx.save();
    
    // Glow shadow
    ctx.shadowBlur = 8;
    ctx.shadowColor = gameState[1] ? "rgba(52, 199, 89, 0.4)" : "rgba(255, 59, 48, 0.4)";
    
    // Glowing active core
    ctx.fillStyle = gameState[1] ? "var(--color-green)" : "var(--color-red)";
    ctx.beginPath();
    ctx.arc(x, y, 10, 0, Math.PI * 2);
    ctx.fill();
    
    // Outer floating ring
    ctx.strokeStyle = "rgba(0, 0, 0, 0.15)";
    ctx.lineWidth = 1.5;
    ctx.shadowBlur = 0;
    ctx.beginPath();
    ctx.arc(x, y, 14, 0, Math.PI * 2);
    ctx.stroke();
    
    // Draw simple traveler eyes to make it look like a character
    ctx.fillStyle = "white";
    ctx.beginPath();
    ctx.arc(x - 3, y - 2, 2, 0, Math.PI*2);
    ctx.arc(x + 3, y - 2, 2, 0, Math.PI*2);
    ctx.fill();
    
    ctx.restore();
}

function animateStep(startRemaining, endRemaining, isSlip) {
    animTarget = endRemaining;
    animCurrent = startRemaining;
    
    let diff = endRemaining - startRemaining;
    let stepCount = 20;
    let currentStep = 0;
    
    function step() {
        if (currentStep >= stepCount) {
            animCurrent = endRemaining;
            animTarget = null;
            drawArena();
            return;
        }
        currentStep++;
        animCurrent = startRemaining + (diff * (currentStep / stepCount));
        drawArena();
        
        // Draw float "SLIP!" indicator
        if (isSlip && currentStep < stepCount / 2) {
            ctx.fillStyle = "var(--color-red)";
            ctx.font = "bold 12px sans-serif";
            ctx.textAlign = "center";
            ctx.fillText("SLIP!", canvas.width / 2, 40);
        }
        
        requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}

// ----------------- STAR2 EXPECTIMINIMAX SEARCH TREE VISUALIZATION -----------------

async function updateTreeVisualizer() {
    const depth = parseInt(document.getElementById("range-depth").value);
    const prune = document.getElementById("check-prune").checked;
    
    try {
        const res = await fetch("/api/engine/tree", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                state: gameState,
                max_depth: depth,
                prune: prune,
                weights: evolvedWeights
            })
        });
        const data = await res.json();
        
        // Update stats row
        document.getElementById("tree-states-checked").innerText = data.stats.evaluated;
        document.getElementById("tree-branches-cut").innerText = data.stats.pruned;
        document.getElementById("tree-root-value").innerText = data.value.toFixed(2);
        
        renderTreeSvg(data.tree, data.best_move);
    } catch (err) {
        console.error("Error retrieving search tree:", err);
    }
}

function renderTreeSvg(rootNode, bestMove) {
    const svg = document.getElementById("treeSvg");
    svg.innerHTML = ""; // Clear SVG
    
    // Calculate dynamic layout sizes based on tree width (weight) and depth
    calculateSubtreeWidths(rootNode);
    
    const leafCount = rootNode.weight || 1;
    const depth = rootNode.max_depth || 3;
    
    // Space leaves by 65px horizontally for readable layouts, minimum 600px
    const dynamicWidth = Math.max(600, leafCount * 65);
    // Space depth levels by 85px vertically, minimum 340px
    const dynamicHeight = Math.max(340, depth * 85);
    
    svg.setAttribute("width", dynamicWidth);
    svg.setAttribute("height", dynamicHeight);
    
    const margin = { top: 30, right: 30, bottom: 40, left: 30 };
    
    // Position nodes recursively inside dynamic canvas
    // Using (depth - 1) levels of vertical spacing to stretch nodes to the bottom
    positionTreeNodes(rootNode, margin.left, dynamicWidth - margin.right, margin.top, (dynamicHeight - margin.top - margin.bottom) / Math.max(1, depth - 1));
    
    // 3. Draw links and nodes
    drawLinksAndNodes(svg, rootNode, bestMove);
}

function calculateSubtreeWidths(node) {
    if (!node.children || node.children.length === 0) {
        node.weight = 1;
        node.max_depth = 1;
        return;
    }
    
    let sum = 0;
    let maxChildDepth = 0;
    node.children.forEach(c => {
        calculateSubtreeWidths(c);
        sum += c.weight;
        if (c.max_depth > maxChildDepth) {
            maxChildDepth = c.max_depth;
        }
    });
    node.weight = sum;
    node.max_depth = maxChildDepth + 1;
}

function positionTreeNodes(node, xLeft, xRight, y, levelHeight) {
    node.x = (xLeft + xRight) / 2;
    node.y = y;
    
    if (!node.children || node.children.length === 0) return;
    
    const totalWeight = node.weight;
    let currentLeft = xLeft;
    node.children.forEach(c => {
        let childPercent = c.weight / totalWeight;
        let childRight = currentLeft + (xRight - xLeft) * childPercent;
        positionTreeNodes(c, currentLeft, childRight, y + levelHeight, levelHeight);
        currentLeft = childRight;
    });
}

function drawLinksAndNodes(svg, node, bestMove) {
    // Collect all links and nodes
    const links = [];
    const nodes = [];
    
    function traverse(n) {
        nodes.push(n);
        if (!n.children) return;
        n.children.forEach(c => {
            links.push({ parent: n, child: c });
            traverse(c);
        });
    }
    traverse(node);
    
    // 1. Draw Links
    links.forEach(l => {
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("x1", l.parent.x);
        line.setAttribute("y1", l.parent.y);
        line.setAttribute("x2", l.child.x);
        line.setAttribute("y2", l.child.y);
        
        // Highlight best move branch glow
        const isBestBranch = (l.parent.type === "MAX" || l.parent.type === "MIN") && 
                             l.child.type === "CHANCE" && 
                             l.child.name.endsWith(`M${l.parent.best_move}`);
                             
        line.setAttribute("class", isBestBranch ? "link best-branch" : "link");
        svg.appendChild(line);
        
        // Draw Probability text on link
        if (l.child.probability !== undefined && l.child.probability !== null) {
            const probText = document.createElementNS("http://www.w3.org/2000/svg", "text");
            probText.setAttribute("x", (l.parent.x + l.child.x) / 2 + 5);
            probText.setAttribute("y", (l.parent.y + l.child.y) / 2 - 5);
            probText.setAttribute("class", "node-prob");
            probText.textContent = `p=${l.child.probability.toFixed(1)}`;
            svg.appendChild(probText);
        }
    });
    
    // 2. Draw Nodes
    nodes.forEach(n => {
        const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
        group.setAttribute("class", "node-group");
        
        let color = "grey";
        let shape = "circle"; // circle, rect, diamond
        
        if (n.type === "MAX") {
            color = "var(--color-green)";
            shape = "rect";
        } else if (n.type === "MIN") {
            color = "var(--color-red)";
            shape = "circle";
        } else if (n.type === "CHANCE") {
            color = "var(--color-blue)";
            shape = "diamond";
        } else if (n.type === "PRUNED") {
            color = "var(--color-text-muted)";
            shape = "circle-dashed";
        } else if (n.type === "TERMINAL" || n.type === "LEAF") {
            color = "#86868b";
            shape = "rect-round";
        }
        
        // Render node shape
        if (shape === "rect") {
            const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            rect.setAttribute("x", n.x - 10);
            rect.setAttribute("y", n.y - 10);
            rect.setAttribute("width", 20);
            rect.setAttribute("height", 20);
            rect.setAttribute("rx", 3);
            rect.setAttribute("fill", "#ffffff");
            rect.setAttribute("stroke", color);
            rect.setAttribute("stroke-width", "2");
            group.appendChild(rect);
        } else if (shape === "rect-round") {
            const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            rect.setAttribute("x", n.x - 14);
            rect.setAttribute("y", n.y - 8);
            rect.setAttribute("width", 28);
            rect.setAttribute("height", 16);
            rect.setAttribute("rx", 8);
            rect.setAttribute("fill", "#f5f5f7");
            rect.setAttribute("stroke", color);
            rect.setAttribute("stroke-width", "1.5");
            group.appendChild(rect);
        } else if (shape === "diamond") {
            const polygon = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
            // Coordinate diamonds
            polygon.setAttribute("points", `${n.x},${n.y-12} ${n.x+12},${n.y} ${n.x},${n.y+12} ${n.x-12},${n.y}`);
            polygon.setAttribute("fill", "#ffffff");
            polygon.setAttribute("stroke", color);
            polygon.setAttribute("stroke-width", "2");
            group.appendChild(polygon);
        } else if (shape === "circle-dashed") {
            const circ = document.createElementNS("http://www.w3.org/2000/svg", "circle");
            circ.setAttribute("cx", n.x);
            circ.setAttribute("cy", n.y);
            circ.setAttribute("r", 9);
            circ.setAttribute("fill", "#f5f5f7");
            circ.setAttribute("stroke", "var(--color-red)");
            circ.setAttribute("stroke-width", "1.5");
            circ.setAttribute("stroke-dasharray", "3,3");
            group.appendChild(circ);
        } else {
            // standard circle
            const circ = document.createElementNS("http://www.w3.org/2000/svg", "circle");
            circ.setAttribute("cx", n.x);
            circ.setAttribute("cy", n.y);
            circ.setAttribute("r", 9);
            circ.setAttribute("fill", "#ffffff");
            circ.setAttribute("stroke", color);
            circ.setAttribute("stroke-width", "2");
            group.appendChild(circ);
        }
        
        // 1. Draw Name (above the node)
        const labelName = document.createElementNS("http://www.w3.org/2000/svg", "text");
        labelName.setAttribute("x", n.x);
        labelName.setAttribute("y", n.y - (n.type === "CHANCE" ? 16 : 14));
        labelName.setAttribute("class", "node-text node-name");
        labelName.setAttribute("text-anchor", "middle");
        
        let nameContent = n.name;
        if (n.type === "CHANCE") {
            nameContent = n.name.replace("Chance_M", "M");
        } else if (n.type === "PRUNED") {
            nameContent = "∅";
        }
        labelName.textContent = nameContent;
        group.appendChild(labelName);
        
        // 2. Draw Value (below the node, if available)
        if (n.value !== null && n.value !== undefined) {
            const labelVal = document.createElementNS("http://www.w3.org/2000/svg", "text");
            labelVal.setAttribute("x", n.x);
            labelVal.setAttribute("y", n.y + (shape.startsWith("rect") || shape === "diamond" ? 22 : 18));
            labelVal.setAttribute("class", "node-text node-val");
            labelVal.setAttribute("text-anchor", "middle");
            labelVal.textContent = n.value;
            group.appendChild(labelVal);
        }
        
        svg.appendChild(group);
    });
}

// ----------------- TABS UTILITY -----------------

function switchTab(tabId) {
    // Hide all tab contents
    document.querySelectorAll(".tab-content").forEach(el => el.classList.remove("active"));
    // Deactivate all tab buttons
    document.querySelectorAll(".tab-btn").forEach(el => {
        el.classList.remove("active");
        el.setAttribute("aria-selected", "false");
    });
    
    // Show active tab content
    document.getElementById(tabId).classList.add("active");
    // Find active tab button and activate it
    const activeBtn = Array.from(document.querySelectorAll(".tab-btn")).find(btn => 
        btn.getAttribute("onclick").includes(tabId)
    );
    if (activeBtn) {
        activeBtn.classList.add("active");
        activeBtn.setAttribute("aria-selected", "true");
    }
}

// ----------------- CHART INITIALIZATION -----------------

function initCharts() {
    const qCtx = document.getElementById("qChart").getContext("2d");
    qChartInstance = new Chart(qCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Mean TD Temporal Error',
                data: [],
                borderColor: '#0071e3',
                backgroundColor: 'rgba(0, 113, 227, 0.05)',
                borderWidth: 2,
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { grid: { color: '#e5e5e7' }, ticks: { color: '#86868b' } },
                y: { grid: { color: '#e5e5e7' }, ticks: { color: '#86868b' } }
            },
            plugins: { legend: { display: false } }
        }
    });

    const gaCtx = document.getElementById("gaChart").getContext("2d");
    gaChartInstance = new Chart(gaCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Best Champion Fitness',
                    data: [],
                    borderColor: '#34c759',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.2
                },
                {
                    label: 'Average Fitness',
                    data: [],
                    borderColor: '#ff9500',
                    borderWidth: 1.5,
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0.2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { grid: { color: '#e5e5e7' }, ticks: { color: '#86868b' } },
                y: { grid: { color: '#e5e5e7' }, ticks: { color: '#86868b' } }
            },
            plugins: { legend: { labels: { color: '#1d1d1f' } } }
        }
    });
}

// ----------------- MACHINE LEARNING (Q-LEARNING) LABS -----------------

async function trainQLearning() {
    const episodes = parseInt(document.getElementById("train-episodes").value);
    const statusBox = document.getElementById("q-status");
    
    statusBox.innerText = `Training in self-play mode... (Cycles: ${episodes})`;
    statusBox.className = "train-status text-orange";
    
    try {
        const res = await fetch("/api/engine/train", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                episodes: episodes,
                n_planks: boardConfig.length - 1,
                slip_prob: slipProb,
                play_mode: playMode
            })
        });
        const data = await res.json();
        
        // Update Chart
        const labels = data.history.map(h => h.episode);
        const tdErrors = data.history.map(h => h.avg_td_error);
        
        qChartInstance.data.labels = labels;
        qChartInstance.data.datasets[0].data = tdErrors;
        qChartInstance.update();
        
        statusBox.innerText = `Agent trained! Q-table populated with ${Object.keys(data.q_table).length} states. Epsilon decayed.`;
        statusBox.className = "train-status text-green";
        
        addLog("system", `Q-Learning model finished training over ${episodes} iterations. Epsilon decayed to 0.01.`);
    } catch (err) {
        console.error("Error training Q-learning:", err);
        statusBox.innerText = "Training failed. Check server logs.";
        statusBox.className = "train-status text-red";
    }
}

// ----------------- GENETIC ALGORITHM WEIGHT OPTIMIZATION LABS -----------------

async function evolveGA(generations) {
    let count = 0;
    
    async function runGeneration() {
        if (count >= generations) {
            updateTreeVisualizer();
            return;
        }
        
        try {
            const res = await fetch("/api/engine/evolve", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    pop_size: 10,
                    mutation_rate: 0.15,
                    reset: false
                })
            });
            const data = await res.json();
            
            // Append metrics to Chart
            gaChartInstance.data.labels.push(data.generation);
            gaChartInstance.data.datasets[0].data.push(data.best_fitness);
            gaChartInstance.data.datasets[1].data.push(data.avg_fitness);
            gaChartInstance.update();
            
            // Display best weights chromosome in UI
            document.getElementById("wt-gold").innerText = data.best_weights[0].toFixed(2);
            document.getElementById("wt-trap").innerText = data.best_weights[1].toFixed(2);
            document.getElementById("wt-prog").innerText = data.best_weights[2].toFixed(2);
            document.getElementById("wt-risk").innerText = data.best_weights[3].toFixed(2);
            
            // Store evolved weights temporarily
            evolvedWeights = data.best_weights;
            
            count++;
            runGeneration();
        } catch (err) {
            console.error("GA evolution error:", err);
        }
    }
    
    runGeneration();
}

async function resetGA() {
    try {
        await fetch("/api/engine/evolve", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                pop_size: 10,
                mutation_rate: 0.15,
                reset: true
            })
        });
        
        // Reset Charts
        gaChartInstance.data.labels = [];
        gaChartInstance.data.datasets[0].data = [];
        gaChartInstance.data.datasets[1].data = [];
        gaChartInstance.update();
        
        addLog("system", "Genetic Algorithm population reset. Random weight chromosomes initialized.");
    } catch (err) {
        console.error("Error resetting GA:", err);
    }
}

function applyEvolvedWeights() {
    addLog("system", `Applied evolved heuristic weights to the active Adversarial Solver: [Gold: ${evolvedWeights[0].toFixed(2)}, Trap: ${evolvedWeights[1].toFixed(2)}, Progress: ${evolvedWeights[2].toFixed(2)}, Risk: ${evolvedWeights[3].toFixed(2)}]`);
    updateTreeVisualizer();
}
