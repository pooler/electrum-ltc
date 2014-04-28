#!/usr/bin/python

# python setup.py sdist --format=zip,gztar

from setuptools import setup
import os
import sys
import platform
import imp


version = imp.load_source('version', 'lib/version.py')
util = imp.load_source('version', 'lib/util.py')

if sys.version_info[:3] < (2, 6, 0):
    sys.exit("Error: Electrum requires Python version >= 2.6.0...")

usr_share = '/usr/share'
if not os.access(usr_share, os.W_OK):
    usr_share = os.getenv("XDG_DATA_HOME", os.path.join(os.getenv("HOME"), ".local", "share"))

data_files = []
if (len(sys.argv) > 1 and (sys.argv[1] == "sdist")) or (platform.system() != 'Windows' and platform.system() != 'Darwin'):
    print "Including all files"
    data_files += [
        (os.path.join(usr_share, 'applications/'), ['electrum-doge.desktop']),
        (os.path.join(usr_share, 'app-install', 'icons/'), ['icons/electrum-doge.png'])
    ]
    if not os.path.exists('locale'):
        os.mkdir('locale')
    for lang in os.listdir('locale'):
        if os.path.exists('locale/%s/LC_MESSAGES/electrum.mo' % lang):
            data_files.append((os.path.join(usr_share, 'locale/%s/LC_MESSAGES' % lang), ['locale/%s/LC_MESSAGES/electrum.mo' % lang]))

appdata_dir = util.appdata_dir()
if not os.access(appdata_dir, os.W_OK):
    appdata_dir = os.path.join(usr_share, "electrum-doge")

data_files += [
    (appdata_dir, ["data/README"]),
    (os.path.join(appdata_dir, "cleanlook"), [
        "data/cleanlook/name.cfg",
        "data/cleanlook/style.css"
    ]),
    (os.path.join(appdata_dir, "sahara"), [
        "data/sahara/name.cfg",
        "data/sahara/style.css"
    ]),
    (os.path.join(appdata_dir, "minidoge"), [
        "data/minidoge/name.cfg",
        "data/minidoge/style.css"
    ]),
    (os.path.join(appdata_dir, "dark"), [
        "data/dark/name.cfg",
        "data/dark/style.css"
    ])
]


setup(
    name="Electrum-Doge",
    version=version.ELECTRUM_VERSION,
    install_requires=['slowaes', 'ecdsa>=0.9', 'ltc_scrypt'],
    package_dir={
        'electrum_doge': 'lib',
        'electrum_doge_gui': 'gui',
        'electrum_doge_plugins': 'plugins',
    },
    scripts=['electrum-doge'],
    data_files=data_files,
    py_modules=[
        'electrum_doge.account',
        'electrum_doge.bitcoin',
        'electrum_doge.blockchain',
        'electrum_doge.bmp',
        'electrum_doge.commands',
        'electrum_doge.daemon',
        'electrum_doge.i18n',
        'electrum_doge.interface',
        'electrum_doge.mnemonic',
        'electrum_doge.msqr',
        'electrum_doge.network',
        'electrum_doge.plugins',
        'electrum_doge.pyqrnative',
        'electrum_doge.scrypt',
        'electrum_doge.simple_config',
        'electrum_doge.socks',
        'electrum_doge.transaction',
        'electrum_doge.util',
        'electrum_doge.verifier',
        'electrum_doge.version',
        'electrum_doge.wallet',
        'electrum_doge.wallet_bitkey',
        'electrum_doge_gui.gtk',
        'electrum_doge_gui.qt.__init__',
        'electrum_doge_gui.qt.amountedit',
        'electrum_doge_gui.qt.console',
        'electrum_doge_gui.qt.history_widget',
        'electrum_doge_gui.qt.icons_rc',
        'electrum_doge_gui.qt.installwizard',
        'electrum_doge_gui.qt.lite_window',
        'electrum_doge_gui.qt.main_window',
        'electrum_doge_gui.qt.network_dialog',
        'electrum_doge_gui.qt.password_dialog',
        'electrum_doge_gui.qt.qrcodewidget',
        'electrum_doge_gui.qt.receiving_widget',
        'electrum_doge_gui.qt.seed_dialog',
        'electrum_doge_gui.qt.transaction_dialog',
        'electrum_doge_gui.qt.util',
        'electrum_doge_gui.qt.version_getter',
        'electrum_doge_gui.stdio',
        'electrum_doge_gui.text',
        'electrum_doge_plugins.aliases',
        'electrum_doge_plugins.exchange_rate',
        'electrum_doge_plugins.labels',
        'electrum_doge_plugins.pointofsale',
        'electrum_doge_plugins.qrscanner',
        'electrum_doge_plugins.virtualkeyboard',
    ],
    description="Lightweight Dogecoin Wallet",
    author="paybee",
    author_email="paybee@github",
    license="GNU GPLv3",
    url="http://electrum-doge.org",
    long_description="""Lightweight Dogecoin Wallet"""
)
