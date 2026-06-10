# Specter's Bridge AI Laboratory — Speaker Scripts

> **5 Team Members | 18 Slides | ~2 minutes per speaker**  
> Each script is written word-for-word. Read naturally — don't rush. Pause at commas and between slides.  
> Transition phrases are included at the end of each member's section.

---

## 🎤 Member 1 — Introduction, Problem & PEAS

**Slides**: 1 → 4  
**Estimated Time**: ~2 minutes

---

### Slide 1 — Title Slide

> Good morning/afternoon, everyone. Our project is called **Specter's Bridge AI Laboratory**. It's a stochastic adversarial game — think of it as a haunted bridge where two players compete to cross safely. We've implemented three different AI algorithms to solve this game and built an interactive web dashboard to visualize everything in real time. Let me start by introducing our team.

### Slide 2 — Team Introduction

> Our team has five members. I'll be covering the introduction and the problem setup. [Member 2] will explain the core tree search algorithm and how we prune it efficiently. [Member 3] will walk you through Q-Learning and how the agent learns by itself. [Member 4] will present the Genetic Algorithm that optimizes our heuristic weights. And finally, [Member 5] will show you the live demo and wrap up with results.

### Slide 3 — Problem Statement & Game Rules

> So what's the game about? Imagine a bridge made of twelve planks. Two players take turns crossing it. The first player, called the **Traveler** or MAX, wants to reach the end and collect as many points as possible. The second player, the **Specter** or MIN, is trying to minimize the Traveler's advantage. On each turn, a player can either **step one plank forward**, which is completely safe and deterministic, or **leap two planks**, which is faster but risky — there's a twenty percent chance of slipping and only advancing one plank. The bridge also has special planks: **treasures** that give you plus two points, **traps** that cost you minus three, and **slippery planks** that make your slip chance two-and-a-half times worse. The player who steps on the final plank wins a bonus of plus ten points.

### Slide 4 — PEAS Framework

> To formally define our AI agent, we use the PEAS framework. The **Performance Measure** is the net score difference — treasures, traps, and the win bonus. The **Environment** is a one-dimensional discrete bridge that is stochastic and adversarial. The **Actuators** are the two possible moves: Step 1 or Leap 2. And the **Sensors** give the agent the current state — how many planks are remaining, whose turn it is, and both players' scores. This gives us a complete formal specification of the problem.

> *With that foundation laid out, I'll hand it over to [Member 2], who will explain how we search for optimal moves using Expectiminimax.*

---

## 🎤 Member 2 — State Model, Expectiminimax & Star2 Pruning

**Slides**: 5 → 9  
**Estimated Time**: ~2.5 minutes

---

### Slide 5 — State Representation & Transition Model

> Thank you. Let me start with how we represent the game mathematically. Every game state is a tuple of four values: the number of remaining planks, whose turn it is, and both players' scores. The transitions are straightforward. If you choose Step 1, you deterministically advance one plank. If you choose Leap 2, there are two possible outcomes: with eighty percent probability you land two planks ahead, and with twenty percent probability you slip and only move one. On slippery planks, that twenty percent base rate is multiplied by two-point-five, making slips much more likely.

### Slide 6 — Algorithm 1: Expectiminimax Overview

> Now, to find the optimal move, we build a **game tree** using Expectiminimax. This is an extension of regular Minimax designed for stochastic games. The tree has three types of nodes. **MAX nodes** represent the Traveler choosing the action with the highest expected value. **MIN nodes** represent the Specter choosing the lowest. And **Chance nodes** sit in between — they calculate the probability-weighted average of their children's values. So the expected utility at a Chance node is simply the sum of each outcome's probability times its value.

### Slide 7 — Chance Nodes & Expected Utility

> Let me zoom in on how Chance nodes work. When a player chooses Leap 2, the environment essentially flips a weighted coin. The Chance node takes the success outcome, multiplies it by zero-point-eight, takes the slip outcome, multiplies it by zero-point-two, and adds them together. This expected value is then passed up to the parent MAX or MIN node. This is the fundamental reason why this game requires Expectiminimax rather than plain Minimax — we have to account for randomness in the environment.

### Slide 8 — Star2 Pruning: Why Alpha-Beta Fails

> Now, you might ask — why not just use Alpha-Beta pruning to speed things up? The problem is that Alpha-Beta works by cutting branches when one player has already found a guaranteed better option elsewhere. But Chance nodes compute **weighted averages**. You can't know the average until you've evaluated all the children. Cutting a branch early would give you a mathematically incorrect expected value. So standard Alpha-Beta simply cannot be applied to stochastic nodes without risking errors.

### Slide 9 — Star2 Pruning: Bounding Math

> That's where **Star2 Pruning** comes in. The key insight is: even though we can't know the exact expected value early, we can **bound** it. We pre-compute the maximum and minimum possible heuristic values — V-max and V-min — based on the game's reward structure. Then, after evaluating some children, we calculate the best-case and worst-case for the remaining ones. If the tightened search window collapses — meaning alpha-child becomes greater than or equal to beta-child — we know the remaining branches can't change the parent's decision, and we prune immediately. Our profiling results confirm this: at depth four, Star2 reduced the number of evaluated nodes from one hundred twenty-one down to seventy-four — that's a nearly **thirty-nine percent reduction** in computation.

> *That covers the planning approach. Now I'll pass it to [Member 3], who will show how we solve the same game without any tree search at all — using reinforcement learning.*

---

## 🎤 Member 3 — Q-Learning, Bellman Update & Convergence

**Slides**: 10 → 12  
**Estimated Time**: ~2 minutes

---

### Slide 10 — Algorithm 2: Q-Learning Overview

> Thanks. So Expectiminimax works great, but it requires searching through a game tree every time you want to make a decision. What if the agent could just **learn** the right moves through experience? That's exactly what Q-Learning does. It's a model-free reinforcement learning algorithm — the agent doesn't need a model of the environment. Instead, it learns a Q-value for every state-action pair. The Q-value tells the agent: "If I'm in this state and I take this action, what's the expected future reward?" We use a compressed state — just the remaining planks and whose turn it is — which gives us only twenty-four possible states. The agent trains by playing against itself, using epsilon-greedy exploration that decays over time.

### Slide 11 — Q-Learning: Bellman Update & Self-Play

> The heart of Q-Learning is the **Bellman update equation**. When the agent takes action *a* in state *s*, reaches state *s-prime*, and receives reward *R*, it updates the Q-value using temporal-difference learning. The update rule is: Q of s, a gets adjusted toward R plus gamma times the target. The target depends on who plays next — if it's MAX's turn, we take the maximum Q-value at the next state; if it's MIN's turn, we take the minimum. Our reward function is elegant: it's simply the change in score differential at each step. Because this telescopes over the entire game, it's mathematically guaranteed to equal the final game outcome.

### Slide 12 — Exploratory Starts & Convergence Results

> Here's the most interesting part. When we first trained the agent starting from the beginning of the bridge every time, we only got about seventy-five percent policy agreement with the tree search. Why? Because in a normal game, some states are simply **unreachable** — for example, it might be impossible for MAX to have exactly seven planks remaining during regular play. Since Q-Learning only updates states it visits, those states stayed untrained. Our fix was **Exploratory Starts**: thirty percent of training episodes begin from a completely random state and random turn. This ensures every single state gets visited and trained. The result? After fifteen thousand episodes, Q-Learning's policy matches the Expectiminimax solution in **one hundred percent** of all sixteen state-action pairs. Complete convergence.

> *Now [Member 4] will show how we used evolution to find the best heuristic weights automatically.*

---

## 🎤 Member 4 — Genetic Algorithm

**Slides**: 13 → 14  
**Estimated Time**: ~1.5 minutes

---

### Slide 13 — Algorithm 3: Genetic Algorithm Overview

> Thank you. The third algorithm we implemented is a **Genetic Algorithm** for optimizing the heuristic weights used by the Expectiminimax solver. Our heuristic evaluates non-terminal states using four weights: how much to value MAX's score, how much to penalize MIN's score, how important progress along the bridge is, and how much to avoid nearby traps. Each chromosome in our population is a list of these four floating-point weights. To evaluate fitness, we run a **round-robin tournament** — every chromosome plays matches against every other chromosome using the Expectiminimax solver, and wins are counted as fitness points. Parents are selected using **two-way tournament selection**, and the top two chromosomes survive directly to the next generation through elitism.

### Slide 14 — GA: Crossover, Mutation & Results

> For creating offspring, we use **single-point crossover** — a random index splits two parent chromosomes, and we swap the segments to produce a child. Then we apply **Gaussian mutation** with a standard deviation of zero-point-five and a fifteen percent mutation rate. Importantly, we enforce strict **polarity constraints**: weights for MAX's score and progress must stay positive, while weights for MIN's score and trap risk must stay negative. This prevents the algorithm from evolving nonsensical strategies. Our default weights are two, negative two, one-point-five, and negative three. The population typically converges within five to eight generations, producing refined weights that perform measurably better in tournament play.

> *With all three algorithms covered, let me hand over to [Member 5] for the live demonstration and our final results.*

---

## 🎤 Member 5 — Demo, Testing, Conclusion & Q&A

**Slides**: 15 → 18  
**Estimated Time**: ~2 minutes

---

### Slide 15 — Live Demo / Dashboard Screenshots

> Thank you. Let me show you what all of this looks like in practice. We built a full interactive web dashboard using a **FastAPI** backend and a modern JavaScript frontend. The dashboard lets you play the game manually or watch the AI agents play in real time. You can visualize the Expectiminimax decision tree with all the MAX, MIN, and Chance nodes color-coded. There's a Q-table heatmap that shows the learned values for every state, and a GA evolution tracker that plots fitness improvement across generations. The entire application is deployed on Vercel for live access. Let me quickly walk through the interface…

*(If doing a live demo, navigate through the dashboard here. If not, point to the screenshots on the slide.)*

### Slide 16 — Testing & Verification Results

> Now let's talk about correctness. We ran rigorous tests across all three algorithms. First, **Star2 Pruning** was verified to produce identical optimal moves as unpruned Expectiminimax at every search depth — it only removes redundant computation, never changes the answer. Our profiling shows consistent improvement: at depth two, we go from thirteen to twelve nodes; at depth three, from forty to twenty-nine; and at depth four, from one hundred twenty-one down to seventy-four — that's a nearly thirty-nine percent reduction. For **Q-Learning**, we verified that all sixteen state-action pairs converge to the same optimal policy as the tree search — that's one hundred percent alignment. For the **Genetic Algorithm**, we confirmed that all evolved chromosomes maintain correct polarity constraints throughout evolution. And all five API endpoints were tested with both valid inputs and edge cases.

### Slide 17 — Conclusion & Key Takeaways

> To summarize our project: we took a stochastic adversarial game and solved it using three fundamentally different AI approaches. **Expectiminimax** gives us exact optimal decisions through tree search. **Star2 Pruning** makes that search efficient by using mathematical bounds to skip unnecessary branches. **Q-Learning** achieves the exact same optimal policy but learns it entirely from experience, without ever building a tree. And **Genetic Algorithms** can automatically tune the heuristic weights that guide the tree search. The most remarkable finding is that all three approaches — planning, learning, and evolution — converge to the **same strategic decisions**. This demonstrates the mathematical consistency underlying these different paradigms of artificial intelligence.

### Slide 18 — Q&A / Thank You

> That concludes our presentation. We'd like to thank you for your time and attention. We're now happy to take any questions you might have about the algorithms, the implementation, or the results. Thank you!

---

> **End of Speaker Scripts**
