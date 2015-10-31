# Simple API wrapper

# These URLs were gleaned from using the website

import datetime
import json
import re
import time

import click
import requests
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
        self.headers = {'User-Agent': 'Simple CLI v0.0.2 (https://github.com/nickpegg/simple-cli)'}
        self.session = None
        self.base_url = "https://bank.simple.com"
        self.api_base_url = self.base_url + '/api'

    def login(self, username, password):
        """
        Logs the user in. Returns True if successful.
        """

        self.session = requests.Session()

        if not username or not password:
            raise Exception("Cannot log in, need both username and password")

        # Get CSRF token for login
        # [todo] Find this properly with beautifulsoup or something
        resp = self.session.get(self.base_url + '/signin', headers=self.headers)
        match = re.search(r'input value="(.+?)" name="_csrf"', resp.text)
        if match:
            csrf_token = match.group(1)
        else:
            raise Exception("Couldn't get csrf token")

        auth = {
            'username': username,
            'password': password,
            '_csrf': csrf_token,
        }

        # log in
        resp = self.session.post('https://bank.simple.com/signin',
                                 headers=self.headers,
                                 data=auth)

        if resp.status_code not in range(200, 400) or 'form id="login"' in resp.text:
            self.session = None     # log in failed, clobber session

        return self.session is not None

    @login_required
    def _get(self, url, params={}):
        """
        GETs a URL and checks the return stuff for validity
        """

        data = {}

        response = self.session.get(url, headers=self.headers)

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

        url = self.api_base_url + "/transactions/new_transactions?timestamp={}"
        url = url.format(start)

        # Get the transactions and wrap each one as a Transaction so that
        # we have a human-friendly str() available
        data = self._get(url)
        data['transactions'] = [Transaction(t) for t in data['transactions']]

        return data

    def balances(self):
        url = self.api_base_url + "/account/balances"

        data = self._get(url)

        for k, v in data.items():
            data[k] = v / 10000.0    # Convert to dollars

        return Balances(data)

    def goals(self, archived=True, completed=True):
        url = self.api_base_url + "/goals/data"

        return [Goal(x) for x in self._get(url)]

    def payments(self):
        url = self.api_base_url + "/payments/next_payments"
        data = self._get(url)

        return [Payment(x) for x in data]

    def card(self):
        url = self.api_base_url + "/card"

        return Card(self._get(url))


# Wrapper classes to provide a human-friendly __str__
class Transaction(dict):
    def __str__(self):
        amount = self['amounts']['amount'] / 10000.0
        tipped = self['amounts'].get('tip', 0.0) / 10000.0

        if self['bookkeeping_type'] == 'debit':
            humanized = 'Spent '
            humanized += click.style('${:.2f}'.format(amount), fg='red')
            humanized += ' at '
        else:
            humanized = 'Got '
            humanized += click.style('${:.2f}'.format(amount), fg='green')
            humanized += ' from '

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
        output += "Total:\t\t${:.2f}\n".format(self['total'])
        output += "Deposits:\t${:.2f}\n".format(self['deposits'])
        output += "Bills:\t\t-${:.2f}\n".format(self['bills'])
        output += "Pending:\t-${:.2f}\n".format(self['pending'])
        output += "Goals\t\t-${:.2f}\n".format(self['goals'])


        output += "\nSafe-to-Spend:\t"
        if self['safe_to_spend'] <= 0.0:
            color = 'red'
        else:
            color = 'green'
        output += click.style("${:.2f}\n".format(self['safe_to_spend']), fg=color, bold=True)

        return output


class Payment(dict):
    def __str__(self):
        output = 'Sending ${:.2f} to {}, arriving by {}'
        amount = self['amount'] / 100.0

        return output.format(amount,
                             self['contact']['contact_name'],
                             self['arrive_by'])


class Card(dict):
    def __str__(self):
        output = ''

        status = self['card_status'].capitalize()
        if status == 'Suspended':
            status = click.style(status, fg='red', bold=True)

        # [todo] I think clint has some fancy columns stuff
        output += "Name on card:\t" + self['customer_name'] + "\n"
        output += "Last four:\t" + self['indent'] + "\n"
        output += "Expiration:\t" + self['expiration_date'] + "\n"
        output += "Status:\t\t" + status + "\n"

        return output
