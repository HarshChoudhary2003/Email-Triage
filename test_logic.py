import json
from env import EmailTriageEnv, Action

def test_logic():
    print("Testing Task 1: Binary Triage")
    env = EmailTriageEnv(task_id="task_1_binary_triage")
    obs = env.reset()
    
    # Correct action for urgent email (e001)
    action = Action(binary_label="actionable")
    obs, reward, done, info = env.step(action)
    print(f"Step 1 Reward: {reward.step_reward} (Expected: 1.0)")
    assert reward.step_reward == 1.0
    
    # Incorrect action for low priority email
    # Next email in 'easy' set is e007 (low)
    action = Action(binary_label="actionable")
    obs, reward, done, info = env.step(action)
    print(f"Step 2 Reward: {reward.step_reward} (Expected: < 1.0)")
    assert reward.step_reward < 1.0

    print("\nTesting Task 2: Priority Labeling")
    env = EmailTriageEnv(task_id="task_2_priority_labeling")
    env.reset()
    # e002 is urgent
    action = Action(priority_label="high", requires_reply=True) # adjacent
    obs, reward, done, info = env.step(action)
    print(f"Step 1 Reward: {reward.step_reward} (Expected: partial credit for 'high' skip from 'urgent')")
    assert 0.0 < reward.step_reward < 1.0

    print("\nAll logic tests passed!")

if __name__ == "__main__":
    test_logic()
