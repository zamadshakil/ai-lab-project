import unittest
import math
import sys
import os

# Include parent directory in search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import BridgeEnv, ExpectiminimaxSolver, QLearningAgent, GeneticHeuristicEvolver

class TestEngine(unittest.TestCase):
    def setUp(self):
        # Create standard small 6-plank environment for fast exact checks
        self.env = BridgeEnv(n_planks=6, slip_prob=0.2, play_mode="normal")

    def test_environment_initialization(self):
        state = self.env.get_initial_state()
        self.assertEqual(state, (6, True, 0, 0))
        self.assertFalse(self.env.is_terminal(state))
        self.assertEqual(self.env.get_legal_moves(state), [1, 2])

    def test_transitions_deterministic_step(self):
        state = (6, True, 0, 0)
        # Step 1 is deterministic
        transitions = self.env.get_transitions(state, move=1)
        self.assertEqual(len(transitions), 1)
        next_s, prob = transitions[0]
        self.assertEqual(prob, 1.0)
        # Verify landing on plank 1 (6-5 = 1)
        # In default board, plank 1 is normal, so no score adjustments
        self.assertEqual(next_s, (5, False, 0, 0))

    def test_transitions_stochastic_leap(self):
        state = (6, True, 0, 0)
        # Leap 2 is stochastic (80% success to 4, 20% slip to 5)
        transitions = self.env.get_transitions(state, move=2)
        self.assertEqual(len(transitions), 2)
        
        # Check outcomes
        states = [t[0] for t in transitions]
        probs = [t[1] for t in transitions]
        
        self.assertIn((4, False, 0, 0), states)
        self.assertIn((5, False, 0, 0), states)
        self.assertEqual(probs, [0.8, 0.2])

    def test_expectiminimax_solver_no_prune(self):
        solver = ExpectiminimaxSolver(self.env, max_depth=3)
        state = self.env.get_initial_state()
        val, move, tree, stats = solver.solve(state, prune=False)
        
        # Verify node count is higher when pruning is disabled
        self.assertTrue(stats["evaluated"] > 0)
        self.assertEqual(stats["pruned"], 0)
        self.assertIn(move, [1, 2])

    def test_expectiminimax_solver_with_prune(self):
        solver = ExpectiminimaxSolver(self.env, max_depth=4)
        state = self.env.get_initial_state()
        
        # Run without pruning
        _, _, _, stats_no_prune = solver.solve(state, prune=False)
        # Run with pruning
        _, _, _, stats_prune = solver.solve(state, prune=True)
        
        # Verify Star2 pruning evaluates fewer nodes and cuts branches
        self.assertTrue(stats_prune["evaluated"] < stats_no_prune["evaluated"])
        self.assertTrue(stats_prune["pruned"] > 0)

    def test_q_learning_training(self):
        agent = QLearningAgent(self.env, alpha=0.1, gamma=0.9, epsilon=0.2)
        history = agent.train(episodes=50)
        self.assertTrue(len(history) > 0)
        
        # Choose action greedily after training
        state = self.env.get_initial_state()
        action = agent.choose_action(state, force_greedy=True)
        self.assertIn(action, [1, 2])

    def test_genetic_algorithm_step(self):
        evolver = GeneticHeuristicEvolver(self.env, pop_size=4, mutation_rate=0.2)
        res = evolver.evolve_generation()
        self.assertEqual(res["generation"], 1)
        self.assertEqual(len(res["best_weights"]), 4)

if __name__ == "__main__":
    unittest.main()
