"""
Desktop Selenium Chrome WhatsApp Provider (core/whatsapp/selenium_driver.py)
Implements persistent QR login profiles, XPath locators, and typing simulation.
"""

import os
import re
import time
import random
import urllib.parse
from core.whatsapp.base import WhatsAppBaseProvider

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.keys import Keys
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    webdriver = None


class SeleniumChromeProvider(WhatsAppBaseProvider):
    """Handles Chrome browser automation for WhatsApp Web."""

    def __init__(self, log_callback=None, profile_dir=None):
        self.log_callback = log_callback or (lambda msg, lvl="INFO": None)
        self.profile_dir = profile_dir or os.path.join(os.getcwd(), "whatsapp_chrome_profile")
        self.driver = None
        self.is_paused = False
        self.is_stopped = False

    def log(self, message, level="INFO"):
        self.log_callback(message, level)

    def initialize(self):
        if not webdriver:
            self.log("Selenium is not installed! Run: pip install selenium webdriver-manager", "ERROR")
            return False

        self.log("Initializing Chrome browser with persistent profile...", "INFO")
        os.makedirs(self.profile_dir, exist_ok=True)

        options = Options()
        options.add_argument(f"--user-data-dir={self.profile_dir}")
        options.add_argument("--disable-notifications")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            # Mask navigator.webdriver for anti-bot detection
            try:
                self.driver.execute_cdp_cmd(
                    "Page.addScriptToEvaluateOnNewDocument",
                    {
                        "source": """
                            Object.defineProperty(navigator, 'webdriver', {
                                get: () => undefined
                            });
                        """
                    }
                )
            except Exception:
                pass
            self.driver.maximize_window()
            self.log("Opening WhatsApp Web...", "SUCCESS")
            self.driver.get("https://web.whatsapp.com")
            return True
        except Exception as e:
            self.log(f"Failed to launch Chrome driver: {str(e)}", "ERROR")
            return False

    def wait_for_login(self, timeout=120):
        self.log("Waiting for WhatsApp Web session... (Scan QR if needed)", "WARNING")
        start = time.time()
        while time.time() - start < timeout:
            if self.is_stopped:
                return False
            try:
                pane = self.driver.find_elements(By.XPATH, "//div[@id='pane-side'] | //div[@contenteditable='true'] | //div[@data-tab='3']")
                if pane:
                    self.log("WhatsApp Web session authenticated successfully!", "SUCCESS")
                    return True
            except Exception:
                pass
            time.sleep(2)
        return False

    def send_message(self, phone, text_content, media_path=None, sim_typing=True):
        if not self.driver:
            return False, "Driver is not running."

        clean_phone = re.sub(r"[^\d]", "", str(phone or ""))
        encoded = urllib.parse.quote(text_content or "")
        url = f"https://web.whatsapp.com/send?phone={clean_phone}&text={encoded}"
        self.driver.get(url)

        wait = WebDriverWait(self.driver, 25)

        invalid_xpaths = [
            "//div[contains(text(), 'Phone number shared via url is invalid')]",
            "//div[contains(text(), 'The phone number shared via url is invalid')]",
            "//div[contains(text(), 'URL is invalid')]",
            "//div[contains(text(), 'not on WhatsApp')]",
            "//div[contains(text(), 'isn’t on WhatsApp')]",
            "//div[contains(text(), 'is not on WhatsApp')]"
        ]

        msg_box_xpaths = [
            "//footer//div[@contenteditable='true']",
            "//div[@contenteditable='true'][@data-tab='10']",
            "//div[@contenteditable='true'][@data-tab='6']",
            "//div[@role='textbox'][@contenteditable='true']"
        ]

        try:
            msg_box = None
            for _ in range(25):
                if self.is_stopped:
                    return False, "Cancelled by user"

                # Check for invalid number dialog
                for xpath in invalid_xpaths:
                    invalid_els = self.driver.find_elements(By.XPATH, xpath)
                    if invalid_els:
                        # Dismiss modal dialog if present so it doesn't block next contact
                        try:
                            ok_btn = self.driver.find_elements(By.XPATH, "//div[@role='button'][contains(., 'OK')] | //button[contains(., 'OK')]")
                            if ok_btn:
                                ok_btn[0].click()
                                time.sleep(0.5)
                        except Exception:
                            pass
                        return False, "Invalid / Unregistered WhatsApp Number"

                # Check if message box has loaded
                for mb_xpath in msg_box_xpaths:
                    found = self.driver.find_elements(By.XPATH, mb_xpath)
                    if found:
                        msg_box = found[0]
                        break
                if msg_box:
                    break
                time.sleep(1)

            if not msg_box:
                # Double check for invalid number modal before failing
                for xpath in invalid_xpaths:
                    if self.driver.find_elements(By.XPATH, xpath):
                        return False, "Invalid / Unregistered WhatsApp Number"
                return False, "Chat message box failed to load"

            # Optional attachment handling
            if media_path and os.path.exists(media_path):
                clip_xpaths = [
                    "//div[@title='Attach']",
                    "//span[@data-icon='plus']",
                    "//span[@data-icon='plus-alt']",
                    "//span[@data-icon='clip']",
                    "//button[@aria-label='Attach']"
                ]
                clip_btn = None
                for cx in clip_xpaths:
                    try:
                        clip_btn = wait.until(EC.element_to_be_clickable((By.XPATH, cx)))
                        if clip_btn:
                            break
                    except Exception:
                        continue

                if clip_btn:
                    clip_btn.click()
                    time.sleep(1)

                    ext = os.path.splitext(media_path)[1].lower()
                    is_img_vid = ext in [".jpg", ".jpeg", ".png", ".webp", ".mp4"]
                    input_xpath = "//input[@accept='image/*,video/mp4,video/3gpp,video/quicktime']" if is_img_vid else "//input[@accept='*']"

                    file_input = wait.until(EC.presence_of_element_located((By.XPATH, input_xpath)))
                    file_input.send_keys(os.path.abspath(media_path))
                    time.sleep(2)

            # Send message: First try send button, with instant fallback to Enter key
            send_btn_xpaths = [
                "//span[@data-icon='send']/parent::button",
                "//button[@aria-label='Send']",
                "//button[span[@data-icon='send']]",
                "//footer//button[contains(@aria-label, 'Send') or span[@data-icon='send']]"
            ]

            sent = False
            for xpath in send_btn_xpaths:
                try:
                    btn = self.driver.find_element(By.XPATH, xpath)
                    if btn.is_displayed() and btn.is_enabled():
                        btn.click()
                        sent = True
                        break
                except Exception:
                    continue

            # Resilient fallback: Press ENTER in the message box if button click didn't trigger
            if not sent and msg_box:
                try:
                    msg_box.send_keys(Keys.ENTER)
                    sent = True
                except Exception:
                    pass

            if not sent:
                return False, "Send trigger failed (Send button & Enter key unreachable)"

            time.sleep(1.5)
            return True, "Sent successfully"

        except Exception as e:
            return False, f"Execution error: {str(e)}"

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
