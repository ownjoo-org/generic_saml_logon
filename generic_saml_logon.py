import argparse

from bs4 import BeautifulSoup
from json import loads
from typing import Optional
from requests import Session, Response

USERNAME_KEYS: list = ['username', 'user_name', 'client_id']
PASSWORD_KEYS: list = ['password', 'passwd', 'client_secret']
MAX_REDIRECTS: int = 10


def get_form_data(markup: str) -> dict:
    result: dict = {}

    soup: BeautifulSoup = BeautifulSoup(markup=markup, features='html.parser')
    form = soup.find('form')
    meta_refresh = soup.find('meta', attrs={'http-equiv': 'refresh'})
    if form:
        result['action'] = form.get('action')
        result['method'] = form.get('method')
        form_inputs: list = form.find_all(name='input')
        for form_input in form_inputs:
            result[form_input.get('name')] = form_input.get('value')
    elif meta_refresh:
        content: str = meta_refresh.get('content')
        data_url: str = meta_refresh.get('data-url')
        if data_url:
            result['action'] = data_url
            result['method'] = 'GET'
        elif content and 'url=' in content:
            content_url = content.split('url=')[1]
            result['action'] = content_url
            result['method'] = 'GET'
    else:
        raise ValueError(f'No form or meta refresh found: {soup}')

    return result


def get_saml_response(session: Session, sp_url: str, username: str, password: str, max_redirects: Optional[int]) -> str:
    result: Optional[str] = None

    url: str = sp_url
    form_data: dict = {}
    requests_remaining: int = max_redirects or MAX_REDIRECTS
    method: str = 'GET'

    while requests_remaining and not result:
        if method.upper() == 'GET':
            response: Response = session.get(url=url, params=form_data)
        else:
            response: Response = session.post(url=url, data=form_data)
        requests_remaining -= 1

        form_data = get_form_data(markup=response.text)
        if form_data:
            url = form_data.pop('action', '')
            method = form_data.pop('method', '')
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
        help='The user name for your IdP account',
    )
    parser.add_argument(
        '--password',
        type=str,
        required=True,
        help='The password for your IdP account',
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
        print('No SAMLResponse...  This API is probably more sophisticated than this generic SAML code supports.')
