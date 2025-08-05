
# Banksia

**Türkçe**: Banksia, başta orman yangınları olmak üzere çevresel tüm yangın risklerini hesaplamak, gözlemlemek ve haber vermek için bağımsız bir yazılımcı tarafından geliştirilen açık projedir. Amaç, en ücra yerleşim birimlerinde bile düşük gereksinimlerle çalışabilen bir sistem kurmaktır. Proje henüz tamamlanmamış olup katkılara açıktır. Lütfen etik ilkelere bağlı kalınız. Lisans "F.U.C.K. \u2014 Freedom Under Conditioned Knowledge" olarak adlandırılır.

**English**: Banksia is an independent effort to compute, monitor and alert wildfire risk across Turkey. It gathers weather data and satellite observations, trains machine learning models and serves results through a FastAPI backend with a Vue dashboard. The project is still evolving and contributions are welcome, provided privacy and personal data are respected. Licensed under **F.U.C.K. \u2014 Freedom Under Conditioned Knowledge**.
=======
# Turkey Fire Risk Detection System


This project collects weather data from the MGM API and stores it in a database. By default SQLite is used, but a TimescaleDB/PostgreSQL instance can be configured for large datasets. A FastAPI service exposes recent records and statistics, and a lightweight Vue dashboard visualizes the data.

Satellite fire observations from several sources can be fetched with helper functions:

- ``fetch_modis_data`` – NASA MODIS active fire data
- ``fetch_viirs_data`` – VIIRS high-resolution fire detections
- ``fetch_sentinel2_data`` – Sentinel‑2 burned area imagery
- ``fetch_effis_data`` – European Forest Fire Information System

These datasets can be merged with weather records for advanced ML-based risk prediction.

## Usage

- Collect data manually:

```bash
python data_collector.py --output weather_data --db-url postgres://user:pass@localhost/weather
```
If the output path is a directory, monthly archives like
`weather_2025_06.json` will be created inside it. This keeps files small
as the dataset grows.

Use the optional S3 flags to back up the JSON after each run:

```bash
python data_collector.py --output weather.json --s3-bucket my-bucket --s3-key weather/latest.json
```

Or run the lightweight script:

```bash
python weather_script.py
```

- Start the API server:

```bash
API_KEY=yourkey uvicorn fastapi_app:app --reload
```
- Connect to the websocket for real-time updates with `websocat`:

```bash
websocat ws://localhost:8000/ws/weather -E
```

- Open the dashboard at http://localhost:8000/dashboard/ after starting the API server. The static files live in the `frontend/` directory.

### Additional components

- Save to PostgreSQL by providing a database URL in `collector.postgres_storage`.
- Write metrics to InfluxDB using `collector.influx_storage`.
- Retrieve real-time updates through the `/ws/weather` websocket.
- `/api/data-range`, `/api/hourly-average`, and `/api/risk-score` endpoints provide
  more advanced queries.
- Set `SLACK_WEBHOOK` to receive alerts when risk levels exceed a threshold.
- Protect API endpoints by setting `API_KEY` and sending `X-API-Key` headers.
- Upload results to S3 using `--s3-bucket` and `--s3-key`.

The ``risk_analyzer`` module offers a basic scoring function and can train a ``RandomForestRegressor`` on historical data for predictive analytics. Weather
records now include ``wind_dir`` and ``condition`` fields for richer analysis.
### Visualize satellite risk correlation
Use `visualize.plot_brightness_vs_risk` to create a scatter plot linking MODIS brightness with computed risk scores.


## Asynchronous API

Set `ASYNC_DB=1` to enable asynchronous database access using `aiosqlite`. All API endpoints run non-blocking queries when this flag is active. The SQLite
database automatically creates an index on the `date` column to speed up range
queries as the dataset grows.

## Kubernetes deployment

The `k8s/` directory now provides a more complete setup for running the API on a
cluster. Environment variables are defined in a `ConfigMap`, secrets store the
API key, and a persistent volume keeps the SQLite database. A `HorizontalPodAutoscaler`
scales the deployment based on CPU usage.

Apply the manifests in the following order:

```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
```

## Model versioning

`dvc.yaml` defines a simple training stage. Run `dvc repro` to train a model and store the output in `models/model.joblib`.

## Microservices

Two lightweight FastAPI apps expose distinct functionality:

- `services/collector_service.py` provides a `/collect` endpoint to fetch the latest data and store it in the configured locations.
- `services/risk_service.py` exposes `/risk` which returns recent weather records with basic risk scores and `/risk-ml` which serves predictions from a trained model saved at `models/model.joblib` (override with `MODEL_PATH`).

Run them individually with `uvicorn`:

```bash
uvicorn services.collector_service:app --port 8001
uvicorn services.risk_service:app --port 8002
```

## Real-time streaming with Kafka

Use `streaming.kafka_streamer` to continuously push weather data to Kafka and consume it for storage.

```bash
python -m streaming.kafka_streamer stream_to_kafka --topic weather
```

Consume the stream and store records in SQLite:

```bash
python -m streaming.kafka_streamer consume_to_db --db weather.db --topic weather
```

## Monitoring

Prometheus metrics are exposed at `/metrics` when the API is running. Configure
Prometheus to scrape the service. A simple Grafana instance can read from the
Prometheus data source and display dashboards. Example Prometheus job:

```yaml
scrape_configs:
  - job_name: weather-api
    static_configs:
      - targets: ['localhost:8000']
```

Run Grafana with Docker and point it at the Prometheus endpoint:

```bash
docker run -p 3000:3000 grafana/grafana
```

Add a Prometheus data source at `http://localhost:9090` and import or create a
dashboard to visualize the counters.


## Backup strategy

Initialize Git LFS to track monthly archives and trained models:

```bash
git lfs install
git lfs track "backups/*" "models/*.joblib"
```

Run the collector with S3 options to upload each archive as well:

```bash
python data_collector.py --output backups/weather.json \
    --s3-bucket my-bucket --s3-key weather/latest.json
```

## Advanced hyperparameter tuning

The training pipeline can optimize RandomForest parameters with Optuna:

```bash
python train_model.py --tune --trials 30
```
<<

## License

This project is distributed under the **F.U.C.K.\u2014Freedom Under Conditioned Knowledge** license. See the `LICENSE` file for details.

