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
import pprint
import string
from time import gmtime, strftime

default_sub='fakefakefake'
limit=1000

def url_to_subreddit(url):
	"""Extract the subreddit name from a Reddit URL"""
	urlList = string.split(url,'/')
	return urlList[4]

def get_karma_breakdown(user,reddit,limit, thing_type="submissions"):
    """
	Create a dictionary with karma breakdown by subreddit.

	Takes a user and a thing_type (either 'submissions' or 'comments')
	as input. Return a directory where the keys are display names of
	subreddits, like proper or python, and the values are how much
	karma the user has gained in that subreddit.

	Function borrowed from: https://github.com/Damgaard/Reddit-Bots
	
	Thanks /u/_Damgaard_
	"""
    karma_by_subreddit = {}
    user = reddit.get_redditor(user)
    gen = (user.get_comments(limit=limit) if thing_type == "comments" else
           user.get_submitted(limit=limit))
    for thing in gen:
        subreddit = thing.subreddit.display_name
        karma_by_subreddit[subreddit] = (karma_by_subreddit.get(subreddit, 0)
                                         + thing.ups - thing.downs)
    return karma_by_subreddit

def calc_karma_totals(comment_karma,submission_karma):
	"""Calculate the combined karma that the user has in each subreddit.

	Takes the karma breakdwon for comments and submissions as a dictionaries
	for input. Returns a dictionary that has the sum of both comment and combined 
	karma broken down by subreddit.
	"""
	combined_karma = {}
	subreddits = set(comment_karma.keys()).union(set(submission_karma.keys()))
	for subreddit in subreddits:
		if (comment_karma.get(subreddit) is not None
			and submission_karma.get(subreddit) is not None):
			combined_karma[subreddit] = comment_karma.get(subreddit) 
			+ submission_karma.get(subreddit)
		elif comment_karma.get(subreddit) is not None: 
			combined_karma[subreddit] =comment_karma.get(subreddit) 
		elif submission_karma.get(subreddit) is not None:
			combined_karma[subreddit] =submission_karma.get(subreddit) 
		else:
			raise Exception("Cannot Find Subreddit") #This should never happen
	return combined_karma


def get_user_info(user,reddit,get_karma=True):
	user_info = {}
	if get_karma:
		user_info['submission_karma_breakdown'] = get_karma_breakdown(user,reddit,limit)
		user_info['comment_karma_breakdown'] = get_karma_breakdown(user,reddit,limit,'comment')
		user_info['combined_karma_breakdown'] = calc_karma_totals(
			user_info['comment_karma_breakdown'],
			user_info['submission_karma_breakdown'])
	user_info['redditor']=user

	return user_info

def get_target_info(subredditName,reddit):
	target_info = {}
	target = reddit.get_subreddit(subredditName)
	moderators = reddit.get_moderators(target)
	target_info['praw_subreddit'] = target
	target_info['moderators'] = []
	for moderator in moderators:
		target_info['moderators'].append(get_user_info(moderator,reddit,False))
	
	target_info['latest_submissions'] = target.get_new()
	target_info['latest_comments'] = target.get_new()

	return target_info

def format_karma_report(user):
	comment = "### Karma Breakdown ###\n"
	comment = (comment + "Karma for the user's latest "+
			str(limit)+" comments and submissions\n\n")
	comment = comment + "Subreddit | Link | Comment | Total \n" 
	comment = comment + "Subreddit | -:-| -:- | -:- \n" 

	for key in user['combined_karma_breakdown'].keys():
		comment = (comment + key + " | " +
			str(user['submission_karma_breakdown'].get(key)) + " | " +
			str(user['comment_karma_breakdown'].get(key)) + " | " +
			str(user['combined_karma_breakdown'].get(key)) + " \n ") 

	return comment

def format_user_report(user):
	"""
	Create a markdown formated string from the information in the given user.

	Takes a user diectionary that has a PRAW User object, and karma breakdown
	dictionaries for submissions and comment karma
	"""

	name = user['redditor'].name
	comment = "## Report for /u/"+name+"/ ##\n\n"
	comment = (comment + "User account was created at " +
		strftime("%A, %d %B %Y %H:%M:%S +0000", gmtime(user['redditor'].created_utc)) 
		+ "\n\n")
	
	comment = (comment + "User has verified E-mail:" + 
		str(user['redditor'].has_verified_email) + "\n\n")
	comment = (comment + "User has Reddit Gold^tm:" + 
		str(user['redditor'].is_gold) + "\n\n")
	comment = (comment + "User Total Comment Karma:" + 
		str(user['redditor'].comment_karma) + "\n\n")
	comment = (comment + "User Total Submission Karma:" + 
		str(user['redditor'].link_karma)+ "\n\n")

	if(user.get('submission_karma_breakdown') is not None):
		comment = comment + format_karma_report(user)
	
	comment = comment+"\n\n"
	
	return comment

def format_target_report(target_sub):
	subreddit_name =target_sub['praw_subreddit'].display_name
	comment = ""
	comment = (comment +"Subreddit /r/"+subreddit_name+"/ currently has "+
			  str(len(target_sub['moderators'])) + "Moderators") 
	comment = (comment + "### Moderators of /r/"+subreddit_name+ "\n\n")
	for moderator in target_sub['moderators']:
		comment = comment+format_user_report(moderator)

	return comment

	
def format_comment(target_sub,author):
	comment = "# Report for Requestor \n\n" 
	comment = comment + format_user_report(author)
	comment = comment + "# Report for Requested Subreddit \n\n" 
	comment = comment + format_target_report(target_sub)
	return comment

def publish_comment(submission,comment):
	

def main():
	argparser = argparse.ArgumentParser(description=__doc__)
	argparser.add_argument('--subreddit',help='Chooses a subreddit to target',default=default_sub)
	argparser.add_argument('--no-comment',help='Do not post comments in threads',default=False,dest='no_comment')
	argparser.add_argument('--print-comment',help='Print comments to stdout',default=False,dest='print_comment')
	argparser.add_argument('--ignore-dup',help='Ingore Duplicates, comment to thread even if the bot already has',default=False,dest='ignore_dup')

	args = argparser.parse_args()

	subredditName=args.subreddit
	no_comment = args.no_comment
	print_comment = args.print_comment	
	ignore_dup = args.ignore_dup	

	reddit = praw.Reddit('redditRequestMonitor bot by /u/ki6uoc (development)')
	reddit.login()
	
	subreddit=reddit.get_subreddit(subredditName)

	submissions=subreddit.get_new(limit=10)

	for submission in submissions:
		already_posted = False 
		if not ignore_dup:
			for comment in praw.helpers.flatten_tree(submission.comments):
				if comment.author.name == r.user.name:
					already_posted = True		
	
		if not already_posted:
			authorInfo = get_user_info(submission.author,reddit)
			targetSubInfo = get_target_info(url_to_subreddit(submission.url),reddit)

			comment = format_comment(targetSubInfo,authorInfo)

			if(print_comment):
				print(comment)
			
			if not no_comment:
				publish_comment(submission,comment)
		
	sys.exit();


if __name__ == "__main__":
	main()
