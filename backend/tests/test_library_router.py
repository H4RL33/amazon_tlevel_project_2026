from unittest.mock import patch

from httpx import AsyncClient


async def test_create_and_list_chat_sessions(authenticated_client: AsyncClient) -> None:
    create_resp = await authenticated_client.post("/library/chats")
    assert create_resp.status_code == 200
    session_id = create_resp.json()["id"]

    list_resp = await authenticated_client.get("/library/chats")
    assert list_resp.status_code == 200
    assert any(s["id"] == session_id for s in list_resp.json())


async def test_get_chat_session_404_for_nonexistent(authenticated_client: AsyncClient) -> None:
    resp = await authenticated_client.get("/library/chats/999999")
    assert resp.status_code == 404


async def test_post_chat_message_streams_sse_and_persists(authenticated_client: AsyncClient) -> None:
    create_resp = await authenticated_client.post("/library/chats")
    session_id = create_resp.json()["id"]

    def fake_event_stream():
        yield {"chunk": {"bytes": b'{"contentBlockDelta": {"delta": {"text": "Hi "}}}'}}
        yield {"chunk": {"bytes": b'{"contentBlockDelta": {"delta": {"text": "there."}}}'}}

    with (
        patch("app.services.chat_service.embed_text", return_value=[0.1] * 1024),
        patch("app.services.chat_service._fetch_mentor_context", return_value=[]),
        patch("app.services.chat_service.get_bedrock_client") as mock_get_client,
    ):
        mock_get_client.return_value.invoke_model_with_response_stream.return_value = {
            "body": fake_event_stream()
        }

        async with authenticated_client.stream(
            "POST", f"/library/chats/{session_id}/messages", json={"message": "Hi"}
        ) as resp:
            assert resp.status_code == 200
            body_text = ""
            async for chunk in resp.aiter_text():
                body_text += chunk

    assert "Hi " in body_text
    assert "there." in body_text

    detail_resp = await authenticated_client.get(f"/library/chats/{session_id}")
    messages = detail_resp.json()["messages"]
    assert [m["role"] for m in messages] == ["user", "mentor"]


async def test_old_mentor_endpoint_is_removed(authenticated_client: AsyncClient) -> None:
    resp = await authenticated_client.post("/library/mentor", json={"message": "hi"})
    assert resp.status_code == 404
