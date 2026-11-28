import csv
import io
import zipfile
from collections import defaultdict


def rows(src):
    with zipfile.ZipFile(src.get("olist.zip")) as archive:

        def table(name):
            return list(
                csv.DictReader(
                    io.TextIOWrapper(
                        archive.open("olist_" + name + "_dataset.csv"), encoding="utf-8-sig"
                    )
                )
            )

        items = defaultdict(list)
        for r in table("order_items"):
            items[r["order_id"]].append(r)
        buyers = {r["customer_id"]: r["customer_state"] for r in table("customers")}
        sellers = {r["seller_id"]: r["seller_state"] for r in table("sellers")}
        categories = {
            r["product_id"]: r["product_category_name"] or "Unknown" for r in table("products")
        }
        for r in sorted(table("orders"), key=lambda v: v["order_id"]):
            records = items[r["order_id"]]
            if len(records) != 1:
                continue
            item = records[0]
            seller = item["seller_id"]
            issued = r["order_purchase_timestamp"][:10]
            estimated = r["order_estimated_delivery_date"][:10]
            delivered = r["order_delivered_customer_date"][:10]
            hand = r["order_delivered_carrier_date"]
            limit = item["shipping_limit_date"]
            late = int(delivered > estimated) if delivered and estimated else ""
            # A shipping limit is a timestamp; the customer promise is a calendar day.
            hand_late = int(hand > limit) if hand and limit else ""
            yield (
                r["order_id"],
                issued,
                issued[:7],
                seller,
                sellers[seller],
                buyers[r["customer_id"]],
                r["order_status"],
                hand_late,
                late,
                max(delivered, hand[:10])[:7],
                categories[item["product_id"]],
            )
