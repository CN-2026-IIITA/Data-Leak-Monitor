from fastapi import APIRouter, Depends, Request, BackgroundTasks
from sqlalchemy.orm import Session
import json
import gzip

import models
import schemas
import auth
from database import get_db
from rules_engine import evaluate_traffic_batch
from enrichment import resolve_geo, resolve_domain
from logger import logger

router = APIRouter(prefix="/api/ingest", tags=["Ingestion"])

def background_enrich_and_detect(traffic_ids, devices_dicts):
    db = next(get_db())
    try:
        records = db.query(models.TrafficRecord).filter(models.TrafficRecord.id.in_(traffic_ids)).all()
        logger.info(f"Background: Processing {len(records)} records for enrichment+detection")
        new_traffic = []
        
        # 1. Enrich
        for t_model in records:
            if not t_model.domain or t_model.domain_source == "unknown":
                try:
                    resolved = resolve_domain(t_model.dest_ip)
                    if resolved and resolved != "unknown":
                        t_model.domain = resolved
                        t_model.domain_source = "rdns"
                except Exception as e:
                    logger.debug(f"Domain resolution failed for {t_model.dest_ip}: {e}")
                
            if not t_model.dest_country:
                try:
                    geo = resolve_geo(t_model.dest_ip)
                    t_model.dest_country = geo.get("country_code", "??")
                except Exception as e:
                    logger.debug(f"Geo resolution failed for {t_model.dest_ip}: {e}")
                
            t_dict = {c.name: getattr(t_model, c.name) for c in t_model.__table__.columns}
            new_traffic.append(t_dict)
            
        db.commit()
        
        # 2. Run Rules Engine
        logger.info(f"Background: Running rules engine on {len(new_traffic)} enriched records")
        generated_alerts = evaluate_traffic_batch(new_traffic, devices_dicts, db)
        logger.info(f"Background: Rules engine generated {len(generated_alerts)} alerts")
        for alert in generated_alerts:
            logger.info(f"Generated alert: [{alert.severity}] {alert.title}")
            
        if generated_alerts:
            for alert_obj in generated_alerts:
                mac = alert_obj.device_mac
                if not mac:
                    continue
                dev = db.query(models.Device).filter(models.Device.mac == mac).first()
                if dev:
                    dev.status = "online"  # Mark as active
        db.commit()
        logger.info(f"Background: Committed successfully. {len(generated_alerts)} alerts saved.")
    except Exception as e:
        import traceback
        logger.error(f"Background enrich/detect failed: {e}\n{traceback.format_exc()}")
    finally:
        db.close()

@router.post("")
async def ingest_data(request: Request, background_tasks: BackgroundTasks, api_key: models.APIKey = Depends(auth.verify_api_key), db: Session = Depends(get_db)):
    """Receives batched flow data from the Local Agent and runs the Detection Pipeline."""
    
    msg_id = request.headers.get("X-Message-ID")
    if msg_id:
        if db.query(models.ProcessedMessage).filter(models.ProcessedMessage.id == msg_id).first():
            logger.info(f"Ignored duplicate message: {msg_id}")
            return {"status": "ok", "msg": "Duplicate message ignored"}

    try:
        raw_body = await request.body()
        if request.headers.get("Content-Encoding") == "gzip":
            raw_body = gzip.decompress(raw_body)
        
        payload_data = json.loads(raw_body)
        payload = schemas.AgentPayload(**payload_data)
        
        # 1. Update/Create Devices (Anchored by MAC)
        for dev_in in payload.devices:
            if not dev_in.mac or dev_in.mac == "ff:ff:ff:ff:ff:ff":
                continue
            # Normalize MAC to lowercase to prevent case-sensitive duplicates
            dev_in.mac = dev_in.mac.lower()
            db_dev = db.query(models.Device).filter(models.Device.mac == dev_in.mac).first()
            if db_dev:
                db_dev.status = "online"
                db_dev.ip = dev_in.ip
                if dev_in.hostname and db_dev.hostname_source != "manual":
                    db_dev.hostname = dev_in.hostname
                    db_dev.hostname_source = dev_in.hostname_source
                current_ips = set(db_dev.ip_history or [])
                current_ips.update(dev_in.ip_history)
                db_dev.ip_history = list(current_ips)
            else:
                new_dev = models.Device(**dev_in.dict())
                db.add(new_dev)

        # 2. Fast Insert Traffic Records (without enrichment)
        traffic_ids = []
        for t_in in payload.traffic_records:
            t_dict = t_in.dict()
            # Normalize MAC references to lowercase
            if t_dict.get("device_mac"):
                t_dict["device_mac"] = t_dict["device_mac"].lower()
            if t_dict.get("src_mac"):
                t_dict["src_mac"] = t_dict["src_mac"].lower()
            if t_dict.get("dest_mac"):
                t_dict["dest_mac"] = t_dict["dest_mac"].lower()
            t_model = models.TrafficRecord(**t_dict)
            db.add(t_model)
            traffic_ids.append(t_model.id)

        # 3. Add any agent-side Alerts
        for a_in in payload.alerts:
            db.add(models.Alert(**a_in.dict()))

        # 4. Add any agent-side Anomalies
        for anom_in in payload.anomalies:
            db.add(models.Anomaly(**anom_in.dict()))

        # Mark message as processed
        if msg_id:
            db.add(models.ProcessedMessage(id=msg_id))

        db.commit()

        # Queue background task for slow enrichment and rule evaluation
        devices_dicts = [d.dict() for d in payload.devices]
        background_tasks.add_task(background_enrich_and_detect, traffic_ids, devices_dicts)

        # Broadcast to connected WebSocket clients
        try:
            if hasattr(request.app.state, "manager"):
                import json as json_mod
                await request.app.state.manager.broadcast(json_mod.dumps({
                    "type": "update",
                    "records": len(traffic_ids),
                    "alerts": len(payload.alerts),
                    "timestamp": __import__("time").time()
                }))
        except Exception as e:
            logger.warning(f"WebSocket broadcast failed: {e}")
        
        return {
            "status": "success",
            "ingested": True,
            "records": len(traffic_ids)
        }
        
    except Exception as e:
        import traceback
        logger.error(f"Ingest failed: {e}\n{traceback.format_exc()}")
        db.rollback()
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=500, content={"detail": str(e)})
