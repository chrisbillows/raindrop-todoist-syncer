from raindrop import RaindropGetNewOauth, MissingRefreshTokenError

"""
Temp file just as a place to run oauth referesher before automating. DELETE WHEN THAT 
IS BUILT.
"""

if __name__ == "__main__":
    try:
        rd_oauth = RaindropGetNewOauth()
        new_oauth_code = rd_oauth.new_token_process_runner()
        print(new_oauth_code)
    except MissingRefreshTokenError as e:
        print(e)
