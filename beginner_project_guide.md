# A Simple Guide to Specter's Bridge: How Our AI Chasm Game Works!

Welcome to your beginner-friendly guide! If you are preparing to present this project or want to explain it to someone who doesn't code, this document is for you. We will explain everything using simple analogies.

---

## 1. What is "Specter's Bridge"? (The Game)

Imagine a long wooden bridge spanning a dark, foggy chasm. The bridge is made of a line of wooden planks (for example, 12 planks). 

Two players are playing a turn-based board game on this bridge:
1.  **The Traveler (MAX)**: This player starts at the beginning of the bridge and wants to cross it. They want to collect **treasures** (+2 points) and reach the end safely to get a **win bonus** (+10 points).
2.  **The Specter (MIN)**: This is the opponent. The Specter's goal is to make life hard for the Traveler. They want to lure the Traveler into **traps** (-3 points) and make them lose.

### The Rules of Movement
On your turn, you can choose one of two ways to move:
*   **Step 1**: Walk forward safely by exactly **1 plank**. This is $100\%$ safe—no slipping!
*   **Leap 2**: Try to jump forward by **2 planks**. This is faster, but because the bridge is slippery, there is a chance you will **slip** and only advance **1 plank**! If you land on a *slippery plank*, you are almost guaranteed to slip.

The game ends when someone lands on the very last plank.

---

## 2. The Three AI "Brains" We Built

To play this game, we built three different types of Artificial Intelligence. Each has a completely different way of "thinking."

---

### Brain #1: Expectiminimax & Star2 Pruning (The "Chess Player")
This AI plays by **thinking ahead**. It builds a virtual map of all future moves (a "decision tree") and calculates what might happen.

*   **How it thinks**:
    *   "If I Step 1, I will land here. But what will my opponent do next?"
    *   "If I Leap 2, there is an $80\%$ chance I succeed and land on a treasure, and a $20\%$ chance I slip and land on a trap. Let's calculate the average (expected) value."
*   **What is Star2 Pruning?**
    *   Thinking ahead can take a lot of computer memory if the bridge is long.
    *   **Pruning** means cutting off branches of the tree that are useless to look at. For example, if a player already found a move that guarantees them a score of $+8$, they don't need to spend time calculating a high-risk move that, at best, gives them $+3$.
    *   **Star2** is a smart mathematical rule that calculates the absolute best and worst possible outcomes of random events (like slipping) and cuts them off early if they can't possibly beat our current best option.

---

### Brain #2: Q-Learning (The "Video Game Player")
This AI does not plan ahead or draw a map. Instead, it learns by **trial and error**—just like a human playing a video game for the first time.

*   **How it learns**:
    *   It starts knowing nothing. It makes completely random moves.
    *   If it lands on a treasure, it gets a "cookie" (a positive reward).
    *   If it falls into a trap, it gets a "shock" (a penalty).
    *   It plays the game **15,000 times** in self-play (playing against itself).
    *   It writes down the scores in a notebook called a **Q-Table**. Over time, it learns: *"In state X, Leap 2 is better because Step 1 usually leads to a trap."*
*   **What are Exploratory Starts?**
    *   If the AI always starts from the very beginning of the bridge, it might always play the same way and never learn how to recover if it slips in the middle.
    *   To fix this, we start $30\%$ of the practice matches from random planks in the middle of the bridge. This forces the AI to learn how to play from every single spot, making it a master player.

---

### Brain #3: Genetic Algorithm (The "Darwinian Breeder")
How does the "Chess Player" (Brain #1) know if a board position is good? It uses a math formula (called a **Heuristic**) that weights different things:
*   *How much gold is nearby?*
*   *How close am I to the end?*
*   *Are there traps ahead?*

But how do we know what weights to use? We let a **Genetic Algorithm** "evolve" them!

*   **How it works**:
    1.  **Chromosomes**: We create a population of 10 random sets of weights. You can think of each set as an animal with different DNA.
    2.  **Tournament**: We let these sets play matches against each other. The ones that win get a higher **fitness score**.
    3.  **Survival of the Fittest**: We keep the best players and throw away the losers.
    4.  **Crossover (Mating)**: We mix the DNA (weights) of two winning parents to create a "child" set of weights.
    5.  **Mutation**: We add a tiny random change (a mutation) to the child's DNA so it can discover new strategies.
    *   We run this for several generations until we get the ultimate set of weights!

---

## 3. Quick Summary of What We Proved!

1.  **Star2 Pruning works**: It reduced the computer's calculations by **$50\%$**, making the AI run twice as fast while making the exact same moves.
2.  **Q-learning matches planning**: After playing against itself 15,000 times, the Q-learning agent learned to make the **exact same optimal decisions** as the planning tree search ($100\%$ policy convergence).
3.  **Clean modern design**: The website has a clean Notion/Apple light layout that adapts perfectly to desktop, tablet, and mobile screens.
