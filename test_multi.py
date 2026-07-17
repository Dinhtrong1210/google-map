"""
test_multi.py - Test multi-account flow with new URL
"""
import time
import os
import sys
from review_bot import GoogleMapsReviewBot

def test_single_account():
    """Test single account with new URL"""
    new_url = "https://www.google.com/maps/place/Ng%C3%A2n+h%C3%A0ng+n%C3%B4ng+nghi%E1%BB%87p+v%C3%A0+ph%C3%A1t+tri%E1%BB%83n+n%C3%B4ng+th%C3%B4n+Vi%E1%BB%87t+Nam/@18.5380314,105.2831131,11z/data=!4m10!1m2!2m1!1zTmfDom4gaMOgbmcgTsO0bmcgbmdoaeG7h3AgdsOgIFBow6F0IHRyaeG7g24gTsO0bmcgdGjDtG4gVmnhu4d0IE5hbQ!3m6!1s0x3139d1e337e2a979:0x7474a65d26136071!8m2!3d18.7130519!4d105.675656!15sCkNOZ8OibiBow6BuZyBOw7RuZyBuZ2hp4buHcCB2w6AgUGjDoXQgdHJp4buDbiBOw7RuZyB0aMO0biBWaeG7h3QgTmFtIgOIAQGSAQRiYW5r4AEA!16s%2Fg%2F12hr5pgz6?entry=ttu&g_ep=EgoyMDI2MDcxNC4wIKXMDSoASAFQAw%3D%3D"
    
    email = "ngotuanpro88@gmail.com"
    password = "Dungmedia24@"
    comment = "Dich vu rat tot, nhan vien nhiet tinh! Se quay lai!"
    stars = 5
    
    print("=" * 60)
    print("TEST SINGLE ACCOUNT - NEW URL")
    print("=" * 60)
    
    bot = GoogleMapsReviewBot(headless=False, user_data_dir="profiles/test_single", debug_port=9222)
    bot.set_status_callback(lambda msg, err=False: print(f"{'[ERR]' if err else '[OK]'} {msg}"))
    
    try:
        if not bot.start_browser():
            print("❌ Failed to start browser")
            return False
        
        if not bot.login_google(email, password):
            print("❌ Failed to login")
            return False
        
        if not bot.navigate_to_place(new_url):
            print("❌ Failed to navigate to place")
            return False
        
        if not bot.click_write_review_button():
            print("❌ Failed to click write review button")
            return False
        
        if not bot.select_star_rating(stars):
            print("❌ Failed to select star rating")
            return False
        
        if not bot.write_comment(comment):
            print("❌ Failed to write comment")
            return False
        
        if not bot.submit_review():
            print("❌ Failed to submit review")
            return False
        
        print("✅ SINGLE ACCOUNT TEST PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        bot.close_browser()

if __name__ == "__main__":
    test_single_account()
