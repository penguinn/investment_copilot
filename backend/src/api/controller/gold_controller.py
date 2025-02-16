import logging
from typing import Dict

from asgiref.sync import async_to_sync
from django.http import JsonResponse

from ...service.gold_service import GoldService

logger = logging.getLogger(__name__)

# 创建服务实例
gold_service = GoldService()


def gold_index(request):
    """获取黄金指数"""
    try:
        # 定义需要获取的黄金指数
        gold_indices: Dict[str, Dict[str, str]] = {
            "AU9999": {"name": "沪金99.99"},
            "XAU": {"name": "伦敦金"},
        }

        # 使用服务类获取数据
        data = async_to_sync(gold_service.get_gold_data)(gold_indices)
        return JsonResponse({"code": 0, "data": data})
    except Exception as e:
        logger.error(f"Failed to get gold index: {str(e)}", exc_info=True)
        return JsonResponse(
            {"code": 1, "message": f"获取黄金指数失败: {str(e)}"}, status=500
        )
