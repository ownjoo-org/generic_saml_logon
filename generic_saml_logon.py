import argparse
import re

from bs4 import BeautifulSoup, PageElement
from json import loads
from typing import Optional
from requests import HTTPError
from requests import Session, Response
from urllib.parse import urlparse, ParseResult

USERNAME_KEYS: list = ['username', 'user_name', 'client_id']
PASSWORD_KEYS: list = ['password', 'passwd', 'client_secret']
MAX_REDIRECTS: int = 10


def get_form_data(markup: str) -> dict:
    result: dict = {}

    soup: BeautifulSoup = BeautifulSoup(markup=markup, features='html.parser')

    form = soup.find('form')
    if form:
        result['action'] = form.get('action')
        result['method'] = form.get('method')
        result.update(dict(form.find_all(name='input')))

    return result


def get_saml_response(session: Session, sp_url: str, username: str, password: str, max_redirects: Optional[int]) -> str:
    result: Optional[str] = None

    url: str = sp_url
    form_data: dict = {}
    requests_remaining: int = max_redirects or MAX_REDIRECTS
    method: str = 'GET'

    while requests_remaining and not result:
        if method == 'GET':
            response: Response = session.get(url=url, params=form_data)
        else:
            response: Response = session.post(url=url, data=form_data)
        requests_remaining -= 1

        form_data = get_form_data(markup=response.text)
        if form_data:
            url = form_data.get('action')
            method = str(form_data.get('method')).upper()
            for input_name in form_data:
                if input_name.lower() in USERNAME_KEYS:
                    form_data[input_name] = username
                elif input_name.lower() in PASSWORD_KEYS:
                    form_data[input_name] = password

            result = form_data.get('SAMLResponse')

    return result


def main(
        sp_url: str,
        username: str,
        password: str,
        proxies: Optional[dict] = None,
        max_redirects: Optional[int] = None,
) -> str:
    session = Session()
    session.proxies = proxies
    result: str = get_saml_response(
        session=session,
        sp_url=sp_url,
        username=username,
        password=password,
        max_redirects=max_redirects or MAX_REDIRECTS,
    )
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--sp_url',
        type=str,
        required=True,
        help="The URL of the service you want to authenticate to...",
    )
    parser.add_argument(
        '--username',
        type=str,
        required=True,
        help='The user name for your PingFederate account',
    )
    parser.add_argument(
        '--password',
        type=str,
        required=True,
        help='The password for your PingFederate account',
    )
    parser.add_argument(
        '--max_redirects',
        type=int,
        required=False,
        help='The maximum number of redirects to allow before giving up',
        default=MAX_REDIRECTS
    )
    parser.add_argument(
        '--proxies',
        type=str,
        required=False,
        help="JSON structure specifying 'http' and 'https' proxy URLs",
    )

    args = parser.parse_args()

    proxies: Optional[dict] = None
    if args.proxies:
        proxies: dict = loads(args.proxies)

    if data := main(
        sp_url=args.sp_url,
        username=args.username,
        password=args.password,
        proxies=proxies,
        max_redirects=args.max_redirects,
    ):
        print(data)
    else:
        print('No results found')
