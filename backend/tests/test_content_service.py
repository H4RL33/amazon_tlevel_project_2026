from app.services import content_service


async def test_get_presigned_url_calls_boto3_generate_presigned_url(monkeypatch) -> None:
    captured = {}

    class FakeS3Client:
        def generate_presigned_url(self, operation, Params, ExpiresIn):
            captured["operation"] = operation
            captured["params"] = Params
            captured["expires_in"] = ExpiresIn
            return "https://example-bucket.s3.amazonaws.com/some-key?signed=1"

    monkeypatch.setattr(content_service.boto3, "client", lambda service, region_name: FakeS3Client())

    url = await content_service.get_presigned_url("some-key", expiry_seconds=120)

    assert url == "https://example-bucket.s3.amazonaws.com/some-key?signed=1"
    assert captured["operation"] == "get_object"
    assert captured["params"]["Key"] == "some-key"
    assert captured["expires_in"] == 120
