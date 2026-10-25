import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from streamlit.testing.v1 import AppTest
at=AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=15).run()
assert not at.exception, at.exception
for page in ['Waste intake','Verify recovery','Energy market','Traceability','About','Overview']:
 at.sidebar.radio[0].set_value(page).run()
 assert not at.exception, (page,at.exception)
 print('PASS page:',page)
at.sidebar.radio[0].set_value('Waste intake').run()
at.button[0] # sidebar reset is first button
next(b for b in at.button if b.label == 'Register batch').click().run()
assert not at.exception
assert len(at.session_state['ecosystem']['deposits'])==4
at.sidebar.radio[0].set_value('Verify recovery').run()
at.number_input[0].set_value(30)
at.number_input[1].set_value(8)
next(b for b in at.button if b.label == 'Verify and issue rewards').click().run()
assert not at.exception
assert len(at.session_state['ecosystem']['processed'])==4
at.sidebar.radio[0].set_value('Energy market').run()
next(b for b in at.button if b.label == 'Settle trade').click().run()
assert not at.exception
assert len(at.session_state['ecosystem']['trades'])==1
print('PASS intake, processing, and trading interactions')
