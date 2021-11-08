from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

from time import sleep
from linebot import LineBotApi
from linebot.models import TextSendMessage
from dotenv import load_dotenv
import os
import subprocess
import re
import datetime

# Load .env file
load_dotenv()

# Get environment variables
CHANNEL_ACCESS_TOKEN = os.environ['CHANNEL_ACCESS_TOKEN']
DESTINATION_LINE_ID = os.environ['DESTINATION_LINE_ID']
EMAIL = os.environ['EMAIL']
PASSWORD = os.environ['PASSWORD']
TWO_STEP_AUTHENTICATION_SETTING_CODE = os.environ['TWO_STEP_AUTHENTICATION_SETTING_CODE']

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)


def get_monthly_bills():

    # Define browser
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--hide-scrollbars")
    options.add_argument("--single-process")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--window-size=880x996")
    options.add_argument("--no-sandbox")
    options.add_argument("--homedir=/tmp")
    options.add_argument(
        f'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36')

    browser = webdriver.Chrome(
        ChromeDriverManager().install(),
        options=options
    )

    print('start login')

    # Jump to email sing-in page
    url = 'https://id.moneyforward.com/sign_in/email'
    browser.get(url)
    sleep(3)

    # Enter email
    elem_loginMethod = browser.find_element_by_xpath(
        '/html/body/main/div/div/div/div/div[1]/section/form/div[2]/div/input')
    elem_loginMethod.send_keys(EMAIL)

    # Jump to password input page
    elem_login = browser.find_element_by_xpath(
        '/html/body/main/div/div/div/div/div[1]/section/form/div[2]/div/div[3]/input')
    elem_login.click()
    sleep(3)

    # Enter password
    elem_password = browser.find_element_by_xpath(
        '/html/body/main/div/div/div/div/div[1]/section/form/div[2]/div/input[2]')
    elem_password.send_keys(PASSWORD)

    # Jump to tow-step-authentication page
    elem_login = browser.find_element_by_xpath(
        '/html/body/main/div/div/div/div/div[1]/section/form/div[2]/div/div[3]/input')
    elem_login.click()
    sleep(3)

    # Receive auth code for tow-step-authentication
    two_step_authentication = ['oathtool', '--totp',
                               '--base32', TWO_STEP_AUTHENTICATION_SETTING_CODE]
    auth_code = re.findall(
        r'\d+', subprocess.check_output(two_step_authentication).decode('utf-8'))

    # Enter auth code
    elem_auth_number = browser.find_element_by_xpath(
        '/html/body/main/div/div/div/section/div[1]/section/form/div[2]/div/div[1]/input')
    elem_auth_number.send_keys(auth_code[0])

    print('logged in to Money Foward Id')

    # Jump to already-logged-in servise list page by Money Foward ID
    elem_auth = browser.find_element_by_xpath(
        '/html/body/main/div/div/div/section/div[1]/section/form/div[2]/div/div[2]/input')
    elem_auth.click()
    sleep(3)

    # Jump to Money Forward ME account select page
    elem_money_forward = browser.find_element_by_xpath(
        '/html/body/main/div/div/div/div[1]/div/ul/li/a')
    elem_money_forward.click()
    sleep(3)

    # Jump to Money Forward ME Top page
    elem_choose_account = browser.find_element_by_xpath(
        '/html/body/main/div/div/div/div/div[1]/section/form/div[2]/div/div[2]/input')
    elem_choose_account.click()
    sleep(3)

    # Jump to Money Forward ME household expenses page
    elem_household_expenses = browser.find_element_by_xpath(
        '//*[@id="header-container"]/header/div[2]/ul/li[2]/a')
    elem_household_expenses.click()
    sleep(3)

    # Jump to previous month's household expenses page
    elem_household_expenses_prev_month = browser.find_element_by_xpath(
        '//*[@id="in_out"]/div[2]/button[1]')
    elem_household_expenses_prev_month.click()
    sleep(3)

    print('start getting bills')

    last_month = datetime.datetime.now().month - 1
    text = f'{last_month}月の公共料金\n'
    bills = [{'title': '電気代: ', 'service': '楽天でんき'},
             {'title': 'ガス代: ', 'service': '楽天ガス'},
             {'title': '水道代: ', 'service': '水道局'},
             {'title': '通信費: ', 'service': '楽天ブロードバンド'}]

    # Create text content to send to LINE
    text = calc_bills(browser, bills, text)
    messages = TextSendMessage(text=text)
    # Push massages to LINE
    line_bot_api.push_message(DESTINATION_LINE_ID, messages=messages)

    print('everything done')

    browser.close()


def calc_bills(browser, bills, text):
    total = 0
    for bill in bills:
        span_tags = browser.find_elements_by_xpath(
            f'//span[contains(text(), "{bill["service"]}")]')
        # Add only available bills to text
        if not span_tags:
            text += f'\n{bill["title"]}0円'
        else:
            for span_tag in span_tags:
                price = span_tag.find_element_by_xpath('../../../td[4]')
                print(price.text)
                text += f'\n{bill["title"]}{price.text[1:]}円'
                total += int(price.text[1:].replace(',', ''))

    # Get comment depending on how much money you have spent on utitlities
    comment = get_comment(total)

    total = f'\n\n合計: {total}円\n{comment}'
    text += total
    print(text)
    return text


def get_comment(total):

    comment = ''

    if(total > 50000):
        comment += '富豪。'
    elif(total > 40000):
        comment += '贅沢してんじゃないの！？節約しよ！'
    elif(total > 30000):
        comment += 'もうちょっと出費抑えたき！'
    elif(total > 20000):
        comment += 'ぼちぼちの出費やね'
    elif(total > 10000):
        comment += '4桁円まで削ろう'
    else:
        comment += '前人未到の域、節約の神。'

    return comment


get_monthly_bills()
