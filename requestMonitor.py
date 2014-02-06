#!/usr/bin/python

"""
RequestMonitor.py

The main() script file that is intended to be called on a crontab to 
monitor /r/redditRequest and post information about the subreddits mentioned
and the submitter of each thread. 
"""
import praw
import sys
import argparse

default_sub='fakefakefake'


def main():
	argparser = argparse.ArgumentParser(description=__doc__)
	argparser.add_argument('--subreddit',help='Chooses a subreddit to target')
	
	args = argparser.parse_args()

	subreddit=default_sub
	if(args.subreddit):
		subreddit=args.subreddit

	reddit = praw.Reddit('redditRequestMonitor bot by /u/ki6uoc (development)')
	#	reddit.login('RedditRequestBot','cd43bbfa035c9bc4cdbf7d3e99e77eeb')
	reddit.login()
	


	sys.exit();


if __name__ == "__main__":
	main()
