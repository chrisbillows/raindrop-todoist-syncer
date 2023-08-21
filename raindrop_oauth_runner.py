from raindrop import RaindropGetNewOauth, ExistingTokenError

if __name__ == "__main__":
    # TODO: this will be for the first run only. Auto refresh will be built into main.
    try:
        rd_oauth = RaindropGetNewOauth()
        new_oauth_code = rd_oauth.new_token_process_runner()
        print(new_oauth_code)
    except ExistingTokenError as e:
        print(e)
    
