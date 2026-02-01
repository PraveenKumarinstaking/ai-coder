import urllib.request
import urllib.error
import json

BASE_URL = "http://localhost:8000/api"

def test_login_flow():
    print("Testing Login Flow...")
    
    # 1. Login
    login_data = json.dumps({
        "email": "admin@erp.com",
        "password": "admin123"
    }).encode('utf-8')
    
    req = urllib.request.Request(
        f"{BASE_URL}/users/login",
        data=login_data,
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            print("LOGIN SUCCESS")
            data = json.loads(response.read().decode('utf-8'))
            token = data.get("access_token")
            print(f"Token received: {token[:20]}...")
            
            # 2. Use Token
            user_req = urllib.request.Request(
                f"{BASE_URL}/users/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            try:
                with urllib.request.urlopen(user_req) as user_response:
                    print("TOKEN VALIDATION SUCCESS")
                    user_data = json.loads(user_response.read().decode('utf-8'))
                    print(f"User: {user_data.get('email')}")
            except urllib.error.HTTPError as e:
                print(f"TOKEN VALIDATION FAILED: {e.code}")
                print(e.read().decode('utf-8'))
                
    except urllib.error.HTTPError as e:
        print(f"LOGIN FAILED: {e.code}")
        print(e.read().decode('utf-8'))
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    test_login_flow()
