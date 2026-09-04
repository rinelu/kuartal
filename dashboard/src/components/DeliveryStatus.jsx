/**
 * Delivery status - dashboard.md §2. Channel, last-sent time,
 * opened/not opened, time-to-verdict.
 * TODO(dashboard owner): real layout + "delivery failed / retry" state
 * (flagged as a contract gap in kuartal/api/mock_data.py).
 *
 * @param {string} channel
 * @param {string} lastSent
 * @param {boolean} opened
 * @param {string} timeToVerdict
 */
export default function DeliveryStatus({ channel, lastSent, opened, timeToVerdict }) {
  return (
    <section className="kt-hairline kt-mono">
      <p>{channel} · sent {lastSent}</p>
      <p>{opened ? "Opened" : "Not opened"} · time-to-verdict {timeToVerdict}</p>
    </section>
  );
}
