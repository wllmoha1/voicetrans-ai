import urllib.request
import json

def test_server():
    print("Testing live server endpoints...")

    # 1. Test languages
    res = urllib.request.urlopen("http://127.0.0.1:8000/api/languages")
    langs = json.loads(res.read())["languages"]
    print(f"-> Languages returned: {len(langs)}")
    assert len(langs) >= 20, "Should have 20+ languages"

    # 2. Test landing page
    res2 = urllib.request.urlopen("http://127.0.0.1:8000/")
    html = res2.read().decode("utf-8")
    assert "VoiceTrans AI" in html, "Landing page title missing"
    print("-> Landing page HTML: OK")

    # 3. Test Register
    reg_payload = {
        "username": "somali_caller_1",
        "email": "caller1@example.com",
        "password": "Password123!",
        "full_name": "Axmed Nuur",
        "native_language": "so",
        "target_language": "en",
        "preferred_voice": "male"
    }
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/auth/register",
        data=json.dumps(reg_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        res3 = urllib.request.urlopen(req)
        reg_data = json.loads(res3.read())
        token = reg_data["access_token"]
        print(f"-> Register OK: User '{reg_data['user']['username']}' registered.")
    except urllib.error.HTTPError as e:
        if e.code == 400: # Already registered, let's login
            login_req = urllib.request.Request(
                "http://127.0.0.1:8000/api/auth/login",
                data=json.dumps({"login": "somali_caller_1", "password": "Password123!"}).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            res_login = urllib.request.urlopen(login_req)
            login_data = json.loads(res_login.read())
            token = login_data["access_token"]
            print(f"-> Login OK: User logged in.")
        else:
            raise

    # 4. Test Create Room
    req2 = urllib.request.Request(
        "http://127.0.0.1:8000/api/rooms/create",
        data=b"{}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    )
    res4 = urllib.request.urlopen(req2)
    room_data = json.loads(res4.read())
    room_id = room_data["room_id"]
    call_url = room_data["call_url"]
    print(f"-> Create Room OK: Room ID={room_id}, Call URL={call_url}")

    # 5. Test Room Status
    res5 = urllib.request.urlopen(f"http://127.0.0.1:8000/api/rooms/{room_id}/status")
    status_data = json.loads(res5.read())
    assert status_data["exists"] is False or status_data["participant_count"] == 0
    print(f"-> Room Status OK: Initial participants={status_data['participant_count']}")

    print("\n ALL LIVE SERVER ENDPOINT TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_server()
