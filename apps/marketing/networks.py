"""The social networks the shop posts to, and what each allows.

Every network gets drafts.  Posting itself happens one of two ways
(publishers.py):

- **live**, through the network's own API, for the networks named in
  settings.MARKETING_POST_LIVE that have one we can use: Bluesky (free),
  Facebook Pages and Instagram (Meta's Graph API, free, needs a Business
  account linked to a Page) and Pinterest (free API, needs an app);
- **by hand** for everything else: at its time the post shows on the
  owner's dashboard with its text ready to copy, and the owner marks it
  posted.  X and TikTok are always by hand: X charges for API posting,
  and TikTok lets unaudited apps post only privately.

Text limits are the networks' own, counted roughly as Python characters
(Bluesky counts graphemes, X counts each link as 23).
"""

import re
from dataclasses import dataclass

URL_RE = re.compile(r"https?://\S+")


@dataclass(frozen=True)
class Network:
    name: str
    label: str
    max_chars: int
    # Whether the link goes in the text (else in the post's own link field,
    # or nowhere: Instagram captions don't make links clickable).
    link_in_text: bool = True
    needs_image: bool = False
    needs_video: bool = False
    # Has an API we post through when the owner turns it on.
    api: bool = False
    # Links count as this many characters (X's t.co), or 0 for their length.
    link_chars: int = 0
    why_by_hand: str = ""
    advice: str = ""

    def length(self, text):
        if self.link_chars:
            return len(URL_RE.sub("x" * self.link_chars, text))
        return len(text)


NETWORKS = {
    network.name: network for network in (
        Network("instagram", "Instagram", 2200, link_in_text=False, needs_image=True, api=True,
                advice="Needs a photo.  Links in captions are not clickable: say \"link in bio\" if you need one."),
        Network("facebook", "Facebook", 5000, link_in_text=False, api=True,
                advice="The link shows as a preview card under the text."),
        Network("pinterest", "Pinterest", 500, link_in_text=False, needs_image=True, api=True,
                advice="Needs a photo; the pin links to the shop page.  Title is the first line, up to 100 "
                       "characters."),
        Network("bluesky", "Bluesky", 300, api=True, advice="300 characters including the link."),
        Network("x", "X", 280, link_chars=23,
                why_by_hand="X charges for posting through its API, so you post these yourself.",
                advice="280 characters; a link counts as 23."),
        Network("tiktok", "TikTok", 2200, link_in_text=False, needs_video=True,
                why_by_hand="TikTok needs a video, and lets apps it hasn't audited post only privately, so you post "
                            "these yourself.",
                advice="The draft is the caption for your video."),
    )
}

CHOICES = [(network.name, network.label) for network in NETWORKS.values()]


def get(name):
    return NETWORKS[name]
