def puzzle1():
    clear_screen()

    print("=== The Guardian's Riddle ===")
    print("Answer correctly to claim the key!")
    print()
    print("What has keys but cannot open locks?")
    print()
    print("A. A clock")
    print("B. A piano")
    print("C. A book")
    print("D. A candle")
    print()
    print("Press A, B, C or D.")

    flush_input()

    while True:
        answer = wait_for_key({"A", "B", "C", "D"})

        if answer == "B":
            print("Correct! You obtained the key.")
            print("Press Enter to return to the maze.")
            wait_for_key({"\r", "\n"})
            return True
        else:
            print("Wrong answer! Try again.")

def puzzle2():
    clear_screen()

    print("=== The Three Doors ===")
    print("The key is hidden behind exactly one door.")
    print("Exactly ONE of these statements is true.")
    print()
    print("Door A: The key is behind Door B.")
    print("Door B: The key is NOT behind Door B.")
    print("Door C: The key is NOT behind Door A.")
    print()
    print("Which door hides the key?")
    print("Press A, B or C.")

    flush_input()

    while True:
        answer = wait_for_key({"A", "B", "C"})

        if answer == "A":
            print("Correct! Door A opens and reveals the key.")
            print("Press Enter to return to the maze.")
            wait_for_key({"\r", "\n"})
            return True
        else:
            print("Wrong door! Think again.")

def puzzle3():
    clear_screen()
    flush_input()

    with puzzle_input_mode():
        print("=== The Sphinx's Riddle ===")
        print("Deep in the forest, a sphinx guards an ancient key.")
        print("Sphinx: Solve my riddle to claim the key.")
        print()
        print("What creature walks on four legs in the morning,")
        print("two at noon, and three in the evening?")
        print()
        print("Type your answer in English, then press Enter.")

        while True:
            answer = input("Your answer: ").strip().lower()

            if answer in [
                "human", "a human", "humans",
                "person", "a person",
                "man", "a man", "human being", "a human being"
            ]:
                print("Correct! The answer is a human.")
                print("A baby crawls on hands and knees.")
                print("An adult walks on two legs.")
                print("An elderly person may use a walking stick.")
                print()
                print("The sphinx allows you to take the key.")

                input("Press Enter to return to the maze...")
                return True

            else:
                print("Wrong answer! Try again.")
                print("Hint: Think about the stages of life,")
                print("not the time of day.")
