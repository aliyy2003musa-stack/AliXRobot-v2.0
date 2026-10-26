# test_omniSim.py
from visualization.geometry import create_advanced_path

print("--- RUNNING OLIVER'S TESTS ---\n")

# TEST 1: The "Typo" Bug (Finding 2)
print("TEST 1: Sending a misspelled profile name ('S-Curve' instead of 's_curve')...")
try:
    # This should FAIL and raise an error
    create_advanced_path([0,0], [1,1], samples=10, profile="S-Curve")
    print("❌ FAIL: The app accepted the typo silently! (Old behavior)")
except ValueError as e:
    print(f"✅ PASS: The app caught the typo and said: '{e}'")

print("\n" + "-"*40 + "\n")

# TEST 2: The "1 Step" Bug (Finding 3)
print("TEST 2: Asking for only 1 step (impossible to animate)...")
try:
    # This should FAIL and raise an error
    create_advanced_path([0,0], [1,1], samples=1, profile="linear")
    print("❌ FAIL: The app returned a single point silently! (Old behavior)")
except ValueError as e:
    print(f"✅ PASS: The app caught the bad step count and said: '{e}'")

print("\n" + "-"*40 + "\n")

# TEST 3: The "0 Steps" Bug (Finding 3)
print("TEST 3: Asking for 0 steps...")
try:
    # This should FAIL and raise an error
    create_advanced_path([0,0], [1,1], samples=0, profile="linear")
    print("❌ FAIL: The app returned an empty list silently! (Old behavior)")
except ValueError as e:
    print(f"✅ PASS: The app caught the zero steps and said: '{e}'")

print("\n" + "-"*40 + "\n")

# TEST 4: The "Happy Path" (Making sure it still works!)
print("TEST 4: Sending perfect data...")
try:
    path = create_advanced_path([0,0,0], [10,10,10], samples=5, profile="smoothstep")
    if len(path) == 5:
        print(f"✅ PASS: The app successfully generated {len(path)} points!")
    else:
        print(f"❌ FAIL: Expected 5 points, got {len(path)}")
except Exception as e:
    print(f" FAIL: The app crashed on good data! Error: {e}")