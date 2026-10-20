from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload
from backend.auth import get_current_user, require_roles
from backend.database import get_db
from backend.models import Patient, Visit, LabResult, ProgressionLabel, Notification, User
from backend.schemas import PatientCreate, VisitCreate

router=APIRouter(tags=['Patients and visits'])
def patient_query(): return select(Patient).options(selectinload(Patient.visits).selectinload(Visit.lab_results))
def patient_to_dict(p:Patient,db:Session):
    label=db.scalar(select(ProgressionLabel).where(ProgressionLabel.patient_id==p.patient_id))
    return {'patient_id':p.patient_id,'full_name':p.full_name,'source_code':p.source_code,'source_patient_id':p.source_patient_id,
      'age_at_baseline':p.age_at_baseline,'gender':p.gender,'ihd':p.ihd,'cvd':p.cvd,'hypertension':p.hypertension,'diabetes':p.diabetes,'dyslipidemia':p.dyslipidemia,
      'baseline_sbp':p.baseline_sbp,'baseline_dbp':p.baseline_dbp,'baseline_bmi':p.baseline_bmi,'baseline_egfr':p.baseline_egfr,'baseline_hb':p.baseline_hb,'baseline_chol':p.baseline_chol,'baseline_tg':p.baseline_tg,'baseline_ldl':p.baseline_ldl,'baseline_hdl':p.baseline_hdl,'baseline_albuminuria':p.baseline_albuminuria,'raasi':p.raasi,'glp1ra':p.glp1ra,'sglt2i':p.sglt2i,'statin':p.statin,
      'latest_analysis':({'risk_level':'HIGH' if label.rapid_progression else 'LOW','probability':None,'target_definition':label.target_definition,'egfr_slope_ours':label.egfr_slope_ours} if label else None),
      'visits':[{'visit_id':v.visit_id,'visit_number':v.visit_number,'day_from_baseline':v.day_from_baseline,'visit_date':v.visit_date,'encounter_type':v.encounter_type,'lab_results':[{'lab_result_id':l.lab_result_id,'creatinine_mg_dl':l.creatinine_mg_dl,'egfr_ml_min_1_73m2':l.egfr_ml_min_1_73m2,'acr_mg_g':l.acr_mg_g,'sbp_mmhg':l.sbp_mmhg,'dbp_mmhg':l.dbp_mmhg,'hemoglobin_g_dl':l.hemoglobin_g_dl,'hba1c_percent':l.hba1c_percent,'glucose_mg_dl':l.glucose_mg_dl,'cholesterol_mg_dl':l.cholesterol_mg_dl,'triglycerides_mg_dl':l.triglycerides_mg_dl,'ldl_mg_dl':l.ldl_mg_dl,'hdl_mg_dl':l.hdl_mg_dl,'potassium_mmol_l':l.potassium_mmol_l,'sodium_mmol_l':l.sodium_mmol_l,'albumin_g_dl':l.albumin_g_dl,'data_source':l.data_source} for l in v.lab_results]} for v in sorted(p.visits,key=lambda x:(x.visit_date or date.min,x.visit_id))]}

@router.get('/patients')
def list_patients(search:str|None=None,source_code:str|None=None,limit:int=Query(200,ge=1,le=1000),offset:int=Query(0,ge=0),db:Session=Depends(get_db),user:User=Depends(require_roles('ADMIN','DOCTOR','DEO'))):
    q=patient_query().order_by(Patient.patient_id)
    if search: q=q.where(or_(Patient.patient_id.like(f'%{search}%'),Patient.full_name.like(f'%{search}%'),Patient.source_patient_id.like(f'%{search}%')))
    if source_code: q=q.where(Patient.source_code==source_code)
    rows=db.scalars(q.offset(offset).limit(limit)).unique().all()
    return {'items':[patient_to_dict(p,db) for p in rows],'count':len(rows),'limit':limit,'offset':offset}

@router.post('/patients',status_code=201)
def create_patient(payload:PatientCreate,db:Session=Depends(get_db),user:User=Depends(require_roles('ADMIN','DOCTOR','DEO'))):
    if db.get(Patient,payload.patient_id): raise HTTPException(status_code=409,detail='Patient ID already exists')
    existing=db.scalar(select(Patient).where(Patient.source_code==payload.source_code,Patient.source_patient_id==payload.source_patient_id))
    if existing: raise HTTPException(status_code=409,detail='This source code/source patient ID is already registered')
    data=payload.model_dump(); p=Patient(**data); db.add(p)
    try: db.commit()
    except Exception as exc: db.rollback(); raise HTTPException(status_code=409,detail='Could not save patient; check unique IDs and database schema') from exc
    return {'message':'Patient created','patient_id':p.patient_id}

@router.get('/patients/{patient_id}')
def get_patient(patient_id:str,db:Session=Depends(get_db),user:User=Depends(require_roles('ADMIN','DOCTOR','DEO'))):
    p=db.scalar(patient_query().where(Patient.patient_id==patient_id))
    if not p: raise HTTPException(status_code=404,detail='Patient not found')
    return patient_to_dict(p,db)

@router.put('/patients/{patient_id}')
def update_patient(patient_id:str,payload:PatientCreate,db:Session=Depends(get_db),user:User=Depends(require_roles('ADMIN','DOCTOR','DEO'))):
    p=db.get(Patient,patient_id)
    if not p: raise HTTPException(status_code=404,detail='Patient not found')
    if payload.patient_id!=patient_id: raise HTTPException(status_code=422,detail='Patient ID cannot be changed')
    for key,value in payload.model_dump().items(): setattr(p,key,value)
    try: db.commit()
    except Exception as exc: db.rollback(); raise HTTPException(status_code=409,detail='Could not save patient. Check duplicate source identifiers.') from exc
    return {'message':'Patient updated'}

@router.delete('/patients/{patient_id}',status_code=204)
def delete_patient(patient_id:str,db:Session=Depends(get_db),user:User=Depends(require_roles('ADMIN','DOCTOR'))):
    p=db.get(Patient,patient_id)
    if not p: raise HTTPException(status_code=404,detail='Patient not found')
    db.delete(p); db.commit(); return None

@router.post('/patients/{patient_id}/visits',status_code=201)
def add_visit(patient_id:str,payload:VisitCreate,db:Session=Depends(get_db),user:User=Depends(require_roles('ADMIN','DOCTOR','DEO'))):
    p=db.get(Patient,patient_id)
    if not p: raise HTTPException(status_code=404,detail='Patient not found')
    existing=db.scalar(select(Visit).where(Visit.patient_id==patient_id,Visit.visit_date==payload.visit_date))
    if existing: raise HTTPException(status_code=409,detail='A visit already exists on this date for this patient')
    first_date=min([v.visit_date for v in p.visits if v.visit_date] + [payload.visit_date])
    day_offset=(payload.visit_date-first_date).days
    # If an older visit arrives later, existing offsets must be preserved; unique day offset is based on the explicit date's first stored date.
    visit=Visit(patient_id=patient_id,visit_number=len(p.visits)+1,day_from_baseline=day_offset,visit_date=payload.visit_date,encounter_type=payload.encounter_type)
    db.add(visit); db.flush(); db.add(LabResult(visit_id=visit.visit_id,**payload.labs.model_dump(exclude_unset=True)))
    try:
      db.commit()
    except Exception as exc:
      db.rollback(); raise HTTPException(status_code=409,detail='Could not save visit/lab record. This date/day may already exist.') from exc
    db.refresh(visit)
    return {'message':'Visit and laboratory record created','visit_id':visit.visit_id}

@router.get('/visits')
def list_visits(patient_id:str|None=None,db:Session=Depends(get_db),user:User=Depends(require_roles('ADMIN','DOCTOR','DEO'))):
    q=select(Visit).options(selectinload(Visit.patient),selectinload(Visit.lab_results)).order_by(Visit.visit_date.desc())
    if patient_id: q=q.where(Visit.patient_id==patient_id)
    rows=db.scalars(q.limit(2000)).unique().all()
    return {'items':[{'visit_id':v.visit_id,'patient_id':v.patient_id,'patient_name':v.patient.full_name or v.patient.patient_id,'visit_number':v.visit_number,'visit_date':v.visit_date,'day_from_baseline':v.day_from_baseline,'encounter_type':v.encounter_type,'lab_results':[{'egfr_ml_min_1_73m2':l.egfr_ml_min_1_73m2,'creatinine_mg_dl':l.creatinine_mg_dl,'acr_mg_g':l.acr_mg_g,'sbp_mmhg':l.sbp_mmhg,'dbp_mmhg':l.dbp_mmhg,'hemoglobin_g_dl':l.hemoglobin_g_dl,'potassium_mmol_l':l.potassium_mmol_l} for l in v.lab_results]} for v in rows]}
