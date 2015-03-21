#!/usr/bin/env python

import requests
from bs4 import BeautifulSoup
import re
import sys

USER_PAGE_BASEURL = "http://scifi.stackexchange.com/users/"
USER_PAGE_OPTIONS = "/?tab=activities&sort=reviews"
MAIN_REVIEWS = 200
SUB_REVIEWS = 80


def fetch_webpage ( url, options, http_error_action = None ) :
    try:
        # Fetch the webpage.
        response = requests.get(url, params=options)
        #requests.get(USER_PAGE_BASEURL + user_id, params = USER_PAGE_OPTIONS)

        # print the URL
        #print "Fetching page:", response.url

        # Confirm page was loaded.
        response.raise_for_status()
    except requests.HTTPError:
        if http_error_action == None:
            print "HTTP Error", response.status_code
            sys.exit(1)
        else:
            print "Invalid", http_error_action + ", please try again"
            return None
    except (requests.ConnectionError, requests.Timeout, requests.TooManyRedirects):
        print "Connectivity issue. Please confirm you can access the Stack Exchange site."
        sys.exit(1)

    # Load the page into BeautifulSoup, return soup.
    return BeautifulSoup(response.text)

def fetch_reviews ( user, num_of_reviews ):
    user_options = { "tab" : "allactions", "sort" : "reviews", "page" : 1}
    reviews_so_far = {}
    next_link = ""
    
    while len(reviews_so_far) < num_of_reviews and next_link != None:
        soup = fetch_webpage(USER_PAGE_BASEURL + user, user_options, "review page")
        
        # Get review items from page.
        reviews = soup.find_all( "a", href = re.compile("(close)|(reopen)"), class_ = "reviewed-action")

        for review in reviews:
            reviews_so_far[ review.attrs['href'] ] = review.string

        print "Number of reviews for userid", str(user) + ":", len(reviews_so_far)
        
        user_options['page'] += 1

        next_link = soup.find( rel = "next" )

    # Return dict of reviews that we found.
    return reviews_so_far

def fetch_user(usertype):
    correct_user = "n"
    
    while correct_user not in ('yes', 'ye', 'y', ''):
        user = raw_input("What's is the ID for the " + usertype + " user? ")

        try:
            int(user)
        except ValueError:
            print "Only input numerical IDs."
            continue

        user_soup = fetch_webpage(USER_PAGE_BASEURL + user, None, "user")

        try:
            username = user_soup.find(id="user-displayname").string
        except AttributeError:
            continue
            
        correct_user = raw_input("Is that " + username + "? [Y/n] ").lower()

    return user

class User:
    def __init__ (self, usertype):
        self.userid = fetch_user(usertype)
        self.reviews = {}
        self.comparison = {}

        user_soup = fetch_webpage(USER_PAGE_BASEURL + self.userid, None, "user")
        # Convert to unicode to workaround python issue #175057
        self.username = unicode(user_soup.find(id="user-displayname").string)

    def fetch_reviews(self, num_reviews):
        self.reviews = fetch_reviews(self.userid, num_reviews)

    def clear_reviews(self):
        self.reviews = {}
        self.comparison = {}



main_user = User("main")

# Get list of users to compare against the main user
sub_users = []
another_user = "y"

while another_user in ('yes', 'ye', 'y', ''):
    sub_users.append( User("comparison") )

    another_user = raw_input("Add another user to compare? [Y/n] ").lower()

print "Getting reviews for main user..."
main_user.fetch_reviews(MAIN_REVIEWS)

print "Getting reviews for comparison users..."
for sub in sub_users:
    sub.fetch_reviews(SUB_REVIEWS)

# Compare the reviews.
for sub in sub_users:
    for (key, val) in sub.reviews.items():
        if key in main_user.reviews:
            sub.comparison[ key ] = (val == main_user.reviews[key])

# Report results.
for sub in sub_users:
    # Calculate stats.
    agree = sum( sub.comparison.values() )
    disagree = sum( map( lambda x: not x, sub.comparison.values() ) )

    # Print results.
    print sub.username, "agrees with", main_user.username, agree, "out of", len(sub.comparison), "times."
    print sub.username, "disagrees with", main_user.username, disagree, "out of", len(sub.comparison), "times."

