import argparse
import json
import zstandard
import datetime
import logging

CHUNK_SIZE = 2**27
MAX_WINDOW_SIZE = (2**29) * 2
JSON_DECODER = json.JSONDecoder()

# Parse command line arguments.
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', help='The zst file to process.')
    parser.add_argument('-u', '--user', help='Filter comments by this user.')
    parser.add_argument('-s', '--subreddit', help='Filter comments from this subreddit.')
    date_group = parser.add_mutually_exclusive_group()
    date_group.add_argument('-d', '--date', help='Filter comments from this date (format: YYYY-MM-DD).')
    date_group.add_argument('-dr', '--date_range', nargs=2, help='Filter comments within this date range (format: YYYY-MM-DD YYYY-MM-DD).')
    parser.add_argument('-c', '--comment_only', help='Only display comment text, not metadata.', action='store_true')
    parser.add_argument('-k', '--keyword', help='Search for a keyword or phrase within the comments.')
    parser.add_argument('-l', '--link', help='Display the link to the comment when used with --comment_only.', action='store_true')
    return parser.parse_args()

# Read a chunk from the reader and decode it.
def read_and_decode(reader, chunk_size, max_window_size, previous_chunk=None, bytes_read=0, max_attempts=3):
    for attempt in range(max_attempts):
        chunk = reader.read(chunk_size)
        bytes_read += chunk_size
        if previous_chunk is not None:
            chunk = previous_chunk + chunk
        try:
            return chunk.decode()
        except UnicodeDecodeError:
            if attempt == max_attempts - 1 or bytes_read > max_window_size:
                raise UnicodeError(f"Can't decode after reading {bytes_read:,} bytes and {attempt+1} attempts")
            logging.error(f"Decoding error, reading another chunk. Attempt {attempt+1}")

# Read and decode lines from a zst file.
def read_lines_zst(file_name):
    with open(file_name, 'rb') as file_handle:
        buffer = ''
        reader = zstandard.ZstdDecompressor(max_window_size=MAX_WINDOW_SIZE).stream_reader(file_handle)
        while True:
            chunk = read_and_decode(reader, CHUNK_SIZE, MAX_WINDOW_SIZE)
            if not chunk:
                break
            lines = (buffer + chunk).split("\n")
            for line in lines[:-1]:
                yield line.strip()
            buffer = lines[-1]
        reader.close()

# Parse arguments and filter comments based on the provided criteria.
def main():
    args = parse_args()
    found_results = False
    date = None
    date_range_start = None
    date_range_end = None
    comment_count = 0

    if args.date:
        date = datetime.datetime.strptime(args.date, '%Y-%m-%d').date()
    if args.date_range:
        date_range_start = datetime.datetime.strptime(args.date_range[0], '%Y-%m-%d').date()
        date_range_end = datetime.datetime.strptime(args.date_range[1], '%Y-%m-%d').date()

    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'filtered_comments_{timestamp}.json'
    
    buffered_comments = []
    try:
        for line in read_lines_zst(args.file):
            comment_json = JSON_DECODER.raw_decode(line.strip())[0]

            # Ignore comments from 'automoderator' (in any case), with body (actual comment) '[deleted]' or '[removed]'
            if comment_json.get('author').lower() == 'automoderator' or comment_json.get('body') in ['[deleted]', '[removed]']:
                continue

                continue

            if args.user and comment_json.get('author') != args.user:
                continue

            if args.subreddit and comment_json.get('subreddit') != args.subreddit:
                continue

            comment_date = datetime.datetime.utcfromtimestamp(int(comment_json['created_utc'])).date()
            if date and comment_date != date:
                continue

            if date_range_start and date_range_end and (comment_date < date_range_start or comment_date > date_range_end):
                continue

            if args.keyword and args.keyword.lower() not in comment_json['body'].lower():
                continue

            if args.comment_only:
                comment = comment_json['body']
                if args.link:
                    permalink = comment_json.get('permalink')
                    if permalink:
                        comment += '\nLink: https://www.reddit.com' + permalink
                    else:
                        # Construct the link from the 'link_id'
                        link_id = comment_json.get('link_id')
                        if link_id and link_id.startswith('t3_'):
                            comment += f'\nLink: https://www.reddit.com/comments/{link_id[3:]}/'
                buffered_comments.append(comment)
                comment_count += 1
                found_results = True
            else:
                buffered_comments.append(json.dumps(comment_json, ensure_ascii=False))
                comment_count += 1
                found_results = True
            # Flush buffer when it reaches 100 entries
            if len(buffered_comments) >= 100:
                with open(filename, 'a') as outf:
                    outf.write('\n'.join(buffered_comments) + '\n')
                    buffered_comments = []
    
    except Exception as e:
        logging.error(f"Error processing line: {line}. Error message: {str(e)}")
    
    # Write remaining comments in the buffer
    if buffered_comments:
        with open(filename, 'a') as outf:
            outf.write('\n'.join(buffered_comments) + '\n')

    if not found_results:
        print("No results found for the given search parameters.")
    else:
        print(f"Finished. Found and saved {comment_count} comments.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
