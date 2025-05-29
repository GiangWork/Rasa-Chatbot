from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import requests
import urllib3
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)  # Hoặc logging.ERROR nếu muốn ít log hơn

load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ActionSearchProduct(Action):
    def name(self) -> Text:
        return "action_search_product"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        category_entity = next(tracker.get_latest_entity_values("category"), None)
        product_name_entity = next(tracker.get_latest_entity_values("product_name"), None)
        supplier_entity = next(tracker.get_latest_entity_values("supplier"), None)
        price_from_entity = next(tracker.get_latest_entity_values("price_from"), None)
        price_to_entity = next(tracker.get_latest_entity_values("price_to"), None)

        def parse_price(p_str):
            try:
                return int(p_str) * 1000  # vì người dùng nói 'ngàn'
            except ValueError:
                return None

        price_from = parse_price(price_from_entity) if price_from_entity else None
        price_to = parse_price(price_to_entity) if price_to_entity else None

        def fetch_all_products(api_url: str):
            if not api_url:
                logger.error("[ERROR] PRODUCT_API_URL chưa được cấu hình hoặc không hợp lệ.")
                return None
    
            all_items = []
            current_page = 1
            while True:
                try:
                    url = f"{api_url}?pageIndex={current_page}&pageSize=8"
                    response = requests.get(url, verify=False)
                    response.raise_for_status()
                    data = response.json()
                    items = data["data"]["items"]
                    all_items.extend(items)
                    if current_page >= data["data"]["totalPages"]:
                        break
                    current_page += 1
                except requests.exceptions.RequestException as e:
                    logger.error(f"Lỗi khi gọi API trang {current_page}: {e}")
                    break
            
            return all_items

        products = fetch_all_products(os.getenv('PRODUCT_API_URL'))

        if not products:
            dispatcher.utter_message(text="Mình không lấy được dữ liệu sản phẩm lúc này, bạn vui lòng thử lại sau nhé.")
            return []

        def format_product_details(p):
            id = p.get("id", "00000000-0000-0000-0000-000000000000")
            name = p.get("name", "Không rõ")
            price = p.get("price", 0)
            discount = p.get("discountRate", 0)
            rating = p.get("ratings", 0)
            supplier = p.get("supplierName", "Không rõ")
            
            # Tìm ảnh thumbnail
            image_url = None
            for img in p.get("images", []):
                if img.get("thumbnail"):
                    image_url = img.get("imageUrl")
                    break
            
            if discount > 0:
                price_text = f"{price:,.0f}đ (-{discount}%)"
            else:
                price_text = f"{price:,.0f}đ"

            detail = (
                f"""<b>Tên:</b> <a href="/Product/ProductDetail/{id}" class="text-decoration-none text-dark">{name}</a><br>"""
                f"<b>Giá:</b> {price_text}<br>"
                f"<b>Đánh giá:</b> {rating} sao<br>"
                f"<b>Nhà cung cấp:</b> {supplier}<br>"
            )

            # Nếu có ảnh, thêm vào dưới dạng markdown
            if image_url:
                detail += f"""<div class="d-flex justify-content-center"><img src="{image_url}" alt="ảnh sản phẩm" style="max-width:200px;"></div><br>"""

            return detail

        # ===== 1. Tìm theo tên sản phẩm cụ thể =====
        if product_name_entity:
            matched_products = [
                p for p in products if product_name_entity.lower() in p.get("name", "").lower()
            ]
            if matched_products:
                in_stock = [p for p in matched_products if p.get("stock", 0) > 0]
                out_of_stock = [p for p in matched_products if p.get("stock", 0) == 0]

                if in_stock:
                    messages = [format_product_details(p) for p in in_stock[:3]]
                    dispatcher.utter_message(text="Mình tìm thấy sản phẩm sau ạ:\n\n" + "\n\n".join(messages))
                elif out_of_stock:
                    dispatcher.utter_message(text=f"Dạ sản phẩm '{product_name_entity}' bên mình hiện đang hết hàng ạ.")
                return []

        # ===== 2. Tìm theo danh mục hoặc nhà cung cấp =====
        matched_products = products
        if category_entity:
            matched_products = [
                p for p in matched_products if category_entity.lower() in p.get("categoryName", "").lower()
            ]
        if supplier_entity:
            matched_products = [
                p for p in matched_products if supplier_entity.lower() in p.get("supplierName", "").lower()
            ]

        # ===== 3. Lọc theo khoảng giá =====
        if price_from is not None:
            matched_products = [p for p in matched_products if p.get("price", 0) >= price_from]
        if price_to is not None:
            matched_products = [p for p in matched_products if p.get("price", 0) <= price_to]

        # Lọc sản phẩm còn hàng
        matched_products = [p for p in matched_products if p.get("stock", 0) > 0]

        if not matched_products:
            dispatcher.utter_message(text="Dạ rất tiếc là bên mình không có sản phẩm nào như vậy ạ.")
            return []

        # ===== 3. Gợi ý theo điểm số =====
        def calculate_score(p):
            price = p.get("price", 0)
            discount = p.get("discountRate", 0)
            ratings = p.get("ratings", 0)
            reviews = p.get("reviews", 0)

            w_price = -0.3
            w_discount = 0.2
            w_ratings = 0.4
            w_reviews = 0.1

            score = (
                w_price * price +
                w_discount * discount +
                w_ratings * ratings * 20 +
                w_reviews * reviews
            )
            return score

        matched_products = sorted(matched_products, key=calculate_score, reverse=True)
        selected = matched_products[:3]
        messages = [format_product_details(p) for p in selected]

        dispatcher.utter_message(text="Mình xin gợi ý cho bạn những sản phẩm sau ạ:\n\n" + "\n\n".join(messages))
        return []
