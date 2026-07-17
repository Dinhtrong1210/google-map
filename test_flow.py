from review_bot import GoogleMapsReviewBot
import time, os

def test_callback(msg, is_error=False):
    prefix = "ERROR" if is_error else "INFO"
    print(f"[{prefix}] {msg}")

accounts = [
    {'email': 'ngotuanpro88@gmail.com', 'password': 'Dungmedia24@'},
]
url = 'https://www.google.com/maps/place/Ng%C3%A2n+H%C3%A0ng+N%C3%B4ng+Nghi%E1%BB%87p+V%C3%A0+Ph%C3%A1t+Tri%E1%BB%83n+N%C3%B4ng+Th%C3%B4n+Vi%E1%BB%87t+Nam+@+Chi+Nh%C3%A1nh+H%C3%A0+T%C4%A9nh/@18.5380314,105.2831131,11z/data=!4m10!1m2!2m1!1zTmfDom4gaMOgbmcgTsO0bmcgbmdoaeG7h3AgdsOgIFBow6F0IHRyaeG7g24gTsO0bmcgdGjDtG4gVmnhu4d0IE5hbQ!3m6!1s0x3139b4caf4daf5ad:0x376339de9864bb0a!8m2!3d18.451453!4d105.7777702!15sCkNOZ8OibiBow6BuZyBOw7RuZyBuZ2hp4buHcCB2w6AgUGjDoXQgdHJp4buDbiBOw7RuZyB0aMO0biBWaeG7h3QgTmFtIgOIAQGSAQRiYW5r4AEA!16s%2Fg%2F1hf68qftt?entry=ttu&g_ep=EgoyMDI2MDcxNC4wIKXMDSoASAFQAw%3D%3D'

for i, acc in enumerate(accounts):
    print(f"\n{'='*50}")
    print(f"ACCOUNT {i+1}/{len(accounts)}: {acc['email']}")
    print(f"{'='*50}")

    profile_dir = os.path.join(os.getcwd(), 'profiles', f'profile_{i}')
    os.makedirs(profile_dir, exist_ok=True)

    bot = GoogleMapsReviewBot(
        headless=False,
        user_data_dir=profile_dir,
        debug_port=9222 + i
    )
    bot.set_status_callback(test_callback)

    try:
        if not bot.start_browser():
            continue
        if not bot.login_google(acc['email'], acc['password']):
            continue
        if not bot.navigate_to_place(url):
            continue
        if not bot.click_write_review_button():
            continue
        if not bot.select_star_rating(5):
            continue
        if not bot.write_comment("Test review from multi-account bot!"):
            continue
        if not bot.submit_review():
            continue
        print(f"ACCOUNT {i+1} THANH CONG!")
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        time.sleep(3)
        bot.close_browser()

print("\nHOAN TAT!")
