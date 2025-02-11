from contextlib import closing
from copy import copy
import grpc
from pathlib import Path
import socket
import subprocess
import threading

from .bip32 import BIP32_PRIME
from .bitcoin import is_mweb_address
from . import constants
from .transaction import PartialTransaction, Transaction, TxInput, TxOutpoint
from .mwebd_pb2 import CoinswapRequest, CreateRequest, StatusRequest
from .mwebd_pb2_grpc import RpcStub

data_dir = None
lock = threading.Lock()
port = None
process = None

def set_data_dir(dir):
    global data_dir
    with lock:
        data_dir = Path(dir) / 'mweb'
        data_dir.mkdir(exist_ok=True)

def start_if_needed():
    global port, process
    with lock:
        if process: return
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.bind(('127.0.0.1', 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            port = s.getsockname()[1]
        process = subprocess.Popen([Path(__file__).parent.parent.resolve() / 'mwebd',
            '-c', constants.net.NET_NAME, '-d', data_dir, '-l', f'127.0.0.1:{port}'])
        while True:
            try:
                stub().Status(StatusRequest())
                break
            except: ()

def stub():
    start_if_needed()
    return RpcStub(grpc.insecure_channel(f'127.0.0.1:{port}'))

def stub_async():
    start_if_needed()
    return RpcStub(grpc.aio.insecure_channel(f'127.0.0.1:{port}'))

def create(tx, keystore, fee_estimator, *, dry_run = True, password = None):
    scan_secret = spend_secret = bytes(32)
    if hasattr(keystore, 'scan_secret') and keystore.scan_secret:
        scan_secret = bytes.fromhex(keystore.scan_secret)
    if not dry_run and keystore.may_have_password():
        spend_secret, _ = keystore.get_private_key([BIP32_PRIME + 1], password)
    txins = []
    for txin in tx.inputs():
        if txin.mweb_output_id:
            op = f'{txin.mweb_output_id}:{txin.mweb_address_index}'
            txin = TxInput(prevout=TxOutpoint.from_str(op))
        txins.append(txin)
    tx._inputs, txins = txins, tx._inputs
    raw_tx = bytes.fromhex(tx.serialize_to_network(include_sigs=False))
    tx._inputs = txins
    while True:
        resp = stub().Create(CreateRequest(raw_tx=raw_tx,
            scan_secret=scan_secret, spend_secret=spend_secret,
            fee_rate_per_kb=fee_estimator(1000), dry_run=dry_run))
        if resp.raw_tx: break
        keystore.exchange_with_mwebd()
    if resp.raw_tx == raw_tx: return tx, 0
    tx2 = PartialTransaction.from_tx(Transaction(resp.raw_tx))
    for i, txin in enumerate(tx2.inputs()):
        tx2.inputs()[i] = copy(next(x for x in tx.inputs() if str(x.prevout) == str(txin.prevout)))
    mweb_input = tx.input_value() - tx2.input_value()
    expected_pegin = max(0, tx.output_value() - mweb_input)
    fee_increase = tx2.output_value() - expected_pegin
    if expected_pegin: fee_increase += fee_estimator(41)
    for txout in tx.outputs():
        if is_mweb_address(txout.address) and not dry_run:
            txout.mweb_output_id = resp.output_id.pop(0)
    tx2._original_tx = tx
    return tx2, fee_increase

def coinswap(utxo, keystore, password):
    if not keystore.scan_secret: return
    if not keystore.may_have_password(): return
    scan_secret = bytes.fromhex(keystore.scan_secret)
    spend_secret, _ = keystore.get_private_key([BIP32_PRIME + 1], password)
    resp = stub().Coinswap(CoinswapRequest(
        scan_secret=scan_secret, spend_secret=spend_secret,
        output_id=utxo.mweb_output_id, addr_index=utxo.mweb_address_index))
    return resp.output_id
