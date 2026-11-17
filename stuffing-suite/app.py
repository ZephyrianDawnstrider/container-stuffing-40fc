"""Consolidated Streamlit entrypoint; legacy backups are never imported."""
import io
import zipfile
import json
from datetime import date
from pathlib import Path
import pandas as pd
import streamlit as st
from planner import allocate

st.set_page_config(page_title='Stuffing Suite', layout='wide')
st.title('Stuffing Suite')
st.caption('Plan shipment allocations across editable equipment and rate scenarios.')
st.warning('Weight/volume allocation only, not 3D packing or a guaranteed fit. Confirm vehicle, route, axle/road limits, stacking and load securing before dispatch.')
profiles = json.loads((Path(__file__).parent / 'config/equipment.json').read_text())
st.info('Each equipment selection is a separate scenario. Switching equipment resets its working inputs and rate edits; download the current plan before switching. Nothing is saved between sessions.')
profile = st.selectbox('Equipment', profiles, format_func=lambda p: p['name'])
st.caption(f"{profile['status']} · Source: {profile['source']} · Checked: {profile['checked'] or 'not verified'}")
a,b = st.columns(2)
max_kg = a.number_input('Working payload (kg)', min_value=1.0, value=float(profile['payload_kg']), key='kg_'+profile['id'])
max_m3 = b.number_input('Working volume (m³)', min_value=0.01, value=float(profile['volume_m3']), key='m3_'+profile['id'])
st.caption('Published reference maxima are not guaranteed usable space. Reduce working limits for the actual cargo and allocated equipment.')

st.subheader('Route and pricing')
a,b,c = st.columns(3)
origin = a.text_input('Origin')
destination = b.text_input('Destination')
ship_date = c.date_input('Shipment date', value=date.today())
st.info('No universal freight average is defensible without a lane, date and service. Enter a carrier quote or contract rate below. Missing, expired or ambiguous prices stay UNPRICED, never zero. Historical amounts are preserved in backups, not represented as current market rates.')
columns=['min_kg','max_kg','min_m3','max_m3','amount','currency','basis','origin','destination','valid_from','valid_until','source','included_charges']
initial = pd.DataFrame({k:pd.Series(dtype='float64' if k in columns[:5] else 'str') for k in columns})
with st.expander('Editable rate table (optional)'):
    st.caption('Prices apply only to the selected equipment scenario. Use nonoverlapping bands; boundary overlaps are flagged. Basis: per trip, per tonne, or per m³. Date format: YYYY-MM-DD. Add all included charges and disclose exclusions in source/notes.')
    rates = st.data_editor(initial, num_rows='dynamic', key='rates_'+profile['id'], hide_index=True,
        column_config={'basis':st.column_config.SelectboxColumn(options=['per trip','per tonne','per m³'])})

st.subheader('Jobs')
st.caption('Input weights are kg, volume is m³. Priority is a positive relative score (default 1). Uploaded files stay in this session; nothing is written to a database.')
example='job_id,weight_kg,volume_m3,priority\nDEMO-001,2500,9,1\nDEMO-002,4000,12,2\nDEMO-003,1800,6,1\n'
st.download_button('Download synthetic CSV template', example, 'stuffing_template.csv', 'text/csv')
upload = st.file_uploader('Upload CSV or XLSX (up to 5 MB, 500 jobs)', type=['csv','xlsx'])
use_demo = st.checkbox('Use synthetic demo jobs', value=upload is None)
try:
    if upload is not None and not use_demo:
        if upload.size > 5*1024*1024:
            raise ValueError('File exceeds 5 MB')
        raw = upload.getvalue()
        if upload.name.lower().endswith('.xlsx'):
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                if sum(item.file_size for item in archive.infolist()) > 20*1024*1024:
                    raise ValueError('Expanded spreadsheet exceeds 20 MB')
        data = pd.read_excel(io.BytesIO(raw)) if upload.name.lower().endswith('.xlsx') else pd.read_csv(io.BytesIO(raw))
    elif use_demo:
        data = pd.read_csv(io.StringIO(example))
    else:
        data = None
    if data is not None:
        if len(data)>500:
            raise ValueError('Limit is 500 jobs per run')
        if len(data.columns)<3:
            raise ValueError('Need job ID, weight and volume columns')
        mapped={}
        for label,target,aliases in [('Job ID','job_id',['job_id','job no','job no.']),('Weight (kg)','weight_kg',['weight_kg','weight']),('Volume (m³)','volume_m3',['volume_m3','cbm'])]:
            options=list(data.columns)
            default=next((i for i,x in enumerate(options) if str(x).lower() in aliases),0)
            mapped[target]=st.selectbox(label+' column',options,index=default,key=target)
        if len(set(mapped.values())) != 3:
            raise ValueError('Choose distinct job, weight and volume columns')
        jobs=pd.DataFrame({k:data[v] for k,v in mapped.items()})
        jobs['priority']=data['priority'] if 'priority' in data.columns else 1.0
        jobs=st.data_editor(jobs,hide_index=True,key='jobs')
        # Recompute on reruns: never show results from obsolete inputs.
        if st.button('Plan loads',type='primary'):
            with st.spinner('Allocating jobs…'):
                result=allocate(jobs.to_dict('records'),max_kg,max_m3,rates.to_dict('records'),ship_date.isoformat(),origin,destination)
            st.success(f"{len(result['loads'])} loads · {len(result['unassigned'])} unassigned jobs")
            st.caption('Sequential capacity-constrained allocation prioritizes weighted utilization. Not a global minimum-cost or minimum-vehicle solution. Unpriced loads remain physically allocated.')
            for i,load in enumerate(result['loads'],1):
                st.subheader(f'Load {i}')
                st.write(f"{load['weight_kg']:,.1f} kg ({load['weight_kg']/max_kg:.1%}) · {load['volume_m3']:,.2f} m³ ({load['volume_m3']/max_m3:.1%})")
                st.write(load['price'])
                st.caption(load['solver_status'])
                st.dataframe(load['jobs'],hide_index=True)
            if result['unassigned']:
                st.warning('Unassigned jobs are included in the export with reasons.')
                st.dataframe(result['unassigned'])
            report={'equipment':profile,'working_payload_kg':max_kg,'working_volume_m3':max_m3,'origin':origin,'destination':destination,'shipment_date':ship_date.isoformat(),'rates':rates.to_dict('records'),'result':result}
            st.download_button('Download plan and assumptions (JSON)',json.dumps(report,indent=2,allow_nan=False),'stuffing_plan.json','application/json')
except (ValueError,KeyError,TypeError,zipfile.BadZipFile) as exc:
    st.error(str(exc))
