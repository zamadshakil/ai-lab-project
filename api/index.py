from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Optional, Tuple
import os
import random
import sys

# Add root project folder to python path to resolve engine.py on Vercel
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import BridgeEnv, ExpectiminimaxSolver, QLearningAgent, GeneticHeuristicEvolver

app = FastAPI(title="Specter's Bridge AI Lab - Vercel API")

# Resolve static directory relative to this file (api/index.py)
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Shared global environments and evolver state
global_env = BridgeEnv()
global_q_agent = QLearningAgent(global_env)
global_ga_evolver = None

class BoardSetupRequest(BaseModel):
    n_planks: int = Field(default=12, gt=0)
    slip_prob: float = Field(default=0.2, ge=0.0, le=1.0)
    play_mode: str = Field(default="normal")
    plank_types: Optional[List[str]] = None

class StepRequest(BaseModel):
    agent_type: str
    intended_move: Optional[int] = None
    state: Tuple[int, bool, int, int]
    weights: Optional[Tuple[float, float, float, float]] = None

class TreeRequest(BaseModel):
    state: Tuple[int, bool, int, int]
    max_depth: int = Field(default=3, ge=0)
    prune: bool = True
    weights: Optional[Tuple[float, float, float, float]] = None

class TrainRequest(BaseModel):
    episodes: int = Field(default=5000, gt=0)
    n_planks: int = Field(default=12, gt=0)
    slip_prob: float = Field(default=0.2, ge=0.0, le=1.0)
    play_mode: str = Field(default="normal")

class EvolveRequest(BaseModel):
    pop_size: int = Field(default=10, ge=2)
    mutation_rate: float = Field(default=0.15, ge=0.0, le=1.0)
    reset: bool = False

@app.get("/")
def read_root():
    """Serves the main landing page of the dashboard locally."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h2>Specter's Bridge Dashboard is starting up. Place index.html inside the static folder.</h2>")

@app.post("/api/game/reset")
def reset_game(config: BoardSetupRequest):
    """Initializes a new game environment with custom parameters."""
    global global_env, global_q_agent, global_ga_evolver
    global_env = BridgeEnv(
        n_planks=config.n_planks,
        slip_prob=config.slip_prob,
        play_mode=config.play_mode
    )
    
    if config.plank_types:
        if len(config.plank_types) == config.n_planks + 1:
            global_env.set_board_config(config.plank_types)
        else:
            raise HTTPException(status_code=400, detail="Plank types list length must equal n_planks + 1")
            
    global_q_agent = QLearningAgent(global_env)
    global_ga_evolver = None
    
    state = global_env.get_initial_state()
    return {
        "state": state,
        "plank_types": global_env.plank_types,
        "n_planks": global_env.n_planks,
        "slip_prob": global_env.slip_prob,
        "play_mode": global_env.play_mode
    }

@app.post("/api/game/step")
def play_step(req: StepRequest):
    """Executes a move for the specified agent and returns the transitioned state."""
    state = tuple(req.state)
    remaining, is_max_turn, max_score, min_score = state
    
    if global_env.is_terminal(state):
        raise HTTPException(status_code=400, detail="Game is already in a terminal state.")
        
    legal_moves = global_env.get_legal_moves(state)
    
    intended_move = None
    if req.agent_type == "player":
        if req.intended_move not in legal_moves:
            raise HTTPException(status_code=400, detail=f"Illegal move {req.intended_move} for current state.")
        intended_move = req.intended_move
    elif req.agent_type == "expectiminimax":
        solver = ExpectiminimaxSolver(global_env, max_depth=3, weights=req.weights)
        _, intended_move, _, _ = solver.solve(state, prune=True)
    elif req.agent_type == "heuristic":
        best_val = -float('inf') if is_max_turn else float('inf')
        solver = ExpectiminimaxSolver(global_env, max_depth=1, weights=req.weights)
        for move in legal_moves:
            val, _ = solver._evaluate_chance_node(state, move, 0, -float('inf'), float('inf'), is_max_turn, False)
            if is_max_turn:
                if val > best_val:
                    best_val, intended_move = val, move
            else:
                if val < best_val:
                    best_val, intended_move = val, move
    elif req.agent_type == "qlearning":
        intended_move = global_q_agent.choose_action(state, force_greedy=True)
    elif req.agent_type == "random":
        intended_move = random.choice(legal_moves)
    else:
        raise HTTPException(status_code=400, detail="Invalid agent_type.")
        
    if intended_move is None:
        intended_move = legal_moves[0]
        
    transitions = global_env.get_transitions(state, intended_move)
    next_state, prob = random.choices(
        transitions,
        weights=[t[1] for t in transitions]
    )[0]
    
    reward_diff = (next_state[2] - next_state[3]) - (max_score - min_score)
    is_slip = (intended_move == 2 and (remaining - next_state[0]) == 1)
    
    return {
        "intended_move": intended_move,
        "actual_move": remaining - next_state[0],
        "is_slip": is_slip,
        "next_state": next_state,
        "reward_diff": reward_diff,
        "is_terminal": global_env.is_terminal(next_state)
    }

@app.post("/api/engine/tree")
def get_tree(req: TreeRequest):
    """Computes and returns the Expectiminimax decision tree from the current state."""
    state = tuple(req.state)
    solver = ExpectiminimaxSolver(global_env, max_depth=req.max_depth, weights=req.weights)
    val, best_move, tree, stats = solver.solve(state, prune=req.prune)
    return {
        "value": val,
        "best_move": best_move,
        "tree": tree,
        "stats": stats
    }

@app.post("/api/engine/train")
def train_qlearning(req: TrainRequest):
    """Trains the Q-learning agent in self-play mode and returns learning curves."""
    train_env = BridgeEnv(
        n_planks=req.n_planks,
        slip_prob=req.slip_prob,
        play_mode=req.play_mode
    )
    
    q_agent = QLearningAgent(train_env, alpha=0.15, gamma=0.95, epsilon=0.3)
    history = q_agent.train(episodes=req.episodes)
    
    global global_q_agent
    if req.n_planks == global_env.n_planks and req.slip_prob == global_env.slip_prob:
        global_q_agent = q_agent
        
    formatted_q = {}
    for key, actions in q_agent.q_table.items():
        remaining, is_max = key
        state_str = f"P{remaining} ({'MAX' if is_max else 'MIN'})"
        formatted_q[state_str] = {f"Move {k}": round(v, 3) for k, v in actions.items()}
        
    return {
        "history": history,
        "q_table": formatted_q
    }

@app.post("/api/engine/evolve")
def evolve_ga(req: EvolveRequest):
    """Runs a single generation cycle of the Genetic Algorithm weight optimization."""
    global global_ga_evolver
    if global_ga_evolver is None or req.reset:
        global_ga_evolver = GeneticHeuristicEvolver(
            global_env,
            pop_size=req.pop_size,
            mutation_rate=req.mutation_rate
        )
        
    stats = global_ga_evolver.evolve_generation()
    return stats

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("index:app", host="127.0.0.1", port=8000, reload=True)
