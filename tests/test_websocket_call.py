import asyncio
import json
import websockets

async def test_websocket_call():
    print("Testing WebSocket Call Flow with Two Participants...")
    room_id = "test_live_room_99"

    uri = f"ws://127.0.0.1:8000/ws/call/{room_id}"

    # Participant A joins
    async with websockets.connect(uri) as ws_a:
        msg_a = await ws_a.recv()
        data_a = json.loads(msg_a)
        print("-> Caller A joined event:", data_a.get("type"))
        assert data_a["type"] == "peer_joined"

        # Participant B joins
        async with websockets.connect(uri) as ws_b:
            msg_b = await ws_b.recv()
            data_b = json.loads(msg_b)
            print("-> Caller B joined event:", data_b.get("type"))
            assert data_b["type"] == "peer_joined"

            # Check that Caller A received notification that B joined
            msg_a2 = await ws_a.recv()
            data_a2 = json.loads(msg_a2)
            print("-> Caller A received peer_joined for B:", data_a2.get("type"))
            assert data_a2["type"] == "peer_joined"

            # Caller A sends speaking state
            await ws_a.send(json.dumps({"type": "speaking_state", "is_speaking": True}))
            msg_b_speaking = await ws_b.recv()
            data_speaking = json.loads(msg_b_speaking)
            print("-> Caller B received peer_speaking event:", data_speaking.get("type"))
            assert data_speaking["type"] == "peer_speaking"
            assert data_speaking["is_speaking"] is True

            # Caller A updates language (mid-call)
            await ws_a.send(json.dumps({
                "type": "update_languages",
                "speaking_language": "so",
                "listening_language": "ar",
                "voice_gender": "female"
            }))
            msg_lang = await ws_b.recv()
            data_lang = json.loads(msg_lang)
            print("-> Caller B received languages_updated event:", data_lang.get("type"))
            assert data_lang["type"] == "languages_updated"
            assert data_lang["peer"]["listening_language"] == "ar"

    print("\n ALL WEBSOCKET DUAL-CALLER TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_websocket_call())
