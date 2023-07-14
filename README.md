# RZCF
Back in the day, many of us left 9GAG and ended up sticking with either Reddit or 4chan. For me, it was Reddit. To this day, I'm a big fan. Likewise, I'm a huge fan of corpora for linguistic analysis.
u/stuck_in_the_matrix and u/Wishful1 (and probably other honorable people) have been taking care of archiving Reddit's universe of submissions and comments for years, you can find them [here](https://academictorrents.com/details/7c0645c94321311bb05bd879ddee4d0eba08aaee) and some general information about the project (and the former API access) [here](https://www.reddit.com/r/pushshift/comments/bcxguf/).

I've merely written a small script that allows you to get a first impression of the data. It was actually just for my own tests and use-cases, but I like to share what I did in Python (might help someone somewhere), so here we go..

RZCF (RedditZstCommentFilter) filters Reddit comments from pushift dumps based on various parameters such as the username, date, or a specific keyword or phrase within the comment. The script ignores comments from 'automoderator', as well as comments where the body of the comment is either '[deleted]' or '[removed]', script works on `.zst` Reddit data dumps. The output is saved to a JSON file named `filtered_comments_<timestamp>.json` where `<timestamp>` is the current date and time you run it.

## How to use

To run you need Python 3.x along with zstandard and ijson:

`$ pip install ijson zstandard`

The script works from the command line as follows:

`python3 rzcf.py <filename.zst> [options]` 

-   `-u` or `--user`: Filter comments by a specific user, e. g. `-u john_mustermann`  
   
-   `-d` or `--date`: Filter comments from a specific date. The date should be formatted as `YYYY-MM-DD`, e.g. `-d 2020-05-17`

- `-dr` or `--date-range`: Filters comments based on a specified date range, e.g. `dr 2019-01-01 2019-02-01` (will filter comments made from January 1, 2019, up to February 1, 2019)
    
-   `-k` or `--keyword`: Filter comments containing a specific keyword or phrase, e.g. `-k Weihnachten` `-k "machine learning"`
    
-   `-c` or `--comment_only`: Only output the comment text, without any metadata.
- `-l` or `--link` (only works in combination with `-c`): retrieve/construct URL for respective comment (atm URL only to the whole thread)
    

## Example usage

`python3 rzcf.py askreddit_comments.zst -u john_mustermann -d 2020-05-17 -k "machine learning" -c` 

This command will find all comments from the user `john_mustermann` in the `AskReddit` subreddit, made on the 17th of May 2020, that contain the phrase "machine learning". Only the comment text will be saved to the output file, without any metadata.

side note: during decompression of the `.zst` file, the script reads the data in chunks. This is done to manage memory usage, especially when dealing with large data. I set it to `2**28` (ca. 256 MB), but you can adjust it if needed or necessary by modifying the `chunk_size` constant at the beginning of the script.

Feel free to write a message if you find something wrong, I'm always trying to improve!
