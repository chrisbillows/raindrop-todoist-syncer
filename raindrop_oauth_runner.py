from raindrop import RaindropGetNewOauth, ExistingTokenError

if __name__ == "__main__":
    # you need to delete the expired token first
    try:
        rd_oauth = RaindropGetNewOauth()
        new_oauth_code = rd_oauth.oauth_process_runner()
        print(new_oauth_code)
    except ExistingTokenError as e:
        print(e)
    
