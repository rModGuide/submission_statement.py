#  Submission Statement Bot originally written by u/epicmindwarp.  


import re
import sys
import praw
import time
import traceback

from datetime import datetime as dt, timedelta as td, date


# Set Variables

RGX_CHAR_200 = r'.{200}'     Regex character count of 200 characters.  Change this to change your search criteria.  

SUB_NAME    = 'SUBREDDITNAME'    # Set subreddit here.  To work on multiple subs, separate them by a plus: 'subreddit+subreddit+subreddit'

MINIMUM_HOURS = 1       # Number of hours a post must be old

SLEEP_SECONDS = 2400     # Number of seconds to sleep between scans (2400 = 40 minutes)

#REMOVAL_REPLY = f'Hello u/{submission.author}.\nYour post to r/{submission.subreddit} has been removed. Our rules require a [submission statement](https://reddit.com/r/{submission.subreddit}/wiki/submissions) of at least 100 characters within one hour of posting a link or image post. This is done to encourage more user participation in the community. This post cannot be restored, but you may resubmit it and then post the required submission comment. Please [see here for more info.](http://reddit.com/r/{submission.subreddit}/wiki/submissions) I am a bot. Replies and chats will not receive responses. *If you feel this was done in error, or would like better clarification or need further assistance, please [message the moderators.](https://www.reddit.com/message/compose?to=/r/{submission.subreddit}&subject=Question regarding the removal of this submission by /u/{submission.author}&message=I have a question regarding the removal of this submission: {submission.permalink})'


# Best practices call for importing a separate config file for your reddit login credentials.  Simplicity is emphasized here instead.
def reddit_login():

    print('Connecting to reddit...')

    try:
        reddit = praw.Reddit(   client_id= 'YOUR CLIENT ID',
                                client_secret= 'YOUR CLIENT SECRET',
                                user_agent='Top Comment Enforcer Bot for /r/SUBREDDIT - v0.2 written by u/EpicMindWarp, adapted by u/BuckRowdy',
                                username='YOUR_USERNAME',
                                password='Your_Password')

    except Exception as e:
        print(f'\t### ERROR - Could not login.\n\t{e}')
        traceback.print_exc()
        
    print(f'Logged in as: {reddit.user.me()}')

    return reddit


# Get new submissions from the subreddit.  Set to 50 but you may need to adjust to fit your needs.
def get_latest_submissions(subreddit):

    print(f'Getting posts from {SUB_NAME}...')

    submissions = subreddit.mod.unmoderated(limit=50)

    return submissions



def check_submissions(submissions, valid_posts):

    for submission in submissions:

        # Set up a removal reply
        REMOVAL_REPLY = f'Hello u/{submission.author}.\nYour post to r/{submission.subreddit} has been removed. Our rules require that you make a [submission statement](https://reddit.com/r/{submission.subreddit}/wiki/submissions) of at least 200 characters within one hour of posting a link or image post. This is simply a comment on your own post that explains the post.  You will have to resubmit this post and then make the required submission comment.  Please [see here for more info.](http://reddit.com/r/{submission.subreddit}/wiki/submissions)  As an example, this message is about 588 characters. \n\n*I am a bot. Replies and chats will not receive replies.*  If you feel this was done in error, or would like better clarification or need further assistance, please [message the moderators.](https://www.reddit.com/message/compose?to=/r/{submission.subreddit}&subject=Question regarding the removal of this submission by /u/{submission.author}&message=I have a question regarding the removal of this submission: {submission.permalink})'

        # Ignore self posts
        if submission.is_self:
            continue

        # Get the UTC unix timestamp
        ts = submission.created_utc

        # Convert to datetime format
        post_time = dt.utcfromtimestamp(ts)

        # Skip any post before today
        if post_time <= dt(2022, 4, 30, 0, 0):
            continue

        # Print a line break between each post
        print('\n')

        # Current the current UTC time
        current_time = dt.utcnow()

        # Number of whole hours (seconds / 60 / 60) between posts
        hours_since_post = int((current_time - post_time).seconds / 3600)

        print(f'{post_time} - ({hours_since_post} min) - {submission.title}')

        # Check if we've already marked this as valid
        if submission.id in valid_posts:
            print('\t # Already checked - post valid.')

            # Go to next loop
            continue

        # Check if passed the minimum
        if hours_since_post >= MINIMUM_HOURS:

            # Once the minimum has passed
            # Create a flag, if this stays False, post to be removed
            op_left_correct_comment = False

            # Get all top level comments from the post
            for top_level_comment in submission.comments:


                # Look for a comment by the author
                if top_level_comment.is_submitter:

                    print('\t# OP has commented')

                    # Reset the variable
                    match_found = None

                    # Grab the body
                    comment_body = top_level_comment.body

                    # Check if it matches our regex - multiline not required as it displays \n line breaks
                    match_found = re.search(RGX_CHAR_200, comment_body)

                    # If there is no match found
                    if not match_found is None:

                        # Flag as correct
                        op_left_correct_comment = True

                        # Leave this loop
                        break

            # Check if the flag has changed
            if not op_left_correct_comment:

                print('\t# OP has NOT left a valid comment!')

                # # Remove and lock the post
                submission.mod.remove()
                submission.mod.lock()

                # # Leave a comment and remove it
                removal_comment = submission.reply(REMOVAL_REPLY)
                removal_comment.mod.lock()
                removal_comment.mod.distinguish(how='yes', sticky=True)

                print('\t# Post removed.')

            else:
                # If correct, add to exceptions list
                print('\t # Post valid')
                valid_posts.append(submission.id)

    # Send back the posts we've marked as valid
    return valid_posts

############################################################################
############################################################################
############################################################################

# Bot starts here

if __name__ == "__main__":

    try:
            # Connect to reddit and return the object
            r = reddit_login()

            # Connect to the sub
            subreddit = r.subreddit(SUB_NAME)

    except Exception as e:
        print('\t\n### ERROR - Could not connect to reddit.')
        sys.exit(1)

    # A list of posts already valid, keep this in memory so we don't keep checking these
    valid_posts = []

    # Loop the bot
    while True:

        try:
            # Get the latest submissions after emptying variable
            submissions = None
            submissions = get_latest_submissions(subreddit)
        except Exception as e:
            print('\t### ERROR - Could not get posts from reddit')

        # If there are posts, start scanning
        if not submissions is None:

            # Once you have submissions, check valid posts
            valid_posts = check_submissions(submissions, valid_posts)

        # Loop every X seconds (20 minutes)
        sleep_until = (dt.now() + td(0, SLEEP_SECONDS)).strftime('%H:%M:%S')  # Add 0 days, 1200 seconds
        print(f'\nSleeping until {sleep_until}') #%Y-%m-%d

        time.sleep(SLEEP_SECONDS)
