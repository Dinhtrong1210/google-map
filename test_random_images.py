from review_bot import GoogleMapsReviewBot
import os

bot = GoogleMapsReviewBot(headless=True)
bot.set_status_callback(lambda msg, is_error=False: print(f"[{'ERR' if is_error else 'OK'}] {msg}"))

print("=== Test get_random_images ===")
print(f"Files in images/: {os.listdir('images')}")
images = bot.get_random_images('images', max_count=3)
print(f"Result: {images}")
bot.close_browser()
