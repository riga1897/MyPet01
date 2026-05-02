import shutil
import time

from django.db import connection, OperationalError
from django.http import JsonResponse
from django.views import View
from django.core.cache import cache


class HealthView(View):
    def get(self, request):
        checks: dict[str, str] = {}
        status = 200

        # Database
        try:
            connection.ensure_connection()
            checks["database"] = "ok"
        except OperationalError:
            checks["database"] = "error"
            status = 503

        # Cache / Redis
        try:
            key = f"health_check_{int(time.time())}"
            cache.set(key, "1", timeout=5)
            if cache.get(key) == "1":
                checks["cache"] = "ok"
            else:
                checks["cache"] = "error"
                status = 503
            cache.delete(key)
        except Exception:
            checks["cache"] = "error"
            status = 503

        # Disk
        try:
            usage = shutil.disk_usage("/")
            free_pct = (usage.free / usage.total) * 100
            checks["disk_free_pct"] = f"{free_pct:.1f}%"
            if free_pct < 10:
                checks["disk"] = "warning"
            else:
                checks["disk"] = "ok"
        except Exception:
            checks["disk"] = "error"

        return JsonResponse(
            {"status": "ok" if status == 200 else "degraded", "checks": checks},
            status=status,
        )
