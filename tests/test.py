import importlib
import sys

modules = [
    'tests.test_async_storage',
    'tests.test_data_collector',
    'tests.test_kafka_streamer',
    'tests.test_metrics',
    'tests.test_mgm_client',
    'tests.test_processor',
    'tests.test_risk',
    'tests.test_s3_storage',
    'tests.test_satellite_client',
    'tests.test_services',
    'tests.test_sqlite_storage',
    'tests.test_visualize',
]

for m in modules:
    try:
        module = importlib.import_module(m)
        globals().update({k: v for k, v in module.__dict__.items() if k.startswith('test_')})
    except Exception as exc:  # pragma: no cover - optional deps
        print(f'Skipping {m}: {exc}', file=sys.stderr)
