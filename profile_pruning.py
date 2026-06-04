import time
import math
from engine import BridgeEnv, ExpectiminimaxSolver

def profile():
    n_planks = 15
    slip_prob = 0.2
    play_mode = "normal"
    
    # Initialize the 15-plank environment
    env = BridgeEnv(n_planks=n_planks, slip_prob=slip_prob, play_mode=play_mode)
    state = env.get_initial_state()
    
    print(f"Profiling Expectiminimax on a {n_planks}-plank bridge.")
    print(f"Initial State: {state}")
    print(f"Board configuration: {env.plank_types}")
    print("-" * 80)
    
    depths = [1, 2, 3, 4]
    results = []
    
    for depth in depths:
        # We'll use the default heuristic weights: [2.0, -2.0, 1.5, -3.0]
        solver = ExpectiminimaxSolver(env, max_depth=depth)
        
        # 1. Run without pruning
        # Warm-up run
        solver.solve(state, prune=False)
        
        # Timing runs
        iters = 5000 if depth <= 2 else 1000
        start_time = time.perf_counter()
        for _ in range(iters):
            val_np, move_np, _, stats_np = solver.solve(state, prune=False)
        end_time = time.perf_counter()
        time_np = (end_time - start_time) / iters * 1000.0 # in milliseconds
        nodes_np = stats_np["evaluated"]
        pruned_np = stats_np["pruned"]
        
        # 2. Run with pruning
        # Warm-up run
        solver.solve(state, prune=True)
        
        # Timing runs
        start_time = time.perf_counter()
        for _ in range(iters):
            val_p, move_p, _, stats_p = solver.solve(state, prune=True)
        end_time = time.perf_counter()
        time_p = (end_time - start_time) / iters * 1000.0 # in milliseconds
        nodes_p = stats_p["evaluated"]
        pruned_p = stats_p["pruned"]
        
        # Verify correctness (value should be the same)
        if not math.isclose(val_np, val_p, rel_tol=1e-5):
            print(f"Warning: Discrepancy at depth {depth}! No-prune value = {val_np}, Prune value = {val_p}")
            
        results.append({
            "depth": depth,
            "nodes_np": nodes_np,
            "pruned_np": pruned_np,
            "time_np": time_np,
            "nodes_p": nodes_p,
            "pruned_p": pruned_p,
            "time_p": time_p
        })
        
    print(f"{'Depth':<6} | {'Pruned':<10} | {'Nodes (No Prune)':<18} | {'Nodes (Pruned)':<15} | {'Node Red. (%)':<15} | {'Time No Prune (ms)':<20} | {'Time Pruned (ms)':<18} | {'Speedup':<8}")
    print("-" * 125)
    for r in results:
        node_red = (r["nodes_np"] - r["nodes_p"]) / r["nodes_np"] * 100.0
        speedup = r["time_np"] / r["time_p"]
        print(f"{r['depth']:<6} | {'No':<10} | {r['nodes_np']:<18} | {r['nodes_p']:<15} | {node_red:<14.1f}% | {r['time_np']:<20.4f} | {r['time_p']:<18.4f} | {speedup:.2f}x")
        
    # Write raw output to a file or let us copy it
    import json
    with open("profile_results.json", "w") as f:
        json.dump(results, f, indent=4)

if __name__ == "__main__":
    profile()
