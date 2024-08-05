import webbrowser
import time
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import threading



# chromium-browser --remote-debugging-port=8989 --user-data-dir=/home/SecondSight/chromedata
def start_chromium():
    # Run the command to start Chromium in another terminal
    process=subprocess.run(["chromium-browser", "--remote-debugging-port=8989", "--user-data-dir=/home/SecondSight/chromedata"])


def on_exit():
    # Terminate the Chromium subprocess upon script exit
    try:
        subprocess.run(["pkill", "-f", "chromium-browser"])
    except Exception as e:
        print(f"Error terminating Chromium subprocess: {e}")

# Create a thread object for the start_chromium function

chromium_thread = threading.Thread(target=start_chromium)

# Start the Chromium thread
chromium_thread.start()


opt=Options()
opt.add_experimental_option("debuggerAddress","localhost:8989")

service = Service('/usr/lib/chromium-browser/chromedriver')
driver = webdriver.Chrome(service=service,options=opt)
driver.get("http://www.google.com")


# Replace with the username of the person you want to call
target_username = "Gaurang Dosar"

# Open Telegram web app
driver.get("https://web.telegram.org/k/#5718246342")
driver.maximize_window()


try:
    
    time.sleep(40)
    
    links = driver.find_elements(By.XPATH, "//a[@href]")
    button_present = False
    
    for link in links:
        if "#5718246342" in link.get_attribute("href"):
            print("Button is present")
            link.click()
            button_present = True
            break
    
    if not button_present:
        print("Button is not present")
    
    time.sleep(10)
    button=False
    
    button=driver.find_element(By.XPATH, "//*[@id='column-center']/div/div/div[2]/div[1]/div[2]/button[3]")
    if button:
        print("Button is pressed")
        button.click()

    else:
        print("button is not present")
        print(str(button))
except Exception as e:
    print(str(e))

print("Done")

