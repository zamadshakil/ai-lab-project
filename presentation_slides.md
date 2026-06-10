# Specter's Bridge AI Laboratory — Presentation Slides

> **Total Slides**: 18  
> **Estimated Duration**: 8–10 minutes (5 speakers × ~2 min each)  
> **Design Note**: Use a dark theme with purple/teal accent colors. Minimal text per slide — details go in the speaker script.

---

## Slide 1 — Title Slide

**Title**: Specter's Bridge AI Laboratory  
**Subtitle**: Adversarial Decision-Making Under Uncertainty  
**Bottom Line**: Artificial Intelligence — Term Project | June 2026

**Visuals**:
- Dark gradient background (deep purple → black)
- Stylized illustration of a misty bridge with glowing planks
- Team members' names listed at the bottom

---

## Slide 2 — Team Introduction

**Title**: Meet the Team

**Bullets**:
- Member 1 — *Introduction, Problem Statement & PEAS Framework*
- Member 2 — *State Model, Expectiminimax & Star2 Pruning*
- Member 3 — *Q-Learning, Bellman Updates & Convergence*
- Member 4 — *Genetic Algorithm: Evolution of Heuristic Weights*
- Member 5 — *Live Demo, Testing & Conclusion*

**Visuals**:
- Five avatar placeholders in a horizontal row
- Each avatar has the member's name and assigned topic below

---

## Slide 3 — Problem Statement & Game Rules

**Title**: The Haunted Bridge Crossing

**Bullets**:
- Two players cross a bridge of **N = 12** planks
- **MAX (Traveler)**: Wants to reach the end and maximize score
- **MIN (Specter)**: Wants to minimize Traveler's advantage
- **Step 1**: Move 1 plank — 100% deterministic
- **Leap 2**: Move 2 planks — 80% success, 20% slip (move only 1)

**Visuals**:
- Horizontal diagram of a 12-plank bridge
- Color-coded planks: green (normal), gold (treasure +2), red (trap −3), blue (slippery ×2.5 slip chance)
- Two character icons: Traveler on one end, Specter ghost on the other

---

## Slide 4 — PEAS Framework

**Title**: PEAS Analysis

**Bullets**:
- **Performance**: Net score differential (Treasures: +2, Traps: −3, Win Bonus: +10)
- **Environment**: 1D discrete bridge, stochastic, adversarial, turn-based
- **Actuators**: Step 1 (safe) or Leap 2 (risky)
- **Sensors**: State tuple — remaining planks, active turn, scores

**Visuals**:
- Four-quadrant PEAS diagram with icons for each category
- Small game state example: `(12, MAX, 0, 0)`

---

## Slide 5 — State Representation & Transition Model

**Title**: State Space & Transitions

**Bullets**:
- State: `s = (remaining_planks, is_max_turn, max_score, min_score)`
- Step 1: `P(advance 1) = 1.0` — deterministic
- Leap 2: `P(advance 2) = 0.8`, `P(slip to 1) = 0.2`
- Slippery planks amplify base slip probability by **2.5×**
- Terminal condition: `remaining_planks ≤ 0`

**Visuals**:
- State transition diagram showing a sample move from plank 12
- Branching arrows: one solid (Step 1, 100%), one splitting into two dashed arrows (Leap 2: 80%/20%)

---

## Slide 6 — Algorithm 1: Expectiminimax Overview

**Title**: Expectiminimax Search

**Bullets**:
- Extension of Minimax for **stochastic environments**
- Three node types: MAX (↑), MIN (↓), CHANCE (◇)
- MAX selects the action with the **highest** expected utility
- MIN selects the action with the **lowest** expected utility
- CHANCE computes: `E[V] = Σ pᵢ × V(childᵢ)`

**Visuals**:
- Game tree diagram with 3 levels:
  - Top: Square (MAX) node
  - Middle: Diamond (CHANCE) nodes with probability labels
  - Bottom: Circle (MIN) nodes with utility values
- Color-coded: blue for MAX, red for MIN, yellow for CHANCE

---

## Slide 7 — Chance Nodes & Expected Utility

**Title**: How Chance Nodes Work

**Bullets**:
- When a player chooses Leap 2, the environment rolls dice
- Each outcome has a probability weight
- Expected Utility: `E = 0.8 × V(success) + 0.2 × V(slip)`
- Chance nodes sit **between** player decision nodes
- This is what makes it different from standard Minimax

**Visuals**:
- Zoomed-in diagram of a single Chance node
- Two branches: "Success (p=0.8)" leading to one child, "Slip (p=0.2)" leading to another
- Calculated expected value shown at the Chance node

---

## Slide 8 — Star2 Pruning: Why Alpha-Beta Fails

**Title**: Why Can't We Use Alpha-Beta on Chance Nodes?

**Bullets**:
- Alpha-Beta prunes when one branch **guarantees** a result worse than what's already found
- Chance nodes compute **weighted averages** — partial evaluation is meaningless
- A single child's value doesn't tell us the final expected value
- We need **all** children evaluated… unless we can **bound** the result

**Visuals**:
- Side-by-side comparison:
  - Left: Deterministic tree with Alpha-Beta cutoff (crossed-out branch)
  - Right: Stochastic tree with "?" on partial Chance node — "Can't prune yet!"
- Red "✗" over naive Alpha-Beta applied to Chance node

---

## Slide 9 — Star2 Pruning: Bounding Math

**Title**: Star2 Pruning — Mathematical Bounds

**Bullets**:
- Define global bounds: `V_max` (best possible heuristic), `V_min` (worst possible)
- After evaluating `j−1` children with sum `S`, bound the remaining:
  - `S + pⱼ·Vⱼ + P_rem·V_min  ≤  E  ≤  S + pⱼ·Vⱼ + P_rem·V_max`
- Tighten child search window: `αc = max(V_min, (α − S − P_rem·V_max) / pⱼ)`
- **If `αc ≥ βc` → prune immediately!**

**Visuals**:
- Math formulas displayed cleanly (LaTeX-style rendering)
- Bar chart from profiling results:
  - Depth 4: **121 nodes** (no prune) vs. **74 nodes** (Star2) — **38.8% reduction**
  - Show pruned nodes count: 8 branches pruned

---

## Slide 10 — Algorithm 2: Q-Learning Overview

**Title**: Q-Learning — Model-Free Reinforcement Learning

**Bullets**:
- Agent learns **without** a model of the environment
- Learns Q-values: `Q(state, action)` → expected future reward
- Compressed state: `(remaining_planks, is_max_turn)` — only 24 states
- Trains via **self-play**: MAX and MIN both use Q-table
- Epsilon-greedy exploration with decay: `ε *= 0.9995`

**Visuals**:
- Diagram of the RL loop: State → Action → Environment → Reward → State'
- Small Q-table snippet showing sample values for states P12, P11, P10

---

## Slide 11 — Q-Learning: Bellman Update & Self-Play

**Title**: Temporal-Difference Learning

**Bullets**:
- **Bellman Update**: `Q(s,a) ← Q(s,a) + α · (R + γ · Target − Q(s,a))`
- If next turn is MAX: `Target = max Q(s', a')`
- If next turn is MIN: `Target = min Q(s', a')`
- Reward function: `R = Δ(score_diff)` — change in score differential
- Telescoping property guarantees alignment with game outcome

**Visuals**:
- The Bellman equation displayed prominently
- Animated arrow showing TD error: `Target − Q(s,a)` being added back
- Learning rate α and discount factor γ labeled

---

## Slide 12 — Exploratory Starts & Convergence Results

**Title**: Achieving 100% Policy Convergence

**Bullets**:
- **Problem**: Normal game start leaves some states unreachable
- **Solution**: 30% of episodes start from random `(plank, turn)` pairs
- **Result**: Q-learning policy matches Expectiminimax in **100% of states**
- Verified across all 16 state-action pairs (8 planks × 2 turns)

**Visuals**:
- Before/After comparison table:
  - Without Exploratory Starts: ~75% convergence
  - With Exploratory Starts: 100% convergence
- Convergence chart: TD error dropping to near-zero over 15,000 episodes
- Checkmark grid: 16/16 states matching tree search policy

---

## Slide 13 — Algorithm 3: Genetic Algorithm Overview

**Title**: Genetic Algorithm — Evolving Heuristic Weights

**Bullets**:
- **Goal**: Optimize the 4 heuristic weights used by Expectiminimax
- **Chromosome**: `[w_max_score, w_min_score, w_progress, w_trap_risk]`
- **Fitness**: Round-robin tournament — chromosomes play matches against each other
- **Selection**: 2-way Tournament Selection
- **Elitism**: Top 2 chromosomes survive to next generation

**Visuals**:
- Chromosome visualization: 4 colored gene blocks with weight values
- Circular GA lifecycle diagram: Initialize → Evaluate → Select → Crossover → Mutate → Repeat

---

## Slide 14 — GA: Crossover, Mutation & Results

**Title**: Genetic Operators & Evolution Results

**Bullets**:
- **Single-Point Crossover**: Random split index; swap weight segments
- **Gaussian Mutation**: Small random shift (σ = 0.5), rate = 15%
- **Polarity Enforcement**: Positive weights stay ≥ 0.1, negative weights stay ≤ −0.1
- **Default Weights**: `[2.0, −2.0, 1.5, −3.0]`
- Population converges within ~5–8 generations

**Visuals**:
- Crossover diagram: Two parent chromosomes split and recombined
- Mutation diagram: One gene highlighted with a Gaussian shift arrow
- Line chart: Average fitness vs. generation number, showing convergence

---

## Slide 15 — Live Demo / Dashboard Screenshots

**Title**: Interactive Web Dashboard

**Bullets**:
- Built with **FastAPI** backend + modern JavaScript frontend
- Real-time game board with animated plank traversal
- Interactive decision tree visualization (MAX/MIN/CHANCE nodes)
- Q-table heatmap and GA evolution charts
- Deployed on Vercel for live access

**Visuals**:
- Full-screen screenshot of the dashboard
- Annotated callouts pointing to:
  - Game board area
  - Decision tree panel
  - Q-learning training curve
  - GA weight evolution tracker

---

## Slide 16 — Testing & Verification Results

**Title**: Testing & Correctness Verification

**Bullets**:
- **Star2 Pruning**: Verified identical optimal moves with and without pruning at all depths
- **Profiling**: Depth-4 search — 121 → 74 nodes (38.8% fewer evaluations)
- **Q-Learning Convergence**: 16/16 state policies match tree search (100%)
- **GA Polarity**: All evolved weights maintain correct sign constraints
- **API Endpoints**: All 5 routes tested with valid & edge-case inputs

**Visuals**:
- Results table:

| Metric | Without Pruning | With Star2 | Improvement |
|--------|----------------|------------|-------------|
| Depth 2 | 13 nodes | 12 nodes | 7.7% |
| Depth 3 | 40 nodes | 29 nodes | 27.5% |
| Depth 4 | 121 nodes | 74 nodes | 38.8% |

- Green checkmark badges next to each test category

---

## Slide 17 — Conclusion & Key Takeaways

**Title**: Key Takeaways

**Bullets**:
- Expectiminimax extends Minimax to handle **stochastic environments**
- Star2 Pruning enables efficient search through **mathematical bounding**
- Q-Learning achieves **identical optimal policies** without a game tree
- Genetic Algorithms can **auto-tune** heuristic parameters via evolution
- All three algorithms converge to the **same strategic decisions**

**Visuals**:
- Three algorithm icons side-by-side with convergence arrows pointing to a central "Optimal Policy" badge
- Summary infographic with key numbers: 12 planks, 3 algorithms, 100% convergence, ~39% pruning

---

## Slide 18 — Q&A / Thank You

**Title**: Thank You — Questions?

**Bullets**:
- "We're happy to answer your questions"
- GitHub Repository link
- Live Dashboard link
- Team contact information

**Visuals**:
- Clean "Thank You" typography with subtle gradient animation
- QR code linking to the live dashboard
- Team members' names listed at the bottom

---

> **End of Slide Deck**
