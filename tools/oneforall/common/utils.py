# coding=utf-8
import re
import sys
import time
import random
import ipaddress
import platform
from config import Oneforall
from pathlib import Path
from records import Record, RecordCollection
from tools.oneforall.common.domain import Domain
from web.utils.logs import logger

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/68.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:61.0) '
    'Gecko/20100101 Firefox/68.0',
    'Mozilla/5.0 (X11; Linux i586; rv:31.0) Gecko/20100101 Firefox/68.0']


def match_subdomain(domain, text, distinct=True):
    """
    匹配text中domain的子域名

    :param str domain: 域名
    :param str text: 响应文本
    :param bool distinct: 结果去重
    :return: 匹配结果
    :rtype: set or list
    """
    regexp = r'(?:[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?\.){0,}' \
             + domain.replace('.', r'\.')
    result = re.findall(regexp, text, re.I)
    if not result:
        return set()
    deal = map(lambda s: s.lower(), result)
    if distinct:
        return set(deal)
    else:
        return list(deal)


def gen_random_ip():
    """
    生成随机的点分十进制的IP字符串
    """
    while True:
        ip = ipaddress.IPv4Address(random.randint(0, 2 ** 32 - 1))
        if ip.is_global:
            return ip.exploded


def gen_fake_header():
    """
    生成伪造请求头
    """
    ua = random.choice(user_agents)
    ip = gen_random_ip()
    headers = {
        'Accept': 'text/html,application/xhtml+xml,'
                  'application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Referer': 'https://www.google.com/',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': ua,
        'X-Forwarded-For': ip,
        'X-Real-IP': ip
    }
    return headers


def get_random_proxy():
    """
    获取随机代理
    """
    try:
        return random.choice(Oneforall.proxy_pool)
    except IndexError:
        return None


def split_list(ls, size):
    """
    将ls列表按size大小划分并返回新的划分结果列表

    :param list ls: 要划分的列表
    :param int size: 划分大小
    :return 划分结果

    >>> split_list([1, 2, 3, 4], 3)
    [[1, 2, 3], [4]]
    """
    if size == 0:
        return ls
    return [ls[i:i + size] for i in range(0, len(ls), size)]


def get_domains(target):
    """
    获取域名

    :param set or str target:
    :return: 域名集合
    """
    domains = list()
    logger.log('DEBUG', f'正在获取域名')
    if isinstance(target, (set, tuple)):
        domains = list(target)
    elif isinstance(target, list):
        domains = target
    elif isinstance(target, str):
        path = Path(target)
        if path.is_file():
            with open(target, encoding='utf-8', errors='ignore') as file:
                for line in file:
                    domain = Domain(line.strip()).match()
                    if domain:
                        domains.append(domain)
        elif Domain(target).match():
            domains = [target]
    logger.log('INFOR', f'获取到{len(domains)}个域名')
    return domains


def get_semaphore():
    """
    获取查询并发值

    :return: 并发整型值
    """
    system = platform.system()
    if system == 'Windows':
        return 800
    elif system == 'Linux':
        return 800
    elif system == 'Darwin':
        return 800


def check_path(path, name, format):
    """
    检查结果输出目录路径

    :param path: 保存路径
    :param name: 导出名字
    :param format: 保存格式
    :return: 保存路径
    """
    return path
    # filename = f'{name}.{format}'
    # default_path = Oneforall.result_save_path.joinpath(filename)
    # if path is None:
    #     path = default_path
    # try:
    #     path = Path(path)
    # except Exception as e:
    #     logger.log('ERROR', e.args)
    #     path = default_path
    # else:
    #     if not path.exists():
    #         logger.log('ALERT', f'不存在{path}目录将会新建')
    #         path.mkdir(parents=True, exist_ok=True)
    #         path = path.joinpath(filename)
    #     if path.is_dir():
    #         path = path.joinpath(filename)
    #     if path.exists():
    #         logger.log('ALERT', f'存在{path}文件将会覆盖')
    # # 意外情况
    # if not path:
    #     path = default_path
    # logger.log('DEBUG', f'结果保存路径{path}')
    # return path


def check_format(format, count):
    """
    检查导出格式

    :param format: 传入的导出格式
    :param count: 数量
    :return: 导出格式
    """
    formats = ['txt', 'rst', 'csv', 'tsv', 'json', 'yaml', 'html',
               'jira', 'xls', 'xlsx', 'dbf', 'latex', 'ods']
    if format == 'xls' and count > 65000:
        logger.log('ALERT', 'xls文件限制为最多65000行')
        logger.log('ALERT', '使用xlsx格式导出')
        return 'xlsx'
    if format in formats:
        return format
    else:
        logger.log('ALERT', f'不支持{format}格式导出')
        logger.log('ALERT', '默认使用csv格式导出')
        return 'csv'


def save_data(path, data):
    """
    保存结果数据到文件

    :param path: 保存路径
    :param data: 待存数据
    :return: 保存成功与否
    """
    return True
    # try:
    #     with open(path, 'w', encoding="utf-8",
    #               errors='ignore', newline='') as file:
    #         file.write(data)
    #         logger.log('ALERT', f'结果输出{path}')
    #         return True
    # except TypeError:
    #     with open(path, 'wb') as file:
    #         file.write(data)
    #         logger.log('ALERT', f'结果输出{path}')
    #         return True
    # except Exception as e:
    #     logger.log('ERROR', e.args)
    #     return False


def check_response(method, resp):
    """
    检查响应 输出非正常响应返回json的信息

    :param method: 请求方法
    :param resp: 响应体
    :return: 是否正常响应
    """
    if resp.status_code == 200 and resp.content:
        return True
    logger.log('ALERT', f'{method} {resp.url} {resp.status_code} - '
                        f'{resp.reason} {len(resp.content)}')
    content_type = resp.headers.get('Content-Type')
    if content_type and 'json' in content_type and resp.content:
        try:
            msg = resp.json()
        except Exception as e:
            logger.log('DEBUG', e.args)
        else:
            logger.log('ALERT', msg)
    return False


def mark_subdomain(old_data, new_data):
    """
    标记新增子域并返回新的数据集

    :param old_data: 之前数据集
    :param new_data: 现在数据集
    :return: 已标记的新的数据集
    """
    # 第一次收集子域的情况
    if not old_data:
        for index, item in enumerate(new_data):
            item['new'] = 1
            new_data[index] = item
        return new_data
    # 非第一次收集子域的情况
    old_subdomains = {item.get('subdomain') for item in old_data}
    for index, item in enumerate(new_data):
        subdomain = item.get('subdomain')
        if subdomain in old_subdomains:
            item['new'] = 0
        else:
            item['new'] = 1
        new_data[index] = item
    return new_data


def remove_string(string):
    # Excel文件中单元格值不能直接存储以下非法字符
    return re.sub(r'[\000-\010]|[\013-\014]|[\016-\037]', r'', string)


def check_value(values):
    for i, value in enumerate(values):
        if value is None:
            continue
        if isinstance(value, str) and len(value) > 32767:
            # Excel文件中单元格值长度不能超过32767
            values[i] = value[:32767]
    return values


def export_all(format, path, datas):
    """
    将所有结果数据导出到一个文件

    :param str format: 导出文件格式
    :param str path: 导出文件路径
    :param list datas: 待导出的结果数据
    """
    format = check_format(format, len(datas))
    timestamp = get_timestamp()
    name = f'all_subdomain_result_{timestamp}'
    path = check_path(path, name, format)
    row_list = list()
    for row in datas:
        row.pop('header')
        row.pop('response')
        row.pop('module')
        row.pop('source')
        row.pop('elapsed')
        row.pop('count')
        keys = row.keys()
        values = row.values()
        if format in {'xls', 'xlsx'}:
            values = check_value(values)
        row_list.append(Record(keys, values))
    rows = RecordCollection(iter(row_list))
    content = rows.export(format)
    save_data(path, content)


def get_timestamp():
    return int(time.time())


def get_classname(clsobj):
    return clsobj.__class__.__name__


def python_version():
    return sys.version


def count_valid(data):
    return len(list(filter(lambda item: item.get('valid') == 1, data)))
