import json
import pandas as pd
import streamlit as st
from model import STREAMS, PARTICIPANTS, initial_state, deposit, process, trade, verify

st.set_page_config(page_title='AgriLoop | Circular resource exchange', page_icon='🌱', layout='wide')
st.markdown('''<style>
.stApp {background: #f7f9f6;} h1,h2,h3 {color:#183e32;}
[data-testid="stMetric"] {background:white;border:1px solid #dce6dc;border-radius:12px;padding:18px;}
[data-testid="stSidebar"] {background:#eaf1e9;}
</style>''', unsafe_allow_html=True)
if 'ecosystem' not in st.session_state:
    st.session_state.ecosystem = initial_state()
s = st.session_state.ecosystem
with st.sidebar:
    st.markdown('## 🌱 AgriLoop')
    st.caption('CIRCULAR RESOURCE EXCHANGE')
    page = st.radio('Workspace', ['Overview', 'Waste intake', 'Verify recovery', 'Energy market', 'Traceability', 'About'])
    st.divider()
    st.caption('Research prototype · session-local data')
    st.caption('1 E-Coin = 1 verified kWh\n\nR-Coins = recovered kg × purity')
    if st.button('Reset demo', width='stretch'):
        st.session_state.ecosystem = initial_state()
        st.rerun()

st.title(page)
st.caption('From separated waste to traceable resources and local energy.')
st.info('Simulation only: manually entered verification, demo credits, and a local hash-linked ledger. No live IoT, blockchain, utility settlement, or certified EPR/carbon credits.')

def show_table(rows):
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, width='stretch')
    else:
        st.caption('No records yet.')

if page == 'Overview':
    a,b,c,d = st.columns(4)
    a.metric('Waste received', f'{sum(x["mass_kg"] for x in s["deposits"]):,.1f} kg')
    b.metric('Material recovered', f'{sum(x["recovered_kg"] for x in s["processed"]):,.1f} kg')
    c.metric('Verified generation', f'{sum(x["verified_kwh"] for x in s["processed"]):,.1f} kWh')
    d.metric('Ledger events', len(s['ledger']))
    left,right = st.columns([1.6,1])
    with left:
        st.subheader('Waste streams')
        frame = pd.DataFrame(s['deposits'])
        st.bar_chart(frame.groupby('stream')['mass_kg'].sum(), color='#2b8062')
    with right:
        st.subheader('Resource journey')
        st.markdown('**01 · Receive**\n\nRecord sorted waste and collection readiness.\n\n**02 · Verify**\n\nConfirm recovered mass and metered generation.\n\n**03 · Exchange**\n\nTransfer energy balances and demo credit.')
    st.subheader('Participant wallets')
    show_table([dict(participant=k, E_Coins=v['E'], R_Coins=v['R'], demo_credit=v['cash']) for k,v in s['wallets'].items()])
    st.subheader('Latest activity')
    show_table([dict(event=x['event'], time=x['timestamp'], block=x['index']) for x in s['ledger'][-5:][::-1]])

elif page == 'Waste intake':
    st.subheader('Register a waste batch')
    with st.form('intake', clear_on_submit=True):
        a,b = st.columns(2)
        owner = a.selectbox('Participant', PARTICIPANTS)
        stream = b.selectbox('Waste stream', STREAMS)
        mass = a.number_input('Input mass (kg)', min_value=0.1, max_value=100000., value=100., step=1.)
        fill = b.slider('Smart bin fill (%)', 0, 100, 70)
        st.caption('At 80% fill, the batch is marked ready for collection. Intake alone issues no tokens.')
        submitted = st.form_submit_button('Register batch', type='primary')
    if submitted:
        try:
            batch = deposit(s, owner, stream, mass, fill)
            st.success(f'{batch} registered. '+('Collection threshold reached.' if fill >= 80 else 'Below collection threshold.'))
        except ValueError as exc: st.error(str(exc))
    st.subheader('Intake register')
    show_table(s['deposits'])

elif page == 'Verify recovery':
    st.subheader('Confirm processing outputs')
    st.caption('Verification is an operator simulation. No hardware authenticity checks are performed.')
    pending = [x for x in s['deposits'] if x['status'] != 'Verified']
    if not pending:
        st.success('All batches processed. Register a new batch in Waste intake.')
    else:
        selected = st.selectbox('Pending batch', [x['id'] for x in pending])
        row = next(x for x in pending if x['id'] == selected)
        st.write(f'**{row["stream"]}** · {row["mass_kg"]:,.1f} kg · {row["owner"]}')
        with st.form('verify'):
            a,b,c = st.columns(3)
            recovered = a.number_input('Recovered material (kg)', min_value=0., max_value=float(row['mass_kg']), value=0.)
            energy = b.number_input('Verified exported electricity (kWh)', min_value=0., value=0., disabled=row['stream']=='E-waste')
            purity = c.slider('Material purity (%)', 0, 100, 95)
            submitted = st.form_submit_button('Verify and issue rewards', type='primary')
        if submitted:
            try:
                process(s, selected, recovered, 0. if row['stream']=='E-waste' else energy, purity)
                st.rerun()
            except ValueError as exc: st.error(str(exc))
    show_table(s['processed'])

elif page == 'Energy market':
    st.subheader('Settle a bilateral demo trade')
    st.caption('Transfers existing E-Coins; no new energy is minted. This prototype does not implement an auction or physical power delivery.')
    with st.form('trade'):
        a,b = st.columns(2)
        seller = a.selectbox('Seller', PARTICIPANTS, index=0)
        buyer = b.selectbox('Buyer', PARTICIPANTS, index=3)
        energy = a.number_input('Energy (kWh / E-Coins)', min_value=0.1, value=5., step=0.1)
        price = b.number_input('Demo credit per kWh', min_value=0.01, value=0.30, step=0.01)
        submitted = st.form_submit_button('Settle trade', type='primary')
    if submitted:
        try:
            trade(s, seller, buyer, energy, price)
            st.success(f'Transferred {energy:.2f} E-Coins for {energy*price:.2f} demo credits.')
        except ValueError as exc: st.error(str(exc))
    show_table([dict(participant=k, **v) for k,v in s['wallets'].items()])
    st.subheader('Trade history')
    show_table(s['trades'])

elif page == 'Traceability':
    st.subheader('Audit the event chain')
    if verify(s['ledger']): st.success('Chain integrity verified: all event hashes and previous-hash links match.')
    else: st.error('Chain integrity check failed.')
    st.caption('Hash-linking detects edits relative to this in-memory chain; it does not establish distributed consensus or prove physical sensor readings.')
    event = st.selectbox('Event filter', ['All'] + sorted({x['event'] for x in s['ledger']}))
    rows = [x for x in s['ledger'] if event=='All' or x['event']==event]
    show_table([dict(block=x['index'], event=x['event'], timestamp=x['timestamp'], hash=x['hash']) for x in rows])
    if rows:
        chosen = st.selectbox('Inspect block', [x['index'] for x in rows])
        st.json(next(x for x in rows if x['index']==chosen))
    st.download_button('Export full ledger (JSON)', json.dumps(s['ledger'], indent=2), 'agriloop-ledger.json', 'application/json')
    st.download_button('Export waste register (CSV)', pd.DataFrame(s['deposits']).to_csv(index=False), 'waste-register.csv', 'text/csv')

else:
    st.subheader('A practical companion to the conceptual paper')
    st.write('Based on “A Blockchain-Agri-IoT Conceptual Framework for Multi-Stream Waste Recycling, Traceability, and Peer-to-Peer Transactive Energy Markets” by Shirley anak Rufus, UNIMAS.')
    st.markdown('''The demonstration covers agricultural biomass, MSW plastics, and e-waste. Tokens are issued after processing output is entered: **one E-Coin per verified kWh**, and **one R-Coin per purity-adjusted recovered kg**. These are illustrative accounting units, not currencies or compliance certificates.

All participants are fictional. Each browser session starts with three sample batches and 100 demo credits per participant. Data stays in Streamlit session memory and is lost when the session ends or the server restarts. Export the ledger before closing if needed.

A production system would need authenticated operators, calibrated and signed telemetry, durable storage, a consortium ledger, market rules, independently validated conversion factors, and safeguards against duplicate recovery claims. Carbon credit issuance and EPR redemption are outside this demo.''')
