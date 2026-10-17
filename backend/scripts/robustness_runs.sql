COPY (
 SELECT e.id AS experiment_id, e.batch_id, e.status, l.name AS layout_name, o.name AS order_list_name,
        o.order_amount, c.mover_amount, c.dispensing_time, c.time_limit, c.warmup, c.random_seed,
        (e.result->>'scheduled_cmax')::numeric AS scheduled_cmax,
        (e.result->>'routed_cmax')::numeric AS routed_cmax,
        (e.result->>'lower_bound_cmax')::numeric AS lower_bound_cmax,
        (e.result->>'routing_overhead_pct')::numeric AS routing_overhead_pct
 FROM experiments e JOIN configurations c ON c.id=e.configuration_id
      JOIN order_lists o ON o.id=e.order_list_id JOIN layouts l ON l.id=e.layout_id
 WHERE e.batch_id IN (15,16) ORDER BY e.batch_id, e.id
) TO STDOUT WITH CSV HEADER;
