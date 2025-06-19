import boto3
from pathlib import Path
from collector.s3_storage import upload_file


def test_upload_file(tmp_path, mocker):
    path = tmp_path / "d.json"
    path.write_text("{}")

    client = mocker.Mock()
    boto_mock = mocker.patch("boto3.client", return_value=client)
    upload_file(path, "bucket", "d.json")
    boto_mock.assert_called_with("s3")
    client.upload_file.assert_called_once_with(str(path), "bucket", "d.json")

