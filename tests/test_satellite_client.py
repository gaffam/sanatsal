import pandas as pd
from collector.satellite_client import (
    fetch_modis_data,
    fetch_viirs_data,
    fetch_sentinel2_data,
    fetch_effis_data,
)

def test_fetch_modis_data(mocker):
    csv_content = "latitude,longitude,brightness\n1,2,300\n"
    mock_response = mocker.Mock()
    mock_response.text = csv_content
    mock_response.raise_for_status.return_value = None
    mocker.patch("requests.get", return_value=mock_response)
    df = fetch_modis_data("http://example.com/test.csv")
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["latitude", "longitude", "brightness"]


def test_fetch_viirs_data(mocker):
    csv_content = "lat,lon,bright\n1,2,350\n"
    mock_response = mocker.Mock()
    mock_response.text = csv_content
    mock_response.raise_for_status.return_value = None
    mocker.patch("requests.get", return_value=mock_response)
    df = fetch_viirs_data("http://example.com/viirs.csv")
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["lat", "lon", "bright"]


def test_fetch_sentinel2_data(mocker):
    csv_content = "x,y,level\n1,2,5\n"
    mock_response = mocker.Mock()
    mock_response.text = csv_content
    mock_response.raise_for_status.return_value = None
    mocker.patch("requests.get", return_value=mock_response)
    df = fetch_sentinel2_data("http://example.com/s2.csv")
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["x", "y", "level"]


def test_fetch_effis_data(mocker):
    csv_content = "lat,lon,intensity\n1,2,9\n"
    mock_response = mocker.Mock()
    mock_response.text = csv_content
    mock_response.raise_for_status.return_value = None
    mocker.patch("requests.get", return_value=mock_response)
    df = fetch_effis_data("http://example.com/effis.csv")
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["lat", "lon", "intensity"]

