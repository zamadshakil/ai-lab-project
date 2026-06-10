# Viva Presentation & Concept Guide: Specter's Bridge AI Laboratory

Welcome to the ultimate preparation guide for your Term Project Viva. This guide breaks down the core concepts, formulations, algorithms, and key Q&A topics of **Specter's Bridge** in a simple, intuitive, yet mathematically precise manner.

---

## 1. Project Overview & PEAS Framework

Specter's Bridge is a zero-sum, stochastic, adversarial game played on a 1D hazard board (a bridge of planks). 

### PEAS Description
*   **Performance Measure**: Maximize Traveler's net score (Traps: $-3$, Treasures: $+2$, Win Bonus: $+10$) vs. Specter trying to minimize it.
*   **Environment**: 1D bridge, discrete planks, stochastic transition (slips on Leap 2), containing treasures, traps, and slippery planks.
*   **Actuators**: Step 1 (deterministic) or Leap 2 (stochastic, prone to slip).
*   **Sensors**: State representation (remaining planks, active player turn, current score differential).

---

## 2. Core Game Formulation (Game Theory & MDP)

The game is modeled as a zero-sum, turn-based stochastic game between two players: **MAX (Traveler)** and **MIN (Specter)**.

### State Representation
A state $s$ is defined as a tuple:
$$s = (\text{remaining\_planks}, \text{is\_max\_turn}, \text{max\_score}, \text{min\_score})$$
*   To keep reinforcement learning compact and state visitation high, the RL agent uses a compressed representation: $s_{RL} = (\text{remaining\_planks}, \text{is\_max\_turn})$.

### Transition Model & Stochastics
*   **Step 1**: Moving 1 plank is $100\%$ deterministic.
    $$P(s_{t+1} = \text{Transition}(s_t, 1, 1) \mid s_t, \text{action}=1) = 1.0$$
*   **Leap 2**: Moving 2 planks is stochastic:
    *   With probability $1 - p_{slip}$, the leap succeeds (player advances 2 planks).
    *   With probability $p_{slip}$, the player slips (player advances only 1 plank).
    *   Slippery planks scale the base slip probability $p$ by $2.5\times$ (capped at $1.0$).

---

## 3. Expectiminimax Search & Star2 Pruning

When it is a player's turn, we use **Expectiminimax Search** to plan ahead by constructing a game tree containing three types of nodes:
1.  **MAX Nodes (Square)**: Traveler chooses the action that yields the highest expected value.
2.  **MIN Nodes (Circle)**: Specter chooses the action that yields the lowest expected value.
3.  **Chance Nodes (Diamond)**: Represents the environment's random nature, computing the expected utility as the weighted sum of child outcomes.

```
       [ MAX Node ]  <-- Choose Max
        /        \
   (Move 1)     (Move 2)
      /            \
 { Chance }     { Chance }  <-- Calculate Expected Value (Probability * Child Value)
    |             /      \
  [ MIN ]     [ MIN ]  [ MIN ]  <-- Choose Min
```

### What is Star2 Pruning?
Standard Alpha-Beta pruning cannot be directly applied to Chance nodes because we don't know the exact value of a branch until we evaluate all its random outcomes. 

**Star2 Pruning** solves this by establishing global bounds on the heuristic evaluation:
*   $V_{max}$: The maximum possible heuristic value a state can have.
*   $V_{min}$: The minimum possible heuristic value a state can have.

If we are at a Chance node and have already evaluated $j-1$ outcomes with sum $S_{j-1} = \sum_{i=1}^{j-1} p_i V_i$, the final expected value $E$ is mathematically bounded by:
$$S_{j-1} + p_j V_j + (1 - \sum_{i=1}^j p_i) V_{min} \le E \le S_{j-1} + p_j V_j + (1 - \sum_{i=1}^j p_i) V_{max}$$

#### Dynamic Window Bounding (Symmetric Tightening)
To prune the remaining branches, we update the search windows ($\alpha_c, \beta_c$) passed down to the $j$-th child node:
*   **For MAX parent (Chance node children are MIN nodes)**:
    $$\alpha_c = \max\left(V_{min}, \frac{\alpha - S_{j-1} - P_{rem} V_{max}}{p_j}\right)$$
    $$\beta_c = \min\left(V_{max}, \frac{\beta - S_{j-1} - P_{rem} V_{min}}{p_j}\right)$$
*   **For MIN parent (Chance node children are MAX nodes)**:
    $$\alpha_c = \max\left(V_{min}, \frac{\alpha - S_{j-1} - P_{rem} V_{max}}{p_j}\right)$$
    $$\beta_c = \min\left(V_{max}, \frac{\beta - S_{j-1} - P_{rem} V_{min}}{p_j}\right)$$

If at any point $\alpha_c \ge \beta_c$, the search window collapses and we **prune the remaining outcomes immediately**, avoiding expensive evaluations.

---

## 4. Reinforcement Learning: Tabular Q-Learning

To solve the game without looking ahead in a tree, we use **Model-Free Q-Learning**. The agent learns the quality of actions ($Q$-values) through self-play.

### Bellman Update Equation
When the agent takes action $a$ in state $s$, transitions to $s'$, and receives reward $R$, the $Q$-value is updated via Temporal Difference (TD) learning:
$$Q(s, a) \leftarrow Q(s, a) + \alpha \left( R + \gamma \cdot \text{Target} - Q(s, a) \right)$$
where:
*   $\alpha$ is the learning rate (how fast we update our estimates).
*   $\gamma$ is the discount factor (importance of future rewards).
*   $\text{Target}$ is determined by who plays next:
    *   If $s'$ is MAX's turn: $\text{Target} = \max_{a'} Q(s', a')$
    *   If $s'$ is MIN's turn: $\text{Target} = \min_{a'} Q(s', a')$ (minimizing MAX's utility).

### Policy Convergence (Exploratory Starts)
Since players play optimally, starting training episodes from a fixed position leaves certain states unreachable, resulting in untrained Q-values. To achieve **100% policy convergence**, we use **Exploratory Starts**:
*   $30\%$ of training cycles start from a random legal plank index and random active player turn. This ensures that every state-action pair is visited and learned.

---

## 5. Evolutionary Search: Genetic Algorithms

To optimize the evaluation weights $W = [w_0, w_1, w_2, w_3]$ used by the Expectiminimax heuristic, we use a **Genetic Algorithm (GA)**.

1.  **Chromosome**: A list of 4 float weights representing `[max_score, min_score, progress, trap_risk]`.
2.  **Fitness Evaluation**: Round-Robin tournament. Chromosomes play matches against all other members in the population. A win grants $+1$ fitness.
3.  **Selection**: Tournament selection. Two chromosomes are chosen at random, and the one with higher fitness is selected as a parent.
4.  **Crossover**: Single-Point Crossover. A random index is chosen to split the parents' weights, and the segments are swapped to create a child.
5.  **Mutation**: Gaussian shift is added to random genes. Polarity constraints are strictly enforced (e.g., $w_{trap}$ must remain negative, $w_{progress}$ must remain positive).

---

## 6. Viva Q&A (Standard Examiner Questions)

### Q1: Why does Expectiminimax use Chance Nodes?
**Answer**: Because the environment is stochastic (Leap 2 can slip). Unlike Minimax which assumes deterministic turns, Expectiminimax takes the probability-weighted average of all outcomes at a chance node to compute the *expected utility* of a move.

### Q2: What is the difference between Alpha-Beta pruning and Star2 pruning?
**Answer**: Alpha-Beta pruning works on deterministic nodes (MAX/MIN) by cutting branches that cannot affect the final minimax decision. Star2 pruning works on stochastic nodes (Chance) by using mathematical bounds ($V_{max}, V_{min}$) to compute if the expected value of a random event cannot possibly fall within the active search window ($\alpha, \beta$).

### Q3: Why did policy alignment fail to reach 100% convergence initially, and how did you fix it?
**Answer**: It failed because of unreachable states. In a normal game starting from the beginning, some state configurations (e.g., MAX's turn with 7 planks left) are mathematically impossible to reach. Since Q-learning only updates states it visits, these states remained untrained (Q-value = 0). We fixed this by introducing **Exploratory Starts** ($30\%$ of episodes start from random states), which ensures the entire state space is fully trained, achieving exactly $100\%$ policy convergence.

### Q4: How does the Q-learning reward function align with the game's objectives?
**Answer**: We define the step reward $R_t$ as the change in the score differential:
$$R_t = \Delta \text{Score} = (Score_{max, t+1} - Score_{min, t+1}) - (Score_{max, t} - Score_{min, t})$$
Because the sum of step rewards along a game path telescopes, it is mathematically guaranteed to equal the final game score differential, perfectly aligning the reinforcement learning agent's objective with the game's ultimate goal.

### Q5: How do you prevent Genetic Algorithm chromosomes from evolving nonsense weights (like positive weights for traps)?
**Answer**: We enforce strict polarity constraints during the mutation phase. Positive genes (Traveler's score, Progress) are clamped to be $\ge 0.1$, and negative genes (Traps, risk) are clamped to be $\le -0.1$.
