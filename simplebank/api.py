# Simple API wrapper

# These URLs were gleaned from using the website

import datetime
import json
import re
import time

import requests
import yaml
from clint.textui.cols import console_width


def login_required(func):
    """
    Decorator that ensures that the user has been logged in first
    """

    def check(self, *args, **kwargs):
        if not self.session is not None:
            raise Exception("Not logged in")
        else:
            return func(self, *args, **kwargs)
    return check


class Api(object):
    def __init__(self):
        self.session = None
        self.base_url = "https://bank.simple.com"

    def login(self, username, password):
        """
        Logs the user in. Returns True if successful.
        """

        self.session = requests.Session()

        if not username or not password:
            raise Exception("Cannot log in, need both username and password")

        # Get CSRF token for login
        # [todo] Find this properly with beautifulsoup or something
        resp = self.session.get(self.base_url + '/signin')
        match = re.search(r'input value="(.+?)" name="_csrf"', resp.text)
        if match:
            csrf_token = match.group(1)
        else:
            raise Exception("Couldn't get csrf token")

        headers = {
            'Referer': 'https://bank.simple.com/signin',
            'Origin': 'https://bank.simple.com'
        }
        auth = {
            'username': username,
            'password': password,
            '_csrf': csrf_token,
        }

        # log in
        resp = self.session.post('https://bank.simple.com/signin',
                                 headers=headers,
                                 data=auth)

        if resp.status_code not in range(200, 400) or 'form id="login"' in resp.text:
            # log in failed, clobber session
            print('failed to log in')
            self.session = None

        return self.session is not None

    @login_required
    def _get(self, url, params={}):
        """
        GETs a URL and checks the return stuff for validity
        """

        data = {}

        response = self.session.get(url)

        if response.status_code in range(500, 600):
            raise Exception("Got a status {} from {}".format(response.status_code, url))
        elif 'form id="login"' in response.text:
            raise Exception("Not logged in to Simple")

        try:
            data = json.loads(response.text)
        except:
            raise Exception("Unable to load JSON from {}".format(url))

        return data

    # Ugh, this is all too boiler-plate-y. Should find a more clever way.
    def transactions(self, start=0):
        """
        Grabs all of the tansactions since <start>
        where <start> is the number of seconds since the epoch
        """

        url = self.base_url + "/transactions/new_transactions?timestamp={}"
        url = url.format(start)

        # Get the transactions and wrap each one as a Transaction so that
        # we have a human-friendly str() available
        data = self._get(url)
        data['transactions'] = [Transaction(t) for t in data['transactions']]

        return data

    def balances(self):
        url = self.base_url + "/account/balances"

        data = self._get(url)

        for k, v in data.items():
            data[k] = v / 1000.0    # Convert to dollars

        return Balances(data)

    def goals(self, archived=True, completed=True):
        url = self.base_url + "/goals/data"

        return [Goal(x) for x in self._get(url)]

    def payments(self):
        url = self.base_url + "/payments/next_payments"

        return self._get(url)

    def card(self):
        url = self.base_url + "/card"

        return Card(self._get(url))


# Wrapper classes to provide a human-friendly __str__
class Transaction(dict):
    def __str__(self):
        amount = self['amounts']['amount'] / 10000.0
        tipped = self['amounts'].get('tip', 0.0) / 10000.0

        if self['bookkeeping_type'] == 'debit':
            humanized = 'Spent ${:.2f} at '.format(amount)
        else:
            humanized = 'Got ${:.2f} from '.format(amount)

        humanized += self['description']

        if tipped:
            humanized += ' (tipped ${:.2f})'.format(tipped)

        if self['is_hold']:
            humanized += ' *PENDING*'

        return humanized


class Goal(dict):
    def is_completed(self):
        completed = self['contributed_amount'] >= self['amount'] \
            or self['finish'] <= time.time() * 1000

        return completed

    def __str__(self):
        contributed = self['contributed_amount'] / 10000.0
        title_line = self['name'] + ' - ${:.2f}'.format(contributed)

        if not self.is_completed() and not self['archived']:
            target = self['target_amount'] / 10000.0
            daily_contribution = self.get('next_contribution', {}).get('amount', 0.0) / 10000.0

            title_line += ' / ${:.2f}'.format(target)

            if self['paused']:
                title_line += ' - PAUSED'
            elif not self['paused'] and daily_contribution:
                title_line += ' - Saving ${:.2f} per day'.format(daily_contribution)

            # build the progress bar
            finish_date = datetime.datetime.fromtimestamp(self['finish'] / 1000.0)

            if finish_date.year == datetime.datetime.now().year:
                progress_line_end = finish_date.strftime(' %b %d ')
            else:
                progress_line_end = finish_date.strftime(' %b %d, %Y ')

            bar_length = console_width({}) - len(progress_line_end) - 4
            percent_done = float(contributed) / target
            complete_length = int(bar_length * percent_done)
            incomplete_length = bar_length - complete_length

            bar = '  [' + '$' * complete_length + '.' * incomplete_length + ']'
            progress_line = bar + progress_line_end

            output = "\n" + title_line + "\n" + progress_line

        else:
            output = title_line

        return output


class Balances(dict):
    def __str__(self):
        output = ''

        # [todo] I think clint has some fancy columns stuff
        # [todo] use some fancy colors on the dollar amounts
        output += "Total:\t\t${:.2f}\n".format(self['total'])
        output += "Deposits:\t\${:.2f}\n".format(self['deposits'])
        output += "Bills:\t\t-${:.2f}\n".format(self['bills'])
        output += "Pending:\t\t-${:.2f}\n".format(self['pending'])
        output += "Goals\t\t-${:.2f}\n".format(self['goals'])

        output += "\nSafe to Spend:\t${:.2f}\n".format(self['save_to_spend'])

        return output


class Card(dict):
    def __str__(self):
        output = ''

        # [todo] I think clint has some fancy columns stuff
        output += "Name on card:\t" + self['customer_name'] + "\n"
        output += "Last four:\t\t" + self['indent'] + "\n"
        output += "Expiration:\t\t" + self['expiration_date'] + "\n"
        output += "Status:\t\t" + self['card_status'].capitalize() + "\n" 

        return output
