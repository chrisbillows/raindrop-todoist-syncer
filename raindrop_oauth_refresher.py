from raindrop import RaindropOauthHandler, MissingRefreshTokenError

"""
Temp file just as a place to run oauth referesher before automating. DELETE WHEN THAT
IS BUILT.

THIS DOESN'T REMOVE OLD TOKEN!
"""

if __name__ == "__main__":
    try:
        rd_oauth = RaindropOauthHandler()
        new_oauth_code = rd_oauth.refresh_token_process_runner()
        print(new_oauth_code)
    except MissingRefreshTokenError as e:
        print(e)
