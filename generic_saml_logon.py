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


def get_form_data(soup: BeautifulSoup) -> dict:
    result: dict = {}

    form = soup.find('form')
    if form:
        result['action'] = form.get('action')
        result['method'] = form.get('method')
        result.update(dict(form.find_all(name='input')))

    return result


def get_saml_response(session: Session, sp_url: str, username: str, password: str) -> str:
    result: Optional[str] = None

    url: str = sp_url
    form_data: dict = {}
    request_limit: int = 10
    method: str = 'GET'

    while not result and request_limit:
        if method == 'GET':
            response: Response = session.get(url=url, params=form_data)
        else:
            response: Response = session.post(url=url, data=form_data)
        request_limit -= 1
        soup: BeautifulSoup = BeautifulSoup(response.text, 'html.parser')
        saml_response: PageElement = soup.find(attrs={'name': 'SAMLResponse'})
        if saml_response:
            result: str = saml_response.get('value')
            break
        else:
            form_data = get_form_data(html=response.text)
            url = form_data.get('action')
            method = str(form_data.get('method')).upper()
            for input in form_data:
                if input.lower() in USERNAME_KEYS:
                    form_data[input] = username
                elif input.lower() in PASSWORD_KEYS:
                    form_data[input] = password

    return result


def main(
        sp_url: str,
        username: str,
        password: str,
        proxies: Optional[dict] = None,
) -> str:
    session = Session()
    session.proxies = proxies
    result: str = get_saml_response(
        session=session,
        sp_url=sp_url,
        username=username,
        password=password,
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
    ):
        print(data)
    else:
        print('No results found')
