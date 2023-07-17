# Copyright (C) 2015, Wazuh Inc.
# Created by Wazuh, Inc. <info@wazuh.com>.
# This program is free software; you can redistribute
# it and/or modify it under the terms of GPLv2


import hashlib
import json
import maltiverse
import pytest
import socket
import os
import logging

from unittest.mock import patch, mock_open, MagicMock

UNABLE_TO_CONNECT_SOCKET_ERROR_CODE = 6
SENDING_MESSAGE_SOCKET_ERROR_CODE = 7

response_example = {
    "blacklist": [
        {
            "description": "Malicious IP",
            "source": "Threat Intel Source 1",
            "external_references": [
                {
                    "source_name": "mitre-attack",
                    "external_id": "Some_id",
                    "url": "some_url",
                    "description": "something",
                }
            ],
        },
        {"description": "Suspicious Domain", "source": "Threat Intel Source 2"},
    ],
    "type": "ip",
    "creation_time": "2022-01-01T00:00:00Z",
    "modification_time": "2022-01-02T00:00:00Z",
}
alerts_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data/alerts.json')
sys_args_template = ['/var/ossec/integrations/maltiverse.py', alerts_file, 'API key', 
                     'http://<IP>:3001/api/v1/hooks/<HOOK_ID>']


def assert_expected_schema(response):
    """Assert that the response contains the expected schema fields."""
    list_of_fields = ["blacklist", "type", "creation_time", "modification_time"]
    for f in list_of_fields:
        assert f in response


def test_get_ip():
    """Test the `ip_get` method of the Maltiverse class."""
    example_token = "example_token"
    example_ip = "77.53.9.158"
    testing_maltiverse = maltiverse.Maltiverse(auth_token=example_token)

    with patch("maltiverse.requests.Session.get") as mock_get:
        mock_response = mock_get.return_value
        mock_response.json.return_value = response_example

        result = testing_maltiverse.ip_get(example_ip)
        assert_expected_schema(result)
        mock_get.assert_called_once_with(
            f'https://api.maltiverse.com/ip/{example_ip}'
        )


def test_get_hostname():
    """Test the `hostname_get` method of the Maltiverse class."""
    example_token = "example_token"
    example_hostname = "paypal.com-information-update-activity-account.gq"
    testing_maltiverse = maltiverse.Maltiverse(auth_token=example_token)

    with patch("maltiverse.requests.Session.get") as mock_get:
        mock_response = mock_get.return_value
        mock_response.json.return_value = response_example

        result = testing_maltiverse.hostname_get(example_hostname)
        assert_expected_schema(result)
        mock_get.assert_called_once_with(
            f'https://api.maltiverse.com/hostname/{example_hostname}'
        )


def test_get_url():
    """Test the `url_get` method of the Maltiverse class."""
    example_token = "example_token"
    example_url = "http://assocolours.com/mu/i/LoginVerification.php"
    example_urlchecksum = hashlib.sha256(example_url.encode("utf-8")).hexdigest()
    testing_maltiverse = maltiverse.Maltiverse(auth_token=example_token)

    with patch("maltiverse.requests.Session.get") as mock_get:
        mock_response = mock_get.return_value
        mock_response.json.return_value = response_example

        result = testing_maltiverse.url_get(example_urlchecksum)
        assert_expected_schema(result)
        mock_get.assert_called_once_with(
            f'https://api.maltiverse.com/url/{example_urlchecksum}'
        )


@pytest.mark.parametrize(
    "algorithm, mock_path",
    [
        ("md5", "maltiverse.Maltiverse.sample_get_by_md5"),
        ("sha1", "maltiverse.Maltiverse.sample_get_by_sha1"),
    ],
)
def test_get_sample(algorithm, mock_path):
    """Test that the `sample_get` method uses the correct algorithm."""
    example_token = "example_token"
    testing_maltiverse = maltiverse.Maltiverse(auth_token=example_token)
    with patch(mock_path) as mock_lambda:
        mock_lambda.return_value = response_example

        result = testing_maltiverse.sample_get("", algorithm)

        mock_lambda.assert_called_once()
        assert_expected_schema(result)


def test_get_by_md5():
    """Test the `sample_get_by_md5` method of the Maltiverse class."""
    example_token = "example_token"
    example_sample = "someSample"
    testing_maltiverse = maltiverse.Maltiverse(auth_token=example_token)

    with patch("maltiverse.requests.Session.get") as mock_get:
        mock_response = mock_get.return_value
        mock_response.json.return_value = response_example

        result = testing_maltiverse.sample_get_by_md5(example_sample)
        assert_expected_schema(result)
        mock_get.assert_called_once_with(
            f'https://api.maltiverse.com/sample/md5/{example_sample}'
        )


def test_get_by_sha1():
    """Test the `sample_get_by_sha1` method of the Maltiverse class."""
    example_token = "example_token"
    example_sample = "someSample"
    testing_maltiverse = maltiverse.Maltiverse(auth_token=example_token)

    with patch("maltiverse.requests.Session.get") as mock_get:
        mock_response = mock_get.return_value
        mock_response.json.return_value = response_example

        result = testing_maltiverse.sample_get_by_sha1(example_sample)
        assert_expected_schema(result)
        mock_get.assert_called_once_with(
            f'https://api.maltiverse.com/sample/sha1/{example_sample}'
        )


@pytest.mark.parametrize("number_of_arguments", [1, 2, 3])
def test_main_exit_with_invalid_number_of_arguments(number_of_arguments):
    """Test that the `main` function exits with the expected code for an invalid number of arguments."""
    with patch("builtins.open", mock_open()):
        with pytest.raises(SystemExit) as excinfo:
            maltiverse.main(list(range(0, number_of_arguments)))

    assert excinfo.value.code == 2


@pytest.mark.parametrize(
    "invalid_url",
    [
        "example.com",  # Missing schema
        "http://",  # Missing hostname
        ":8080/path",  # Missing netloc
    ],
)
def test_process_args_exit_with_invalid_hook_url(invalid_url):
    """Test that the `process_args` function exits with the expected code for an invalid hook URL."""
    with pytest.raises(SystemExit) as excinfo:
        maltiverse.process_args(["a", "b", "c", invalid_url])

    assert excinfo.value.code == 6


def test_load_alert():
    """Test that the `load_alert` function returns the contents of the file as a dictionary."""
    alert_data = {"key": "value"}
    file_path = "alert.json"

    with patch("builtins.open", create=True) as mock_open:
        mock_file = mock_open.return_value.__enter__.return_value
        mock_file.read.return_value = json.dumps(alert_data)

        result = maltiverse.load_alert(file_path)

    assert result == alert_data


def test_load_alert_exit_with_invalid_file():
    """Test that the `load_alert` function exits with the expected code for an invalid file path."""
    invalid_file_path = "idontexists.txt"

    with pytest.raises(SystemExit) as excinfo:
        maltiverse.load_alert(invalid_file_path)

    assert excinfo.value.code == maltiverse.ERR_FILE_NOT_FOUND


def test_load_alert_exit_with_invalid_file_content():
    """Test that the `load_alert` function exits with the expected code for invalid file content."""
    file_path = "somepath"

    with pytest.raises(SystemExit) as excinfo, patch("builtins.open") as mock_open:
        mock_file = mock_open.return_value.__enter__.return_value
        mock_file.read.return_value = "invalid json"

        maltiverse.load_alert(file_path)

    assert excinfo.value.code == maltiverse.ERR_INVALID_JSON


@pytest.mark.parametrize(
    "data, expected_call",
    [
        (
            {
                "syscheck": {"md5_after": "some"},
                "id": "some",
            },
            "maltiverse.Maltiverse.sample_get_by_md5",
        ),
        (
            {
                "syscheck": {"sha1_after": "some"},
                "id": "some",
            },
            "maltiverse.Maltiverse.sample_get_by_sha1",
        ),
        ({"data": {"srcip": "8.8.8.8"}, "id": "some"}, "maltiverse.Maltiverse.ip_get"),
        (
            {"data": {"hostname": "somehostname"}, "id": "some"},
            "maltiverse.Maltiverse.hostname_get",
        ),
        ({"data": {"url": "someurl"}, "id": "some"}, "maltiverse.Maltiverse.url_get"),
    ],
)
def test_request_maltiverse_info_make_expected_calls(data, expected_call):
    """Test that the `request_maltiverse_info` function makes the expected API calls."""
    example_token = "example_token"
    testing_maltiverse = maltiverse.Maltiverse(example_token)

    with patch("maltiverse.maltiverse_alert") as alert_mock, patch(
        expected_call
    ) as call_mock:
        alert_mock.return_value = {}
        result = maltiverse.request_maltiverse_info(data, testing_maltiverse)

    assert len(result) == 1
    call_mock.assert_called_once()


@pytest.mark.parametrize(
    "ecs_type, expected",
    [
        ("ip", "ipv4-addr"),
        ("hostname", "domain-name"),
        ("sample", "file"),
        ("url", "url"),
    ],
)
def test_match_ecs_type(ecs_type, expected):
    """Test that the `match_ecs_type` function correctly maps Maltiverse types to ECS types."""
    assert expected == maltiverse.match_ecs_type(ecs_type)


@pytest.mark.parametrize(
    "data, expected",
    [
        ({"classification": "malicious", "blacklist": [1, 2]}, "High"),
        ({"classification": "malicious", "blacklist": [1]}, "Medium"),
        ({"classification": "suspicious", "blacklist": [1, 2]}, "Medium"),
        ({"classification": "neutral", "blacklist": [1, 2]}, "Low"),
        ({"classification": "neutral", "blacklist": []}, "None"),
        ({"classification": "whitelist", "blacklist": [1, 2]}, "Low"),
        ({"classification": "whitelist", "blacklist": []}, "None"),
        ({}, "Not Specified"),
    ],
)
def test_get_ioc_confidence(data, expected):
    """Test the `get_ioc_confidence` function to ensure correct confidence ratings are returned."""
    assert expected == maltiverse.get_ioc_confidence(data)


@pytest.mark.parametrize(
    "msg,agent,expected",
    [
        ("msg", {}, '1:maltiverse:"msg"'),
        ("msg", {"id": "000", "name": "Agent1", "ip": "192.168.0.1"}, '1:maltiverse:"msg"'),
        ("msg", {"id": "001", "name": "Agent1", "ip": "192.168.0.1"}, '1:[001] (Agent1) 192.168.0.1->maltiverse:"msg"')
    ]
)
def test_send_event(msg, agent, expected):
    """Test sending an event to a specific agent."""
    with patch("maltiverse.socket.socket") as mock_socket:
        maltiverse.send_event(msg, agent)

    mock_socket.assert_called_with(socket.AF_UNIX, socket.SOCK_DGRAM)
    mock_socket.return_value.connect.assert_called_once_with(maltiverse.SOCKET_ADDR)
    mock_socket.return_value.send.assert_called_with(
        expected.encode()
    )
    mock_socket.return_value.close.assert_called()


@pytest.mark.parametrize("error_code, expected_exit_code", [
    (111, UNABLE_TO_CONNECT_SOCKET_ERROR_CODE),
    (90, SENDING_MESSAGE_SOCKET_ERROR_CODE),
])
def test_send_event_exits_when_socket_exception_raised(error_code, expected_exit_code):
    """Test `send_event` function exits with the expected code when socket methods raise an exception.

    Parameters
    ----------
    error_code : int
        Error code number for the socket error to be raised.
    expected_exit_code : int
        Error code number for the expected exit exception.
    """
    test_msg = {}
    error = socket.error()
    error.errno = error_code

    with patch('maltiverse.socket.socket') as mock_socket:
        mock_socket.side_effect = error
        with pytest.raises(SystemExit) as e:
            maltiverse.send_event(test_msg)
        assert e.value.code == expected_exit_code


def test_maltiverse_alert():
    """Test that maltiverse_alert generates the expected alert dictionary."""
    example_ioc_dict = response_example
    example_alert_id = 123
    example_ioc_name = "some_name"

    expected_result = {
        "integration": "maltiverse",
        "alert_id": example_alert_id,
        "maltiverse": {"source": response_example},
        "threat": {
            "indicator": {
                "name": example_ioc_name,
                "type": "ipv4-addr",
                "ip": example_ioc_name,
                "description": "Malicious IP, Suspicious Domain",
                "provider": "Threat Intel Source 1, Threat Intel Source 2",
                "first_seen": "2022-01-01T00:00:00Z",
                "modified_at": "2022-01-02T00:00:00Z",
                "last_seen": "2022-01-02T00:00:00Z",
                "confidence": "Not Specified",
                "sightings": 2,
                "reference": f"https://maltiverse.com/ip/{example_ioc_name}",
            },
            "software": {
                "id": "Some_id",
                "reference": "some_url",
                "name": "something"
            }
        },
    }

    result = maltiverse.maltiverse_alert(
        example_alert_id, example_ioc_dict, example_ioc_name
    )

    assert result == expected_result


def test_maltiverse_alert_does_not_include_sources():
    """Test that maltiverse_alert excludes the maltiverse source when include_full_source is False."""
    example_ioc_dict = response_example
    example_alert_id = 123
    example_ioc_name = "some_name"

    result = maltiverse.maltiverse_alert(
        example_alert_id, example_ioc_dict, example_ioc_name, include_full_source=False
    )
    assert "maltiverse" not in result


@pytest.mark.parametrize(
    "ioc,expected",
    [
        # Process the mitre information
        (
            {
                "blacklist": [
                    {
                        "external_references": [
                            {
                                "external_id": "Something",
                                "url": "some_url",
                                "description": "",
                                "source_name": "mitre-attack",
                            }
                        ]
                    }
                ]
            },
            {"software": {"id": "Something", "reference": "some_url", "name": ""}},
        ),
        # Skips the mitre information due to the source name
        (
            {
                "blacklist": [
                    {
                        "external_references": [
                            {
                                "external_id": "Something",
                                "url": "some_url",
                                "description": "",
                                "source_name": "something",
                            }
                        ]
                    }
                ]
            },
            {},
        ),
        # Skips the mitre information due to the external_id name
        (
            {
                "blacklist": [
                    {
                        "external_references": [
                            {
                                "external_id": "something",
                                "url": "some_url",
                                "description": "",
                                "source_name": "mitre-attack",
                            }
                        ]
                    }
                ]
            },
            {},
        ),
        # Skips the mitre information due to being an empty dict
        ({}, {}),
    ],
)
def test_get_mitre_information(ioc, expected):
    """Test that get_mitre_information extracts the expected mitre information from the IOC dictionary."""
    result = maltiverse.get_mitre_information(ioc)

    assert result == expected


def test_logger(caplog):
    """Test the correct execution of the logger."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    with patch("maltiverse.socket.socket") as mock_socket:
        with patch("maltiverse.request_maltiverse_info", return_value={}):
            with caplog.at_level(logging.DEBUG, logger='maltiverse'):
                args = sys_args_template[:]
                args.append('info')
                maltiverse.main(args)

    # Assert console log correctness
    assert caplog.records[0].message == 'Running Maltiverse script'
    assert caplog.records[1].message == f'Alerts file location: {sys_args_template[1]}'
    assert caplog.records[-1].levelname == 'INFO'
    assert "DEBUG" not in caplog.text
    # Assert the log file is created and is not empty
    assert os.path.exists(maltiverse.LOG_FILE)
    assert os.path.getsize(maltiverse.LOG_FILE) > 0
