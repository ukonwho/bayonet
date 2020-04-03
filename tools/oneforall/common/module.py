# coding=utf-8
"""
模块基类
"""

import json
import re
import threading
import time

import requests
from config import Oneforall
from web.utils.logs import logger
from tools.oneforall.common import utils
from tools.oneforall.common.domain import Domain
from tools.oneforall.common.database import Database

lock = threading.Lock()


class Module(object):
    def __init__(self):
        self.module = 'Module'
        self.source = 'BaseModule'
        self.cookie = None
        self.header = dict()
        self.proxy = None
        self.delay = Oneforall.request_delay  # 请求睡眠时延
        self.timeout = Oneforall.request_timeout  # 请求超时时间
        self.verify = Oneforall.request_verify  # 请求SSL验证
        self.domain = ''  # 要进行子域名收集的域名
        self.subdomains = set()  # 存放发现的子域
        self.records = dict()  # 存放子域解析记录
        self.results = list()  # 存放模块结果
        self.start = time.time()  # 模块开始执行时间
        self.end = None  # 模块结束执行时间
        self.elapsed = None  # 模块执行耗时

    def check(self, *apis):
        """
        简单检查是否配置了api信息

        :param apis: api信息元组
        :return: 检查结果
        """
        if not all(apis):
            logger.log('ALERT', f'{self.source}模块没有配置API跳过执行')
            return False
        return True

    def begin(self):
        """
        输出模块开始信息
        """
        logger.log('DEBUG', f'开始执行{self.source}模块收集{self.domain}的子域')

    def finish(self):
        """
        输出模块结束信息
        """
        self.end = time.time()
        self.elapsed = round(self.end - self.start, 1)
        logger.log('DEBUG', f'结束执行{self.source}模块收集{self.domain}的子域')
        logger.log('INFOR', f'{self.source}模块耗时{self.elapsed}秒发现子域'
                            f'{len(self.subdomains)}个')
        logger.log('DEBUG', f'{self.source}模块发现{self.domain}的子域\n'
                            f'{self.subdomains}')

    def head(self, url, params=None, check=True, **kwargs):
        """
        自定义head请求

        :param str url: 请求地址
        :param dict params: 请求参数
        :param bool check: 检查响应
        :param kwargs: 其他参数
        :return: requests响应对象
        """
        try:
            resp = requests.head(url,
                                 params=params,
                                 cookies=self.cookie,
                                 headers=self.header,
                                 proxies=self.proxy,
                                 timeout=self.timeout,
                                 verify=self.verify,
                                 **kwargs)
        except Exception as e:
            logger.log('ERROR', e.args)
            return None
        if not check:
            return resp
        if utils.check_response('HEAD', resp):
            return resp
        return None

    def get(self, url, params=None, check=True, **kwargs):
        """
        自定义get请求

        :param str url: 请求地址
        :param dict params: 请求参数
        :param bool check: 检查响应
        :param kwargs: 其他参数
        :return: requests响应对象
        """
        try:
            resp = requests.get(url,
                                params=params,
                                cookies=self.cookie,
                                headers=self.header,
                                proxies=self.proxy,
                                timeout=self.timeout,
                                verify=self.verify,
                                **kwargs)
        except Exception as e:
            logger.log('ERROR', e.args)
            return None
        if not check:
            return resp
        if utils.check_response('GET', resp):
            return resp
        return None

    def post(self, url, data=None, check=True, **kwargs):
        """
        自定义post请求

        :param str url: 请求地址
        :param dict data: 请求数据
        :param bool check: 检查响应
        :param kwargs: 其他参数
        :return: requests响应对象
        """
        try:
            resp = requests.post(url,
                                 data=data,
                                 cookies=self.cookie,
                                 headers=self.header,
                                 proxies=self.proxy,
                                 timeout=self.timeout,
                                 verify=self.verify,
                                 **kwargs)
        except Exception as e:
            logger.log('ERROR', e.args)
            return None
        if not check:
            return resp
        if utils.check_response('POST', resp):
            return resp
        return None

    def get_header(self):
        """
        获取请求头

        :return: 请求头
        """
        # logger.log('DEBUG', f'获取请求头')
        if Oneforall.enable_fake_header:
            return utils.gen_fake_header()
        else:
            return self.header

    def get_proxy(self, module):
        """
        获取代理

        :param str module: 模块名
        :return: 代理字典
        """
        if not Oneforall.enable_proxy:
            logger.log('TRACE', f'所有模块不使用代理')
            return self.proxy
        if Oneforall.proxy_all_module:
            logger.log('TRACE', f'{module}模块使用代理')
            return utils.get_random_proxy()
        if module in Oneforall.proxy_partial_module:
            logger.log('TRACE', f'{module}模块使用代理')
            return utils.get_random_proxy()
        else:
            logger.log('TRACE', f'{module}模块不使用代理')
            return self.proxy

    @staticmethod
    def match(domain, html, distinct=True):
        """
        正则匹配出子域

        :param str domain: 域名
        :param str html: 要匹配的html响应体
        :param bool distinct: 匹配结果去除
        :return: 匹配出的子域集合或列表
        :rtype: set or list
        """
        logger.log('TRACE', f'正则匹配响应体中的子域')
        regexp = r'(?:\>|\"|\'|\=|\,)(?:http\:\/\/|https\:\/\/)?' \
                 r'(?:[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?\.){0,}' \
                 + domain.replace('.', r'\.')
        result = re.findall(regexp, html, re.I)
        if not result:
            return set()
        regexp = r'(?:http://|https://)'
        deal = map(lambda s: re.sub(regexp, '', s[1:].lower()), result)
        if distinct:
            return set(deal)
        else:
            return list(deal)

    @staticmethod
    def register(domain):
        """
        获取注册域名

        :param str domain: 域名
        :return: 注册域名
        """
        return Domain(domain).registered()

    def save_json(self):
        """
        将各模块结果保存为json文件

        :return： 是否保存成功
        """
        if not Oneforall.save_module_result:
            return False
        logger.log('TRACE', f'将{self.source}模块发现的子域结果保存为json文件')
        path = Oneforall.result_save_path.joinpath(self.domain, self.module)
        path.mkdir(parents=True, exist_ok=True)
        name = self.source + '.json'
        path = path.joinpath(name)
        with open(path, mode='w', encoding='utf-8', errors='ignore') as file:
            result = {'domain': self.domain,
                      'name': self.module,
                      'source': self.source,
                      'elapsed': self.elapsed,
                      'count': len(self.subdomains),
                      'subdomains': list(self.subdomains),
                      'records': self.records}
            json.dump(result, file, ensure_ascii=False, indent=4)
        return True

    def gen_result(self):
        """
        生成结果
        """
        if not len(self.subdomains):  # 该模块一个子域都没有发现的情况
            result = {'id': None,
                      'url': None,
                      'subdomain': None,
                      'port': None,
                      'ips': None,
                      'status': None,
                      'reason': None,
                      'valid': None,
                      'new': None,
                      'title': None,
                      'banner': None,
                      'header': None,
                      'response': None,
                      'module': self.module,
                      'source': self.source,
                      'elapsed': self.elapsed,
                      'count': 0}
            self.results.append(result)
        else:
            for subdomain in self.subdomains:
                url = 'http://' + subdomain
                ips = self.records.get(subdomain)
                result = {'id': None,
                          'url': url,
                          'subdomain': subdomain,
                          'port': None,
                          'ips': ips,
                          'status': None,
                          'reason': None,
                          'valid': None,
                          'new': None,
                          'title': None,
                          'banner': None,
                          'module': self.module,
                          'header': None,
                          'response': None,
                          'source': self.source,
                          'elapsed': self.elapsed,
                          'count': len(self.subdomains)}
                self.results.append(result)

    def save_db(self):
        """
        将模块结果存入数据库中

        """
        lock.acquire()
        db = Database()
        db.create_table(self.domain)
        db.save_db(self.domain, self.results, self.source)
        db.close()
        lock.release()
