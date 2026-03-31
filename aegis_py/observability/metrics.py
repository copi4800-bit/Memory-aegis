import logging
from .runtime import get_global_runtime_observability

# Configure logger for Aegis Sync
logger = logging.getLogger("aegis.sync.metrics")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

class SyncMetricsTracker:
    @staticmethod
    def record_sync_success(origin_node_id: str, payload_id: str, applied_count: int, skipped_count: int, conflicts_count: int):
        logger.info(f"[SYNC SUCCESS] Node={origin_node_id} | Payload={payload_id} | Applied={applied_count} | Skipped={skipped_count} | Conflicts={conflicts_count}")
        get_global_runtime_observability().observe(
            tool="sync_payload_apply",
            result="success",
            details={
                "origin_node_id": origin_node_id,
                "payload_id": payload_id,
                "applied_count": applied_count,
                "skipped_count": skipped_count,
                "conflicts_count": conflicts_count,
            },
        )
        
    @staticmethod
    def record_sync_failure(origin_node_id: str, payload_id: str, payload_size: int, error_msg: str):
        logger.error(f"[SYNC FAILURE] Node={origin_node_id} | Payload={payload_id} | Size={payload_size} | Error={error_msg}")
        get_global_runtime_observability().observe(
            tool="sync_payload_apply",
            result="error",
            error_code="sync_failure",
            details={
                "origin_node_id": origin_node_id,
                "payload_id": payload_id,
                "payload_size": payload_size,
                "error": error_msg,
            },
        )

    @staticmethod
    def log_sync_lag(origin_node_id: str, lag_seconds: float):
        if lag_seconds > 60:
            logger.warning(f"[SYNC LAG] Node={origin_node_id} is lagging by {lag_seconds:.2f} seconds")
        else:
            logger.info(f"[SYNC LAG] Node={origin_node_id} | Lag={lag_seconds:.2f}s")
        get_global_runtime_observability().observe(
            tool="sync_payload_lag",
            result="warning" if lag_seconds > 60 else "success",
            details={
                "origin_node_id": origin_node_id,
                "lag_seconds": round(float(lag_seconds), 3),
            },
        )
