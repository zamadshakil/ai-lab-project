import random
import math
import json

class BridgeEnv:
    """
    State-Space Environment for 'The Haunted Bridge Crossing'.
    Models the bridge as a 1D hazard board with customizable length,
    traps, treasures, and stochastic actions (step/leap).
    """
    def __init__(self, n_planks=12, slip_prob=0.2, play_mode="normal"):
        if not isinstance(n_planks, int) or n_planks <= 0:
            raise ValueError("n_planks must be a positive integer.")
        if not (0.0 <= slip_prob <= 1.0):
            raise ValueError("slip_prob must be between 0.0 and 1.0 inclusive.")
            
        self.n_planks = n_planks
        self.slip_prob = slip_prob
        self.play_mode = play_mode # "normal" or "misere"
        
        # Configure rewards and hazards
        self.win_bonus = 10
        self.treasure_val = 2
        self.trap_val = -3
        
        # Generate default board config
        # Planks are 1-indexed. Plank 0 is the starting area. Plank n_planks is the goal.
        self.plank_types = ["normal"] * (n_planks + 1)
        self.generate_default_hazards()
        
    def generate_default_hazards(self):
        """
        Populate the bridge with some treasures and traps.
        Ensures a non-trivial decision landscape.
        """
        # Set hazards only if within board index boundaries
        hazards = {
            3: "trap",
            7: "trap",
            4: "treasure",
            8: "treasure",
            5: "slippery",
            10: "slippery"
        }
        for idx, h_type in hazards.items():
            if idx <= self.n_planks:
                self.plank_types[idx] = h_type

    def set_board_config(self, config):
        """Allows direct customization of planks."""
        self.plank_types = config
        self.n_planks = len(config) - 1

    def get_initial_state(self):
        # State: (remaining_planks, is_max_turn, max_score, min_score)
        return (self.n_planks, True, 0, 0)

    def is_terminal(self, state):
        remaining, _, _, _ = state
        return remaining <= 0

    def get_legal_moves(self, state):
        remaining, _, _, _ = state
        if remaining <= 0:
            return []
        elif remaining == 1:
            return [1] # Can only step 1 if only 1 plank remains
        else:
            return [1, 2] # Can step 1 or leap 2

    def get_slip_prob_at_state(self, remaining):
        """Calculate the slip probability based on current plank type."""
        current_plank_idx = self.n_planks - remaining
        if 0 <= current_plank_idx <= self.n_planks:
            p_type = self.plank_types[current_plank_idx]
            if p_type == "slippery":
                return min(1.0, self.slip_prob * 2.5) # Slippery planks make slipping highly likely
        return self.slip_prob

    def transition(self, state, intended_move, actual_move):
        """
        Applies a deterministic step to the state.
        This represents one branch of the chance node.
        """
        remaining, is_max_turn, max_score, min_score = state
        next_remaining = max(0, remaining - actual_move)
        
        # Calculate landing index
        landed_plank_idx = self.n_planks - next_remaining
        
        # Calculate reward/penalty
        reward = 0
        if 0 <= landed_plank_idx <= self.n_planks:
            p_type = self.plank_types[landed_plank_idx]
            if p_type == "treasure":
                reward = self.treasure_val
            elif p_type == "trap":
                reward = self.trap_val
                
        # Update scores
        next_max_score = max_score
        next_min_score = min_score
        if is_max_turn:
            next_max_score += reward
        else:
            next_min_score += reward
            
        # Switch turn
        next_is_max_turn = not is_max_turn
        
        # Check terminal win/loss rewards
        if next_remaining == 0:
            # The player who just moved landed on the final plank.
            # That player is the opponent of next_is_max_turn.
            p1_won = not next_is_max_turn # True if P1 (MAX) made the final move
            
            if self.play_mode == "normal":
                # Normal Play: Last mover wins
                if p1_won:
                    next_max_score += self.win_bonus
                else:
                    next_min_score += self.win_bonus
            else:
                # Misere Play: Last mover loses
                if p1_won:
                    next_max_score -= self.win_bonus
                else:
                    next_min_score -= self.win_bonus
                    
        return (next_remaining, next_is_max_turn, next_max_score, next_min_score)

    def get_transitions(self, state, move):
        """
        Returns list of (next_state, probability) for a given move.
        This defines the Chance Node outcomes.
        """
        remaining, is_max_turn, max_score, min_score = state
        if move == 1:
            # Step 1 is 100% deterministic
            next_s = self.transition(state, 1, 1)
            return [(next_s, 1.0)]
        elif move == 2:
            # Leap 2 has chance of slip
            p_slip = self.get_slip_prob_at_state(remaining)
            s_success = self.transition(state, 2, 2)
            s_slip = self.transition(state, 2, 1)
            
            if p_slip == 0:
                return [(s_success, 1.0)]
            elif p_slip == 1.0:
                return [(s_slip, 1.0)]
            else:
                # 80% success (leap 2), 20% slip (step 1)
                return [(s_success, 1.0 - p_slip), (s_slip, p_slip)]
        return []


class ExpectiminimaxSolver:
    """
    Expectiminimax search solver equipped with Star2 Pruning.
    Uses bounded heuristics to prune stochastic chance branches.
    """
    def __init__(self, env, max_depth=4, weights=None):
        self.env = env
        self.max_depth = max_depth
        # Heuristic weights: [w_max_score, w_min_score, w_progress, w_trap_risk]
        self.weights = weights if weights else [2.0, -2.0, 1.5, -3.0]
        
        # Count actual treasures and traps on board
        n_treasures = sum(1 for p in env.plank_types if p == "treasure")
        n_traps = sum(1 for p in env.plank_types if p == "trap")
        
        score_max = n_treasures * env.treasure_val + env.win_bonus
        score_min = n_traps * env.trap_val - env.win_bonus
        
        w0, w1, w2, w3 = self.weights
        
        # Term 0: w0 * max_score
        t0_max = max(0, w0) * score_max + min(0, w0) * score_min
        t0_min = max(0, w0) * score_min + min(0, w0) * score_max
        
        # Term 1: w1 * min_score
        t1_max = max(0, w1) * score_max + min(0, w1) * score_min
        t1_min = max(0, w1) * score_min + min(0, w1) * score_max
        
        # Term 2: w2 * progress
        t2_max = max(0, w2) * env.n_planks + min(0, w2) * 0
        t2_min = max(0, w2) * 0 + min(0, w2) * env.n_planks
        
        # Term 3: w3 * trap_risk
        t3_max = max(0, w3) * 1.5 + min(0, w3) * 0
        t3_min = max(0, w3) * 0 + min(0, w3) * 1.5
        
        self.V_max = t0_max + t1_max + t2_max + t3_max
        self.V_min = t0_min + t1_min + t2_min + t3_min
        
        # Statistics
        self.nodes_evaluated = 0
        self.nodes_pruned = 0

    def heuristic(self, state):
        """
        First-principles heuristic function representing the utility of non-terminal states.
        """
        remaining, is_max_turn, max_score, min_score = state
        progress = self.env.n_planks - remaining
        
        # Calculate trap risk ahead
        trap_risk = 0
        current_plank_idx = self.env.n_planks - remaining
        # Look 1 and 2 steps ahead
        for step in [1, 2]:
            next_idx = current_plank_idx + step
            if next_idx <= self.env.n_planks:
                if self.env.plank_types[next_idx] == "trap":
                    trap_risk += 1.0 / step # Traps closer have higher risk weight
                elif self.env.plank_types[next_idx] == "slippery":
                    trap_risk += 0.5 / step
                    
        # Heuristic evaluation from MAX's perspective
        h_val = (self.weights[0] * max_score + 
                 self.weights[1] * min_score + 
                 self.weights[2] * progress + 
                 self.weights[3] * trap_risk)
        return h_val

    def get_static_utility(self, state):
        """Return the exact score differential at terminal states."""
        _, _, max_score, min_score = state
        return self.weights[0] * max_score + self.weights[1] * min_score

    def solve(self, state, prune=True):
        """Helper to call solver and return statistics."""
        self.nodes_evaluated = 0
        self.nodes_pruned = 0
        val, move, tree = self._expectiminimax(state, self.max_depth, -math.inf, math.inf, prune)
        return val, move, tree, {
            "evaluated": self.nodes_evaluated,
            "pruned": self.nodes_pruned
        }

    def _expectiminimax(self, state, depth, alpha, beta, prune):
        self.nodes_evaluated += 1
        remaining, is_max_turn, max_score, min_score = state
        
        # Build node meta for frontend tree rendering
        node_name = f"P{remaining}"
        node_type = "MAX" if is_max_turn else "MIN"
        
        if self.env.is_terminal(state):
            val = self.get_static_utility(state)
            return val, None, {
                "name": node_name,
                "type": "TERMINAL",
                "value": round(val, 2),
                "state": state,
                "children": []
            }
            
        if depth == 0:
            val = self.heuristic(state)
            return val, None, {
                "name": node_name,
                "type": "LEAF",
                "value": round(val, 2),
                "state": state,
                "children": []
            }
            
        tree_children = []
        best_move = None
        
        if is_max_turn:
            best_val = -math.inf
            for move in self.env.get_legal_moves(state):
                # Chance node evaluation
                chance_val, chance_tree = self._evaluate_chance_node(state, move, depth - 1, alpha, beta, True, prune)
                tree_children.append(chance_tree)
                
                if chance_val > best_val:
                    best_val = chance_val
                    best_move = move
                if prune:
                    alpha = max(alpha, best_val)
                    if beta <= alpha:
                        self.nodes_pruned += 1 # Pruned remaining moves
                        break
            return best_val, best_move, {
                "name": node_name,
                "type": node_type,
                "value": round(best_val, 2),
                "state": state,
                "children": tree_children,
                "best_move": best_move
            }
        else:
            best_val = math.inf
            for move in self.env.get_legal_moves(state):
                chance_val, chance_tree = self._evaluate_chance_node(state, move, depth - 1, alpha, beta, False, prune)
                tree_children.append(chance_tree)
                
                if chance_val < best_val:
                    best_val = chance_val
                    best_move = move
                if prune:
                    beta = min(beta, best_val)
                    if beta <= alpha:
                        self.nodes_pruned += 1
                        break
            return best_val, best_move, {
                "name": node_name,
                "type": node_type,
                "value": round(best_val, 2),
                "state": state,
                "children": tree_children,
                "best_move": best_move
            }

    def _evaluate_chance_node(self, state, move, depth, alpha, beta, parent_is_max, prune):
        """
        Evaluates a Chance node, applying Star2 search window bounding.
        """
        transitions = self.env.get_transitions(state, move)
        expected_val = 0.0
        
        # Build chance node tree representation
        chance_children = []
        
        # Variables for Star2 pruning
        s_eval = 0.0 # Sum of evaluated probabilities * values
        p_eval = 0.0 # Sum of evaluated probabilities
        
        for idx, (next_state, prob) in enumerate(transitions):
            # Compute Star2 bounding search windows for the remaining child nodes
            if prune:
                p_rem = 1.0 - (p_eval + prob) # Probabilities of remaining children
                if parent_is_max:
                    # MAX node parent: set new alpha_child
                    alpha_c = (alpha - s_eval - p_rem * self.V_max) / prob
                    alpha_c = max(self.V_min, alpha_c)
                    beta_c = beta
                else:
                    # MIN node parent: set new beta_child
                    alpha_c = alpha
                    beta_c = (beta - s_eval - p_rem * self.V_min) / prob
                    beta_c = min(self.V_max, beta_c)
            else:
                alpha_c, beta_c = -math.inf, math.inf
                
            # If search window is collapsed, prune immediately!
            if prune and alpha_c >= beta_c:
                self.nodes_pruned += (len(transitions) - idx)
                # Render pruned indicator in tree
                chance_children.append({
                    "name": f"Pruned_S{self.env.n_planks - next_state[0]}",
                    "type": "PRUNED",
                    "value": None,
                    "probability": prob,
                    "children": []
                })
                # Add bounding fallback to expected sum
                if parent_is_max:
                    expected_val += prob * self.V_min # Conservative estimate
                else:
                    expected_val += prob * self.V_max
                continue
                
            # Recursively evaluate the child node (which belongs to the opposing player)
            val_child, _, tree_child = self._expectiminimax(next_state, depth, alpha_c, beta_c, prune)
            chance_children.append(tree_child)
            tree_child["probability"] = prob # Attach probability to link
            
            expected_val += prob * val_child
            s_eval += prob * val_child
            p_eval += prob
            
        return expected_val, {
            "name": f"Chance_M{move}",
            "type": "CHANCE",
            "value": round(expected_val, 2),
            "children": chance_children
        }


class QLearningAgent:
    """
    Model-Free Tabular Q-Learning Agent.
    Learns state utilities under hazard environments via temporal-difference learning.
    State representation: (remaining_planks, is_max_turn)
    We omit scores in tabular representation to keep the state space compact (12x2 = 24 states).
    """
    def __init__(self, env, alpha=0.1, gamma=0.9, epsilon=0.1):
        self.env = env
        self.alpha = alpha # Learning rate
        self.gamma = gamma # Discount factor
        self.epsilon = epsilon # Exploration rate
        self.q_table = {} # Maps state -> {move: value}
        
    def get_state_key(self, state):
        remaining, is_max_turn, _, _ = state
        return (remaining, is_max_turn)

    def get_q_values(self, key):
        if key not in self.q_table:
            # Initialize legal actions with zero
            remaining, is_max_turn = key
            moves = [1] if remaining == 1 else [1, 2]
            self.q_table[key] = {m: 0.0 for m in moves}
        return self.q_table[key]

    def choose_action(self, state, force_greedy=False):
        remaining, _, _, _ = state
        if remaining == 0:
            return None
            
        key = self.get_state_key(state)
        q_vals = self.get_q_values(key)
        legal_moves = list(q_vals.keys())
        
        # Epsilon-greedy selection
        if not force_greedy and random.random() < self.epsilon:
            return random.choice(legal_moves)
            
        # Select best action based on active turn (MAX wants highest, MIN wants lowest)
        _, is_max_turn = key
        if is_max_turn:
            best_val = -math.inf
            best_moves = []
            for move, val in q_vals.items():
                if val > best_val:
                    best_val = val
                    best_moves = [move]
                elif val == best_val:
                    best_moves.append(move)
            return random.choice(best_moves)
        else:
            # MIN wants to minimize utility for MAX
            best_val = math.inf
            best_moves = []
            for move, val in q_vals.items():
                if val < best_val:
                    best_val = val
                    best_moves = [move]
                elif val == best_val:
                    best_moves.append(move)
            return random.choice(best_moves)

    def update(self, state, action, reward, next_state):
        key = self.get_state_key(state)
        next_key = self.get_state_key(next_state)
        
        q_vals = self.get_q_values(key)
        
        # Compute dynamic temporal difference target
        if self.env.is_terminal(next_state):
            target = reward
        else:
            next_q_vals = self.get_q_values(next_key)
            _, is_max_next = next_key
            # Expect next agent to play optimally
            if is_max_next:
                target = reward + self.gamma * max(next_q_vals.values())
            else:
                target = reward + self.gamma * min(next_q_vals.values())
                
        # TD update
        q_vals[action] += self.alpha * (target - q_vals[action])

    def train(self, episodes=10000):
        """Train the agent by self-play."""
        history = []
        for ep in range(episodes):
            state = self.env.get_initial_state()
            total_td_error = 0.0
            steps = 0
            
            while not self.env.is_terminal(state):
                remaining, is_max, max_s, min_s = state
                action = self.choose_action(state)
                
                # Sample stochastic outcome from transition model
                transitions = self.env.get_transitions(state, action)
                next_state, prob = random.choices(
                    transitions,
                    weights=[t[1] for t in transitions]
                )[0]
                
                # Define reward step differential (treasure/trap collection)
                # Win/loss triggers final utility difference
                r_diff = (next_state[2] - next_state[3]) - (max_s - min_s)
                    
                # Update Q value
                old_q = self.get_q_values(self.get_state_key(state))[action]
                self.update(state, action, r_diff, next_state)
                new_q = self.get_q_values(self.get_state_key(state))[action]
                total_td_error += abs(new_q - old_q)
                
                state = next_state
                steps += 1
                
            # Decay epsilon inside the training loop to guide exploration
            self.epsilon = max(0.01, self.epsilon * 0.9995)
            
            if ep % 500 == 0:
                history.append({
                    "episode": ep,
                    "avg_td_error": total_td_error / max(1, steps)
                })
                
        return history


class GeneticHeuristicEvolver:
    """
    Genetic Algorithm Engine to optimize Expectiminimax heuristic weights.
    Chromosomes: List of 4 floating point weights:
    [w_max_score, w_min_score, w_progress, w_trap_risk]
    """
    def __init__(self, env, pop_size=10, mutation_rate=0.15):
        self.env = env
        self.pop_size = pop_size
        self.mutation_rate = mutation_rate
        self.population = self.initialize_population()
        self.generation_count = 0

    def initialize_population(self):
        pop = []
        for _ in range(self.pop_size):
            # Randomized weights matching our boundaries
            chrome = [
                random.uniform(0.5, 4.0),   # max_score weight (positive)
                random.uniform(-4.0, -0.5), # min_score weight (negative)
                random.uniform(0.5, 3.0),   # progress weight (positive)
                random.uniform(-4.0, -0.5)  # trap_risk weight (negative)
            ]
            pop.append(chrome)
        return pop

    def run_tournament(self, weights_a, weights_b, games=10):
        """Evaluate two heuristic sets by playing matches against each other."""
        wins_a = 0
        wins_b = 0
        
        solver_a = ExpectiminimaxSolver(self.env, max_depth=3, weights=weights_a)
        solver_b = ExpectiminimaxSolver(self.env, max_depth=3, weights=weights_b)
        
        for g in range(games):
            state = self.env.get_initial_state()
            # Alternating starting turns
            turn_flag = (g % 2 == 0)
            
            while not self.env.is_terminal(state):
                remaining, is_max_turn, _, _ = state
                
                # Match solver turns
                if is_max_turn:
                    # Player 1 (MAX)
                    if turn_flag:
                        _, move, _, _ = solver_a.solve(state, prune=True)
                    else:
                        _, move, _, _ = solver_b.solve(state, prune=True)
                else:
                    # Player 2 (MIN)
                    if turn_flag:
                        _, move, _, _ = solver_b.solve(state, prune=True)
                    else:
                        _, move, _, _ = solver_a.solve(state, prune=True)
                        
                # Transition env
                transitions = self.env.get_transitions(state, move)
                state = random.choices(
                    [t[0] for t in transitions],
                    weights=[t[1] for t in transitions]
                )[0]
                
            # Score results
            _, _, final_max, final_min = state
            if final_max > final_min:
                if turn_flag: wins_a += 1
                else: wins_b += 1
            elif final_min > final_max:
                if turn_flag: wins_b += 1
                else: wins_a += 1
                
        return wins_a, wins_b

    def evaluate_fitness_all(self):
        """Run round-robin tournament to count scores for population fitness."""
        fitness = [0.0] * self.pop_size
        
        # Everyone plays everyone
        for i in range(self.pop_size):
            for j in range(i + 1, self.pop_size):
                wins_i, wins_j = self.run_tournament(self.population[i], self.population[j], games=4)
                fitness[i] += wins_i
                fitness[j] += wins_j
                
        return fitness

    def select_parent(self, fitness):
        """2-way Tournament Selection."""
        i1 = random.randint(0, self.pop_size - 1)
        i2 = random.randint(0, self.pop_size - 1)
        if fitness[i1] >= fitness[i2]:
            return self.population[i1]
        return self.population[i2]

    def crossover(self, parent_a, parent_b):
        """Single-point crossover for float array."""
        idx = random.randint(1, 3)
        child = parent_a[:idx] + parent_b[idx:]
        return child

    def mutate(self, chromosome):
        """Mutation operator adding minor Gaussian shifts."""
        mutated = list(chromosome)
        for i in range(4):
            if random.random() < self.mutation_rate:
                shift = random.gauss(0, 0.5)
                # Keep polarity rules
                if i in [0, 2]: # positive weights
                    mutated[i] = max(0.1, mutated[i] + shift)
                else: # negative weights
                    mutated[i] = min(-0.1, mutated[i] + shift)
        return mutated

    def evolve_generation(self):
        """Executes one full cycle of GA evolution."""
        fitness = self.evaluate_fitness_all()
        
        # Elitism: Keep the best two chromosomes
        best_indices = sorted(range(self.pop_size), key=lambda i: fitness[i], reverse=True)
        new_pop = [self.population[best_indices[0]], self.population[best_indices[1]]]
        
        # Fill rest of population with offspring
        while len(new_pop) < self.pop_size:
            p_a = self.select_parent(fitness)
            p_b = self.select_parent(fitness)
            child = self.crossover(p_a, p_b)
            child = self.mutate(child)
            new_pop.append(child)
            
        self.population = new_pop
        self.generation_count += 1
        
        # Return summary
        best_fit = fitness[best_indices[0]]
        avg_fit = sum(fitness) / self.pop_size
        return {
            "generation": self.generation_count,
            "best_fitness": best_fit,
            "avg_fitness": avg_fit,
            "best_weights": new_pop[0]
        }
