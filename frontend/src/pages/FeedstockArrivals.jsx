import { useEffect, useState } from "react";
import { fetchFeedstockDeliveries, fetchFeedstocks } from "../api/client";
import DataTable from "../components/DataTable";

export default function FeedstockArrivals() {
  const [deliveries, setDeliveries] = useState([]);
  const [feedstocks, setFeedstocks] = useState([]);

  useEffect(() => {
    fetchFeedstocks().then(setFeedstocks);
    fetchFeedstockDeliveries().then(setDeliveries);
  }, []);

  const feedstockName = (id) => feedstocks.find((f) => f.id === id)?.name ?? id;

  const columns = [
    { key: "arrival_date", label: "Arrival Date" },
    { key: "feedstock_id", label: "Feedstock", render: (r) => feedstockName(r.feedstock_id) },
    { key: "quantity_tonnes", label: "Quantity (t)" },
    { key: "certificate_number", label: "PoS / Certificate #" },
    { key: "origin_country", label: "Origin" },
  ];

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Feedstock Arrivals</h2>
      <DataTable columns={columns} rows={deliveries} emptyMessage="No feedstock deliveries recorded yet." />
    </div>
  );
}
