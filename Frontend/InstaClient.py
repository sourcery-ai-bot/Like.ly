import bottle
import beaker.middleware
#from bson import json_util
from datetime import datetime
from json import dumps
from pprint import pprint
import http
import json
import requests
from bottle import route, redirect, post, run, request, hook
from instagram import client, subscriptions

bottle.debug(True)

class PreviousPost:
    #A class that will be used to create previous post JSON objects to put in the database
    def __init__(self, PostID, Link, UserID, RealLikes, Location, PostTime):
        self.PostID = PostID
        self.Link = Link
        self.UserID = UserID
        self.RealLikes = RealLikes
        self.Location = Location
        self.PostTime = PostTime

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                sort_keys=True, indent=4)

class newPostSchema:
#A class that will be used to create new post JSON objects to put in the database"
    def __init__(self, PostID, Image, UserID, RealLikes, EstimatedLikes, EstimatedTime, Location, PostTime):
        self.PostID = PostID
        self.Image = Image
        self.UserID = UserID
        self.RealLikes = RealLikes
        self.EstimatedLikes = EstimatedLikes
        self.EstimatedTime = EstimatedTime
        self.Location = Location
        self.PostTime = PostTime

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__)

class userSchema:
# A class that will be used to create user JSON objects to put in the database
    def __init__(self, UserID, Name, AverageLocation, Followers, LastPictureTime, TimeBetweenEachPicture):
        self.UserID = UserID
        self.Name = Name
        self.AverageLocation = AverageLocation
        self.Followers = Followers
        self.LastPictureTime = LastPictureTime
        self.TimeBetweenEachPicture = TimeBetweenEachPicture

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
            sort_keys=True, indent=4)

session_opts = {
    'session.type': 'file',
    'session.data_dir': './session/',
    'session.auto': True,
}

app = beaker.middleware.SessionMiddleware(bottle.app(), session_opts)

CONFIG = {
    'client_id': 'e7903fc1a2c74d48bb5327fbc78fed53',
    'client_secret': 'e25fff3e4b9b431d8b22efb7944f6a4b',
    'redirect_uri': 'http://localhost:8515/oauth_callback'
}

unauthenticated_api = client.InstagramAPI(**CONFIG)

@hook('before_request')
def setup_request():
    request.session = request.environ['beaker.session']

def process_tag_update(update):
    print(update)

reactor = subscriptions.SubscriptionsReactor()
reactor.register_callback(subscriptions.SubscriptionType.TAG, process_tag_update)

@route('/')
def home():
    try:
        url = unauthenticated_api.get_authorize_url(scope=["likes","comments","relationships", "basic", "follower_list", "public_content"])
        return '<a href="%s">Connect with Instagram</a>' % url
    except Exception as e:
        print(e)

def get_nav():
    nav_menu = ("<h1>Python Instagram</h1>"
                "<ul>"
            #     "<li><a href='/recent'>User Recent Media</a> Calls user_recent_media - Get a list of a user's most recent media</li>"
                #    "<li><a href='/user_media_feed'>User Media Feed</a> Calls user_media_feed - Get the currently authenticated user's media feed uses pagination</li>"
            #        "<li><a href='/location_recent_media'>Location Recent Media</a> Calls location_recent_media - Get a list of recent media at a given location, in this case, the Instagram office</li>"
            #    "<li><a href='/media_search'>Media Search</a> Calls media_search - Get a list of media close to a given latitude and longitude</li>"
            #    "<li><a href='/user_search'>User Search</a> Calls user_search - Search for users on instagram, by name or username</li>"
            #        "<li><a href='/user_follows'>User Follows</a> Get the followers of @instagram uses pagination</li>"
            #        "<li><a href='/location_search'>Location Search</a> Calls location_search - Search for a location by lat/lng</li>"
                   "<li> <div> <input type='file' name='pic' accept='image/*'><a href='/tag_search'> </div> Upload your picture and find out how many likes you'll get!</li>"
                "</ul>")
    return nav_menu

@route('/oauth_callback')
def on_callback():
    code = request.GET.get("code")
    if not code:
        return 'Missing code'
    try:
        access_token, user_info = unauthenticated_api.exchange_code_for_access_token(code)
        if not access_token:
            return 'Could not get access token'
        api = client.InstagramAPI(access_token=access_token, client_secret=CONFIG['client_secret'])
        request.session['access_token'] = access_token
    except Exception as e:
        print(e)
    return get_nav()

"""
@route('/recent')
def on_recent():
    content = "<h2>User Recent Media</h2>"
    access_token = request.session['access_token']
    if not access_token:
        return 'Missing Access Token'
    try:
        api = client.InstagramAPI(access_token=access_token, client_secret=CONFIG['client_secret'])
        recent_media, next = api.user_recent_media()
        photos = []
        for media in recent_media:
            photos.append('<div style="float:left;">')
            if(media.type == 'video'):
                photos.append('<video controls width height="150"><source type="video/mp4" src="%s"/></video>' % (media.get_standard_resolution_url()))
            else:
                photos.append('<img src="%s"/>' % (media.get_standard_resolution_url()))
            photos.append("<br/> <a href='/media_like/%s'>Like</a>  <a href='/media_unlike/%s'>Un-Like</a>  LikesCount=%s</div>" % (media.id,media.id,media.like_count))
        content += ''.join(photos)
    except Exception as e:
        print(e)
    return "%s %s <br/>Remaining API Calls = %s/%s" % (get_nav(),content,api.x_ratelimit_remaining,api.x_ratelimit)
"""

@route('/user_media_feed')
def on_user_media_feed():
    access_token = request.session['access_token']
    content = "<h2>User Media Feed</h2>"
    if not access_token:
        return 'Missing Access Token'
    try:
        api = client.InstagramAPI(access_token=access_token, client_secret=CONFIG['client_secret'])
        media_feed, next = api.user_media_feed()
        photos = []
        conn = http.client.HTTPConnection("104.199.211.96:65")
        headers = {
            'authorization': "Basic YWRtaW46YnJheGRheTEyMw==",
            'content-type': "application/json",
            'cache-control': "no-cache",
            }

        for media in media_feed:
            picture = PreviousPost(media.id, media.get_standard_resolution_url(), media.user.id, media.like_count, media.location, media.created_time)
            payload = picture.toJSON()
            print(payload)
            # conn.request("POST", "http://104.199.211.96:65/PreviousPost", payload, headers)

            # res = conn.getfresponse()
            # data = res.read()
            photos.append('<img src="%s"/>' % media.get_standard_resolution_url())

        counter = 1
        while next and counter < 3:
            media_feed, next = api.user_media_feed(with_next_url=next)
            photos.extend(
                '<img src="%s"/>' % media.get_standard_resolution_url()
                for media in media_feed
            )

            counter += 1
        content += ''.join(photos)
    except Exception as e:
        print(e)
    return f"{get_nav()} {content} <br/>Remaining API Calls = {api.x_ratelimit_remaining}/{api.x_ratelimit}"

@route('/location_recent_media')
def location_recent_media():
    access_token = request.session['access_token']
    content = "<h2>Location Recent Media</h2>"
    if not access_token:
        return 'Missing Access Token'
    try:
        api = client.InstagramAPI(access_token=access_token, client_secret=CONFIG['client_secret'])
        recent_media, next = api.location_recent_media(location_id=514276)
        photos = [
            '<img src="%s"/>' % media.get_standard_resolution_url()
            for media in recent_media
        ]

        content += ''.join(photos)
    except Exception as e:
        print(e)
    return f"{get_nav()} {content} <br/>Remaining API Calls = {api.x_ratelimit_remaining}/{api.x_ratelimit}"
"""
@route('/media_search')
def media_search():
    access_token = request.session['access_token']
    content = "<h2>Media Search</h2>"
    if not access_token:
        return 'Missing Access Token'
    try:
        api = client.InstagramAPI(access_token=access_token, client_secret=CONFIG['client_secret'])
        media_search = api.media_search(lat="37.7808851",lng="-122.3948632",distance=1000)
        photos = []
        for media in media_search:
            photos.append('<img src="%s"/>' % media.get_standard_resolution_url())
        content += ''.join(photos)
    except Exception as e:
        print(e)
    return "%s %s <br/>Remaining API Calls = %s/%s" % (get_nav(),content,api.x_ratelimit_remaining,api.x_ratelimit)

@route('/media_popular')
def media_popular():
    access_token = request.session['access_token']
    content = "<h2>Popular Media</h2>"
    if not access_token:
        return 'Missing Access Token'
    try:
        api = client.InstagramAPI(access_token=access_token, client_secret=CONFIG['client_secret'])
        media_search = api.media_popular()
        photos = []
        for media in media_search:
            photos.append('<img src="%s"/>' % media.get_standard_resolution_url())
        content += ''.join(photos)
    except Exception as e:
        print(e)
    return "%s %s <br/>Remaining API Calls = %s/%s" % (get_nav(),content,api.x_ratelimit_remaining,api.x_ratelimit)
"""
@route('/user_search')
def user_search():
    access_token = request.session['access_token']
    content = "<h2>User Search</h2>"
    if not access_token:
        return 'Missing Access Token'
    try:
        api = client.InstagramAPI(access_token=access_token, client_secret=CONFIG['client_secret'])
        user_search = api.user_search(q="Instagram")
        users = [
            '<li><img src="%s">%s</li>' % (user.profile_picture, user.username)
            for user in user_search
        ]

        content += ''.join(users)
    except Exception as e:
        print(e)
    return f"{get_nav()} {content} <br/>Remaining API Calls = {api.x_ratelimit_remaining}/{api.x_ratelimit}"

@route('/user_follows')
def user_follows():
    access_token = request.session['access_token']
    content = "<h2>User Follows</h2>"
    if not access_token:
        return 'Missing Access Token'
    try:
        api = client.InstagramAPI(access_token=access_token, client_secret=CONFIG['client_secret'])
        # 25025320 is http://instagram.com/instagram
        user_followed_by, next = api.user_followed_by()
        users = [
            '<li><img src="%s">%s</li>' % (user.profile_picture, user.username)
            for user in user_followed_by
        ]

        while next:
            user_followed_by, next = api.user_followed_by(with_next_url=next)
            users.extend(
                '<li><img src="%s">%s</li>'
                % (user.profile_picture, user.username)
                for user in user_followed_by
            )

        content += ''.join(users)
    except Exception as e:
        print(e)
    return f"{get_nav()} {content} <br/>Remaining API Calls = {api.x_ratelimit_remaining}/{api.x_ratelimit}"

@route('/location_search')
def location_search():
    access_token = request.session['access_token']
    content = "<h2>Location Search</h2>"
    if not access_token:
        return 'Missing Access Token'
    try:
        api = client.InstagramAPI(access_token=access_token, client_secret=CONFIG['client_secret'])
        location_search = api.location_search(lat="37.7808851",lng="-122.3948632",distance=1000)
        locations = [
            '<li>%s  <a href="https://www.google.com/maps/preview/@%s,%s,19z">Map</a>  </li>'
            % (
                location.name,
                location.point.latitude,
                location.point.longitude,
            )
            for location in location_search
        ]

        content += ''.join(locations)
    except Exception as e:
        print(e)
    return f"{get_nav()} {content} <br/>Remaining API Calls = {api.x_ratelimit_remaining}/{api.x_ratelimit}"

@route('/tag_search')
def tag_search():
    access_token = request.session['access_token']
    return "<h2>Predicted Likes: 156</h2>"

@route('/realtime_callback')
@post('/realtime_callback')
def on_realtime_callback():
    mode = request.GET.get("hub.mode")
    challenge = request.GET.get("hub.challenge")
    verify_token = request.GET.get("hub.verify_token")
    if challenge:
        return challenge
    x_hub_signature = request.header.get('X-Hub-Signature')
    raw_response = request.body.read()
    try:
        reactor.process(CONFIG['client_secret'], raw_response, x_hub_signature)
    except subscriptions.SubscriptionVerifyError:
        print("Signature mismatch")

bottle.run(app=app, host='localhost', port=8515, reloader=True)
