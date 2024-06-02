import argparse
import json
import requests
from bs4 import BeautifulSoup



def parse_args():
    parser = argparse.ArgumentParser(description='Arg parser skyenf')
    parser.add_argument('--img_folder', default='images/', help='save img folder')
    parser.add_argument('--json_path', default='json_files/teachers_dict.json', help='save json path')
    parser.add_argument('--base_url', default='https://skyeng.ru/teachers/', help='Base skyeng url')
    parser.add_argument('--num_pages', default=2, help='Number of parcsed pages')
    args = parser.parse_args()
    return args


def get_base_page(url):
    response = requests.get(url)

    if response.status_code == 200:
        print('Success!')
        text = response.text
    else:
        print(f'Error: {response.status_code}')
    soup = BeautifulSoup(text, 'lxml')
    return soup


def get_teachers_links(soup):
    teachers_links = []
    page_list = soup.find('div', class_='catalog-listing')
    teachers = page_list.find_all('div', class_='list-card-body')
    for row in page_list.find_all('a', class_='list-card-link'):
        teachers_links.append(row.get('href'))
    return teachers_links


def get_teacher_page_content(teacher_url):
    print(teacher_url)
    response_teacher = requests.get(teacher_url)

    if response_teacher.status_code == 200:
        print('Success!')
        text_teacher = response_teacher.text
    else:
        print(f'Error: {response_teacher.status_code}')

    soup_teacher = BeautifulSoup(text_teacher, 'lxml')
    teacher_aside = soup_teacher.find('div', class_='teacher-aside')
    teacher_content = soup_teacher.find('div', class_='teacher-content')
    return teacher_aside, teacher_content


def get_teacher_stat(teacher_stat, teacher_dict):
    teacher_dict['students'] = 0
    teacher_dict['num_lessons'] = 0
    teacher_dict['reit'] = 0
    teacher_dict['experience'] = 0
    for i in range(len(teacher_stat)):
        if teacher_stat[i].span.text == 'довольныхученика' or teacher_stat[i].span.text == 'довольныхучеников' or teacher_stat[i].span.text == 'довольныйученик':
            teacher_dict['students'] = int(teacher_stat[i].find('b').text.replace(' ', ''))
        if teacher_stat[i].span.text == 'урокав Skyeng' or teacher_stat[i].span.text == 'уроковв Skyeng' or teacher_stat[i].span.text == 'урокв Skyeng':
            teacher_dict['num_lessons'] = int(teacher_stat[i].find('b').text.replace(' ', ''))
        if teacher_stat[i].span.text == 'рейтингсреди учеников':
            teacher_dict['reit'] = float(teacher_stat[i].find('b').text.split('из')[0].replace(' ', ''))
        if teacher_stat[i].span.text == 'летопыта':
            teacher_dict['experience'] = int(teacher_stat[i].find('b').text.replace(' ', ''))
    return teacher_dict


def parse_teacher_info(teacher_aside, teacher_content):
    if not teacher_content:
        print('Teacher content not find')
        print(teacher_content)
    teacher_dict = {}
    teacher_dict['name'] = teacher_content.find('h1', class_='teacher-name').text
    teacher_dict['price'] = teacher_content.find('div', class_='teacher-price').text
    benefits = []
    for row in teacher_content.find('ul', class_='teacher-ul ng-star-inserted').find_all('li'):
        benefits.append(row.text)
    teacher_dict['benefits'] = benefits    
    
    teacher_stat = teacher_content.find_all('ul')[1].find_all('li')
    teacher_dict = get_teacher_stat(teacher_stat, teacher_dict)

    levels = []
    for row in teacher_content.find_all('div', class_='level-item ng-star-inserted'):
        levels.append(row.text)
    teacher_dict['levels'] = levels
    teacher_dict['about'] = teacher_content.find('div', class_='teacher-text -desktop').text

    teachers_tags = []
    teachers_interests = []
    for row in teacher_content.find_all('div', class_='tags')[0].find_all('span'):
        teachers_tags.append(row.text)
    for row in teacher_content.find_all('div', class_='tags')[1].find_all('span'):
        teachers_interests.append(row.text)
    teacher_dict['teachers_tags'] = teachers_tags
    teacher_dict['teachers_interesrs'] = teachers_interests

    img_url = teacher_aside.find('img')['src']
    img_name = img_url.split('/')[3]
    download_img(img_url, img_name)
    teacher_dict['img_path'] = img_name
    return teacher_dict


def download_img(img_url, img_name):
    print(f'--- download image {img_url} ---')
    print(f'--- saved to {img_folder + img_name + ".jpeg"} ---')
    img_file = requests.get(img_url).content
    with open(img_folder + img_name + '.jpeg', 'wb') as f:
        f.write(img_file)


def one_teacher_process(teacher_link):
    teacher_url = 'https://skyeng.ru/' + teacher_link    
    teacher_aside, teacher_content = get_teacher_page_content(teacher_url)    
    teacher_dict = parse_teacher_info(teacher_aside, teacher_content)
    teacher_dict['url'] = teacher_url
    return teacher_dict


if __name__ == '__main__':
    args = parse_args()
    img_folder = args.img_folder #'/home/asergeeva/Desktop/parser/skyeng_info/images/'
    page_url_base = args.base_url #'https://skyeng.ru/teachers/'   
    num_pages = args.num_pages
    save_path = args.json_path
    teachers_dict = {}
    page_counter = 0
    for page_num in range(1, num_pages):
        print(f'\n--- page {page_num} ---\n')
        if page_num == 1:
            page_url_postfix = '?from=main_new_menu'
        else:
            page_url_postfix = f'page-{page_num}/?from=main_new_menu'   
        page_url = page_url_base + page_url_postfix   
        print('page url: ', page_url)
        soup = get_base_page(page_url)
        teachers_links = get_teachers_links(soup)
        for i_teacher in range(0, len(teachers_links), 2):
            print(f'--- run {i_teacher} ---')
            teacher_link = teachers_links[i_teacher]
            key = teacher_link.split('/')[3]
            teacher_dict = one_teacher_process(teacher_link)
            print(teacher_dict)
            teachers_dict[key] = teacher_dict
        print(' ------ ')

    print('save teachers dict to: ', save_path)
    with open(save_path, 'w') as f:
        json.dump(teacher_dict, f)


