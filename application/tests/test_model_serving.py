"""
Tests for Model Serving and Live Prediction API.
Verifies health checks, single prediction, batch prediction, and metadata retrieval.
"""

import os
import tempfile
import pytest
from fastapi.testclient import TestClient

from application.src.schema_validator import CanonicalCompanyEntity
from application.src.train_model import train_and_evaluate_model
from application.src.serve_model import create_fastapi_app, CompanyPredictionRequest, PredictionServiceEngine

@pytest.fixture(scope="module")
def trained_model_dir():
    """Trains a quick model pipeline in a temporary directory for serving tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        entities = [
            CanonicalCompanyEntity(
                company_id=f"COMP-{i:04d}",
                canonical_name=f"Enterprise {i}",
                country="US" if i % 2 == 0 else "DE",
                founded_year=2000 + (i % 20),
                employee_count=50 + i * 10,
                industry_sector="Technology" if i % 3 == 0 else "Manufacturing",
                annual_revenue=float((50 + i * 10) * 250000)
            )
            for i in range(1, 60)
        ]
        train_and_evaluate_model(entities, output_model_dir=tmp_dir)
        yield tmp_dir

def test_prediction_service_engine(trained_model_dir):
    engine = PredictionServiceEngine(model_dir=trained_model_dir)
    assert engine.model is not None

    req = CompanyPredictionRequest(
        company_name="Unforeseen AI Labs",
        employee_count=120,
        founded_year=2016,
        industry_sector="Technology",
        country="US"
    )
    result = engine.predict_single(req)

    assert result["company_name"] == "Unforeseen AI Labs"
    assert result["predicted_annual_revenue_usd"] > 0.0
    assert result["firm_size_tier"] == "Medium Enterprise"
    assert "predicted_revenue_formatted" in result

def test_fastapi_endpoints(trained_model_dir):
    app = create_fastapi_app(model_dir=trained_model_dir)
    client = TestClient(app)

    # 1. Health check
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "HEALTHY"
    assert health_resp.json()["model_loaded"] is True

    # 2. Metadata check (including 10 assumptions)
    meta_resp = client.get("/metadata")
    assert meta_resp.status_code == 200
    meta_data = meta_resp.json()
    assert meta_data["status"] == "SUCCESS"
    assert len(meta_data["metadata"]["assumptions"]) == 10

    # 3. Single prediction
    pred_resp = client.post("/predict", json={
        "company_name": "Nordic Precision Robotics",
        "employee_count": 80,
        "founded_year": 2018,
        "industry_sector": "Manufacturing",
        "country": "NL"
    })
    assert pred_resp.status_code == 200
    body = pred_resp.json()
    assert body["company_name"] == "Nordic Precision Robotics"
    assert body["predicted_annual_revenue_usd"] > 0.0

    # 4. Batch prediction
    batch_resp = client.post("/batch-predict", json={
        "companies": [
            {
                "company_name": "Company Alpha",
                "employee_count": 40,
                "founded_year": 2020,
                "industry_sector": "Retail",
                "country": "GB"
            },
            {
                "company_name": "Company Beta",
                "employee_count": 500,
                "founded_year": 1995,
                "industry_sector": "Energy",
                "country": "US"
            }
        ]
    })
    assert batch_resp.status_code == 200
    batch_body = batch_resp.json()
    assert batch_body["count"] == 2
    assert len(batch_body["predictions"]) == 2

    # 5. Frontend HTML UI endpoint
    ui_resp = client.get("/")
    assert ui_resp.status_code == 200
    assert "text/html" in ui_resp.headers.get("content-type", "")
    assert "Ray AI Platform" in ui_resp.text

    # 6. Preset Data endpoint
    preset_resp = client.get("/api/preset-data?type=unforeseen")
    assert preset_resp.status_code == 200
    assert "Vendor_Legal_Name" in preset_resp.json()["csv_text"]

    # 7. Dynamic CSV Inspection endpoint
    sample_csv = (
        "Vendor_Company,Tax_Code,HQ_Country,Year_Est,Staff_Count,Gross_Sales\n"
        "Apex BioSystems,TAX-DE-8822,DE,2015,140,$35,000,000\n"
        "Nova Instruments,TAX-US-9911,US,2010,450,$110,000,000\n"
    )
    inspect_resp = client.post("/api/inspect-csv", json={
        "csv_text": sample_csv,
        "filename": "unforeseen_partner.csv"
    })
    assert inspect_resp.status_code == 200
    inspect_data = inspect_resp.json()
    assert inspect_data["total_rows"] == 2
    assert inspect_data["detected_concepts"]["name"] == "Vendor_Company"
    assert inspect_data["detected_concepts"]["tax_id"] == "Tax_Code"
    assert inspect_data["detected_concepts"]["revenue"] == "Gross_Sales"

    # 8. Dynamic Ingestion and Entity Resolution endpoint
    resolve_resp = client.post("/api/ingest-and-resolve", json={
        "csv_text": sample_csv,
        "filename": "unforeseen_partner.csv"
    })
    assert resolve_resp.status_code == 200
    resolve_data = resolve_resp.json()
    assert resolve_data["ingested_count"] == 2
    assert resolve_data["unique_canonical_count"] == 2

    # 9. Direct CSV Model Prediction endpoint
    predict_csv_resp = client.post("/api/predict-csv", json={
        "csv_text": sample_csv
    })
    assert predict_csv_resp.status_code == 200
    predict_csv_data = predict_csv_resp.json()
    assert predict_csv_data["prediction_count"] == 2
    assert predict_csv_data["mean_predicted_revenue"] > 0.0

    # 10. S3 Dry-Run Ingestion endpoint
    s3_resp = client.post("/api/upload-s3", json={
        "csv_text": sample_csv,
        "filename": "custom_feed.csv",
        "bucket": "demo-data-bucket",
        "dry_run": True,
        "auto_trigger": False
    })
    assert s3_resp.status_code == 200
    s3_data = s3_resp.json()
    assert s3_data["status"] == "DRY-RUN VALIDATION PASSED"
    assert "s3://demo-data-bucket/incoming/custom_feed.csv" in s3_data["s3_uri"]

    # 11. Event-Driven Pipeline Signal Trigger & Status
    trig_resp = client.post("/api/trigger-pipeline", json={
        "csv_text": sample_csv,
        "filename": "signal_event_feed.csv"
    })
    assert trig_resp.status_code == 200
    trig_data = trig_resp.json()
    assert trig_data["status"] == "SIGNAL_TRIGGERED"
    assert "job_id" in trig_data

    # Query Pipeline Status
    status_resp = client.get("/api/pipeline-status")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] in ["RUNNING", "SUCCESS", "PENDING"]
