import main

lby_api_server = "http://127.0.0.1:5279"

def test_parse_channel_file_empty():
    res = main.split_content_in_lines("")
    assert res is not None
    assert len(res) == 0

def test_parse_channel_file_empty_lines():
    res = main.split_content_in_lines("#\n#\n#\n\n\n\n     \n    \n")
    assert res is not None
    assert len(res) == 0


def test_parse_channel_file_some_content():
    res = main.split_content_in_lines("#\n#\n#\n\n\n\n  some channel    \n    \n")
    assert res is not None
    assert len(res) == 1


def test_parse_datetime_to_timestamp():
    date_str = "2021-05-01"
    ts = main.parse_datetime_to_timestamp(date_str)
    assert ts > 1e9

def test_split_lines_in_url_and_time():
    string = "line1, 2021-05-01\nline 2 , 2021-05-02\nline 3"
    lines = main.split_content_in_lines(string)
    parsed_lines = main._split_lines_in_url_and_time(lines)
    assert len(parsed_lines) == 3
    assert len(parsed_lines[1]) == 2
    assert len(parsed_lines[2]) == 2

def test_get_channel_ids_for_channel_uris():
    channels = [("lbry://@ScottManley#5", None), ("lbry://@kauffj#f", None)]
    claims = main.get_channel_ids_for_channel_uris(channels, lby_api_server)
    assert len(claims) == 2
    assert claims[0][0][0:3] == "548", "Error or maybe Scott Manley changed their claim ID on the channel"
    assert claims[1][0][0:3] == "f3d", "Error or maybe Jeremy Kauffman changed their claim ID on the channel"


def test_get_aggregated_list_of_streams_to_cache():
    channel_data = main.resolve_channel("lbry://@ScottManley#5", lby_api_server)
    channel_name = next(iter(channel_data.keys()))
    claim_id = channel_data[channel_name]["claim_id"]
    no_claims = channel_data[channel_name]["meta"]["claims_in_channel"]
    claim_list = [(claim_id, None)]  # Scott Manley
    result = main.get_aggregated_list_from_channels_claims(claim_list, lby_api_server)
    assert len(result) > 30, "We did not get more than one page of data"
    assert len(result) == no_claims, "We did not get all claims in the channel"


def test_get_aggregated_list_of_streams_to_cache_multiple_channels():
    channel_data = main.resolve_channel("lbry://@ScottManley#5", lby_api_server)
    channel_name = next(iter(channel_data.keys()))
    claim_id = channel_data[channel_name]["claim_id"]
    claim_list = [(claim_id, main.parse_datetime_to_timestamp('2021-05-01')), (claim_id, main.parse_datetime_to_timestamp('2021-05-01'))]  # Scott Manley
    result = main.get_aggregated_list_from_channels_claims(claim_list, lby_api_server)
    assert len(result) > 0


def test_extract_video_url_from_stream_claims():
    channel_data = main.resolve_channel("lbry://@ScottManley#5", lby_api_server)
    channel_name = next(iter(channel_data.keys()))
    claim_id = channel_data[channel_name]["claim_id"]
    claim_list = [(claim_id, main.parse_datetime_to_timestamp('2021-05-01'))]  # Scott Manley
    result = main.get_aggregated_list_from_channels_claims(claim_list, lby_api_server)
    assert len(result) > 0

    video_list = main.extract_video_url_from_stream_claims(result)
    assert len(video_list) == len(result)


def test_download_videos_from_urls():
    channel_data = main.resolve_channel("lbry://@ScottManley#5", lby_api_server)
    channel_name = next(iter(channel_data.keys()))
    claim_id = channel_data[channel_name]["claim_id"]
    claim_list = [(claim_id, main.parse_datetime_to_timestamp('2021-05-01'))]  # Scott Manley
    result = main.get_aggregated_list_from_channels_claims(claim_list, lby_api_server)
    assert len(result) > 0

    video_list = main.extract_video_url_from_stream_claims(result)
    assert len(video_list) == len(result)

    video_list = video_list[0:3]
    main.queue_download_video_chunks_from_urls(video_list, lby_api_server)


