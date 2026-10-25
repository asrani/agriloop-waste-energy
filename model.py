"""Session-local simulation; no blockchain, metering, or real payment integration."""
from datetime import datetime, timezone
import hashlib
import json
import math

STREAMS = ('Agricultural biomass', 'MSW plastics', 'E-waste')
PARTICIPANTS = ('Farm cooperative', 'Community recycler', 'Recovery hub', 'Neighbourhood buyer')

def digest(block):
    payload = {k: v for k, v in block.items() if k != 'hash'}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def append(state, event, payload):
    block = dict(index=len(state['ledger']) + 1,
                 timestamp=datetime.now(timezone.utc).isoformat(), event=event,
                 payload=payload, previous_hash=state['ledger'][-1]['hash'] if state['ledger'] else '0' * 64)
    block['hash'] = digest(block)
    state['ledger'].append(block)

def verify(ledger):
    previous = '0' * 64
    for index, block in enumerate(ledger, 1):
        if block['index'] != index or block['previous_hash'] != previous or block['hash'] != digest(block):
            return False
        previous = block['hash']
    return True

def initial_state():
    state = dict(ledger=[], deposits=[], processed=[], trades=[],
                 wallets={name: {'E': 0., 'R': 0., 'cash': 100.} for name in PARTICIPANTS})
    for owner, stream, mass, recovered, energy in [
        (PARTICIPANTS[0], STREAMS[0], 240., 70., 86.),
        (PARTICIPANTS[1], STREAMS[1], 85., 61., 0.),
        (PARTICIPANTS[2], STREAMS[2], 42., 19., 0.)]:
        deposit(state, owner, stream, mass, 92)
        process(state, state['deposits'][-1]['id'], recovered, energy, 95)
    return state

def number(value, minimum=0):
    if not isinstance(value, (int, float)) or not math.isfinite(value) or value < minimum:
        raise ValueError('Enter a finite, non-negative number.')

def deposit(state, owner, stream, mass, fill):
    number(mass); number(fill)
    if mass <= 0 or fill > 100 or owner not in state['wallets'] or stream not in STREAMS:
        raise ValueError('Check the participant, stream, mass, and fill level.')
    row = dict(id=f'W-{len(state["deposits"])+1:04d}', owner=owner, stream=stream,
               mass_kg=float(mass), fill_pct=fill, status='Awaiting recovery verification')
    state['deposits'].append(row)
    append(state, 'Waste received', row.copy())
    return row['id']

def process(state, deposit_id, recovered, energy, purity):
    number(recovered); number(energy); number(purity)
    row = next((d for d in state['deposits'] if d['id'] == deposit_id), None)
    if not row or row['status'] == 'Verified':
        raise ValueError('Select an unprocessed waste batch; duplicate minting is blocked.')
    if recovered > row['mass_kg'] or purity > 100:
        raise ValueError('Recovered mass cannot exceed input mass; purity must be 0–100%.')
    if row['stream'] == 'E-waste' and energy > 0:
        raise ValueError('This demo routes e-waste to material recovery only.')
    reward = dict(deposit_id=deposit_id, owner=row['owner'], recovered_kg=float(recovered),
                  verified_kwh=float(energy), purity_pct=purity,
                  e_coins=float(energy), r_coins=round(recovered * purity / 100, 6))
    state['wallets'][row['owner']]['E'] += reward['e_coins']
    state['wallets'][row['owner']]['R'] += reward['r_coins']
    state['processed'].append(reward)
    row['status'] = 'Verified'
    append(state, 'Recovery verified and rewards minted', reward.copy())

def trade(state, seller, buyer, energy, price):
    number(energy); number(price)
    if seller == buyer or seller not in state['wallets'] or buyer not in state['wallets']:
        raise ValueError('Choose two different participants.')
    if energy <= 0 or price <= 0:
        raise ValueError('Energy and unit price must be greater than zero.')
    cost = round(energy * price, 6)
    if state['wallets'][seller]['E'] < energy:
        raise ValueError('Seller has insufficient E-Coins.')
    if state['wallets'][buyer]['cash'] < cost:
        raise ValueError('Buyer has insufficient demo credit.')
    state['wallets'][seller]['E'] -= energy
    state['wallets'][buyer]['E'] += energy
    state['wallets'][seller]['cash'] += cost
    state['wallets'][buyer]['cash'] -= cost
    row = dict(seller=seller, buyer=buyer, energy_kwh=energy, price_per_kwh=price, demo_credit=cost)
    state['trades'].append(row)
    append(state, 'P2P energy transfer', row.copy())
