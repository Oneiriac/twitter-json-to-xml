# Parses a file of JSON tweet objects (as collected by e.g. FireAnt):
# outputs selected information about each tweet to an XML file.
# Ignores retweets, but will output retweeted tweets and quoted tweets in the JSON collection.
# Author: Damon Cai

import json
from lxml import etree
from datetime import datetime


class TweetCollection:
    def __init__(self, input_json):
        self.tweet_ids = set()
        self.xml_root = etree.Element("tweets")
        self.parsed_tweets = self.json_reader(input_json)
        self.output_tweets = []

    def write_xml(self, output):
        """
        Writes tweets to an XML file, sorted by time (earlier first)
        :param output: path of the file to which the XML tree will be written
        :return: None
        """
        self.output_tweets.clear()
        for tweet in self.parsed_tweets:
            self.add_tweet(tweet)

        self.output_tweets.sort(key=lambda x: datetime.strptime(x.attrib["created_at"], "%a %b %d %H:%M:%S %z %Y"))

        for tweet_elem in self.output_tweets:
            self.xml_root.append(tweet_elem)

        with open(output, 'w', encoding='utf-8') as output:
            xml_string = etree.tostring(self.xml_root, encoding='utf-8', xml_declaration=True, pretty_print=True).decode('utf-8')
            output.write(xml_string)

    def add_tweet(self, tweet_dict):
        """
        Adds a <tweet> element to a collection of <tweet> elements stored in self.output_tweets
        Attributes:
            - "created_at"
            - "id"
            - "quoted_from"
        :param tweet_dict: dict parsed from a tweet JSON object
        :return: None
        """
        # Check if tweet has already been created; if not, create the tweet
        if tweet_dict["id"] in self.tweet_ids:
            return
        else:
            self.tweet_ids.add(tweet_dict["id"])

        # Filter out retweets, but parse the original tweet
        if "retweeted_status" in tweet_dict:
            self.add_tweet(tweet_dict["retweeted_status"])
            return

        # Create <tweet> element and append it to self.output_tweets
        tweet_elem = etree.Element("tweet")
        self.output_tweets.append(tweet_elem)
        # Add attributes
        tweet_elem.set("id", tweet_dict["id_str"])
        tweet_elem.set("created_at", tweet_dict["created_at"])
        # Check if tweet is quoted from another tweet; if it is, add that tweet
        if "quoted_status" in tweet_dict:
            tweet_elem.set("quoted_from", tweet_dict["quoted_status"]["id_str"])
            self.add_tweet(tweet_dict["quoted_status"])
        # Create <tweet_body> element under <tweet>
        body_elem = etree.SubElement(tweet_elem, "body")

        # Check if tweet is truncated: if it has been, use the extended_tweet for text
        if tweet_dict["truncated"]:
            tweet_text = tweet_dict["extended_tweet"]["full_text"]
        else:
            tweet_text = tweet_dict["text"]

        body_elem.text = tweet_text

        # Add the <details> element under <tweet>
        self.add_details(tweet_elem, tweet_dict)

    def add_user(self, parent_elem, user_dict):
        """
        Adds a <user> XML element to a parent XML element using information contained in user_dict
        :param parent_elem: parent XML element to which <user> will be added as a child
        :param user_dict: the dict corresponding to the parsed "user" attribute of a JSON tweet object
        :return: None
        """
        user_elem = etree.SubElement(parent_elem, "user")
        user_elem.set("screen_name", user_dict["screen_name"])
        user_elem.set("id", user_dict["id_str"])

    def add_details(self, parent_elem, tweet_dict):
        """
        Adds a <details> XML element to a parent XML element and populates it with sub-elements:
            - <user>: author
            - <hashtag> (multiple possible)
            - <user_mentions>: contains...
                - <user> (multiple possible): users mentioned in the tweet
            - <url> (multiple possible)
        :param parent_elem: parent XML element to which <details> will be added as a child (usually a <tweet>)
        :param tweet_dict: dict parsed from a tweet JSON object
        :return: None
        """
        # Create <details> element under <tweet>
        details_elem = etree.SubElement(parent_elem, "details")
        # Create <user> under <details>
        self.add_user(details_elem, tweet_dict["user"])

        # If tweet is truncated, use the extended_tweet dict instead
        if tweet_dict["truncated"]:
            entities_dict = tweet_dict["extended_tweet"]["entities"]
        else:
            entities_dict = tweet_dict["entities"]

        # Create <hashtag> elements under <details>
        for hashtag in entities_dict["hashtags"]:
            hashtag_elem = etree.SubElement(details_elem, "hashtag")
            hashtag_elem.text = hashtag["text"]
        # Create <user_mentions> element under <details>, containing <user> elements
        mentions_elem = etree.SubElement(details_elem, "user_mentions")
        for mentioned_user in entities_dict["user_mentions"]:
            self.add_user(mentions_elem, mentioned_user)
        # Create <url> elements under <details>
        for url in entities_dict["urls"]:
            url_elem = etree.SubElement(details_elem, "url")
            url_elem.text = url["expanded_url"]

    def json_reader(self, file):
        """
        Generator for parsing a JSON file.
        :param file: JSON file where each JSON object is on a single line of its own
        :return: generator of dicts parsed from JSON objects
        """
        with open(file, 'r', encoding='utf-8') as f:
            for line in f:
                yield json.loads(line)


def main():
    tweets = TweetCollection('tweets-larger.json')
    tweets.write_xml('tweets.xml')


if __name__ == "__main__":
    main()
