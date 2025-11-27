import requests
import time

BASE_URL = "http://localhost:8000"

def test_toggling():
    print("1. Starting Scraper (Fast Mode)...")
    res = requests.post(f"{BASE_URL}/start", json={"visual_mode": False})
    print(f"Response: {res.json()}")
    
    time.sleep(2)
    status = requests.get(f"{BASE_URL}/status").json()
    print(f"Status: Running={status['is_running']}, Mode={status['visual_mode']}")
    
    if not status['is_running']:
        print("Scraper stopped (likely due to login failure). Cannot test toggling while stopped.")
        # Even if stopped, we can test if the endpoint works, but the effect is on the running instance.
        return

    print("\n2. Switching to Visual Mode...")
    res = requests.post(f"{BASE_URL}/mode", json={"visual_mode": True})
    print(f"Response: {res.json()}")
    
    time.sleep(5) # Wait for browser launch
    status = requests.get(f"{BASE_URL}/status").json()
    print(f"Status: Running={status['is_running']}, Mode={status['visual_mode']}")
    
    print("\n3. Switching back to Fast Mode...")
    res = requests.post(f"{BASE_URL}/mode", json={"visual_mode": False})
    print(f"Response: {res.json()}")
    
    time.sleep(2)
    status = requests.get(f"{BASE_URL}/status").json()
    print(f"Status: Running={status['is_running']}, Mode={status['visual_mode']}")
    
    print("\n4. Stopping Scraper...")
    requests.post(f"{BASE_URL}/stop")
    print("Stopped.")

if __name__ == "__main__":
    try:
        test_toggling()
    except Exception as e:
        print(f"Test failed: {e}")
