import sys
import os
import math

from engine import BridgeEnv, ExpectiminimaxSolver, QLearningAgent

def run_verification():
    print("======================================================================")
    print("       VERIFYING CONVERGENCE OF PLANNING VS. REINFORCEMENT LEARNING   ")
    print("======================================================================")
    
    # 1. Initialize environment
    n_planks = 8
    slip_prob = 0.2
    # Standard normal play: win bonus is +10
    env = BridgeEnv(n_planks=n_planks, slip_prob=slip_prob, play_mode="normal")
    
    # 2. Compute Exact Utilities using Expectiminimax (Tree Search Planning)
    # Use standard win/loss heuristic weights: [1.0, -1.0, 0.0, 0.0]
    # This evaluates exact terminal value differentials at all search horizons
    weights = [1.0, -1.0, 0.0, 0.0]
    solver = ExpectiminimaxSolver(env, max_depth=n_planks + 2, weights=weights)
    
    exact_vals = {}
    exact_moves = {}
    
    for r in range(1, n_planks + 1):
        for turn in [True, False]:
            # Construct a pure state representation at plank r
            # state: (remaining, is_max_turn, max_score, min_score)
            state = (r, turn, 0, 0)
            val, move, _, _ = solver.solve(state, prune=True)
            exact_vals[(r, turn)] = val
            exact_moves[(r, turn)] = move

    # 3. Train Q-Learning Agent (Temporal-Difference Learning)
    # We train for 15,000 episodes
    print(f"\nTraining Q-Learning Agent via self-play (15,000 episodes)...")
    agent = QLearningAgent(env, alpha=0.15, gamma=1.0, epsilon=0.3)
    agent.train(episodes=15000)
    
    print("\nComparing optimal action selection:")
    print("----------------------------------------------------------------------")
    print("Planks Left | Turn | Expectiminimax Value | Q-Value Max | Optimal Action")
    print("            |      | (Tree Search)        | (TD Learner)| Solver | Q-Agent")
    print("----------------------------------------------------------------------")
    
    match_count = 0
    total_states = 0
    
    for r in range(1, n_planks + 1):
        for turn in [True, False]:
            state = (r, turn, 0, 0)
            key = (r, turn)
            
            # Exact solver details
            solver_val = exact_vals[key]
            solver_move = exact_moves[key]
            
            # Q-agent details
            q_vals = agent.get_q_values(key)
            q_move = agent.choose_action(state, force_greedy=True)
            best_q_val = q_vals[q_move]
            
            solver_move_str = f"Leap 2" if solver_move == 2 else "Step 1"
            q_move_str = f"Leap 2" if q_move == 2 else "Step 1"
            turn_str = "MAX" if turn else "MIN"
            
            print(f"    P{r:<7} | {turn_str:<4} | {solver_val:<20.3f} | {best_q_val:<11.3f} | {solver_move_str:<6} | {q_move_str:<7}")
            
            if solver_move == q_move:
                match_count += 1
            total_states += 1
            
    print("----------------------------------------------------------------------")
    match_percentage = (match_count / total_states) * 100
    print(f"Policy Alignment: {match_count}/{total_states} states matched ({match_percentage:.1f}%)")
    print("======================================================================")

if __name__ == "__main__":
    run_verification()
