# Importing the necessary Libraries
import os
import time
import requests
from selenium import webdriver
from flask_cors import CORS,cross_origin
from flask import Flask, render_template, request,jsonify


# import request
app = Flask(__name__) # initialising the flask app with the name 'app'

#response = 'Welcome!'


@app.route('/')  # route for redirecting to the home page
@cross_origin()
def home():
    return render_template('index.html')

def fetch_image_urls(query: str, max_links_to_fetch: int, wd: webdriver, sleep_between_interactions: int = 1):
    def scroll_to_end(wd):
        wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(sleep_between_interactions)

        # build the google query

    search_url = "https://www.google.com/search?safe=off&site=&tbm=isch&source=hp&q={q}&oq={q}&gs_l=img"
    #search_url = "https://www.google.com/search?q={q}&hl=en&tbm=isch"
    # load the page
    wd.get(search_url.format(q=query))

    image_urls = set()
    image_count = 0
    results_start = 0
    while image_count < max_links_to_fetch:
        scroll_to_end(wd)

        # get all image thumbnail results
        thumbnail_results = wd.find_elements_by_css_selector("img.Q4LuWd")
        number_results = len(thumbnail_results)

        print(f"Found: {number_results} search results. Extracting links from {results_start}:{number_results}")

        for img in thumbnail_results[results_start:number_results]:
            # try to click every thumbnail such that we can get the real image behind it
            try:
                img.click()
                time.sleep(sleep_between_interactions)
            except Exception:
                continue

            # extract image urls
            actual_images = wd.find_elements_by_css_selector('img.n3VNCb')
            for actual_image in actual_images:
                if actual_image.get_attribute('src') and 'http' in actual_image.get_attribute('src'):
                    image_urls.add(actual_image.get_attribute('src'))

            image_count = len(image_urls)

            if len(image_urls) >= max_links_to_fetch:
                print(f"Found: {len(image_urls)} image links, done!")
                break
        else:
            print("Found:", len(image_urls), "image links, looking for more ...")
            time.sleep(30)
            return
            load_more_button = wd.find_element_by_css_selector(".mye4qd")
            if load_more_button:
                wd.execute_script("document.querySelector('.mye4qd').click();")

        # move the result startpoint further down
        results_start = len(thumbnail_results)

    return image_urls

def persist_image(folder_path:str,url:str, counter, search_words):
    try:
        image_content = requests.get(url).content

    except Exception as e:
        print(f"ERROR - Could not download {url} - {e}")

    try:
        f = open(os.path.join(folder_path, search_words + "_" + str(counter) + ".jpg"), 'wb')
        f.write(image_content)
        f.close()
        print(f"SUCCESS - saved {url} - as {folder_path}")
    except Exception as e:
        print(f"ERROR - Could not save {url} - {e}")


def search_and_download(search_term: str, driver_path: str, target_path='./static', number_images=10):
    #target_folder = os.path.join(target_path, '_'.join(search_term.lower().split(' '))) # make the folder name inside images with the search string
    target_folder = target_path
    if not os.path.exists(target_folder):
        os.makedirs(target_folder) # make directory using the target path if it doesn't exist already

    with webdriver.Chrome(executable_path=driver_path) as wd:
        res = fetch_image_urls(search_term, number_images, wd=wd, sleep_between_interactions=2)

    search_words = search_term.lower().split(' ')[0]
    counter = 0
    for elem in res:
        persist_image(target_folder, elem, counter, search_words)
        counter += 1


@app.route('/searchImages', methods=['GET','POST'])
def searchImages():
    if request.method == 'POST':
        print("entered searchImages post")
        keyWord = request.form['keyword'] # assigning the value of the input keyword to the variable keyword

    else:
        print("did not enter post")
    print('search image key word = ' + keyWord)

    delete_existing_images()

    DRIVER_PATH = './chromedriver'
    # num of images you can pass it from here  by default it's 10 if you are not passing
    # number_images = 10
    search_and_download(search_term=keyWord, driver_path=DRIVER_PATH)  # method to download images

    return show_images()

def delete_existing_images():
    list_of_jpg_files = list_only_jpg_files('static')
    for image in list_of_jpg_files:
        try:
            if(image == 'style.css'):
                continue
            os.remove("./static/"+image)
        except Exception as e:
            print('error in deleting:  ',e)
    return 0

def show_images():
    list_of_jpg_files = list_only_jpg_files('static') # obtaining the list of image files from the static folder
    print(list_of_jpg_files)
    try:
        if(len(list_of_jpg_files)>0): # if there are images present, show them on a wen UI
            return render_template('showImage.html',user_images = list_of_jpg_files)
        else:
            return "Please try with a different string" # show this error message if no images are present in the static folder
    except Exception as e:
        print('no Images found ', e)
        return "Please try with a different string"

def list_only_jpg_files(folder_name):
        list_of_jpg_files=[]
        list_of_files=os.listdir(folder_name)
        print('list of files==')
        print(list_of_files)
        for file in list_of_files:
            name_array= file.split('.')
            if(name_array[1] == 'jpg' or name_array[1] == 'jpeg'):
                list_of_jpg_files.append(file)
            else:
                print('filename does not end with jpg')
        return list_of_jpg_files

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000) # port to run on local machine
    #app.run(debug=True) # to run on cloud
