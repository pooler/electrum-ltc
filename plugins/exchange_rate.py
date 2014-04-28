from PyQt4.QtGui import *
from PyQt4.QtCore import *

import datetime
import decimal
import httplib
import json
import threading
import time
import re
from decimal import Decimal
from electrum_doge.plugins import BasePlugin
from electrum_doge.i18n import _
from electrum_doge_gui.qt.util import *
from electrum_doge_gui.qt.amountedit import AmountEdit


EXCHANGES = ["PayBee",
             "Prelude"]


class Exchanger(threading.Thread):

    def __init__(self, parent):
        threading.Thread.__init__(self)
        self.daemon = True
        self.parent = parent
        self.quote_currencies = None
        self.lock = threading.Lock()
        self.query_rates = threading.Event()
        self.use_exchange = self.parent.config.get('use_exchange', "PayBee")
        self.parent.exchanges = EXCHANGES
        self.parent.currencies = ["EUR","GBP","USD"]
        self.parent.win.emit(SIGNAL("refresh_exchanges_combo()"))
        self.parent.win.emit(SIGNAL("refresh_currencies_combo()"))
        self.is_running = False

    def get_json(self, site, get_string):
        try:
            connection = httplib.HTTPSConnection(site)
            connection.request("GET", get_string)
        except Exception:
            raise
        resp = connection.getresponse()
        if resp.reason == httplib.responses[httplib.NOT_FOUND]:
            raise
        try:
            json_resp = json.loads(resp.read())
        except Exception:
            raise
        return json_resp


    def exchange(self, btc_amount, quote_currency):
        with self.lock:
            if self.quote_currencies is None:
                return None
            quote_currencies = self.quote_currencies.copy()
        if quote_currency not in quote_currencies:
            return None
        return btc_amount * decimal.Decimal(str(quote_currencies[quote_currency]))

    def stop(self):
        self.is_running = False

    def update_rate(self):
        self.use_exchange = self.parent.config.get('use_exchange', "PayBee")
        update_rates = {
            "PayBee": self.update_pb,
            "Prelude": self.update_pl,
        }
        try:
            update_rates[self.use_exchange]()
        except KeyError:
            return

    def run(self):
        self.is_running = True
        while self.is_running:
            self.query_rates.clear()
            self.update_rate()
            self.query_rates.wait(150)


    def update_pl(self):
        try:
            jsonresp = self.get_json('api.prelude.io', "/last/DOGE")
        except Exception:
            return
        try:
            jsonresp_usd = self.get_json('api.prelude.io', "/last-usd/DOGE")
        except Exception:
            return
        quote_currencies = {"BTC": 0.0, "USD": 0.0}
        try:
            btcprice = jsonresp["last"]
            usdprice = jsonresp_usd["last"]
            quote_currencies["BTC"] = decimal.Decimal(str(btcprice))
            quote_currencies["USD"] = decimal.Decimal(str(usdprice))
            with self.lock:
                self.quote_currencies = quote_currencies
        except KeyError:
            pass
        self.parent.set_currencies(quote_currencies)

    def update_pb(self):
        quote_currencies = {}
        try:
            jsonresp = self.get_json('api.payb.ee', "/rates/crypto.DOGE")
        except Exception:
            return
        for cur in jsonresp:
            try:
                quote_currencies[cur["code"]] = cur["rate"]
            except Exception:
                pass
        with self.lock:
            self.quote_currencies = quote_currencies
        self.parent.set_currencies(quote_currencies)


    def get_currencies(self):
        return [] if self.quote_currencies == None else sorted(self.quote_currencies.keys())


class Plugin(BasePlugin):

    def fullname(self):
        return "Exchange rates"

    def description(self):
        return """exchange rates, retrieved from PayBee and other market exchanges"""


    def __init__(self,a,b):
        BasePlugin.__init__(self,a,b)
        self.currencies = [self.config.get('currency', "EUR")]
        self.exchanges = [self.config.get('use_exchange', "PayBee")]

    def init(self):
        self.win = self.gui.main_window
        self.win.connect(self.win, SIGNAL("refresh_currencies()"), self.win.update_status)
        self.btc_rate = Decimal("0.0")
        # Do price discovery
        self.exchanger = Exchanger(self)
        self.exchanger.start()
        self.gui.exchanger = self.exchanger #

    def set_currencies(self, currency_options):
        self.currencies = sorted(currency_options)
        self.win.emit(SIGNAL("refresh_currencies()"))
        self.win.emit(SIGNAL("refresh_currencies_combo()"))

    def get_fiat_balance_text(self, btc_balance, r):
        # return balance as: 1.23 USD
        r[0] = self.create_fiat_balance_text(Decimal(btc_balance) / 100000000)

    def get_fiat_price_text(self, r):
        # return BTC price as: 123.45 USD
        r[0] = self.create_fiat_balance_text(1)
        quote = r[0]
        if quote:
            r[0] = "%s"%quote

    def get_fiat_status_text(self, btc_balance, r2):
        # return status as:   (1.23 USD)    1 BTC~123.45 USD
        text = ""
        r = {}
        self.get_fiat_price_text(r)
        quote = r.get(0)
        if quote:
            price_text = "1 Doge~%s"%quote
            fiat_currency = quote[-3:]
            btc_price = self.btc_rate
            fiat_balance = Decimal(btc_price) * (Decimal(btc_balance)/100000000)
            balance_text = "(%.2f %s)" % (fiat_balance,fiat_currency)
            text = "  " + balance_text + "     " + price_text + " "
        r2[0] = text

    def create_fiat_balance_text(self, btc_balance):
        quote_currency = self.config.get("currency", "EUR")
        self.exchanger.use_exchange = self.config.get("use_exchange", "PayBee")
        cur_rate = self.exchanger.exchange(Decimal("1.0"), quote_currency)
        if cur_rate is None:
            quote_text = ""
        else:
            quote_balance = btc_balance * Decimal(cur_rate)
            self.btc_rate = cur_rate
            quote_text = "%.2f %s" % (quote_balance, quote_currency)
        return quote_text

    def load_wallet(self, wallet):
        self.wallet = wallet


    def requires_settings(self):
        return True


    def toggle(self):
        out = BasePlugin.toggle(self)
        self.win.update_status()
        self.win.tabs.removeTab(1)
        new_send_tab = self.gui.main_window.create_send_tab()
        self.win.tabs.insertTab(1, new_send_tab, _('Send'))
        return out


    def close(self):
        self.exchanger.stop()

    def settings_widget(self, window):
        return EnterButton(_('Settings'), self.settings_dialog)

    def settings_dialog(self):
        d = QDialog()
        d.setWindowTitle("Settings")
        layout = QGridLayout(d)
        layout.addWidget(QLabel(_('Exchange rate API: ')), 0, 0)
        layout.addWidget(QLabel(_('Currency: ')), 1, 0)
        combo = QComboBox()
        combo_ex = QComboBox()
        ok_button = QPushButton(_("OK"))

        def on_change(x):
            try:
                cur_request = str(self.currencies[x])
            except Exception:
                return
            if cur_request != self.config.get('currency', "EUR"):
                self.config.set_key('currency', cur_request, True)
                self.win.update_status()
                try:
                    self.fiat_button
                except:
                    pass
                else:
                    self.fiat_button.setText(cur_request)

        def on_change_ex(x):
            cur_request = str(self.exchanges[x])
            if cur_request != self.config.get('use_exchange', "PayBee"):
                self.config.set_key('use_exchange', cur_request, True)
                self.currencies = []
                combo.clear()
                self.exchanger.query_rates.set()
                cur_currency = self.config.get('currency', "EUR")
                set_currencies(combo)
                self.win.update_status()

        def set_currencies(combo):
            current_currency = self.config.get('currency', "EUR")
            try:
                combo.clear()
            except Exception:
                return
            combo.addItems(self.currencies)
            try:
                index = self.currencies.index(current_currency)
            except Exception:
                index = 0
            combo.setCurrentIndex(index)

        def set_exchanges(combo_ex):
            try:
                combo_ex.clear()
            except Exception:
                return
            combo_ex.addItems(self.exchanges)
            try:
                index = self.exchanges.index(self.config.get('use_exchange', "PayBee"))
            except Exception:
                index = 0
            combo_ex.setCurrentIndex(index)

        def ok_clicked():
            d.accept();

        set_exchanges(combo_ex)
        set_currencies(combo)
        combo.currentIndexChanged.connect(on_change)
        combo_ex.currentIndexChanged.connect(on_change_ex)
        combo.connect(self.win, SIGNAL('refresh_currencies_combo()'), lambda: set_currencies(combo))
        combo_ex.connect(d, SIGNAL('refresh_exchanges_combo()'), lambda: set_exchanges(combo_ex))
        ok_button.clicked.connect(lambda: ok_clicked())
        layout.addWidget(combo,1,1)
        layout.addWidget(combo_ex,0,1)
        layout.addWidget(ok_button,3,1)

        if d.exec_():
            return True
        else:
            return False

    def fiat_unit(self):
        quote_currency = self.config.get("currency", "???")
        return quote_currency

    def fiat_dialog(self):
        if not self.config.get('use_exchange_rate'):
          self.gui.main_window.show_message(_("To use this feature, first enable the exchange rate plugin."))
          return

        if not self.gui.main_window.network.is_connected():
          self.gui.main_window.show_message(_("To use this feature, you must have a network connection."))
          return

        quote_currency = self.fiat_unit()

        d = QDialog(self.gui.main_window)
        d.setWindowTitle("Fiat")
        vbox = QVBoxLayout(d)
        text = "Amount to Send in " + quote_currency
        vbox.addWidget(QLabel(_(text)+':'))

        grid = QGridLayout()
        fiat_e = AmountEdit(self.fiat_unit)
        grid.addWidget(fiat_e, 1, 0)

        r = {}
        self.get_fiat_price_text(r)
        quote = r.get(0)
        if quote:
          text = "1 Doge~%s"%quote
          grid.addWidget(QLabel(_(text)), 4, 0, 3, 0)
        else:
            self.gui.main_window.show_message(_("Exchange rate not available.  Please check your network connection."))
            return

        vbox.addLayout(grid)
        vbox.addLayout(ok_cancel_buttons(d))

        if not d.exec_():
            return

        fiat = str(fiat_e.text())

        if str(fiat) == "" or str(fiat) == ".":
            fiat = "0"

        quote = quote[:-4]
        btcamount = Decimal(fiat) / Decimal(quote)
        if str(self.gui.main_window.base_unit()) == "MDoge":
            btcamount = btcamount / 1000000
        if str(self.gui.main_window.base_unit()) == "KDoge":
            btcamount = btcamount / 1000
        quote = "%.8f"%btcamount
        self.gui.main_window.amount_e.setText( quote )

    def exchange_rate_button(self, grid):
        quote_currency = self.config.get("currency", "EUR")
        self.fiat_button = EnterButton(_(quote_currency), self.fiat_dialog)
        grid.addWidget(self.fiat_button, 4, 3, Qt.AlignHCenter)
