import requests
import datetime
import time
from typing import List, Tuple, Union, Dict
import argparse
import traceback

# TODO refactor maybe in a class
ChannelEntries = List[Tuple[str, Union[float, None]]]  # Typing

def split_content_in_lines(file_content:str)->List[str]:
    """
    Splits a block of strings into lines and keeps lines that are not starting with #

    :param file_content:
    :return:
    """
    file_content = file_content.strip()
    if len(file_content) <= 0:
        return []
    collected_entries = []
    for line in file_content.split("\n"):
        line = line.strip()
        if len(line) <= 0:
            continue
        if line[0] == "#":
            continue
        collected_entries.append(line)
    return collected_entries


def parse_datetime_to_timestamp(date_str:str)->float:
    ts = datetime.datetime.strptime(date_str, "%Y-%m-%d").timestamp()
    return ts


def _split_lines_in_url_and_time(lines:List[str])->ChannelEntries:
    collected_lines = []
    for l in lines:
        try:
            chunks = l.split(",")
            if len(chunks) != 2:
                collected_lines.append((l, None))
            else:
                ts = parse_datetime_to_timestamp(chunks[1].strip())
                collected_lines.append((chunks[0].strip(), ts))
        except:
            print(f"Exception while parsing {l}: \n{traceback.format_exc()}")
    return collected_lines


def _read_channel_list(file_content:str)->ChannelEntries:
    content_lines = split_content_in_lines(file_content)
    content_lines = _split_lines_in_url_and_time(content_lines)
    return content_lines


def read_channel_list(file_name:str="channel_list.txt"):
    content = ""
    with open(file_name) as f:
        content = f.read()
    return _read_channel_list(content)


def resolve_channel(channel_url, lbry_api_server:str):
    resolve_js = {"method": "resolve", "params":
        {
            "urls": channel_url,
            "include_purchase_receipt": False, "include_is_my_output": False,
            "include_sent_supports": False, "include_sent_tips": False, "include_received_tips": False
        }}
    answer = requests.post(lbry_api_server, json=resolve_js).json()
    if answer.get('error', None) is not None:
        raise Exception(f"LBRY_API error: {answer['error']}")
    return answer['result']


def get_channel_ids_for_channel_uris(channel_lines:ChannelEntries, lbry_api_server:str)->ChannelEntries:
    resolved_channel_lines = []
    for (channel_url, timestamp) in channel_lines:
        try:
            answer = resolve_channel(channel_url, lbry_api_server)
            returned_channel_url = next(iter(answer.keys()))
            assert channel_url == returned_channel_url
            claim_id = answer[channel_url]['claim_id']
            resolved_channel_lines.append((claim_id, timestamp))
        except:
            print(f"Exception while parsing {channel_url}: \n{traceback.format_exc()}")

    return resolved_channel_lines


def get_aggregated_list_from_channels_claims(resolved_channel_lines:ChannelEntries, lbry_api_server:str) -> List[Dict]:
    streams_item_list = []
    page_size = 50  # apparenlty max page size or sth.
    for (claim_id, timestamp) in resolved_channel_lines:
        try:
            resolve_js = {"method": "claim_search","params":
                {
                    "channel_ids": [claim_id],
                    "claim_type": "stream", "no_totals":True, "fee_amount":0,
                    "page_size":page_size, "order_by":"timestamp", "has_channel_signature":True,
                    "valid_channel_signature":True,
                }
            }
            if timestamp is not None:
                resolve_js["params"]["timestamp"] = f">{timestamp}"
            crt_stream_page = 1
            while True:
                resolve_js["params"]["page"] = crt_stream_page
                answer = requests.post(lbry_api_server, json=resolve_js).json()
                if answer.get('error', None) is not None:
                    raise Exception(f"LBRY_API error: {answer['error']}")
                result = answer["result"]
                assert crt_stream_page == result["page"]
                assert page_size == result["page_size"]
                returned_items = result["items"]
                streams_item_list.extend(returned_items)
                if len(returned_items) < page_size:
                    break
                crt_stream_page += 1
        except:
            print(f"Exception while searching streams for {claim_id}: \n{traceback.format_exc()}")

    return streams_item_list


def extract_video_url_from_stream_claims(streams_item_list:List[Dict]) -> List[str]:
    video_urls = []
    for i in streams_item_list:
        video_urls.append(i['canonical_url'])

    return video_urls


def queue_download_video_chunks_from_urls(video_urls:List[str], lbry_api_server:str):
    get_js = {"method": "get", "params":
        {
            "save_file":True,
        }}
    for video in video_urls:
        try:
            get_js["params"]["uri"] = video
            answer = requests.post(lbry_api_server, json=get_js).json()
            if answer.get('error', None) is not None:
                raise Exception(f"LBRY_API error: {answer['error']}")
        except:
            print(f"Exception while searching streams for {video}: \n{traceback.format_exc()}")


def start_checking_movies(lbry_api_server, is_looping):
    print("Starting to parse channel_list.txt")
    while True:
        # Read the channel list from file
        url_and_time = read_channel_list("channel_list.txt")
        print(f"Read {len(url_and_time)} entries")
        if len(url_and_time) <= 0:
            print("Channel file is empty, exiting.")
            return
        try:
            # Find the claim_id for each channel
            claim_id_and_time = get_channel_ids_for_channel_uris(url_and_time, lbry_api_server)
            assert len(claim_id_and_time) > 0, "Probably the service is not yet initialized."
            # Find the content of each channel
            channels_claims = get_aggregated_list_from_channels_claims(claim_id_and_time, lbry_api_server)
            # Extract the video URLs
            video_urls_for_channels = extract_video_url_from_stream_claims(channels_claims)
            print(f"Found {len(video_urls_for_channels)} videos on these channels.\nTriggering video downloading and caching.")
            queue_download_video_chunks_from_urls(video_urls_for_channels, lbry_api_server)
        except:
            print(f"Exception while interacting witn lbry-api: \n{traceback.format_exc()}")
            print("Retrying after a short delay.")
            if is_looping:
                time.sleep(30)
                continue
        if not is_looping:
            break
        print("Sleep for a while . . .")
        time.sleep(3600)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", default="", action="store", choices=["start"],
                        help="Searches vor video in the channel_list.txt file and downloads them.\nWaits a while "
                                      "and then checks again if any new content is available in the channels")

    parser.add_argument("-s", "--server", action="store", default="http://127.0.0.1:5279" , dest="server",
                        help="Specify the lbry-sdk api server. Defaults to 127.0.0.1:5279"
                        )

    parser.add_argument("-l", "--loop", action="store_true", default="false" , dest="loop",
                        help="Specify that the channel list will be read and lbry protocl interogated in an infinite loop.\n"
                             "Otherwise, exits after one query."
                        )

    args = parser.parse_args()
    lbry_api_server = args.server
    is_looping = args.loop

    if args.command == "start":
        start_checking_movies(lbry_api_server, is_looping)


