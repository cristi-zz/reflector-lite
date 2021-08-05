import time

import pytest

import main
import requests

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


def test_get_list_of_blolbs_for_a_stream_without_downloading():
    # Test to see if current API version have expected behavior:
    # Goal: Download only the blobs, without extracting the content
    # Download main blob of a claim by hacking get parameters
    # Able to retrieve the blob list?

    # ClaimID: 4daf470b7124f2eeb214a538c54cf48eeaceeff9  the intro video of reflector-lite
    # URI: @ml-visoft#d/02_mini_reflector_for_LBRY_peer_network_initial#4
    # sd_hash: 414e639aee7403c778ae9c84f6889e5f8156e38253bf97cb706061d3a7a86a9b254b928854c8f5a7f406dbd3b5a4ff8b
    # apparently sd_hash is the first blob in the stream
    # The sd_hash can be retrieved from claim_search by going into value/source/sd_hash

    # clearing the knowledge about the file
    request_js = {"method": "file_delete", "params":
        {
            "claim_id":"4daf470b7124f2eeb214a538c54cf48eeaceeff9",
            "delete_all":True,

        }}
    answer = requests.post(lby_api_server, json=request_js).json()
    assert "error" not in answer, f"Error: {answer['error']}"

    # checking to see if is prior know-how about the file exists.
    request_js = {"method": "blob_list", "params":
        {
            "sd_hash":"414e639aee7403c778ae9c84f6889e5f8156e38253bf97cb706061d3a7a86a9b254b928854c8f5a7f406dbd3b5a4ff8b",
        }}
    answer = requests.post(lby_api_server, json=request_js).json()
    items = answer["result"]["items"]
    no_items = answer["result"]["total_items"]
    print(items)
    assert len(items) == 0 and no_items == 0, "The lbry server know-how about current file should be empty"

    # Put a request for the header blob. Check the "save_file":False parameter that will not retrieve the whole blob list.
    request_js = {"method": "get", "params":
        {
            "uri":"@ml-visoft#d/02_mini_reflector_for_LBRY_peer_network_initial#4",
            "save_file":False
        }}
    answer = requests.post(lby_api_server, json=request_js).json()
    assert "error" not in answer, f"Error: {answer['error']}"

    # Check if we know about the existence of more blobs
    request_js = {"method": "blob_list", "params":
        {
            "sd_hash":"414e639aee7403c778ae9c84f6889e5f8156e38253bf97cb706061d3a7a86a9b254b928854c8f5a7f406dbd3b5a4ff8b",
        }}
    answer = requests.post(lby_api_server, json=request_js).json()
    items_in_blob_list = answer["result"]["items"]
    no_items_in_blob_list = answer["result"]["total_items"]
    assert len(items_in_blob_list) > 10 and no_items_in_blob_list > 10, "The local lbry does not know about any more blobls."


def test_try_to_download_a_list_of_blobs():
    # Try to download a blob from a blob list.

    # clearing the knowledge about the file
    request_js = {"method": "file_delete", "params":
        {
            "claim_id":"4daf470b7124f2eeb214a538c54cf48eeaceeff9",
            "delete_all":True,

        }}
    answer = requests.post(lby_api_server, json=request_js).json()
    assert "error" not in answer, f"Error: {answer['error']}"

    # Put a request for the header blob. Check the "save_file":False parameter that will not retrieve the whole blob list.
    request_js = {"method": "get", "params":
        {
            "uri":"@ml-visoft#d/02_mini_reflector_for_LBRY_peer_network_initial#4",
            "save_file":False
        }}
    answer = requests.post(lby_api_server, json=request_js).json()

    # Check if we know about the existence of more blobs
    request_js = {"method": "blob_list", "params":
        {
            "sd_hash":"414e639aee7403c778ae9c84f6889e5f8156e38253bf97cb706061d3a7a86a9b254b928854c8f5a7f406dbd3b5a4ff8b",
        }}
    answer = requests.post(lby_api_server, json=request_js).json()
    items_in_blob_list = answer["result"]["items"]

    request_js = {"method": "blob_get", "params":
        {
            "blob_hash":items_in_blob_list[1],
            "timeout":10,
            "read":False,
        }}
    answer = requests.post(lby_api_server, json=request_js).json()
    assert "error" not in answer, f"Error: {answer['error']}"
    assert f"Downloaded blob {items_in_blob_list[1]}" in answer['result']



@pytest.mark.skip # Downloading directly the sd_hash using blob_get blocks infenitively.
def test_get_list_of_blolbs_for_a_stream_direct_head_download():
    # Goal: Download only the blobs, without extracting the content
    # Test to see if downloading sd_hash blob, gets info about the rest of the blobs, too

    # CONCLUSION: blob_get() only does NOT extract the blob content.

    # ClaimID: 4daf470b7124f2eeb214a538c54cf48eeaceeff9  the intro video of reflector-lite
    # URI: @ml-visoft#d/02_mini_reflector_for_LBRY_peer_network_initial#4
    # sd_hash: 414e639aee7403c778ae9c84f6889e5f8156e38253bf97cb706061d3a7a86a9b254b928854c8f5a7f406dbd3b5a4ff8b
    # apparently sd_hash is the first blob in the stream
    # The sd_hash can be retrieved from claim_search by going into value/source/sd_hash

    # clearing the knowledge about the file
    request_js = {"method": "file_delete", "params":
        {
            "claim_id":"4daf470b7124f2eeb214a538c54cf48eeaceeff9",
            "delete_all":True,

        }}
    answer = requests.post(lby_api_server, json=request_js).json()
    assert "error" not in answer, f"Error: {answer['error']}"

    # checking to see if is prior know-how about the file exists.
    request_js = {"method": "blob_list", "params":
        {
            "sd_hash":"414e639aee7403c778ae9c84f6889e5f8156e38253bf97cb706061d3a7a86a9b254b928854c8f5a7f406dbd3b5a4ff8b",
        }}
    answer = requests.post(lby_api_server, json=request_js).json()
    items = answer["result"]["items"]
    no_items = answer["result"]["total_items"]
    print(items)
    assert len(items) == 0 and no_items == 0, "The lbry server know-how about current file should be empty"

    # Download the blob directly, using sd_hash
    request_js = {"method": "blob_get", "params":
        {
            "blob_hash":"414e639aee7403c778ae9c84f6889e5f8156e38253bf97cb706061d3a7a86a9b254b928854c8f5a7f406dbd3b5a4ff8b",
            "timeout":10,
        }}
    answer = requests.post(lby_api_server, json=request_js).json()
    time.sleep(10) # well, let it download, the method is async?

    # Check if we know about the existence of more blobs
    request_js = {"method": "blob_list", "params":
        {
            "sd_hash":"414e639aee7403c778ae9c84f6889e5f8156e38253bf97cb706061d3a7a86a9b254b928854c8f5a7f406dbd3b5a4ff8b",
        }}
    answer = requests.post(lby_api_server, json=request_js).json()
    items_in_blob_list = answer["result"]["items"]
    no_items_in_blob_list = answer["result"]["total_items"]
    assert len(items_in_blob_list) > 10 and no_items_in_blob_list > 10, "The local lbry does not know about any more blobls."


