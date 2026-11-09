"""Two connected terminal puzzles for The Lost Temple.

Run: python3 temple_puzzles.py
Only built-in Python features are used; no imports are needed.
"""


def puzzle1():
    """Return True on success, or False when the player enters q."""
    print("\n=== Puzzle 1: The Guardian's Riddle ===")
    print("Leo meets a stone guardian inside the lost temple.")
    print("Guardian: What has keys but cannot open locks?")
    print("Enter your answer, 'hint' for a clue, or 'q' to leave.")

    while True:
        answer = input("Your answer: ").strip().lower()

        if answer == "q":
            print("Leo leaves the trial for now.")
            return False
        elif answer == "hint":
            print("Hint: These keys make music.")
        elif answer in ["piano", "a piano", "the piano", "钢琴", "鋼琴"]:
            print("Correct! A piano has musical keys, not door keys.")
            return True
        elif answer in ["keyboard", "a keyboard", "the keyboard"]:
            print("Correct! A keyboard also has keys that cannot open locks.")
            return True
        elif answer == "":
            print("Please type an answer, 'hint', or 'q'.")
        else:
            print("That does not fit the riddle. Try again!")


def puzzle2():
    """Return True on success, or False when the player enters q."""
    print("\n=== Puzzle 2: The Three Doors ===")
    print("Leo enters a chamber containing doors A, B and C.")
    print("The treasure is behind exactly ONE door.")
    print("Exactly ONE of the following three statements is true:")
    print("Door A: The treasure is behind Door B.")
    print("Door B: The treasure is not behind Door B.")
    print("Door C: The treasure is not behind Door A.")
    print("Choose A/B/C, enter 'hint' for a clue, or 'q' to leave.")

    while True:
        choice = input("Choose a door: ").strip().upper()

        if choice == "Q":
            print("Leo leaves the chamber for now.")
            return False
        elif choice == "HINT":
            print("Hint: Statements A and B are opposites.")
            print("One of them must be true. What must statement C be?")
        elif choice == "A":
            print("Correct! Leo opens Door A and finds the ancient treasure.")
            print("Statement A is false, B is true, and C is false.")
            return True
        elif choice == "B" or choice == "C":
            print("That would make TWO statements true. Try again!")
        else:
            print("Please enter A, B, C, 'hint', or 'q'.")


def create_puzzle_state():
    """Create this module's example state, once per new game."""
    return {
        "inventory": [],
        "exp": 0,
        "riddle_solved": False,
        "doors_solved": False
    }


def play_temple_puzzles(state):
    """Update state in place; return True only if both trials are complete.

    Reuse the same state when the player revisits the puzzle location.
    This function does not move the player or modify the maze.
    """
    if state["doors_solved"]:
        print("Both trials are already complete. No extra reward is given.")
        return True

    if not state["riddle_solved"]:
        if not puzzle1():
            return False

        state["riddle_solved"] = True
        if "Golden Key" not in state["inventory"]:
            state["inventory"].append("Golden Key")
        state["exp"] = state["exp"] + 50
        print("Reward: Golden Key and 50 EXP.")

    # Keep the key as a quest item, so the player can return after quitting.
    if "Golden Key" not in state["inventory"]:
        print("The chamber is locked. You need the guardian's Golden Key.")
        return False

    print("\nLeo uses the Golden Key to open the chamber entrance.")
    if not puzzle2():
        return False

    state["doors_solved"] = True
    if "Ancient Treasure" not in state["inventory"]:
        state["inventory"].append("Ancient Treasure")
    state["exp"] = state["exp"] + 50
    print("Reward: Ancient Treasure and 50 EXP.")
    return True


def main():
    state = create_puzzle_state()
    print("Welcome to The Lost Temple!")

    while True:
        completed = play_temple_puzzles(state)
        print("\nEXP:", state["exp"])
        print("Inventory:", state["inventory"])

        if completed:
            print("Leo has passed both trials. Adventure complete!")
            break

        answer = input("Return to the trials? (y/n): ").strip().lower()
        while answer != "y" and answer != "n":
            answer = input("Please enter y or n: ").strip().lower()
        if answer == "n":
            print("Thanks for playing!")
            break


if __name__ == "__main__":
    main()
