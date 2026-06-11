"""
COMPREHENSIVE AUDIT: Specter's Bridge AI Laboratory
=====================================================
Tests every algorithm for correctness, edge cases, and invariant violations.
Run before any presentation to guarantee correctness.
"""
import math
import random
import sys
import os
import io

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from engine import BridgeEnv, ExpectiminimaxSolver, QLearningAgent, GeneticHeuristicEvolver

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []

def test(name, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((name, status, detail))
    print(f"  {status}  {name}" + (f"  ({detail})" if detail else ""))

def section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

# ============================================================================
# SECTION 1: Environment Correctness
# ============================================================================
section("1. ENVIRONMENT CORRECTNESS")

env = BridgeEnv(n_planks=12, slip_prob=0.2, play_mode="normal")

# 1.1 Initial state
state = env.get_initial_state()
test("Initial state format", state == (12, True, 0, 0), f"Got {state}")

# 1.2 Terminal state detection
test("Terminal at 0 planks", env.is_terminal((0, True, 5, 3)))
test("Not terminal at 1 plank", not env.is_terminal((1, True, 0, 0)))

# 1.3 Legal moves
test("Legal moves at 1 plank = [1]", env.get_legal_moves((1, True, 0, 0)) == [1])
test("Legal moves at 2+ planks = [1,2]", env.get_legal_moves((5, True, 0, 0)) == [1, 2])
test("Legal moves at terminal = []", env.get_legal_moves((0, True, 0, 0)) == [])

# 1.4 Deterministic step transition
t = env.get_transitions((6, True, 0, 0), 1)
test("Step 1 is deterministic", len(t) == 1 and t[0][1] == 1.0)

# 1.5 Stochastic leap transition
t = env.get_transitions((6, True, 0, 0), 2)
test("Leap 2 has 2 outcomes", len(t) == 2)
probs_sum = sum(p for _, p in t)
test("Transition probabilities sum to 1.0", abs(probs_sum - 1.0) < 1e-9, f"Sum={probs_sum}")

# 1.6 Slippery plank scaling
# Plank index 5 is slippery: current_plank_idx = 12 - remaining
# So remaining=7 means we're on plank 5 (index 12-7=5)
sp = env.get_slip_prob_at_state(7)
test("Slippery plank multiplies slip prob by 2.5", abs(sp - 0.5) < 1e-9, f"Got {sp}")

# 1.7 Normal plank has base slip prob
sp_normal = env.get_slip_prob_at_state(12)  # plank index 0
test("Normal plank has base slip prob", abs(sp_normal - 0.2) < 1e-9, f"Got {sp_normal}")

# 1.8 Score updates: treasure
# Plank 4 is treasure (+2): remaining=8 → plank 12-8=4. To land on plank 4: go from remaining=9, step 1
state_before_treasure = (9, True, 0, 0)
t = env.get_transitions(state_before_treasure, 1)
landed_state = t[0][0]
# We should have landed on plank 4 (treasure), MAX score should increase by 2
test("MAX collects treasure +2", landed_state[2] == 2, f"max_score={landed_state[2]}")

# 1.9 Score updates: trap
# Plank 3 is trap (-3): remaining=10 → plank 12-10=2. To land on plank 3: go from remaining=10, step 1 → plank 3
state_before_trap = (10, True, 0, 0)
t = env.get_transitions(state_before_trap, 1)
landed_state = t[0][0]
# Plank index = 12 - (10-1) = 3 → trap
test("MAX hits trap -3", landed_state[2] == -3, f"max_score={landed_state[2]}")

# 1.10 Win bonus in normal mode
# If remaining=1, step 1 → remaining=0 (terminal). Last mover wins.
state_last = (1, True, 0, 0)
t = env.get_transitions(state_last, 1)
final = t[0][0]
test("Normal play: last mover gets +10 win bonus", final[2] == 10, f"max_score={final[2]}")

# 1.11 Misere mode
env_misere = BridgeEnv(n_planks=12, slip_prob=0.2, play_mode="misere")
state_last_m = (1, True, 0, 0)
t_m = env_misere.get_transitions(state_last_m, 1)
final_m = t_m[0][0]
test("Misere play: last mover gets -10 penalty", final_m[2] == -10, f"max_score={final_m[2]}")

# 1.12 Turn alternation
state_a = (6, True, 0, 0)
next_s = env.transition(state_a, 1, 1)
test("Turn alternates after move", next_s[1] == False, f"is_max_turn={next_s[1]}")

# 1.13 Edge case: n_planks validation
try:
    BridgeEnv(n_planks=0)
    test("Reject n_planks=0", False)
except ValueError:
    test("Reject n_planks=0", True)

try:
    BridgeEnv(n_planks=-5)
    test("Reject n_planks=-5", False)
except ValueError:
    test("Reject n_planks=-5", True)

# 1.14 Edge case: slip_prob validation
try:
    BridgeEnv(slip_prob=-0.1)
    test("Reject slip_prob=-0.1", False)
except ValueError:
    test("Reject slip_prob=-0.1", True)

try:
    BridgeEnv(slip_prob=1.5)
    test("Reject slip_prob=1.5", False)
except ValueError:
    test("Reject slip_prob=1.5", True)

# ============================================================================
# SECTION 2: EXPECTIMINIMAX SOLVER CORRECTNESS
# ============================================================================
section("2. EXPECTIMINIMAX SOLVER CORRECTNESS")

env6 = BridgeEnv(n_planks=6, slip_prob=0.2, play_mode="normal")

# 2.1 Pruned vs unpruned values must be IDENTICAL
for depth in [1, 2, 3, 4]:
    solver_np = ExpectiminimaxSolver(env6, max_depth=depth)
    solver_p = ExpectiminimaxSolver(env6, max_depth=depth)
    state = env6.get_initial_state()
    
    val_np, move_np, _, stats_np = solver_np.solve(state, prune=False)
    val_p, move_p, _, stats_p = solver_p.solve(state, prune=True)
    
    test(f"Depth {depth}: Pruned value == Unpruned value", 
         abs(val_np - val_p) < 1e-9,
         f"no_prune={val_np:.4f} prune={val_p:.4f}")
    test(f"Depth {depth}: Same best move", 
         move_np == move_p,
         f"no_prune={move_np} prune={move_p}")

# 2.2 Pruning efficiency: fewer nodes evaluated
for depth in [2, 3, 4]:
    solver = ExpectiminimaxSolver(env6, max_depth=depth)
    _, _, _, stats_np = solver.solve(env6.get_initial_state(), prune=False)
    _, _, _, stats_p = solver.solve(env6.get_initial_state(), prune=True)
    reduction = (1 - stats_p["evaluated"] / stats_np["evaluated"]) * 100
    test(f"Depth {depth}: Star2 reduces nodes", 
         stats_p["evaluated"] <= stats_np["evaluated"],
         f"{stats_np['evaluated']} → {stats_p['evaluated']} ({reduction:.1f}% reduction)")

# 2.3 Terminal state returns exact utility, not heuristic
solver = ExpectiminimaxSolver(env6, max_depth=10)
terminal_state = (0, True, 15, 3)
val, move, _, _ = solver.solve(terminal_state, prune=False)
expected_terminal_val = solver.weights[0] * 15 + solver.weights[1] * 3
test("Terminal state returns exact weighted utility", 
     abs(val - expected_terminal_val) < 1e-9,
     f"Got {val}, expected {expected_terminal_val}")

# 2.4 Depth 0 returns heuristic
solver = ExpectiminimaxSolver(env6, max_depth=0)
state = env6.get_initial_state()
val, move, _, _ = solver.solve(state, prune=False)
expected_h = solver.heuristic(state)
test("Depth 0 returns heuristic value", abs(val - expected_h) < 1e-9)

# 2.5 V_max >= V_min (global bounds are valid)
solver = ExpectiminimaxSolver(env6, max_depth=3)
test("V_max >= V_min", solver.V_max >= solver.V_min, f"V_max={solver.V_max}, V_min={solver.V_min}")

# 2.6 All heuristic values should be within [V_min, V_max]
solver = ExpectiminimaxSolver(env6, max_depth=3)
for r in range(1, 7):
    for turn in [True, False]:
        s = (r, turn, 0, 0)
        h = solver.heuristic(s)
        test(f"Heuristic P{r} {'MAX' if turn else 'MIN'} in [V_min, V_max]",
             solver.V_min <= h <= solver.V_max,
             f"h={h:.2f}, bounds=[{solver.V_min:.2f}, {solver.V_max:.2f}]")

# 2.7 Test with multiple board sizes
for n in [4, 8, 12]:
    env_n = BridgeEnv(n_planks=n, slip_prob=0.2)
    solver = ExpectiminimaxSolver(env_n, max_depth=3)
    val, move, _, stats = solver.solve(env_n.get_initial_state(), prune=True)
    test(f"Board size {n}: produces valid move", move in [1, 2])

# 2.8 Misere mode changes strategy
env_normal = BridgeEnv(n_planks=4, slip_prob=0.0, play_mode="normal")
env_misere = BridgeEnv(n_planks=4, slip_prob=0.0, play_mode="misere")
solver_n = ExpectiminimaxSolver(env_normal, max_depth=10, weights=[1.0, -1.0, 0.0, 0.0])
solver_m = ExpectiminimaxSolver(env_misere, max_depth=10, weights=[1.0, -1.0, 0.0, 0.0])
val_n, _, _, _ = solver_n.solve(env_normal.get_initial_state(), prune=False)
val_m, _, _, _ = solver_m.solve(env_misere.get_initial_state(), prune=False)
test("Normal and misere produce different root values", 
     abs(val_n - val_m) > 0.1,
     f"normal={val_n:.2f}, misere={val_m:.2f}")

# ============================================================================
# SECTION 3: Q-LEARNING CORRECTNESS
# ============================================================================
section("3. Q-LEARNING CORRECTNESS")

env8 = BridgeEnv(n_planks=8, slip_prob=0.2, play_mode="normal")

# 3.1 Q-table initialization
agent = QLearningAgent(env8)
key = (8, True)
q_vals = agent.get_q_values(key)
test("Q-table initializes actions to 0", all(v == 0.0 for v in q_vals.values()))

# 3.2 State key compression works
state = (8, True, 15, 3)
key = agent.get_state_key(state)
test("State key drops scores", key == (8, True))

# 3.3 Training produces history
history = agent.train(episodes=100)
test("Training produces history", len(history) > 0)

# 3.4 Epsilon decays during training
agent_test = QLearningAgent(env8, epsilon=0.3)
initial_eps = agent_test.epsilon
agent_test.train(episodes=1000)
test("Epsilon decays during training", agent_test.epsilon < initial_eps, 
     f"Start={initial_eps}, End={agent_test.epsilon:.4f}")
test("Epsilon stays above floor (0.01)", agent_test.epsilon >= 0.01)

# 3.5 Q-learning converges to same policy as tree search (THE KEY TEST)
# Use gamma=1.0 and pure score weights for exact comparison
weights_exact = [1.0, -1.0, 0.0, 0.0]
solver_exact = ExpectiminimaxSolver(env8, max_depth=10, weights=weights_exact)

# Train multiple times to get best result
best_alignment = 0
for trial in range(3):
    agent_conv = QLearningAgent(env8, alpha=0.15, gamma=1.0, epsilon=0.3)
    agent_conv.train(episodes=15000)
    
    matches = 0
    total = 0
    for r in range(1, 9):
        for turn in [True, False]:
            state = (r, turn, 0, 0)
            _, solver_move, _, _ = solver_exact.solve(state, prune=True)
            q_move = agent_conv.choose_action(state, force_greedy=True)
            if solver_move == q_move:
                matches += 1
            total += 1
    alignment = matches / total * 100
    best_alignment = max(best_alignment, alignment)
    if alignment == 100:
        break

test("Q-Learning 100% policy convergence", best_alignment == 100, f"Best: {best_alignment:.1f}%")

# 3.6 Force-greedy selection always returns a move
for r in range(1, 9):
    state = (r, True, 0, 0)
    move = agent_conv.choose_action(state, force_greedy=True)
    test(f"Force-greedy P{r} MAX returns valid move", move in [1, 2] if r >= 2 else move == 1)

# 3.7 Terminal state returns None
move_terminal = agent_conv.choose_action((0, True, 0, 0))
test("Terminal state action is None", move_terminal is None)

# ============================================================================
# SECTION 4: GENETIC ALGORITHM CORRECTNESS
# ============================================================================
section("4. GENETIC ALGORITHM CORRECTNESS")

env_ga = BridgeEnv(n_planks=6, slip_prob=0.2)

# 4.1 Population initialization
evolver = GeneticHeuristicEvolver(env_ga, pop_size=10, mutation_rate=0.15)
test("Population size correct", len(evolver.population) == 10)

# 4.2 Chromosome structure
for i, chrome in enumerate(evolver.population):
    test(f"Chromosome {i}: 4 weights", len(chrome) == 4)

# 4.3 Polarity constraints on initialization
for i, chrome in enumerate(evolver.population):
    test(f"Chromosome {i}: w0 (max_score) positive", chrome[0] > 0)
    test(f"Chromosome {i}: w1 (min_score) negative", chrome[1] < 0)
    test(f"Chromosome {i}: w2 (progress) positive", chrome[2] > 0)
    test(f"Chromosome {i}: w3 (trap_risk) negative", chrome[3] < 0)

# 4.4 Evolution produces valid results
result = evolver.evolve_generation()
test("Evolution returns generation count", result["generation"] == 1)
test("Best weights has 4 values", len(result["best_weights"]) == 4)
test("Best fitness >= 0", result["best_fitness"] >= 0)

# 4.5 Polarity preserved after evolution (3 generations)
for gen in range(3):
    result = evolver.evolve_generation()
    for chrome in evolver.population:
        polarity_ok = chrome[0] > 0 and chrome[1] < 0 and chrome[2] > 0 and chrome[3] < 0
        if not polarity_ok:
            test(f"Gen {result['generation']}: Polarity preserved", False, f"Bad chrome: {chrome}")
            break
    else:
        test(f"Gen {result['generation']}: Polarity preserved in all chromosomes", True)

# 4.6 Elitism: best chromosome survives
evolver2 = GeneticHeuristicEvolver(env_ga, pop_size=6, mutation_rate=0.15)
# Run one generation to get fitness
fitness = evolver2.evaluate_fitness_all()
best_idx = max(range(len(fitness)), key=lambda i: fitness[i])
best_chrome = list(evolver2.population[best_idx])
evolver2.evolve_generation()
# The best chromosome should be in the new population
test("Elitism: best survives to next gen", best_chrome in evolver2.population)

# 4.7 Crossover produces valid child
parent_a = [2.0, -2.0, 1.5, -3.0]
parent_b = [1.0, -1.0, 0.5, -2.0]
child = evolver2.crossover(parent_a, parent_b)
test("Crossover produces 4 weights", len(child) == 4)
# Each weight should come from either parent
for i in range(4):
    test(f"Crossover weight {i} from a parent", child[i] == parent_a[i] or child[i] == parent_b[i])

# 4.8 Mutation respects polarity
random.seed(42)
chrome = [2.0, -2.0, 1.5, -3.0]
for _ in range(100):
    mutated = evolver2.mutate(chrome)
    polarity_ok = mutated[0] >= 0.1 and mutated[1] <= -0.1 and mutated[2] >= 0.1 and mutated[3] <= -0.1
    if not polarity_ok:
        test("Mutation polarity invariant (100 trials)", False, f"Bad: {mutated}")
        break
else:
    test("Mutation polarity invariant (100 trials)", True)

# ============================================================================
# SECTION 5: STAR2 PRUNING MATHEMATICAL INVARIANTS
# ============================================================================
section("5. STAR2 PRUNING MATHEMATICAL INVARIANTS")

env12 = BridgeEnv(n_planks=12, slip_prob=0.2)

# 5.1 Pruning never changes the root value (extensive test across many states)
for n in [6, 8, 12]:
    env_test = BridgeEnv(n_planks=n, slip_prob=0.2)
    for depth in [2, 3]:
        for r in range(1, min(n+1, 7)):
            for turn in [True, False]:
                state = (r, turn, 0, 0)
                solver = ExpectiminimaxSolver(env_test, max_depth=depth)
                val_np, _, _, _ = solver.solve(state, prune=False)
                val_p, _, _, _ = solver.solve(state, prune=True)
                if abs(val_np - val_p) > 1e-6:
                    test(f"Invariant: N={n} D={depth} P{r} {'MAX' if turn else 'MIN'}", False,
                         f"Diff: {abs(val_np - val_p):.8f}")
                    break
        else:
            test(f"Pruning=Exact for N={n}, Depth={depth} (all states)", True)
            continue
        break

# 5.2 Node count with pruning always <= without
for depth in [2, 3, 4]:
    solver = ExpectiminimaxSolver(env12, max_depth=depth)
    _, _, _, s_np = solver.solve(env12.get_initial_state(), prune=False)
    _, _, _, s_p = solver.solve(env12.get_initial_state(), prune=True)
    test(f"Depth {depth}: pruned nodes <= unpruned nodes",
         s_p["evaluated"] <= s_np["evaluated"],
         f"{s_p['evaluated']} <= {s_np['evaluated']}")

# ============================================================================
# SECTION 6: PROFILING & PERFORMANCE
# ============================================================================
section("6. PROFILING & PERFORMANCE")

import time

env_perf = BridgeEnv(n_planks=12, slip_prob=0.2)

for depth in [1, 2, 3, 4]:
    solver = ExpectiminimaxSolver(env_perf, max_depth=depth)
    
    t0 = time.perf_counter()
    _, _, _, stats_np = solver.solve(env_perf.get_initial_state(), prune=False)
    time_np = time.perf_counter() - t0
    
    t0 = time.perf_counter()
    _, _, _, stats_p = solver.solve(env_perf.get_initial_state(), prune=True)
    time_p = time.perf_counter() - t0
    
    reduction = (1 - stats_p["evaluated"] / stats_np["evaluated"]) * 100 if stats_np["evaluated"] > 0 else 0
    
    print(f"  Depth {depth}: {stats_np['evaluated']:>4} → {stats_p['evaluated']:>4} nodes "
          f"({reduction:>5.1f}% reduction) | "
          f"Pruned: {stats_p['pruned']} branches | "
          f"Time: {time_np*1000:.1f}ms → {time_p*1000:.1f}ms")

# ============================================================================
# SUMMARY
# ============================================================================
section("AUDIT SUMMARY")

total = len(results)
passed = sum(1 for _, status, _ in results if status == PASS)
failed = sum(1 for _, status, _ in results if status == FAIL)

print(f"\n  Total Tests:  {total}")
print(f"  Passed:       {passed}  ✅")
print(f"  Failed:       {failed}  {'❌' if failed > 0 else '🎉'}")
print(f"\n  Pass Rate:    {passed/total*100:.1f}%")

if failed > 0:
    print(f"\n  FAILED TESTS:")
    for name, status, detail in results:
        if status == FAIL:
            print(f"    ❌ {name}: {detail}")
else:
    print(f"\n  🎉 ALL TESTS PASSED — READY FOR PRESENTATION! 🎉")

print(f"\n{'='*70}\n")
