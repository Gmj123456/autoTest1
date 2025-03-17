import json
import logging
from pages.base_page import BasePage
from selenium.webdriver.common.by import By
from config.config import ERP_URL, LOGIN_SUCCESS_URL
from selenium.webdriver.common.keys import Keys
from pathlib import Path
import subprocess
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 在文件顶部添加统一日志配置
from utils.logger import setup_logging
setup_logging()

class LoginPage(BasePage):
    USERNAME_INPUT = (
    By.XPATH, "/html/body/div[1]/div/div/div/div[2]/div/div/form/div[1]/form/div[1]/div/div/span/input")
    PASSWORD_INPUT = (
    By.XPATH, "/html/body/div[1]/div/div/div/div[2]/div/div/form/div[1]/form/div[2]/div/div/span/input")
    CAPTCHA_INPUT = (
    By.XPATH, "/html/body/div[1]/div/div/div/div[2]/div/div/form/div[1]/form/div[3]/div[1]/div/div/div/span/span/input")
    CAPTCHA_IMAGE = (By.XPATH, "/html/body/div[1]/div/div/div/div[2]/div/div/form/div[1]/form/div[3]/div[2]/img")
    LOGOUT_BUTTON = (By.XPATH, "//*[@id='app']/section/section/header/div/div/span[6]/a/span/span/span")  # 假设退出登录按钮的定位器
    # CONFIRM_LOGOUT_BUTTON = (By.XPATH, "/html/body/div[8]/div/div[2]/div/div[2]/div/div/div[2]/button[2]")  # 假设确定按钮的定位器
    CONFIRM_LOGOUT_BUTTON = (By.XPATH,"/html/body/div[8]/div/div[2]/div/div[2]/div/div/div[2]/button[2]/span")


    def __init__(self, driver):
        super().__init__(driver)
        # 确保 self.driver 是正确的驱动对象
        self.driver = driver

    def save_captcha_image(self):
        """保存验证码图片"""
        current_dir = Path(__file__).parent.resolve()  # 修改 pathlib.Path → Path
        config_dir = current_dir.parent / 'config'
        config_dir.mkdir(parents=True, exist_ok=True)
        captcha_path = config_dir / 'captcha.png'

        try:
            captcha_image = self.find_element(*self.CAPTCHA_IMAGE)
            captcha_image.screenshot(str(captcha_path))
            logging.info(f"验证码图片已保存到 {captcha_path}")
            return captcha_path
        except NoSuchElementException:
            logging.error("未找到验证码图片元素")
        except WebDriverException as e:
            logging.error(f"截图验证码时出现 WebDriver 异常: {e}")
        return None

    def recognize_captcha(self, captcha_path):
        """调用 OCR 接口识别验证码"""
        if not captcha_path:
            return None
        current_dir = Path(__file__).parent.resolve()  # 修改 pathlib.Path → Path
        ocr_script_path = current_dir.parent / 'utils' / 'ocr.py'
        try:
            # 添加工作目录参数
            result = subprocess.run(
                ['python', str(ocr_script_path), str(captcha_path)], 
                cwd=str(Path(__file__).parent.parent.parent),  # 设置工作目录为项目根目录
                capture_output=True, 
                text=True,
                check=True
            )
            res = result.stdout.splitlines()
            if res:
                captcha_text = res[0].strip()
                logging.info(f"验证码识别结果: {captcha_text}")
                return captcha_text
        except subprocess.CalledProcessError as e:
            logging.error(f"调用 OCR 脚本时出现错误: {e.stderr}")
        return None

    def check_login_result(self, attempts):
        """检查登录结果，等待页面 URL 变为登录成功后的 URL，最多等待 5 秒"""
        try:
            WebDriverWait(self.driver, 5).until(lambda driver: driver.current_url == LOGIN_SUCCESS_URL)
            logging.info("登录成功")
            return True
        except Exception:
            logging.warning(f"第 {attempts + 1} 次登录失败，重新尝试")
            return False

    def get_access_token(self):
        """获取并解析token"""
        try:
            # 等待页面加载完成（根据实际情况调整等待条件）
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            # 获取localStorage中的所有数据
            localStorage = self.driver.execute_script('return window.localStorage;')
            # 尝试从 localStorage 中获取 pro__Access-Token 的值
            access_token_str = localStorage.get('pro__Access-Token')
            if access_token_str:
                try:
                    # 将获取到的字符串解析为 Python 字典
                    access_token_dict = json.loads(access_token_str)
                    # 从字典中提取 "value" 键对应的值
                    value = access_token_dict.get("value")
                    if value:
                        logging.info(f"Token: {value}")
                        return value
                    else:
                        logging.error("pro__Access-Token 中不存在 value 字段")
                except json.JSONDecodeError:
                    logging.error("无法将 pro__Access-Token 的值解析为 JSON 格式")
            else:
                # 如果未找到 pro__Access-Token，打印提示信息
                logging.error("未找到 pro__Access-Token")
        except Exception as e:
            logging.error(f"An error occurred: {e}")
        return None

    def login(self, username, password):
        max_attempts = 5
        attempts = 0

        while attempts < max_attempts:
            try:
                logging.info("开始登录操作")
                self.driver.get(ERP_URL)
                logging.info("已打开登录页面")
                self.send_keys(*self.USERNAME_INPUT, username)
                logging.info(f"已输入用户名：{username}")
                self.send_keys(*self.PASSWORD_INPUT, password)
                logging.info(f"已输入密码：{password}")

                captcha_path = self.save_captcha_image()
                captcha_text = self.recognize_captcha(captcha_path)

                if captcha_text:
                    self.send_keys(*self.CAPTCHA_INPUT, captcha_text + Keys.RETURN)
                    logging.info(f"已输入验证码: {captcha_text}，第 {attempts + 1} 次尝试")
                    result = self.check_login_result(attempts)
                    if result:
                        self.access_token = self.get_access_token()  # 获取token
                        return True
            except Exception as e:
                logging.error(f"登录过程中出现错误: {e}")

            attempts += 1

        logging.error("验证码识别失败次数达到上限，登录失败")
        return False

    def logout(self):
        """退出登录"""
        try:
            logout_button = self.find_element(*self.LOGOUT_BUTTON)
            logout_button.click()
            logging.info("已点击退出登录按钮")
            
            # 修改部分，使用显式等待
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            try:
                # 假设需要等待确认退出登录按钮出现
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(self.CONFIRM_LOGOUT_BUTTON))
                logging.info("确认退出登录按钮已出现")
            except Exception as e:
                logging.error(f"等待确认退出登录按钮出现时出错: {e}")
            
            confirm_button = self.find_element(*self.CONFIRM_LOGOUT_BUTTON)
            confirm_button.click()
            logging.info("已点击确定按钮，完成退出登录")
            return True
        except Exception as e:
            logging.error(f"退出登录时出现错误: {e}")
            return False
