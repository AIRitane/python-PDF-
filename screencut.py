from PIL import Image
import cv2
import time
from selenium import webdriver
from selenium.webdriver.edge.service import Service
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import selenium.common.exceptions as exc

# 参数设置
# webdriver，不同的浏览器不太相同，本代码只支持edge，chorm需要更改部分源码
edge_driver_path = r"xxxx\msedgedriver.exe"
# 文件暂时存放和生成的目录
temp_path = r'xxxx\temp'
# 可知网页
url_str = 'xxxx'
# 每次页面滑动的步长，建议设置小一点，但是设置越小，消耗的时间越长
key_down_step = 5
# 页面最小高度，可以在页面元素里查到，或者将这个值设置为0，先获取一张完整的图像查看图片的高
min_height = 1405
# 去水印，使用粗糙的调节对比度和亮度的方法
is_clean_watermark = True  # 是否清除水印
alpha = 1  # 图片对比度调节
beta = 100  # 图片亮度调节


def mkdir_file():
    if not os.path.exists(temp_path):
        os.makedirs(temp_path)
    if not os.path.exists(temp_path+"\\"+"raw_pic"):
        os.makedirs(temp_path+"\\"+"raw_pic")
    if not os.path.exists(temp_path+"\\"+"clean_watermark_pic"):
        os.makedirs(temp_path+"\\"+"clean_watermark_pic")
    if not os.path.exists(temp_path+"\\"+"out"):
        os.makedirs(temp_path+"\\"+"out")


def get_image(url):
    """
    #设置edge开启的模式，headless就是无界面模式
    # 创建一个参数对象，用来控制edge以无界面模式打开
    :param url:             获取获取网页的地址
    :return:
    """
    edge_service = Service(executable_path=edge_driver_path)
    edge_options = webdriver.EdgeOptions()
    edge_options.add_argument('--headless')
    edge_options.add_argument('--disable-gpu')
    edge_options.add_argument('--log-level=3')
    edge_options.add_argument('--no-sandbox')
    # 创建浏览器对象
    driver = webdriver.Edge(options=edge_options, service=edge_service)
    driver.set_window_size(2000, 2000)
    # 打开网页
    driver.get(url)
    # 简化鼠标模拟操作，直接刷新两次避免弹窗
    time.sleep(5)
    driver.refresh()
    time.sleep(5)

    # 爬取图片
    page_count = 0  # 页面计数
    while True:
        # 找到需要截图的元素
        try:
            element = driver.find_element(
                By.ID, 'pdf-page-{}'.format(page_count))
            while True:
                try:
                    driver.find_element(
                        By.CSS_SELECTOR, '#pdf-page-{} > div > div > div.textLayer'.format(page_count))
                    break
                except:
                    time.sleep(2)
            # 截图
            element.screenshot(temp_path+"\\"+"raw_pic" + "\\" +
                               "temp_{}.png".format(page_count))
            # 图片大小比对
            temp_img = cv2.imread(
                temp_path+"\\"+"raw_pic" + "\\"+"temp_{}.png".format(page_count))
            if temp_img.shape[0] >= min_height:
                print("temp_{}.png".format(page_count)+"保存完成")
                page_count += 1
        except exc.NoSuchElementException as e:
            driver.quit()
            return page_count
        # 下拉
        for _ in range(key_down_step):
            _ = driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.DOWN)
            time.sleep(0.1)


def clean_watermark(pagecount: int):
    for i in range(pagecount):
        img = cv2.imread(temp_path+"\\"+"raw_pic" +"\\"+"temp_{}.png".format(i))
        img = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.equalizeHist(img)
        img = cv2.imwrite(filename=temp_path+"\\"+"clean_watermark_pic"+"\\" +
                          "temp_{}.png".format(i), img=img)
    print("水印清除完成")


def img2pdf(pic_path, save_name, pagecount: int):
    is_first_in = True
    sources = []

    for i in range(pagecount):
        png_file = Image.open(pic_path + "\\"+"temp_{}.png".format(i))
        if png_file.mode != "RGB":
            png_file = png_file.convert("RGB")
        if is_first_in:
            output = png_file
            is_first_in = False
        else:
            sources.append(png_file)
    output.save(temp_path+"\\"+"out" + "\\" + "{}.pdf".format(save_name), "pdf",
                save_all=True, quality=100, append_images=sources, compress_level=0)


mkdir_file()
page_count = get_image(url_str)
img2pdf(temp_path+"\\"+"raw_pic", "raw", page_count)

if is_clean_watermark:
    clean_watermark(page_count)
    img2pdf(temp_path+"\\"+"clean_watermark_pic",
            "clean_watermark_pic", page_count)
